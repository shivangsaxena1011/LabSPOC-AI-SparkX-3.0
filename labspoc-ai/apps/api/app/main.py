from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select, func, inspect, text
from pathlib import Path
from uuid import uuid4
from hashlib import sha256
import json, re, shutil, hmac
from pypdf import PdfReader
from docx import Document as DocxDocument
from .config import settings
from .db import Base, engine, get_db
from .models import Asset, Document, DocumentChunk, Project, VisitSession, AnalyticsEvent, LabZone, AssetPhoto, User, AuditLog, ChunkVector
from .schemas import AssetCreate, VisitCreate, QueryRequest, TourRequest, ProjectCreate, ZoneCreate, ZoneLayoutUpdate, VisitorEventCreate, LoginRequest, EvaluationRequest
from .retrieval import retrieve, find_asset
from .llm import generate_grounded_answer
from .auth import require_admin, require_superadmin, login_user, hash_password
from .embeddings import embed_text

Base.metadata.create_all(bind=engine)
# Lightweight additive migration for installations created before spatial coordinates existed.
def ensure_spatial_columns():
    inspector = inspect(engine)
    if "lab_zones" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("lab_zones")}
    statements = {
        "x": "ALTER TABLE lab_zones ADD COLUMN x FLOAT NOT NULL DEFAULT 0.0",
        "z": "ALTER TABLE lab_zones ADD COLUMN z FLOAT NOT NULL DEFAULT 0.0",
        "width": "ALTER TABLE lab_zones ADD COLUMN width FLOAT NOT NULL DEFAULT 2.0",
        "depth": "ALTER TABLE lab_zones ADD COLUMN depth FLOAT NOT NULL DEFAULT 1.5",
    }
    with engine.begin() as connection:
        for name, statement in statements.items():
            if name not in existing:
                connection.execute(text(statement))
ensure_spatial_columns()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
MEDIA_DIR = Path(settings.upload_dir) / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name, version="0.7.0", description="Spatially grounded, evidence-aware virtual laboratory ambassador API")
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, db: Session = Depends(get_db)):
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
def create_admin_user(payload: dict, db: Session = Depends(get_db), actor: dict = Depends(require_superadmin)):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "viewer"))
    if len(username) < 3 or len(password) < 12 or role not in {"admin", "editor", "viewer"}:
        raise HTTPException(422, "Username must be 3+ chars, password 12+ chars, and role must be admin/editor/viewer")
    if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
        raise HTTPException(409, "Username already exists")
    user = User(id=str(uuid4()), username=username, password_hash=hash_password(password), role=role, active=True)
    db.add(user); db.add(AuditLog(actor=actor.get("username", "admin"), action="user.create", resource_type="user", resource_id=username)); db.commit()
    return {"id": user.id, "username": user.username, "role": user.role, "active": user.active}

@app.get("/api/admin/users")
def list_admin_users(db: Session = Depends(get_db), _: dict = Depends(require_superadmin)):
    return [{"id":u.id,"username":u.username,"role":u.role,"active":u.active,"created_at":u.created_at.isoformat()} for u in db.execute(select(User).order_by(User.username)).scalars().all()]

@app.patch("/api/admin/users/{user_id}/status")
def set_user_status(user_id: str, payload: dict, db: Session = Depends(get_db), actor: dict = Depends(require_superadmin)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.username == actor.get("username") and payload.get("active") is False:
        raise HTTPException(400, "You cannot deactivate your own active session account")
    user.active = bool(payload.get("active")); db.add(AuditLog(actor=actor.get("username", "admin"), action="user.status", resource_type="user", resource_id=user.username)); db.commit()
    return {"id":user.id,"username":user.username,"active":user.active}

@app.get("/api/admin/audit-logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), _: dict = Depends(require_superadmin)):
    limit = max(1, min(limit, 500))
    rows = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).scalars().all()
    return [{"id":x.id,"actor":x.actor,"action":x.action,"resource_type":x.resource_type,"resource_id":x.resource_id,"outcome":x.outcome,"created_at":x.created_at.isoformat()} for x in rows]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.7.0",
            "laboratory": settings.lab_name, "institution": settings.institution_name,
            "llm_provider": settings.llm_provider, "gemini_configured": bool(settings.gemini_api_key) if settings.llm_provider.lower() == "gemini" else False,
            "admin_configured": bool(settings.admin_api_key or settings.jwt_secret)}

