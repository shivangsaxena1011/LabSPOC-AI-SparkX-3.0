from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), default="equipment")
    zone: Mapped[str] = mapped_column(String(120), default="Unassigned")
    description: Mapped[str] = mapped_column(Text, default="")
    manufacturer: Mapped[str] = mapped_column(String(160), default="")
    model_number: Mapped[str] = mapped_column(String(160), default="")
    specifications_json: Mapped[str] = mapped_column(Text, default="{}")
    source_reference: Mapped[str] = mapped_column(String(500), default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), default="")
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    category: Mapped[str] = mapped_column(String(80), default="manual")
    version: Mapped[str] = mapped_column(String(40), default="1.0")
    description: Mapped[str] = mapped_column(String(500), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    document: Mapped["Document"] = relationship(back_populates="chunks")

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    problem: Mapped[str] = mapped_column(Text, default="")
    methodology: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    outcomes: Mapped[str] = mapped_column(Text, default="")
    societal_impact: Mapped[str] = mapped_column(Text, default="")
    demo_url: Mapped[str] = mapped_column(String(500), default="")
    author_name: Mapped[str] = mapped_column(String(160), default="")
    author_type: Mapped[str] = mapped_column(String(60), default="student")
    diagram_url: Mapped[str] = mapped_column(String(500), default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class VisitSession(Base):
    __tablename__ = "visit_sessions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    persona: Mapped[str] = mapped_column(String(80))
    agenda: Mapped[str] = mapped_column(Text, default="")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=5)
    consent_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class LabZone(Base):
    __tablename__ = "lab_zones"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    floor: Mapped[str] = mapped_column(String(80), default="Ground floor")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Normalized scene coordinates for the configurable illustrative floor plan.
    x: Mapped[float] = mapped_column(Float, default=0.0)
    z: Mapped[float] = mapped_column(Float, default=0.0)
    width: Mapped[float] = mapped_column(Float, default=2.0)
    depth: Mapped[float] = mapped_column(Float, default=1.5)

class AssetPhoto(Base):
    __tablename__ = "asset_photos"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    caption: Mapped[str] = mapped_column(String(500), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(30), default="viewer")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(120), default="")
    outcome: Mapped[str] = mapped_column(String(30), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ChunkVector(Base):
    __tablename__ = "chunk_vectors"
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True)
    model: Mapped[str] = mapped_column(String(120))
    vector_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    hotspot_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(String(40), default="answered_with_evidence")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AssetDocumentLink(Base):
    __tablename__ = "asset_document_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    link_type: Mapped[str] = mapped_column(String(40), default="manual")  # manual, sop, spec_sheet, safety
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AssetProjectLink(Base):
    __tablename__ = "asset_project_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(String(255), default="Used in project development and experimentation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
