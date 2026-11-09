from pydantic import BaseModel, Field
from typing import Any

class AssetCreate(BaseModel):
    id: str = Field(min_length=2, max_length=80)
    name: str
    category: str = "equipment"
    zone: str = "Unassigned"
    description: str = ""
    manufacturer: str = ""
    model_number: str = ""
    specifications: dict[str, Any] = {}
    source_reference: str = ""

class VisitCreate(BaseModel):
    persona: str
    agenda: str = ""
    duration_minutes: int = Field(default=5, ge=2, le=60)
    consent_analytics: bool = False

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str | None = None
    hotspot_id: str | None = None
    language: str = "en"

class TourRequest(BaseModel):
    persona: str
    agenda: str = ""
    duration_minutes: int = Field(default=5, ge=2, le=60)
    interests: list[str] = []
    session_id: str | None = None

class VisitorEventCreate(BaseModel):
    event_type: str = Field(min_length=2, max_length=40)
    target_id: str = Field(default="", max_length=120)

class ProjectCreate(BaseModel):
    id: str
    title: str
    problem: str = ""
    methodology: str = ""
    technologies: str = ""
    outcomes: str = ""
    societal_impact: str = ""
    demo_url: str = ""


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

class EvaluationCase(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    expected_document_ids: list[str] = []

class EvaluationRequest(BaseModel):
    cases: list[EvaluationCase] = Field(min_length=1, max_length=100)
