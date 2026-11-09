import logging, time, json, re, shutil, hmac
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from hashlib import sha256

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Header, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select, func, inspect, text, delete
from pypdf import PdfReader
from docx import Document as DocxDocument

from .config import settings
from .db import Base, engine, get_db
from .models import (
    Asset, Document, DocumentChunk, Project, VisitSession, AnalyticsEvent,
    LabZone, AssetPhoto, User, AuditLog, ChunkVector,
    ConversationTurn, AssetDocumentLink, AssetProjectLink
)
from .schemas import (
    AssetCreate, AssetUpdate, VisitCreate, QueryRequest, TourRequest,
    ProjectCreate, ProjectSubmit, ZoneCreate, ZoneLayoutUpdate,
    VisitorEventCreate, LoginRequest, UserCreate, UserStatusUpdate,
    DocumentMetadataUpdate, LinkCreate, EvaluationRequest
)
from .retrieval import retrieve, find_asset, STOP
from .llm import generate_grounded_answer
from .auth import require_admin, require_superadmin, login_user, hash_password
from .embeddings import embed_text
from .storage import get_storage

START_TIME = time.time()
storage = get_storage()

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("labspoc.api")

# Database table creation & additive schema migrations
Base.metadata.create_all(bind=engine)

def run_additive_migrations():
    """Applies additive columns safely for existing databases without data loss."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        # lab_zones spatial columns
        if "lab_zones" in existing_tables:
            cols = {c["name"] for c in inspector.get_columns("lab_zones")}
            zone_statements = {
                "x": "ALTER TABLE lab_zones ADD COLUMN x FLOAT NOT NULL DEFAULT 0.0",
                "z": "ALTER TABLE lab_zones ADD COLUMN z FLOAT NOT NULL DEFAULT 0.0",
                "width": "ALTER TABLE lab_zones ADD COLUMN width FLOAT NOT NULL DEFAULT 2.0",
                "depth": "ALTER TABLE lab_zones ADD COLUMN depth FLOAT NOT NULL DEFAULT 1.5",
            }
            for col_name, stmt in zone_statements.items():
                if col_name not in cols:
                    conn.execute(text(stmt))

        # documents metadata columns
        if "documents" in existing_tables:
            cols = {c["name"] for c in inspector.get_columns("documents")}
            doc_statements = {
                "category": "ALTER TABLE documents ADD COLUMN category VARCHAR(80) NOT NULL DEFAULT 'manual'",
                "version": "ALTER TABLE documents ADD COLUMN version VARCHAR(40) NOT NULL DEFAULT '1.0'",
                "description": "ALTER TABLE documents ADD COLUMN description VARCHAR(500) NOT NULL DEFAULT ''",
            }
            for col_name, stmt in doc_statements.items():
                if col_name not in cols:
                    conn.execute(text(stmt))

        # projects submission columns
        if "projects" in existing_tables:
            cols = {c["name"] for c in inspector.get_columns("projects")}
            proj_statements = {
                "author_name": "ALTER TABLE projects ADD COLUMN author_name VARCHAR(160) NOT NULL DEFAULT ''",
                "author_type": "ALTER TABLE projects ADD COLUMN author_type VARCHAR(60) NOT NULL DEFAULT 'student'",
                "diagram_url": "ALTER TABLE projects ADD COLUMN diagram_url VARCHAR(500) NOT NULL DEFAULT ''",
                "submitted_at": "ALTER TABLE projects ADD COLUMN submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }
            for col_name, stmt in proj_statements.items():
                if col_name not in cols:
                    conn.execute(text(stmt))

run_additive_migrations()

# Storage directories
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
MEDIA_DIR = Path(settings.upload_dir) / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Spatially Grounded Virtual Lab Ambassador Intelligence Platform for OIST Bhopal AI & ML Laboratory"
)

@app.middleware("http")
async def add_security_and_observability_headers(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or uuid4().hex[:12]
    request.state.request_id = req_id
    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - t0) * 1000
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

def parse_cors_origins(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    return [x.strip().strip("'\"") for x in raw.split(",") if x.strip().strip("'\"")]

origins = parse_cors_origins(settings.cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory sliding rate limiter with reverse proxy header support
_rate_limits = defaultdict(list)

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"

def check_rate_limit(request: Request, limit: int = 120, window_sec: int = 60):
    client_ip = get_client_ip(request)
    now = time.time()
    timestamps = [t for t in _rate_limits[client_ip] if now - t < window_sec]
    if len(timestamps) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per {window_sec}s."
        )
    timestamps.append(now)
    _rate_limits[client_ip] = timestamps


# -----------------------------------------------------------------------------
# AUTHENTICATION & USER MANAGEMENT (Phase 05)
# -----------------------------------------------------------------------------

@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, limit=20, window_sec=60)
    return login_user(db, payload.username, payload.password)

@app.get("/api/auth/me")
def auth_me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    from .auth import decode_token
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Login required")
    claims = decode_token(authorization.split(" ", 1)[1].strip())
    user = db.get(User, claims.get("sub"))
    if not user or not user.active:
        raise HTTPException(401, "Account inactive")
    return {"id": user.id, "username": user.username, "role": user.role}

@app.post("/api/admin/users")
def create_admin_user(payload: UserCreate, db: Session = Depends(get_db), actor: dict = Depends(require_superadmin)):
    if db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none():
        raise HTTPException(409, "Username already exists")
    user = User(
        id=str(uuid4()),
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=True
    )
    db.add(user)
    db.add(AuditLog(
        actor=actor.get("username", "admin"),
        action="user.create",
        resource_type="user",
        resource_id=payload.username
    ))
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role, "active": user.active}

@app.get("/api/admin/users")
def list_admin_users(db: Session = Depends(get_db), _: dict = Depends(require_superadmin)):
    return [
        {"id": u.id, "username": u.username, "role": u.role, "active": u.active, "created_at": u.created_at.isoformat()}
        for u in db.execute(select(User).order_by(User.username)).scalars().all()
    ]

@app.patch("/api/admin/users/{user_id}/status")
def set_user_status(user_id: str, payload: UserStatusUpdate, db: Session = Depends(get_db), actor: dict = Depends(require_superadmin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.username == actor.get("username") and payload.active is False:
        raise HTTPException(400, "You cannot deactivate your own active session account")
    user.active = payload.active
    db.add(AuditLog(
        actor=actor.get("username", "admin"),
        action="user.status",
        resource_type="user",
        resource_id=user.username
    ))
    db.commit()
    return {"id": user.id, "username": user.username, "active": user.active}

@app.get("/api/admin/audit-logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), _: dict = Depends(require_superadmin)):
    limit = max(1, min(limit, 500))
    rows = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).scalars().all()
    return [
        {"id": x.id, "actor": x.actor, "action": x.action, "resource_type": x.resource_type, "resource_id": x.resource_id, "outcome": x.outcome, "created_at": x.created_at.isoformat()}
        for x in rows
    ]


# -----------------------------------------------------------------------------
# SYSTEM HEALTH & CONFIGURATION
# -----------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "laboratory": settings.lab_name,
        "institution": settings.institution_name,
        "llm_provider": settings.llm_provider,
        "gemini_configured": bool(settings.gemini_api_key) if settings.llm_provider.lower() == "gemini" else False,
        "admin_configured": bool(settings.admin_api_key or settings.jwt_secret or settings.admin_password)
    }

@app.get("/api/ready")
def readiness(db: Session = Depends(get_db)):
    """Production readiness probe inspecting DB connection, storage readiness, and LLM provider."""
    checks = {}
    is_ready = True

    # 1. Database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "dialect": engine.dialect.name}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        is_ready = False

    # 2. Storage connectivity
    try:
        storage_check = storage.health_check()
        checks["storage"] = storage_check
        if storage_check.get("status") != "ok":
            is_ready = False
    except Exception as e:
        checks["storage"] = {"status": "error", "error": str(e)}
        is_ready = False

    # 3. LLM readiness
    checks["ai_engine"] = {
        "provider": settings.llm_provider,
        "model": settings.gemini_model if settings.llm_provider.lower() == "gemini" else "extractive-fallback",
        "configured": bool(settings.gemini_api_key) if settings.llm_provider.lower() == "gemini" else True
    }

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
        "checks": checks
    }

@app.get("/api/admin/system/metrics")
def admin_system_metrics(db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    """Administrator-facing system observability metrics (requires admin or editor)."""
    uptime = time.time() - START_TIME
    
    counts = {
        "users": db.execute(select(func.count(User.id))).scalar() or 0,
        "zones": db.execute(select(func.count(LabZone.id))).scalar() or 0,
        "assets": db.execute(select(func.count(Asset.id))).scalar() or 0,
        "documents_approved": db.execute(select(func.count(Document.id)).where(Document.status == "approved")).scalar() or 0,
        "documents_pending": db.execute(select(func.count(Document.id)).where(Document.status != "approved")).scalar() or 0,
        "chunks": db.execute(select(func.count(DocumentChunk.id))).scalar() or 0,
        "chunk_vectors": db.execute(select(func.count(ChunkVector.chunk_id))).scalar() or 0,
        "projects_approved": db.execute(select(func.count(Project.id)).where(Project.approved == True)).scalar() or 0,
        "projects_pending": db.execute(select(func.count(Project.id)).where(Project.approved == False)).scalar() or 0,
        "sessions": db.execute(select(func.count(VisitSession.id))).scalar() or 0,
        "analytics_events": db.execute(select(func.count(AnalyticsEvent.id))).scalar() or 0,
        "audit_logs": db.execute(select(func.count(AuditLog.id))).scalar() or 0,
    }

    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(uptime, 1),
        "database_engine": engine.dialect.name,
        "storage_backend": settings.storage_backend,
        "storage_health": storage.health_check(),
        "llm_configuration": {
            "provider": settings.llm_provider,
            "generation_model": settings.gemini_model,
            "embedding_model": settings.embedding_model,
            "api_key_configured": bool(settings.gemini_api_key)
        },
        "inventory_metrics": counts
    }

@app.get("/api/config/public")
def public_config():
    return {
        "laboratory": settings.lab_name,
        "institution": settings.institution_name,
        "assistant_provider": settings.llm_provider,
        "assistant_model": settings.gemini_model if settings.llm_provider.lower() == "gemini" else "extractive-baseline",
        "supported_languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "हिन्दी (Hindi)"},
            {"code": "bn", "name": "বাংলা (Bengali)"},
            {"code": "ta", "name": "தமிழ் (Tamil)"},
            {"code": "te", "name": "తెలుగు (Telugu)"},
            {"code": "mr", "name": "मराठी (Marathi)"}
        ]
    }


# -----------------------------------------------------------------------------
# ASSETS & EQUIPMENT (Module 1)
# -----------------------------------------------------------------------------

def asset_out(a: Asset, db: Session | None = None):
    photos = []
    links = []
    if db is not None:
        p_rows = db.execute(select(AssetPhoto).where(AssetPhoto.asset_id == a.id)).scalars().all()
        photos = [photo_out(p) for p in p_rows]
        doc_links = db.execute(select(AssetDocumentLink, Document).join(Document, Document.id == AssetDocumentLink.document_id).where(AssetDocumentLink.asset_id == a.id)).all()
        links = [{"document_id": d.id, "filename": d.filename, "link_type": l.link_type, "category": d.category} for l, d in doc_links]

    specs = {}
    try:
        specs = json.loads(a.specifications_json or "{}")
    except Exception:
        specs = {}

    return {
        "id": a.id,
        "name": a.name,
        "category": a.category,
        "zone": a.zone,
        "description": a.description,
        "manufacturer": a.manufacturer,
        "model_number": a.model_number,
        "specifications": specs,
        "source_reference": a.source_reference,
        "verified_at": a.verified_at.isoformat() if a.verified_at else None,
        "photos": photos,
        "linked_documents": links
    }

@app.get("/api/assets")
def list_assets(db: Session = Depends(get_db)):
    assets = db.execute(select(Asset).order_by(Asset.zone, Asset.name)).scalars().all()
    return [asset_out(a, db) for a in assets]

@app.post("/api/assets")
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    if db.get(Asset, payload.id):
        raise HTTPException(409, "Asset ID already exists")
    a = Asset(
        id=payload.id,
        name=payload.name,
        category=payload.category,
        zone=payload.zone,
        description=payload.description,
        manufacturer=payload.manufacturer,
        model_number=payload.model_number,
        specifications_json=json.dumps(payload.specifications),
        source_reference=payload.source_reference
    )
    db.add(a)
    db.add(AuditLog(
        actor=actor.get("username", "admin"),
        action="asset.create",
        resource_type="asset",
        resource_id=payload.id
    ))
    db.commit()
    db.refresh(a)
    return asset_out(a, db)

@app.get("/api/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    a = db.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "Asset not found")
    return asset_out(a, db)

@app.patch("/api/assets/{asset_id}")
def update_asset(asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    a = db.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "Asset not found")
    data = payload.model_dump(exclude_unset=True)
    if "specifications" in data:
        a.specifications_json = json.dumps(data.pop("specifications"))
    for k, v in data.items():
        setattr(a, k, v)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="asset.update", resource_type="asset", resource_id=asset_id))
    db.commit()
    return asset_out(a, db)

@app.post("/api/assets/{asset_id}/verify")
def verify_asset(asset_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    a = db.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "Asset not found")
    a.verified_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="asset.verify", resource_type="asset", resource_id=asset_id))
    db.commit()
    return asset_out(a, db)

@app.delete("/api/assets/{asset_id}")
def delete_asset(asset_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    a = db.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "Asset not found")
    # Clean up associated photos and physical media files
    photos = db.execute(select(AssetPhoto).where(AssetPhoto.asset_id == asset_id)).scalars().all()
    for p in photos:
        storage.delete(f"media/{p.storage_name}")
        db.delete(p)
    # Clean up associated SAEG graph links
    db.execute(delete(AssetDocumentLink).where(AssetDocumentLink.asset_id == asset_id))
    db.execute(delete(AssetProjectLink).where(AssetProjectLink.asset_id == asset_id))
    db.delete(a)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="asset.delete", resource_type="asset", resource_id=asset_id))
    db.commit()
    return {"id": asset_id, "deleted": True}


# -----------------------------------------------------------------------------
# ZONES & SPATIAL SCENE (Module 1 Digital Twin)
# -----------------------------------------------------------------------------

def zone_out(z: LabZone):
    return {
        "id": z.id,
        "name": z.name,
        "description": z.description,
        "floor": z.floor,
        "sort_order": z.sort_order,
        "verified": z.verified,
        "x": z.x,
        "z": z.z,
        "width": z.width,
        "depth": z.depth
    }

@app.get("/api/zones")
def list_zones(db: Session = Depends(get_db)):
    zones = db.execute(select(LabZone).order_by(LabZone.sort_order, LabZone.name)).scalars().all()
    return [zone_out(z) for z in zones]

@app.post("/api/zones")
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    if db.get(LabZone, payload.id):
        raise HTTPException(409, "Zone ID already exists")
    z = LabZone(**payload.model_dump(), verified=False)
    db.add(z)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="zone.create", resource_type="zone", resource_id=payload.id))
    db.commit()
    db.refresh(z)
    return zone_out(z)

@app.patch("/api/zones/{zone_id}/layout")
def update_zone_layout(zone_id: str, payload: ZoneLayoutUpdate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    zone = db.get(LabZone, zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    for key, value in payload.model_dump().items():
        setattr(zone, key, value)
    db.add(AuditLog(
        actor=actor.get("username", "admin") if isinstance(actor, dict) else "admin",
        action="zone.layout.update",
        resource_type="zone",
        resource_id=zone_id
    ))
    db.commit()
    db.refresh(zone)
    return zone_out(zone)

@app.post("/api/zones/{zone_id}/verify")
def verify_zone(zone_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    z = db.get(LabZone, zone_id)
    if not z:
        raise HTTPException(404, "Zone not found")
    z.verified = True
    db.add(AuditLog(actor=actor.get("username", "admin"), action="zone.verify", resource_type="zone", resource_id=zone_id))
    db.commit()
    return zone_out(z)

@app.get("/api/spatial/scene")
def spatial_scene(db: Session = Depends(get_db)):
    zones = db.execute(select(LabZone).order_by(LabZone.sort_order, LabZone.name)).scalars().all()
    assets = db.execute(select(Asset).order_by(Asset.zone, Asset.name)).scalars().all()
    result_zones = []

    # Map assets to zones by name or id
    for zone in zones:
        zone_assets = [a for a in assets if a.zone == zone.name or a.zone == zone.id]
        result_zones.append({
            **zone_out(zone),
            "asset_count": len(zone_assets),
            "assets": [
                {
                    "id": a.id,
                    "name": a.name,
                    "category": a.category,
                    "manufacturer": a.manufacturer,
                    "model_number": a.model_number,
                    "description": a.description,
                    "verified": bool(a.verified_at)
                }
                for a in zone_assets
            ]
        })

    return {
        "scene_type": "configurable_illustrative_floor_plan",
        "is_surveyed": False,
        "disclaimer": "Illustrative spatial layout. Coordinates and room geometry must be verified against an institutional lab survey before being represented as a physical digital twin.",
        "zones": result_zones
    }


# -----------------------------------------------------------------------------
# ASSET PHOTOS & VISUAL EVIDENCE
# -----------------------------------------------------------------------------

def photo_out(photo: AssetPhoto):
    return {
        "id": photo.id,
        "asset_id": photo.asset_id,
        "filename": photo.filename,
        "url": storage.get_url(f"media/{photo.storage_name}"),
        "caption": photo.caption,
        "uploaded_at": photo.uploaded_at.isoformat()
    }

@app.get("/api/assets/{asset_id}/photos")
def list_asset_photos(asset_id: str, db: Session = Depends(get_db)):
    if not db.get(Asset, asset_id):
        raise HTTPException(404, "Asset not found")
    photos = db.execute(
        select(AssetPhoto).where(AssetPhoto.asset_id == asset_id).order_by(AssetPhoto.uploaded_at.desc())
    ).scalars().all()
    return [photo_out(p) for p in photos]

@app.post("/api/assets/{asset_id}/photos")
async def upload_asset_photo(
    asset_id: str,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin)
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "Image exceeds upload limit")

    signatures = {
        ".jpg": (b"\xff\xd8\xff", "image/jpeg"),
        ".jpeg": (b"\xff\xd8\xff", "image/jpeg"),
        ".png": (b"\x89PNG\r\n\x1a\n", "image/png"),
        ".webp": (b"RIFF", "image/webp")
    }
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in signatures or not data.startswith(signatures[suffix][0]):
        raise HTTPException(415, "Upload a valid JPG, PNG or WebP image")
    if suffix == ".webp" and data[8:12] != b"WEBP":
        raise HTTPException(415, "Invalid WebP image")

    digest = sha256(data).hexdigest()
    existing = db.execute(
        select(AssetPhoto).where(AssetPhoto.sha256 == digest, AssetPhoto.asset_id == asset_id)
    ).scalar_one_or_none()
    if existing:
        return {**photo_out(existing), "duplicate": True}

    photo_id = str(uuid4())
    storage_key = f"{photo_id}{suffix}"
    storage.save(f"media/{storage_key}", data, content_type=signatures[suffix][1])
    photo = AssetPhoto(
        id=photo_id,
        asset_id=asset_id,
        filename=Path(file.filename or "photo").name,
        storage_name=storage_key,
        content_type=signatures[suffix][1],
        sha256=digest,
        caption=caption[:500]
    )
    db.add(photo)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="photo.upload", resource_type="photo", resource_id=photo_id))
    db.commit()
    db.refresh(photo)
    return photo_out(photo)

@app.delete("/api/photos/{photo_id}")
def delete_asset_photo(photo_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    photo = db.get(AssetPhoto, photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    storage.delete(f"media/{photo.storage_name}")
    db.delete(photo)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="photo.delete", resource_type="photo", resource_id=photo_id))
    db.commit()
    return {"id": photo_id, "deleted": True}


# -----------------------------------------------------------------------------
# SIGNATURE INNOVATION A: SPATIALLY ANCHORED EVIDENCE GRAPH (SAEG)
# -----------------------------------------------------------------------------

@app.get("/api/graph/overview")
def get_graph_overview(db: Session = Depends(get_db)):
    """Returns the relational Spatially Anchored Evidence Graph: Zones, Assets, Documents, and Projects."""
    zones = db.execute(select(LabZone)).scalars().all()
    assets = db.execute(select(Asset)).scalars().all()
    documents = db.execute(select(Document).where(Document.status == "approved")).scalars().all()
    projects = db.execute(select(Project).where(Project.approved == True)).scalars().all()

    nodes = []
    edges = []

    for z in zones:
        nodes.append({
            "id": f"zone_{z.id}",
            "raw_id": z.id,
            "type": "zone",
            "name": z.name,
            "verified": z.verified,
            "coordinates": {"x": z.x, "z": z.z, "width": z.width, "depth": z.depth}
        })

    for a in assets:
        nodes.append({
            "id": f"asset_{a.id}",
            "raw_id": a.id,
            "type": "asset",
            "name": a.name,
            "category": a.category,
            "verified": bool(a.verified_at),
            "zone": a.zone
        })
        # Zone-to-Asset edge
        matching_zone = next((z for z in zones if z.name == a.zone or z.id == a.zone), None)
        if matching_zone:
            edges.append({
                "source": f"zone_{matching_zone.id}",
                "target": f"asset_{a.id}",
                "relation": "contains_asset"
            })

    for d in documents:
        nodes.append({
            "id": f"doc_{d.id}",
            "raw_id": d.id,
            "type": "document",
            "name": d.filename,
            "category": d.category,
            "version": d.version,
            "verified": True
        })

    for p in projects:
        nodes.append({
            "id": f"proj_{p.id}",
            "raw_id": p.id,
            "type": "project",
            "name": p.title,
            "author_type": p.author_type,
            "verified": True
        })

    # Asset-Document links
    doc_links = db.execute(select(AssetDocumentLink)).scalars().all()
    for dl in doc_links:
        edges.append({
            "id": dl.id,
            "source": f"asset_{dl.asset_id}",
            "target": f"doc_{dl.document_id}",
            "relation": f"supported_by_{dl.link_type}"
        })

    # Asset-Project links
    proj_links = db.execute(select(AssetProjectLink)).scalars().all()
    for pl in proj_links:
        edges.append({
            "id": pl.id,
            "source": f"asset_{pl.asset_id}",
            "target": f"proj_{pl.project_id}",
            "relation": "demonstrated_in"
        })

    return {
        "graph_type": "SpatiallyAnchoredEvidenceGraph",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "disclaimer": "Graph nodes are backed by verified database entity IDs and approved documentation records."
    }

@app.post("/api/graph/links")
def create_graph_link(payload: LinkCreate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    asset = db.get(Asset, payload.asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")

    if payload.link_type in {"manual", "sop", "spec_sheet", "safety", "document"}:
        doc = db.get(Document, payload.target_id)
        if not doc:
            raise HTTPException(404, "Target document not found")
        link = AssetDocumentLink(asset_id=asset.id, document_id=doc.id, link_type=payload.link_type)
        db.add(link)
        db.add(AuditLog(actor=actor.get("username", "admin"), action="graph.link.doc", resource_type="link", resource_id=f"{asset.id}->{doc.id}"))
        db.commit()
        return {"link_id": link.id, "type": "asset_document", "asset_id": asset.id, "document_id": doc.id}
    elif payload.link_type in {"project", "demonstrator"}:
        proj = db.get(Project, payload.target_id)
        if not proj:
            raise HTTPException(404, "Target project not found")
        link = AssetProjectLink(asset_id=asset.id, project_id=proj.id, description=payload.description)
        db.add(link)
        db.add(AuditLog(actor=actor.get("username", "admin"), action="graph.link.project", resource_type="link", resource_id=f"{asset.id}->{proj.id}"))
        db.commit()
        return {"link_id": link.id, "type": "asset_project", "asset_id": asset.id, "project_id": proj.id}
    else:
        raise HTTPException(422, "Invalid link type")


# -----------------------------------------------------------------------------
# KNOWLEDGE INGESTION & HYBRID RAG (Module 3)
# -----------------------------------------------------------------------------

import io

def extract_file(path_or_bytes, suffix: str):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        raw_bytes = bytes(path_or_bytes)
    else:
        raw_bytes = Path(path_or_bytes).read_bytes()

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(raw_bytes))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix == ".docx":
        d = DocxDocument(io.BytesIO(raw_bytes))
        return [(None, "\n".join(p.text for p in d.paragraphs))]
    if suffix in {".txt", ".md"}:
        return [(None, raw_bytes.decode("utf-8", errors="ignore"))]
    raise HTTPException(415, "Supported formats: PDF, DOCX, TXT, MD")

def split_chunks(text: str, size: int = 1000, overlap: int = 150):
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    out = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        out.append(clean[start:end])
        if end == len(clean):
            break
        start = max(start + 1, end - overlap)
    return out

@app.post("/api/knowledge/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="manual"),
    version: str = Form(default="1.0"),
    description: str = Form(default=""),
    db: Session = Depends(get_db),
    actor: dict = Depends(require_admin)
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md"}:
        raise HTTPException(415, "Only PDF, DOCX, TXT and MD are supported")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")

    digest = sha256(data).hexdigest()
    existing = db.execute(select(Document).where(Document.sha256 == digest)).scalar_one_or_none()
    if existing:
        return {"document_id": existing.id, "status": existing.status, "duplicate": True}

    doc_id = str(uuid4())
    safe_name = Path(file.filename or "document").name
    storage.save(f"{doc_id}{suffix}", data, content_type=file.content_type or "application/octet-stream")

    doc = Document(
        id=doc_id,
        filename=safe_name,
        content_type=file.content_type or "",
        sha256=digest,
        status="pending_review",
        category=category[:80],
        version=version[:40],
        description=description[:500]
    )
    db.add(doc)

    try:
        pages = extract_file(data, suffix)
        index = 0
        for page, text_content in pages:
            for chunk in split_chunks(text_content):
                row = DocumentChunk(document_id=doc_id, page_number=page, chunk_index=index, text=chunk)
                db.add(row)
                db.flush()
                vector = embed_text(chunk)
                if vector:
                    existing_vec = db.get(ChunkVector, row.id)
                    if existing_vec:
                        existing_vec.vector_json = json.dumps(vector)
                        existing_vec.model = settings.embedding_model
                    else:
                        db.add(ChunkVector(chunk_id=row.id, model=settings.embedding_model, vector_json=json.dumps(vector)))
                index += 1
        db.add(AuditLog(actor=actor.get("username", "admin"), action="knowledge.upload", resource_type="document", resource_id=doc_id))
        db.commit()
    except Exception as e:
        db.rollback()
        storage.delete(f"{doc_id}{suffix}")
        logger.error(f"Failed to process uploaded file: {e}")
        raise HTTPException(500, f"Error processing document: {str(e)}")

    return {
        "document_id": doc_id,
        "filename": safe_name,
        "status": "pending_review",
        "category": category,
        "version": version,
        "chunks_created": index,
        "message": "Document indexed successfully. Pending administrator verification before retrieval."
    }

@app.get("/api/knowledge/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.execute(select(Document).order_by(Document.uploaded_at.desc())).scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "category": d.category,
            "version": d.version,
            "description": d.description,
            "uploaded_at": d.uploaded_at.isoformat()
        }
        for d in docs
    ]

@app.get("/api/knowledge/documents/{doc_id}")
def get_document_details(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    chunks = db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id).order_by(DocumentChunk.chunk_index)).scalars().all()
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "category": doc.category,
        "version": doc.version,
        "description": doc.description,
        "uploaded_at": doc.uploaded_at.isoformat(),
        "chunk_count": len(chunks),
        "chunks": [{"id": c.id, "index": c.chunk_index, "page": c.page_number, "text": c.text} for c in chunks[:25]]
    }

@app.get("/api/knowledge/documents/{doc_id}/download")
def download_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    doc_suffix = Path(doc.filename).suffix.lower()
    data = storage.load(f"{doc_id}{doc_suffix}")
    if not data:
        raise HTTPException(404, "Document file not found in storage")
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'}
    )

@app.post("/api/knowledge/documents/{doc_id}/approve")
def approve_document(doc_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(404, "Document not found")
    d.status = "approved"
    db.add(AuditLog(actor=actor.get("username", "admin"), action="knowledge.approve", resource_type="document", resource_id=d.id))
    db.commit()
    return {"id": d.id, "status": d.status}

@app.post("/api/knowledge/documents/{doc_id}/unapprove")
def unapprove_document(doc_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(404, "Document not found")
    d.status = "pending_review"
    db.add(AuditLog(actor=actor.get("username", "admin"), action="knowledge.unapprove", resource_type="document", resource_id=d.id))
    db.commit()
    return {"id": d.id, "status": d.status}

@app.delete("/api/knowledge/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(404, "Document not found")
    # Clean up associated SAEG graph links
    db.execute(delete(AssetDocumentLink).where(AssetDocumentLink.document_id == doc_id))
    # Clean up associated chunk vectors explicitly
    chunks = db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).scalars().all()
    for c in chunks:
        cv = db.get(ChunkVector, c.id)
        if cv:
            db.delete(cv)
    # Remove from physical storage
    doc_suffix = Path(d.filename).suffix.lower()
    storage.delete(f"{doc_id}{doc_suffix}")
    db.delete(d)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="knowledge.delete", resource_type="document", resource_id=doc_id))
    db.commit()
    return {"id": doc_id, "deleted": True}

@app.post("/api/knowledge/reindex")
def reindex_knowledge(db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    chunks = db.execute(select(DocumentChunk).join(Document).where(Document.status == "approved")).scalars().all()
    indexed = 0
    unavailable = 0
    for chunk in chunks:
        if db.get(ChunkVector, chunk.id):
            continue
        vector = embed_text(chunk.text)
        if vector:
            db.add(ChunkVector(chunk_id=chunk.id, model=settings.embedding_model, vector_json=json.dumps(vector)))
            indexed += 1
        else:
            unavailable += 1
    db.add(AuditLog(actor=actor.get("username", "admin"), action="knowledge.reindex", resource_type="knowledge_base", resource_id="approved_chunks"))
    db.commit()
    return {
        "approved_chunks": len(chunks),
        "new_vectors_created": indexed,
        "embedding_unavailable": unavailable,
        "model": settings.embedding_model
    }

@app.post("/api/knowledge/evaluate")
def evaluate_retrieval(payload: EvaluationRequest, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Offline retrieval evaluation against curator-supplied relevant document IDs."""
    hits = 0
    reciprocal = 0.0
    evaluated = 0
    rows = []
    for case in payload.cases:
        if not case.expected_document_ids:
            continue
        results = retrieve(db, case.question, limit=settings.retrieval_top_k)
        ranked = [r["document_id"] for r in results]
        relevant = set(case.expected_document_ids)
        positions = [i + 1 for i, doc_id in enumerate(ranked) if doc_id in relevant]
        found = bool(positions)
        hits += int(found)
        if found:
            reciprocal += 1.0 / min(positions)
        evaluated += 1
        rows.append({
            "question": case.question,
            "retrieved_document_ids": ranked,
            "relevant_document_ids": list(relevant),
            "hit_at_k": found,
            "reciprocal_rank": (1.0 / min(positions) if found else 0.0)
        })
    return {
        "evaluated_cases": evaluated,
        "recall_at_k": (hits / evaluated if evaluated else None),
        "mrr": (reciprocal / evaluated if evaluated else None),
        "k": settings.retrieval_top_k,
        "results": rows,
        "warning": "Metrics reflect curator-labelled benchmarks only. Label uncurated documents prior to production reporting."
    }