@app.get("/api/config/public")
def public_config():
    return {"laboratory": settings.lab_name, "institution": settings.institution_name,
            "assistant_provider": settings.llm_provider, "assistant_model": settings.gemini_model if settings.llm_provider.lower() == "gemini" else "extractive-baseline"}

@app.get("/api/assets")
def list_assets(db: Session = Depends(get_db)):
    assets = db.execute(select(Asset).order_by(Asset.zone, Asset.name)).scalars().all()
    return [asset_out(a) for a in assets]

def asset_out(a):
    return {"id": a.id, "name": a.name, "category": a.category, "zone": a.zone,
            "description": a.description, "manufacturer": a.manufacturer,
            "model_number": a.model_number, "specifications": json.loads(a.specifications_json or "{}"),
            "source_reference": a.source_reference, "verified_at": a.verified_at.isoformat() if a.verified_at else None}

@app.post("/api/assets")
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    if db.get(Asset, payload.id):
        raise HTTPException(409, "Asset ID already exists")
    a = Asset(id=payload.id, name=payload.name, category=payload.category, zone=payload.zone,
              description=payload.description, manufacturer=payload.manufacturer,
              model_number=payload.model_number, specifications_json=json.dumps(payload.specifications),
              source_reference=payload.source_reference)
    db.add(a); db.commit(); db.refresh(a)
    return asset_out(a)

