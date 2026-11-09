"""Small HS256 session-token implementation; no third-party JWT dependency required."""
import base64, hashlib, hmac, json, secrets, time
from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .models import User, AuditLog
from .db import get_db


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 240_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256": return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 240_000).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def issue_token(user: User) -> str:
    secret = settings.jwt_secret or settings.admin_api_key
    if len(secret) < 32:
        raise HTTPException(503, "Configure JWT_SECRET with at least 32 characters")
    now = int(time.time())
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub":user.id,"username":user.username,"role":user.role,"iat":now,"exp":now+settings.access_token_minutes*60}, separators=(",", ":")).encode())
    signing = f"{header}.{payload}".encode()
    signature = _b64(hmac.new(secret.encode(), signing, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def decode_token(token: str) -> dict:
    try:
        head, body, signature = token.split(".")
        secret = settings.jwt_secret or settings.admin_api_key
        expected = _b64(hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError("signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload.get("exp", 0)) < int(time.time()): raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired access token")

def current_user(authorization: str | None = Header(default=None), x_admin_key: str | None = Header(default=None), db: Session | None = None):
    # Legacy secret remains supported for local migration; use bearer tokens for normal admin sessions.
    if settings.admin_api_key and x_admin_key and hmac.compare_digest(x_admin_key, settings.admin_api_key):
        return {"id":"legacy-admin", "username":"legacy-admin", "role":"admin"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Administrator login required")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload.get("role") not in {"admin", "editor"}:
        raise HTTPException(403, "Insufficient role")
    if db is not None:
        user = db.get(User, payload.get("sub"))
        if not user or not user.active or user.role != payload.get("role"):
            raise HTTPException(401, "Account inactive or permissions changed")
    return payload

def require_admin(authorization: str | None = Header(default=None), x_admin_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    # Header-key compatibility is retained for the existing local starter workflow.
    if settings.admin_api_key and x_admin_key and hmac.compare_digest(x_admin_key, settings.admin_api_key):
        return {"id":"legacy-admin", "username":"legacy-admin", "role":"admin"}
    if not settings.admin_api_key and not settings.jwt_secret:
        raise HTTPException(503, "Admin authentication is not configured")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Administrator login required")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload.get("role") not in {"admin", "editor"}:
        raise HTTPException(403, "Insufficient role")
    user = db.get(User, payload.get("sub"))
    if not user or not user.active or user.role != payload.get("role"):
        raise HTTPException(401, "Account inactive or permissions changed")
    return payload

def require_superadmin(authorization: str | None = Header(default=None), x_admin_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    if settings.admin_api_key and x_admin_key and hmac.compare_digest(x_admin_key, settings.admin_api_key):
        return {"id":"legacy-admin", "username":"legacy-admin", "role":"admin"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Administrator login required")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if payload.get("role") != "admin": raise HTTPException(403, "Administrator role required")
    user = db.get(User, payload.get("sub"))
    if not user or not user.active or user.role != "admin": raise HTTPException(401, "Account inactive or permissions changed")
    return payload

def ensure_bootstrap_admin(db: Session):
    if not settings.admin_username or not settings.admin_password:
        return
    user = db.execute(select(User).where(User.username == settings.admin_username)).scalar_one_or_none()
    if not user:
        user = User(id=secrets.token_hex(16), username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password), role="admin", active=True)
        db.add(user); db.commit()

def login_user(db: Session, username: str, password: str):
    ensure_bootstrap_admin(db)
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or not user.active or not verify_password(password, user.password_hash):
        db.add(AuditLog(actor=username[:120], action="auth.login", outcome="denied")); db.commit()
        raise HTTPException(401, "Invalid username or password")
    db.add(AuditLog(actor=user.username, action="auth.login", outcome="success")); db.commit()
    return {"access_token":issue_token(user), "token_type":"bearer", "expires_in":settings.access_token_minutes*60,
            "user":{"id":user.id,"username":user.username,"role":user.role}}