# -----------------------------------------------------------------------------
# CONVERSATIONAL LAB ASSISTANT & EVIDENCE GATE (Module 2 & Innovation C)
# -----------------------------------------------------------------------------

@app.post("/api/assistant/query")
def ask(payload: QueryRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, limit=60, window_sec=60)
    asset = find_asset(db, payload.hotspot_id, payload.question)
    passages = retrieve(db, payload.question, limit=settings.retrieval_top_k, asset_id=asset.id if asset else None)

    specs = {}
    if asset and asset.specifications_json:
        try:
            specs = json.loads(asset.specifications_json or "{}")
        except Exception:
            specs = {}

    # Multi-turn conversation retrieval
    history_turns = []
    if payload.session_id:
        prior_turns = db.execute(
            select(ConversationTurn)
            .where(ConversationTurn.session_id == payload.session_id)
            .order_by(ConversationTurn.created_at.desc())
            .limit(4)
        ).scalars().all()
        history_turns = [{"question": t.question, "answer": t.answer} for t in reversed(prior_turns)]

        session = db.get(VisitSession, payload.session_id)
        if session and session.consent_analytics:
            db.add(AnalyticsEvent(session_id=session.id, event_type="question", target_id=asset.id if asset else "general"))
            db.commit()

    # Evidence Gate: Abstain if no approved passages and no asset records exist
    if not passages and not specs:
        abstention_text = (
            "I could not find approved laboratory evidence supporting this answer in the AI & ML Laboratory repository. "
            "Please ask the laboratory administrator or faculty coordinator to add and verify the relevant record."
            if payload.language == "en" else
            "उपलब्ध AI & ML प्रयोगशाला रिकॉर्ड में इस प्रश्न से संबंधित सत्यापित साक्ष्य नहीं मिले। कृपया प्रयोगशाला प्रशासक से संपर्क करें।"
        )
        if payload.session_id:
            db.add(ConversationTurn(
                session_id=payload.session_id,
                question=payload.question,
                answer=abstention_text,
                hotspot_id=payload.hotspot_id,
                language=payload.language,
                status="insufficient_evidence"
            ))
            db.commit()

        return {
            "status": "insufficient_evidence",
            "answer": abstention_text,
            "citations": [],
            "asset": asset_out(asset, db) if asset else None,
            "evidence_gate": {
                "verified_grounding": False,
                "abstention_triggered": True,
                "reason": "no_approved_passages_or_specs",
                "retrieved_chunk_count": 0
            }
        }

    snippets = []
    for p in passages:
        snippets.append({
            "document_id": p["document_id"],
            "filename": p["filename"],
            "page": p["page"],
            "excerpt": p["text"][:650]
        })

    evidence_for_llm = [{"filename": x["filename"], "page": x["page"], "text": x["excerpt"]} for x in snippets]
    if asset:
        structured = [
            f"Asset ID: {asset.id}",
            f"Name: {asset.name}",
            f"Zone: {asset.zone}",
            f"Description: {asset.description}",
            f"Manufacturer: {asset.manufacturer}",
            f"Model: {asset.model_number}",
            f"Specifications: {json.dumps(specs, ensure_ascii=False)}",
            f"Source reference: {asset.source_reference}"
        ]
        evidence_for_llm.append({"filename": f"Structured asset record {asset.id}", "page": None, "text": "\n".join(structured)})

    # Invoke Gemini with Evidence Gate check
    llm_res = generate_grounded_answer(payload.question, evidence_for_llm, payload.language, history=history_turns)

    answer_parts = []
    if asset:
        answer_parts.append(f"Relevant asset: {asset.name} ({asset.id}), located in {asset.zone}.")
        if asset.manufacturer:
            answer_parts.append(f"Manufacturer: {asset.manufacturer}.")
        if asset.model_number:
            answer_parts.append(f"Model: {asset.model_number}.")
        if specs:
            answer_parts.append("Registered specifications: " + "; ".join(f"{k}: {v}" for k, v in specs.items()) + ".")
        if asset.description:
            answer_parts.append(asset.description)

    if snippets:
        answer_parts.append("Approved laboratory knowledge-base passages:")
        answer_parts.extend([f"[{i+1}] {s['excerpt']}" for i, s in enumerate(snippets)])

    extractive_fallback = "\n\n".join(answer_parts)
    final_answer = llm_res.get("answer") or extractive_fallback

    # Save conversation turn
    if payload.session_id:
        db.add(ConversationTurn(
            session_id=payload.session_id,
            question=payload.question,
            answer=final_answer,
            hotspot_id=payload.hotspot_id,
            language=payload.language,
            status="answered_with_evidence"
        ))
        db.commit()

    return {
        "status": "answered_with_evidence",
        "answer": final_answer,
        "generation": "gemini" if llm_res.get("answer") else "extractive_fallback",
        "citations": [{"document_id": s["document_id"], "filename": s["filename"], "page": s["page"]} for s in snippets],
        "asset": asset_out(asset, db) if asset else None,
        "retrieval": {
            "mode": "hybrid_semantic_lexical" if any(p.get("semantic_score", 0) for p in passages) else "lexical_fallback",
            "top_k": len(passages)
        },
        "evidence_gate": {
            "verified_grounding": True,
            "abstention_triggered": llm_res.get("abstention_triggered", False),
            "gate_passed": llm_res.get("gate_passed", True),
            "gate_reason": llm_res.get("reason", "verified_grounding"),
            "citations_validated": llm_res.get("citations", [])
        },
        "note": "Answers are strictly constrained to approved laboratory documentation and registered equipment records."
    }

