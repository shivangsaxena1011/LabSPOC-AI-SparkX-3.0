from pydantic import BaseModel, Field
from typing import Any

class AssetCreate(BaseModel):
    id: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=200)
    category: str = "equipment"
    zone: str = "Unassigned"
    description: str = ""
    manufacturer: str = ""
    model_number: str = ""
    specifications: dict[str, Any] = {}
    source_reference: str = ""

class AssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    zone: str | None = None
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    specifications: dict[str, Any] | None = None
    source_reference: str | None = None

class VisitCreate(BaseModel):
    persona: str = Field(min_length=2, max_length=80)
    agenda: str = ""
    duration_minutes: int = Field(default=5, ge=2, le=60)
    consent_analytics: bool = False

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str | None = None
    hotspot_id: str | None = None
    language: str = "en"

class TourRequest(BaseModel):
    persona: str = Field(min_length=2, max_length=80)
    agenda: str = ""
    duration_minutes: int = Field(default=5, ge=2, le=60)
    interests: list[str] = []
    session_id: str | None = None

class VisitorEventCreate(BaseModel):
    event_type: str = Field(min_length=2, max_length=40)
    target_id: str = Field(default="", max_length=120)

class ProjectCreate(BaseModel):
    id: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=240)
    problem: str = ""
    methodology: str = ""
    technologies: str = ""
    outcomes: str = ""
    societal_impact: str = ""
    demo_url: str = ""
    author_name: str = ""
    author_type: str = "student"
    diagram_url: str = ""

class ProjectSubmit(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    problem: str = Field(min_length=10, max_length=5000)
    methodology: str = ""
    technologies: str = ""
    outcomes: str = ""
    societal_impact: str = ""
    demo_url: str = ""
    author_name: str = Field(min_length=2, max_length=160)
    author_type: str = Field(default="student", pattern="^(student|faculty|researcher)$")
    diagram_url: str = ""
    related_asset_ids: list[str] = []

class ZoneCreate(BaseModel):
    id: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    description: str = ""
    floor: str = "Ground floor"
    sort_order: int = 0
    x: float = Field(default=0.0, ge=-8, le=8)
    z: float = Field(default=0.0, ge=-6, le=6)
    width: float = Field(default=2.0, ge=0.8, le=6)
    depth: float = Field(default=1.5, ge=0.8, le=5)

class ZoneLayoutUpdate(BaseModel):
    x: float = Field(ge=-8, le=8)
    z: float = Field(ge=-6, le=6)
    width: float = Field(default=2.0, ge=0.8, le=6)
    depth: float = Field(default=1.5, ge=0.8, le=5)

class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=256)

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=256)
    role: str = Field(default="viewer", pattern="^(admin|editor|viewer)$")

class UserStatusUpdate(BaseModel):
    active: bool

class DocumentMetadataUpdate(BaseModel):
    category: str = Field(default="manual", max_length=80)
    version: str = Field(default="1.0", max_length=40)
    description: str = Field(default="", max_length=500)

class LinkCreate(BaseModel):
    asset_id: str = Field(min_length=2, max_length=80)
    target_id: str = Field(min_length=2, max_length=80)
    link_type: str = Field(default="manual", max_length=40)  # manual, sop, spec_sheet, project
    description: str = Field(default="", max_length=255)

class EvaluationCase(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    expected_document_ids: list[str] = []

class EvaluationRequest(BaseModel):
    cases: list[EvaluationCase] = Field(min_length=1, max_length=100)