@app.get("/api/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    a = db.get(Asset, asset_id)
    if not a: raise HTTPException(404, "Asset not found")
    return asset_out(a)

def zone_out(z):
    return {"id": z.id, "name": z.name, "description": z.description, "floor": z.floor, "sort_order": z.sort_order, "verified": z.verified, "x": z.x, "z": z.z, "width": z.width, "depth": z.depth}

@app.get("/api/zones")
def list_zones(db: Session = Depends(get_db)):
    zones = db.execute(select(LabZone).order_by(LabZone.sort_order, LabZone.name)).scalars().all()
    return [zone_out(z) for z in zones]

@app.post("/api/zones")
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    if db.get(LabZone, payload.id):
        raise HTTPException(409, "Zone ID already exists")
    z = LabZone(**payload.model_dump(), verified=False)
    db.add(z); db.commit(); db.refresh(z)
    return zone_out(z)

@app.patch("/api/zones/{zone_id}/layout")
def update_zone_layout(zone_id: str, payload: ZoneLayoutUpdate, db: Session = Depends(get_db), actor: dict = Depends(require_admin)):
    zone = db.get(LabZone, zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    for key, value in payload.model_dump().items():
        setattr(zone, key, value)
    db.add(AuditLog(actor=actor.get("username", "admin") if isinstance(actor, dict) else "admin",
                    action="zone.layout.update", resource_type="zone", resource_id=zone_id))
    db.commit(); db.refresh(zone)
    return zone_out(zone)

@app.get("/api/spatial/scene")
def spatial_scene(db: Session = Depends(get_db)):
    zones = db.execute(select(LabZone).order_by(LabZone.sort_order, LabZone.name)).scalars().all()
    assets = db.execute(select(Asset).order_by(Asset.zone, Asset.name)).scalars().all()
    result_zones = []
    for zone in zones:
        zone_assets = [asset for asset in assets if asset.zone == zone.name or asset.zone == zone.id]
        result_zones.append({**zone_out(zone), "asset_count": len(zone_assets),
            "assets": [{"id": a.id, "name": a.name, "category": a.category,
                        "manufacturer": a.manufacturer, "model_number": a.model_number,
                        "description": a.description, "verified": bool(a.verified_at)} for a in zone_assets]})
    return {"scene_type": "configurable_illustrative_floor_plan", "is_surveyed": False,
            "disclaimer": "Illustrative spatial layout. Coordinates and room geometry must be verified against an institutional lab survey before being represented as a physical digital twin.",
            "zones": result_zones}

@app.post("/api/zones/{zone_id}/verify")
def verify_zone(zone_id: str, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    z = db.get(LabZone, zone_id)
    if not z: raise HTTPException(404, "Zone not found")
    z.verified = True; db.commit()
    return zone_out(z)

def photo_out(photo: AssetPhoto):
    return {"id": photo.id, "asset_id": photo.asset_id, "filename": photo.filename,
            "url": f"/media/{photo.storage_name}", "caption": photo.caption,
            "uploaded_at": photo.uploaded_at.isoformat()}

@app.get("/api/assets/{asset_id}/photos")
def list_asset_photos(asset_id: str, db: Session = Depends(get_db)):
    if not db.get(Asset, asset_id): raise HTTPException(404, "Asset not found")
    photos = db.execute(select(AssetPhoto).where(AssetPhoto.asset_id == asset_id).order_by(AssetPhoto.uploaded_at.desc())).scalars().all()
    return [photo_out(p) for p in photos]

@app.post("/api/assets/{asset_id}/photos")
async def upload_asset_photo(asset_id: str, file: UploadFile = File(...), caption: str = Form(default=""),
                             db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    asset = db.get(Asset, asset_id)
    if not asset: raise HTTPException(404, "Asset not found")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "Image exceeds upload limit")
    signatures = {".jpg": (b"\xff\xd8\xff", "image/jpeg"), ".jpeg": (b"\xff\xd8\xff", "image/jpeg"),
                  ".png": (b"\x89PNG\r\n\x1a\n", "image/png"), ".webp": (b"RIFF", "image/webp")}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in signatures or not data.startswith(signatures[suffix][0]):
        raise HTTPException(415, "Upload a valid JPG, PNG or WebP image")
    if suffix == ".webp" and data[8:12] != b"WEBP": raise HTTPException(415, "Invalid WebP image")
    digest = sha256(data).hexdigest()
    existing = db.execute(select(AssetPhoto).where(AssetPhoto.sha256 == digest, AssetPhoto.asset_id == asset_id)).scalar_one_or_none()
    if existing: return {**photo_out(existing), "duplicate": True}
    photo_id = str(uuid4()); storage = f"{photo_id}{suffix}"
    (MEDIA_DIR / storage).write_bytes(data)
    photo = AssetPhoto(id=photo_id, asset_id=asset_id, filename=Path(file.filename or "photo").name,
                       storage_name=storage, content_type=signatures[suffix][1], sha256=digest, caption=caption[:500])
    db.add(photo); db.commit(); db.refresh(photo)
    return photo_out(photo)

def extract_file(path: Path, suffix: str):
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix == ".docx":
        d = DocxDocument(str(path))
        return [(None, "\n".join(p.text for p in d.paragraphs))]
    if suffix in {".txt", ".md"}:
        return [(None, path.read_text(encoding="utf-8", errors="ignore"))]
    raise HTTPException(415, "Supported formats: PDF, DOCX, TXT, MD")

def split_chunks(text: str, size: int = 1100, overlap: int = 150):
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean: return []
    out=[]; start=0
    while start < len(clean):
        end=min(len(clean), start+size)
        out.append(clean[start:end])
        if end == len(clean): break
        start=max(start+1, end-overlap)
    return out

@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), _: bool = Depends(require_admin)):
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
    path = Path(settings.upload_dir) / f"{doc_id}{suffix}"
    path.write_bytes(data)
    doc = Document(id=doc_id, filename=safe_name, content_type=file.content_type or "", sha256=digest, status="pending_review")
    db.add(doc)
    try:
        pages = extract_file(path, suffix)
        index = 0
        for page, text in pages:
            for chunk in split_chunks(text):
                row = DocumentChunk(document_id=doc_id, page_number=page, chunk_index=index, text=chunk)
                db.add(row); db.flush()
                vector = embed_text(chunk)
                if vector:
                    db.add(ChunkVector(chunk_id=row.id, model=settings.embedding_model, vector_json=json.dumps(vector)))
                index += 1
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return {"document_id": doc_id, "filename": safe_name, "status": "pending_review",
            "chunks_created": index, "message": "Document indexed but not searchable until an administrator approves it."}

@app.get("/api/knowledge/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.execute(select(Document).order_by(Document.uploaded_at.desc())).scalars().all()
    return [{"id": d.id, "filename": d.filename, "status": d.status, "uploaded_at": d.uploaded_at.isoformat()} for d in docs]

@app.post("/api/knowledge/documents/{doc_id}/approve")
def approve_document(doc_id: str, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    d = db.get(Document, doc_id)
    if not d: raise HTTPException(404, "Document not found")
    d.status = "approved"; db.add(AuditLog(actor="admin", action="knowledge.approve", resource_type="document", resource_id=d.id)); db.commit()
    return {"id": d.id, "status": d.status}

@app.post("/api/assistant/query")
def ask(payload: QueryRequest, db: Session = Depends(get_db)):
    asset = find_asset(db, payload.hotspot_id, payload.question)
    passages = retrieve(db, payload.question, limit=5)
    if asset and asset.specifications_json:
        specs = json.loads(asset.specifications_json or "{}")
    else:
        specs = {}
    if payload.session_id:
        session = db.get(VisitSession, payload.session_id)
        if session and session.consent_analytics:
            db.add(AnalyticsEvent(session_id=session.id, event_type="question", target_id=asset.id if asset else "general"))
            db.commit()

    # Exact structured asset facts are returned as structured data; document evidence is separately cited.
    if not passages and not specs:
        return {"status": "insufficient_evidence",
                "answer": "I could not find approved laboratory evidence supporting this answer. Please ask the laboratory administrator to verify or add the relevant record.",
                "citations": [], "asset": asset_out(asset) if asset else None}
    snippets = []
    for p in passages:
        snippets.append({"document_id": p["document_id"], "filename": p["filename"], "page": p["page"], "excerpt": p["text"][:650]})
    # Gemini receives only approved retrieved passages and structured asset facts.
    evidence_for_llm = [{"filename": x["filename"], "page": x["page"], "text": x["excerpt"]} for x in snippets]
    if asset:
        structured = [f"Asset ID: {asset.id}", f"Name: {asset.name}", f"Zone: {asset.zone}",
                      f"Description: {asset.description}", f"Manufacturer: {asset.manufacturer}",
                      f"Model: {asset.model_number}", f"Specifications: {json.dumps(specs, ensure_ascii=False)}",
                      f"Source reference: {asset.source_reference}"]
        evidence_for_llm.append({"filename": f"Structured asset record {asset.id}", "page": None, "text": "\n".join(structured)})
    generated = generate_grounded_answer(payload.question, evidence_for_llm, payload.language) if evidence_for_llm else None
    answer_parts = []
    if asset:
        answer_parts.append(f"Relevant asset: {asset.name} ({asset.id}), located in {asset.zone}.")
        if asset.manufacturer: answer_parts.append(f"Manufacturer: {asset.manufacturer}.")
        if asset.model_number: answer_parts.append(f"Model: {asset.model_number}.")
        if specs: answer_parts.append("Registered specifications: " + "; ".join(f"{k}: {v}" for k,v in specs.items()) + ".")
        if asset.description: answer_parts.append(asset.description)
    if snippets:
        answer_parts.append("Approved knowledge-base passages relevant to your question:")
        answer_parts.extend([f"[{i+1}] {s['excerpt']}" for i,s in enumerate(snippets)])
    final_answer = generated or "\n\n".join(answer_parts)
    return {"status": "answered_with_evidence", "answer": final_answer, "generation": "gemini" if generated else "extractive_fallback",
            "citations": [{"document_id": s["document_id"], "filename": s["filename"], "page": s["page"]} for s in snippets],
            "asset": asset_out(asset) if asset else None,
            "retrieval": {"mode": "hybrid_semantic_lexical" if any(p.get("semantic_score", 0) for p in passages) else "lexical_fallback", "top_k": len(passages)},
            "note": "Answers are constrained to approved retrieved passages and structured lab records. Check citations before operational use."}

@app.post("/api/visits")
def create_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    vid = str(uuid4())
    v = VisitSession(id=vid, persona=payload.persona, agenda=payload.agenda,
                     duration_minutes=payload.duration_minutes, consent_analytics=payload.consent_analytics)
    db.add(v); db.commit()
    return {"id": vid, "persona": v.persona, "duration_minutes": v.duration_minutes}

@app.post("/api/tours/plan")
def plan_tour(payload: TourRequest, db: Session = Depends(get_db)):
    assets = db.execute(select(Asset)).scalars().all()
    projects = db.execute(select(Project).where(Project.approved == True)).scalars().all()
    # Deterministic, transparent planner over actual configured records; no synthetic stops.
    budget = payload.duration_minutes
    visit = db.get(VisitSession, payload.session_id) if payload.session_id else None
    candidates = []
    interest = set(re.findall(r"[a-zA-Z0-9]+", (payload.agenda + " " + " ".join(payload.interests)).lower()))
    for a in assets:
        text = (a.name + " " + a.zone + " " + a.description + " " + a.category).lower()
        score = sum(1 for t in interest if len(t) > 2 and t in text)
        if score or not interest:
            candidates.append({"id": a.id, "title": a.name, "type": "asset", "zone": a.zone, "score": score})
    for p in projects:
        text = (p.title + " " + p.problem + " " + p.technologies).lower()
        score = sum(1 for t in interest if len(t) > 2 and t in text)
        if score or not interest:
            candidates.append({"id": p.id, "title": p.title, "type": "project", "score": score})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    max_stops = max(1, min(6, budget // 2))
    selected = candidates[:max_stops]
    if not selected:
        return {"status": "no_verified_stops", "message": "No configured laboratory assets or approved projects match this visit. Add verified records before generating a tour.", "stops": []}
    per_stop = max(1, budget // len(selected))
    elapsed = 0; stops=[]
    for item in selected:
        if elapsed + per_stop > budget: break
        elapsed += per_stop
        stops.append({**item, "allocated_minutes": per_stop})
    if visit and visit.consent_analytics:
        db.add(AnalyticsEvent(session_id=visit.id, event_type="tour_generated", target_id=payload.persona))
        db.commit()
    return {"status": "planned", "persona": payload.persona, "duration_minutes": budget,
            "allocated_minutes": elapsed, "stops": stops,
            "planning_note": "Stops are selected only from configured assets and approved projects. This is a transparent baseline planner."}

@app.post("/api/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    if db.get(Project, payload.id): raise HTTPException(409, "Project ID exists")
    p = Project(**payload.model_dump(), approved=False)
    db.add(p); db.commit()
    return {"id": p.id, "title": p.title, "status": "pending_approval"}

@app.get("/api/projects")
def list_projects(db: Session = Depends(get_db)):
    ps = db.execute(select(Project).where(Project.approved == True)).scalars().all()
    return [{"id": p.id, "title": p.title, "problem": p.problem, "methodology": p.methodology,
             "technologies": p.technologies, "outcomes": p.outcomes, "societal_impact": p.societal_impact,
             "demo_url": p.demo_url} for p in ps]

@app.post("/api/visits/{visit_id}/events")
def record_visitor_event(visit_id: str, payload: VisitorEventCreate, db: Session = Depends(get_db)):
    visit = db.get(VisitSession, visit_id)
    if not visit:
        raise HTTPException(404, "Visit session not found")
    if not visit.consent_analytics:
        return {"recorded": False, "reason": "visitor_did_not_consent"}
    allowed = {"zone_view", "project_view", "tour_started", "tour_completed", "language_changed", "question"}
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
    events = db.execute(select(AnalyticsEvent).where(AnalyticsEvent.session_id == visit_id).order_by(AnalyticsEvent.created_at)).scalars().all() if visit.consent_analytics else []
    return {"session_id": visit.id, "persona": visit.persona, "agenda": visit.agenda,
            "duration_minutes": visit.duration_minutes, "analytics_consent": visit.consent_analytics,
            "event_count": len(events), "events": [{"type": e.event_type, "target": e.target_id, "at": e.created_at.isoformat()} for e in events],
            "privacy_note": "This summary contains only session events recorded with explicit analytics consent." if visit.consent_analytics else "Analytics were not enabled; no visitor interaction events were retained."}

@app.get("/api/analytics/overview")
def analytics(db: Session = Depends(get_db)):
    total_sessions = db.execute(select(func.count()).select_from(VisitSession)).scalar_one()
    opted_in = db.execute(select(func.count()).select_from(VisitSession).where(VisitSession.consent_analytics == True)).scalar_one()
    events = db.execute(select(AnalyticsEvent.event_type, AnalyticsEvent.target_id, func.count()).group_by(AnalyticsEvent.event_type, AnalyticsEvent.target_id)).all()
    return {"total_sessions": total_sessions, "consented_sessions": opted_in,
            "events": [{"type": e[0], "target": e[1], "count": e[2]} for e in events],
            "note": "Only actual recorded events from sessions with analytics consent are included."}


@app.post("/api/projects/{project_id}/approve")
def approve_project(project_id: str, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.approved = True
    db.commit()
    return {"id": project.id, "status": "approved"}


@app.post("/api/knowledge/evaluate")
def evaluate_retrieval(payload: EvaluationRequest, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Offline retrieval evaluation against curator-supplied relevant document IDs."""
    hits = 0; reciprocal = 0.0; evaluated = 0; rows = []
    for case in payload.cases:
        if not case.expected_document_ids: continue
        results = retrieve(db, case.question, limit=settings.retrieval_top_k)
        ranked = [r["document_id"] for r in results]
        relevant = set(case.expected_document_ids)
        positions = [i + 1 for i, doc_id in enumerate(ranked) if doc_id in relevant]
        found = bool(positions); hits += int(found)
        if found: reciprocal += 1.0 / min(positions)
        evaluated += 1
        rows.append({"question":case.question,"retrieved_document_ids":ranked,"relevant_document_ids":list(relevant),"hit_at_k":found,"reciprocal_rank":(1.0/min(positions) if found else 0.0)})
    return {"evaluated_cases":evaluated,"recall_at_k":(hits/evaluated if evaluated else None),"mrr":(reciprocal/evaluated if evaluated else None),"k":settings.retrieval_top_k,"results":rows,"warning":"Metrics are only meaningful when expected document IDs are independently curated; this endpoint does not create benchmark labels."}

@app.post("/api/knowledge/reindex")
def reindex_knowledge(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    chunks = db.execute(select(DocumentChunk).join(Document).where(Document.status == "approved")).scalars().all()
    indexed = 0; unavailable = 0
    for chunk in chunks:
        if db.get(ChunkVector, chunk.id): continue
        vector = embed_text(chunk.text)
        if vector:
            db.add(ChunkVector(chunk_id=chunk.id, model=settings.embedding_model, vector_json=json.dumps(vector))); indexed += 1
        else: unavailable += 1
    db.add(AuditLog(actor="admin", action="knowledge.reindex", resource_type="knowledge_base", resource_id="approved_chunks")); db.commit()
    return {"approved_chunks":len(chunks),"new_vectors_created":indexed,"embedding_unavailable":unavailable,"model":settings.embedding_model}