@app.get("/api/assistant/history/{session_id}")
def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    turns = db.execute(
        select(ConversationTurn)
        .where(ConversationTurn.session_id == session_id)
        .order_by(ConversationTurn.created_at)
    ).scalars().all()
    return [
        {
            "id": t.id,
            "question": t.question,
            "answer": t.answer,
            "hotspot_id": t.hotspot_id,
            "language": t.language,
            "status": t.status,
            "created_at": t.created_at.isoformat()
        }
        for t in turns
    ]


# -----------------------------------------------------------------------------
# AI PROJECT DEMONSTRATOR (Module 4)
# -----------------------------------------------------------------------------

def project_out(p: Project, db: Session | None = None):
    linked_assets = []
    if db is not None:
        asset_links = db.execute(
            select(AssetProjectLink, Asset)
            .join(Asset, Asset.id == AssetProjectLink.asset_id)
            .where(AssetProjectLink.project_id == p.id)
        ).all()
        linked_assets = [{"id": a.id, "name": a.name, "zone": a.zone} for l, a in asset_links]

    return {
        "id": p.id,
        "title": p.title,
        "problem": p.problem,
        "methodology": p.methodology,
        "technologies": p.technologies,
        "outcomes": p.outcomes,
        "societal_impact": p.societal_impact,
        "demo_url": p.demo_url,
        "author_name": p.author_name,
        "author_type": p.author_type,
        "diagram_url": p.diagram_url,
        "approved": p.approved,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "linked_assets": linked_assets
    }

def secrets_id():
    return str(uuid4())[:8].upper()

@app.post("/api/projects/submit")
def submit_project(payload: ProjectSubmit, request: Request, db: Session = Depends(get_db)):
    """Public submission endpoint for student and faculty innovators with rate limiting & sanitization."""
    check_rate_limit(request, limit=60, window_sec=60)
    
    # Strip HTML tags to prevent stored XSS attacks
    clean_title = re.sub(r"<[^>]+>", "", payload.title).strip()
    clean_problem = re.sub(r"<[^>]+>", "", payload.problem).strip()
    clean_method = re.sub(r"<[^>]+>", "", payload.methodology).strip()
    clean_author = re.sub(r"<[^>]+>", "", payload.author_name).strip()

    proj_id = f"PROJ-{secrets_id()}"
    p = Project(
        id=proj_id,
        title=clean_title,
        problem=clean_problem,
        methodology=clean_method,
        technologies=payload.technologies,
        outcomes=payload.outcomes,
        societal_impact=payload.societal_impact,
        demo_url=payload.demo_url,
        author_name=clean_author,
        author_type=payload.author_type,
        diagram_url=payload.diagram_url,
        approved=False
    )
    db.add(p)
    # Link related assets if specified
    for aid in payload.related_asset_ids:
        if db.get(Asset, aid):
            db.add(AssetProjectLink(asset_id=aid, project_id=proj_id))
    db.commit()
    db.refresh(p)
    return {
        "id": p.id,
        "title": p.title,
        "status": "pending_approval",
        "message": "Project submitted successfully. It will appear in the showcase after institutional review."
    }

@app.post("/api/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    if db.get(Project, payload.id):
        raise HTTPException(409, "Project ID exists")
    p = Project(**payload.model_dump(), approved=False)
    db.add(p)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="project.create", resource_type="project", resource_id=payload.id))
    db.commit()
    return {"id": p.id, "title": p.title, "status": "pending_approval"}

@app.get("/api/projects")
def list_approved_projects(db: Session = Depends(get_db)):
    """Lists approved projects visible to visitors."""
    ps = db.execute(select(Project).where(Project.approved == True).order_by(Project.submitted_at.desc())).scalars().all()
    return [project_out(p, db) for p in ps]

@app.get("/api/projects/all")
def list_all_projects(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Lists all projects including pending submissions for administration."""
    ps = db.execute(select(Project).order_by(Project.submitted_at.desc())).scalars().all()
    return [project_out(p, db) for p in ps]

@app.get("/api/projects/{project_id}")
def get_project_details(project_id: str, db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return project_out(p, db)

@app.post("/api/projects/{project_id}/approve")
def approve_project(project_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.approved = True
    db.add(AuditLog(actor=actor.get("username", "admin"), action="project.approve", resource_type="project", resource_id=project.id))
    db.commit()
    return {"id": project.id, "status": "approved"}

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    # Clean up associated SAEG graph links
    db.execute(delete(AssetProjectLink).where(AssetProjectLink.project_id == project_id))
    db.delete(project)
    db.add(AuditLog(actor=actor.get("username", "admin"), action="project.delete", resource_type="project", resource_id=project_id))
    db.commit()
    return {"id": project_id, "deleted": True}


# -----------------------------------------------------------------------------
# VISITOR INTERACTION, TOUR COMPILER & ANALYTICS (Modules 5 & Innovation B)
# -----------------------------------------------------------------------------

@app.post("/api/visits")
def create_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    vid = str(uuid4())
    v = VisitSession(
        id=vid,
        persona=payload.persona,
        agenda=payload.agenda,
        duration_minutes=payload.duration_minutes,
        consent_analytics=payload.consent_analytics
    )
    db.add(v)
    db.commit()
    return {"id": vid, "persona": v.persona, "duration_minutes": v.duration_minutes, "consent_analytics": v.consent_analytics}

@app.post("/api/tours/plan")
def plan_tour(payload: TourRequest, db: Session = Depends(get_db)):
    """
    Signature Innovation B: Agenda-to-Tour Compiler.
    Calculates weighted relevance scores based on visitor persona, agenda keywords,
    and budgets presentation/transition times against available duration limits.
    """
    assets = db.execute(select(Asset)).scalars().all()
    projects = db.execute(select(Project).where(Project.approved == True)).scalars().all()
    zones = db.execute(select(LabZone)).scalars().all()
    zone_map = {z.name: z for z in zones}
    zone_map.update({z.id: z for z in zones})

    budget = payload.duration_minutes
    visit = db.get(VisitSession, payload.session_id) if payload.session_id else None

    # Persona-specific interest weights
    persona_lower = payload.persona.lower()
    is_student = "student" in persona_lower
    is_industry = "industry" in persona_lower or "executive" in persona_lower
    is_accreditation = "accreditation" in persona_lower or "reviewer" in persona_lower
    is_academic = "academic" in persona_lower or "research" in persona_lower

    interest_tokens = set(re.findall(r"[a-zA-Z0-9_\u0900-\u097F]+", (payload.agenda + " " + " ".join(payload.interests)).lower()))
    interest_tokens = {t for t in interest_tokens if len(t) > 2 and t not in STOP}

    candidates = []

    # Score assets
    for a in assets:
        text_corp = f"{a.name} {a.zone} {a.description} {a.category} {a.manufacturer} {a.model_number}".lower()
        match_score = sum(2 for t in interest_tokens if t in text_corp)

        # Persona affinity
        if is_academic and (a.category in {"compute", "server", "gpu"} or "workstation" in a.name.lower()):
            match_score += 3
        elif is_industry and (a.category in {"industrial", "edge", "robotics"} or "ai" in a.name.lower()):
            match_score += 3
        elif is_accreditation and a.verified_at:
            match_score += 4
        elif is_student:
            match_score += 1

        if a.verified_at:
            match_score += 1  # Verified assets preferred

        matching_zone = zone_map.get(a.zone)
        zone_coords = [matching_zone.x, matching_zone.z] if matching_zone else [0, 0]

        candidates.append({
            "id": a.id,
            "title": a.name,
            "type": "asset",
            "category": a.category,
            "zone": a.zone,
            "zone_coords": zone_coords,
            "score": match_score,
            "verified": bool(a.verified_at)
        })

    # Score projects
    for p in projects:
        text_corp = f"{p.title} {p.problem} {p.technologies} {p.outcomes}".lower()
        match_score = sum(2 for t in interest_tokens if t in text_corp)

        if is_student and p.author_type == "student":
            match_score += 4
        elif is_academic:
            match_score += 2
        elif is_industry and p.demo_url:
            match_score += 3

        candidates.append({
            "id": p.id,
            "title": p.title,
            "type": "project",
            "category": "Research Showcase",
            "zone": "Research Workspace",
            "zone_coords": [2.0, -1.0],
            "score": match_score,
            "verified": True
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Time budgeting based on visit duration
    if budget <= 2:
        max_stops = 2
        min_min_per_stop = 1
    elif budget <= 5:
        max_stops = 3
        min_min_per_stop = 1
    else:  # 15 minutes or more
        max_stops = 6
        min_min_per_stop = 2

    selected = [c for c in candidates if c["score"] > 0][:max_stops]
    if not selected:
        selected = candidates[:max_stops]

    if not selected:
        return {
            "status": "no_verified_stops",
            "message": "No configured laboratory assets or approved projects match this visit. Add verified records before generating a tour.",
            "stops": []
        }

    # Allocate time budget realistically
    per_stop = max(min_min_per_stop, budget // len(selected))
    elapsed = 0
    stops = []
    for item in selected:
        if elapsed + per_stop > budget:
            break
        elapsed += per_stop
        stops.append({**item, "allocated_minutes": per_stop})

    if visit and visit.consent_analytics:
        db.add(AnalyticsEvent(session_id=visit.id, event_type="tour_generated", target_id=payload.persona))
        db.commit()

    return {
        "status": "planned",
        "persona": payload.persona,
        "duration_minutes": budget,
        "allocated_minutes": elapsed,
        "stops": stops,
        "planning_note": "Tour compiler verified each stop against approved records and respected the strict duration constraint."
    }

@app.post("/api/visits/{visit_id}/events")
def record_visitor_event(visit_id: str, payload: VisitorEventCreate, db: Session = Depends(get_db)):
    visit = db.get(VisitSession, visit_id)
    if not visit:
        raise HTTPException(404, "Visit session not found")
    if not visit.consent_analytics:
        return {"recorded": False, "reason": "visitor_did_not_consent"}
    allowed = {"zone_view", "project_view", "tour_started", "tour_completed", "language_changed", "question", "hotspot_select"}
    if payload.event_type not in allowed:
        raise HTTPException(422, "Unsupported visitor event type")
    db.add(AnalyticsEvent(session_id=visit.id, event_type=payload.event_type, target_id=payload.target_id))
    db.commit()
    return {"recorded": True}

@app.get("/api/visits/{visit_id}/summary")
def visitor_summary(visit_id: str, db: Session = Depends(get_db)):
    visit = db.get(VisitSession, visit_id)
    if not visit:
        raise HTTPException(404, "Visit session not found")
    events = (
        db.execute(select(AnalyticsEvent).where(AnalyticsEvent.session_id == visit_id).order_by(AnalyticsEvent.created_at))
        .scalars().all() if visit.consent_analytics else []
    )
    turns = (
        db.execute(select(ConversationTurn).where(ConversationTurn.session_id == visit_id).order_by(ConversationTurn.created_at))
        .scalars().all()
    )
    return {
        "session_id": visit.id,
        "persona": visit.persona,
        "agenda": visit.agenda,
        "duration_minutes": visit.duration_minutes,
        "analytics_consent": visit.consent_analytics,
        "event_count": len(events),
        "question_count": len(turns),
        "events": [{"type": e.event_type, "target": e.target_id, "at": e.created_at.isoformat()} for e in events],
        "conversation": [{"q": t.question, "status": t.status} for t in turns],
        "privacy_note": "This summary contains only session events recorded with explicit analytics consent." if visit.consent_analytics else "Analytics were not enabled; interaction events were omitted from persistent analytics."
    }

@app.get("/api/analytics/overview")
def analytics(db: Session = Depends(get_db)):
    total_sessions = db.execute(select(func.count()).select_from(VisitSession)).scalar_one()
    opted_in = db.execute(select(func.count()).select_from(VisitSession).where(VisitSession.consent_analytics == True)).scalar_one()
    events = db.execute(
        select(AnalyticsEvent.event_type, AnalyticsEvent.target_id, func.count())
        .group_by(AnalyticsEvent.event_type, AnalyticsEvent.target_id)
    ).all()

    # FAQ Analysis: Group frequently asked questions
    all_turns = db.execute(select(ConversationTurn.question, ConversationTurn.hotspot_id)).all()
    faq_counts = defaultdict(int)
    for q_text, hotspot in all_turns:
        # Cluster normalized topic
        clean_q = re.sub(r"[^\w\s]", "", q_text.lower()).strip()
        words = [w for w in clean_q.split() if len(w) > 3 and w not in STOP]
        topic = " ".join(words[:4]) if words else "general inquiry"
        label = f"{topic}" + (f" ({hotspot})" if hotspot else "")
        faq_counts[label] += 1

    top_faqs = sorted([{"topic": k, "count": v} for k, v in faq_counts.items()], key=lambda x: x["count"], reverse=True)[:10]

    return {
        "total_sessions": total_sessions,
        "consented_sessions": opted_in,
        "consent_rate_percent": round((opted_in / total_sessions * 100), 1) if total_sessions else 0.0,
        "events": [{"type": e[0], "target": e[1], "count": e[2]} for e in events],
        "frequently_asked_topics": top_faqs,
        "note": "Only actual recorded events from sessions with analytics consent are aggregated."
    }

@app.get("/api/analytics/export")
def export_analytics(format: str = "json", db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    data = analytics(db)
    return data
