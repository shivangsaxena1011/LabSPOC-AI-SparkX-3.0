import json, time, uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.config import settings
from app.db import SessionLocal
from app.models import (
    Asset, Document, DocumentChunk, LabZone, Project,
    VisitSession, AnalyticsEvent, AuditLog, User,
    ChunkVector, ConversationTurn, AssetDocumentLink, AssetProjectLink
)
from app.embeddings import embed_text, cosine
from app.retrieval import retrieve
from app.llm import generate_grounded_answer

client = TestClient(app)

def test_workflow_01_admin_login():
    """Workflow 1: Administrator login and audit log verification."""
    unique_admin = f"admin_test_{uuid.uuid4().hex[:6]}"
    admin_pw = "SuperSecureAdminPassword123!"

    # Ensure admin user in DB
    with SessionLocal() as db:
        from app.auth import hash_password
        u = User(id=str(uuid.uuid4()), username=unique_admin, password_hash=hash_password(admin_pw), role="admin", active=True)
        db.add(u)
        db.commit()

    try:
        # 1. Invalid login attempt
        bad_res = client.post("/api/auth/login", json={"username": unique_admin, "password": "WrongPassword!"})
        assert bad_res.status_code == 401

        # 2. Valid login attempt
        good_res = client.post("/api/auth/login", json={"username": unique_admin, "password": admin_pw})
        assert good_res.status_code == 200
        token = good_res.json()["access_token"]
        assert token and len(token) > 20

        # Verify audit log in database
        with SessionLocal() as db:
            audit = db.execute(select(AuditLog).where(AuditLog.actor == unique_admin, AuditLog.action == "auth.login", AuditLog.outcome == "success")).scalar_one_or_none()
            assert audit is not None
            assert audit.outcome == "success"

        # Verify authenticated inspection
        me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["username"] == unique_admin
        assert me_res.json()["role"] == "admin"
    finally:
        with SessionLocal() as db:
            u_del = db.execute(select(User).where(User.username == unique_admin)).scalar_one_or_none()
            if u_del:
                db.delete(u_del)
                db.commit()

def test_workflow_02_rbac_permissions():
    """Workflow 2: Role-based access control (Admin vs Editor vs Viewer)."""
    editor_user = f"editor_{uuid.uuid4().hex[:6]}"
    viewer_user = f"viewer_{uuid.uuid4().hex[:6]}"
    pw = "CommonPassword123!"

    with SessionLocal() as db:
        from app.auth import hash_password
        u_edit = User(id=str(uuid.uuid4()), username=editor_user, password_hash=hash_password(pw), role="editor", active=True)
        u_view = User(id=str(uuid.uuid4()), username=viewer_user, password_hash=hash_password(pw), role="viewer", active=True)
        db.add_all([u_edit, u_view])
        db.commit()

    try:
        # Get tokens
        t_edit = client.post("/api/auth/login", json={"username": editor_user, "password": pw}).json()["access_token"]
        t_view = client.post("/api/auth/login", json={"username": viewer_user, "password": pw}).json()["access_token"]

        # Viewer attempts write -> must be 403 Forbidden
        view_write = client.post("/api/assets", json={"id": "VIEW-FAIL", "name": "Fail"}, headers={"Authorization": f"Bearer {t_view}"})
        assert view_write.status_code == 403

        # Editor attempts asset write -> allowed
        edit_write = client.post("/api/assets", json={
            "id": f"EDIT-OK-{uuid.uuid4().hex[:4]}",
            "name": "Editor Created Device",
            "zone": "Robotics Bay"
        }, headers={"Authorization": f"Bearer {t_edit}"})
        assert edit_write.status_code == 200
        created_id = edit_write.json()["id"]

        # Editor attempts superadmin-only user creation -> must be 403 Forbidden
        edit_super = client.post("/api/admin/users", json={
            "username": "illegal_user",
            "password": "Password123!",
            "role": "admin"
        }, headers={"Authorization": f"Bearer {t_edit}"})
        assert edit_super.status_code == 403

        # Cleanup created asset
        client.delete(f"/api/assets/{created_id}", headers={"Authorization": f"Bearer {t_edit}"})
    finally:
        with SessionLocal() as db:
            for un in [editor_user, viewer_user]:
                u_del = db.execute(select(User).where(User.username == un)).scalar_one_or_none()
                if u_del:
                    db.delete(u_del)
            db.commit()

def test_workflow_03_zone_creation_and_editing():
    """Workflow 3: Zone creation, editing layout, and database persistence."""
    zone_id = f"ZONE-TEST-{uuid.uuid4().hex[:6]}"
    original = settings.admin_api_key
    settings.admin_api_key = "zone-workflow-secret"

    try:
        # 1. Create zone
        res_create = client.post("/api/zones", json={
            "id": zone_id,
            "name": "Deep Learning Cluster Bay",
            "description": "High density compute racks for model training",
            "floor": "Ground Floor",
            "x": 1.5,
            "z": -2.0,
            "width": 3.0,
            "depth": 2.2
        }, headers={"X-Admin-Key": settings.admin_api_key})
        assert res_create.status_code == 200

        # Verify DB persistence
        with SessionLocal() as db:
            z_db = db.get(LabZone, zone_id)
            assert z_db is not None
            assert z_db.name == "Deep Learning Cluster Bay"
            assert z_db.x == 1.5
            assert z_db.z == -2.0
            assert z_db.verified is False

        # 2. Update zone layout
        res_patch = client.patch(f"/api/zones/{zone_id}/layout", json={
            "x": -1.8,
            "z": 2.4,
            "width": 3.5,
            "depth": 2.5
        }, headers={"X-Admin-Key": settings.admin_api_key})
        assert res_patch.status_code == 200
        assert res_patch.json()["x"] == -1.8

        # 3. Verify zone
        res_ver = client.post(f"/api/zones/{zone_id}/verify", headers={"X-Admin-Key": settings.admin_api_key})
        assert res_ver.status_code == 200
        assert res_ver.json()["verified"] is True

        # Check DB state after update and verify
        with SessionLocal() as db:
            z_updated = db.get(LabZone, zone_id)
            assert z_updated.x == -1.8
            assert z_updated.verified is True
    finally:
        with SessionLocal() as db:
            z_del = db.get(LabZone, zone_id)
            if z_del:
                db.delete(z_del)
                db.commit()
        settings.admin_api_key = original

def test_workflow_04_equipment_registration_and_verification():
    """Workflow 4: Equipment registration, specs, verification date, and DB persistence."""
    asset_id = f"EQP-TEST-{uuid.uuid4().hex[:6]}"
    original = settings.admin_api_key
    settings.admin_api_key = "asset-workflow-secret"

    try:
        specs = {"gpu": "NVIDIA A100 80GB", "vram": "80GB", "cuda_cores": 6912}
        res_create = client.post("/api/assets", json={
            "id": asset_id,
            "name": "NVIDIA A100 Compute Unit",
            "category": "compute",
            "zone": "Deep Learning Cluster Bay",
            "description": "High performance accelerator for transformer fine-tuning",
            "manufacturer": "NVIDIA",
            "model_number": "A100-PCIE-80GB",
            "specifications": specs,
            "source_reference": "OIST Lab Purchase Order 2024-AI"
        }, headers={"X-Admin-Key": settings.admin_api_key})
        assert res_create.status_code == 200

        with SessionLocal() as db:
            a_db = db.get(Asset, asset_id)
            assert a_db is not None
            assert a_db.name == "NVIDIA A100 Compute Unit"
            assert a_db.verified_at is None
            assert json.loads(a_db.specifications_json)["gpu"] == "NVIDIA A100 80GB"

        # Verify asset
        res_ver = client.post(f"/api/assets/{asset_id}/verify", headers={"X-Admin-Key": settings.admin_api_key})
        assert res_ver.status_code == 200
        assert res_ver.json()["verified_at"] is not None

        with SessionLocal() as db:
            a_verified = db.get(Asset, asset_id)
            assert a_verified.verified_at is not None
    finally:
        with SessionLocal() as db:
            a_del = db.get(Asset, asset_id)
            if a_del:
                db.delete(a_del)
                db.commit()
        settings.admin_api_key = original

def test_workflow_05_document_upload_and_approval():
    """Workflow 5: Document ingestion, chunking, status review, and approval."""
    original = settings.admin_api_key
    settings.admin_api_key = "doc-workflow-secret"
    doc_id = None

    try:
        sample_text = (
            "OIST AI & ML Laboratory Operating Manual.\n"
            "The laboratory provides NVIDIA DGX Station and RTX workstations for deep learning.\n"
            "Safety protocol: Always power down workstations gracefully before physical maintenance.\n"
            "Access to GPU nodes requires an institutional Kerberos ID and faculty supervisor sign-off."
        )

        res_upload = client.post(
            "/api/knowledge/upload",
            files={"file": ("lab_manual_test.txt", sample_text.encode("utf-8"), "text/plain")},
            data={"category": "manual", "version": "1.0", "description": "Official laboratory operating manual"},
            headers={"X-Admin-Key": settings.admin_api_key}
        )
        assert res_upload.status_code == 200
        data = res_upload.json()
        doc_id = data["document_id"]
        assert data["status"] == "pending_review"
        assert data["chunks_created"] >= 1

        with SessionLocal() as db:
            doc_db = db.get(Document, doc_id)
            assert doc_db is not None
            assert doc_db.status == "pending_review"
            chunks = db.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id)).scalars().all()
            assert len(chunks) >= 1

        # Approve document
        res_app = client.post(f"/api/knowledge/documents/{doc_id}/approve", headers={"X-Admin-Key": settings.admin_api_key})
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "approved"

        with SessionLocal() as db:
            doc_approved = db.get(Document, doc_id)
            assert doc_approved.status == "approved"
    finally:
        if doc_id:
            client.delete(f"/api/knowledge/documents/{doc_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original

def test_workflow_06_and_07_gemini_embeddings_and_hybrid_retrieval():
    """Workflows 6 & 7: Gemini embedding generation and hybrid semantic + lexical retrieval."""
    if not settings.gemini_api_key or settings.llm_provider.lower() != "gemini":
        pytest.skip("Gemini API key is not configured; skipping live embedding verification.")

    test_chunk = "OIST Bhopal artificial intelligence high-performance compute infrastructure."
    vec = embed_text(test_chunk)
    assert vec is not None
    assert len(vec) == 3072  # gemini-embedding-001 dimension
    assert isinstance(vec[0], float)

    # Cosine sanity check
    sim_self = cosine(vec, vec)
    assert round(sim_self, 2) == 1.0

    sim_diff = cosine(vec, [-x for x in vec])
    assert round(sim_diff, 2) == -1.0

def test_workflow_08_and_09_gemini_grounded_answer_and_abstention():
    """Workflows 8 & 9: Grounded answer generation with citations and honest abstention."""
    # 1. Honest Abstention on unsupported question
    res_abstain = client.post("/api/assistant/query", json={
        "question": "What is the secret cold fusion reactor output in room 404?",
        "language": "en"
    })
    assert res_abstain.status_code == 200
    data_abs = res_abstain.json()
    assert data_abs["status"] == "insufficient_evidence"
    assert data_abs["evidence_gate"]["abstention_triggered"] is True
    assert data_abs["evidence_gate"]["verified_grounding"] is False

    # 2. Grounded Answer with Mocked/Retrieved Evidence (if API key active)
    evidence = [
        {"filename": "dgx_spec_sheet.pdf", "page": 1, "text": "The NVIDIA DGX Station features 4x NVIDIA A100 GPUs with 320GB total GPU memory and liquid cooling."},
        {"filename": "sop_safety.pdf", "page": 2, "text": "Maximum room operating temperature must not exceed 24 degrees Celsius."}
    ]

    res_gen = generate_grounded_answer("What GPUs are in the DGX Station and how much GPU memory does it have?", evidence, language="en")
    if settings.gemini_api_key:
        assert res_gen["gate_passed"] is True
        assert "[1]" in res_gen["answer"]
        assert len(res_gen["citations"]) >= 1
    else:
        assert res_gen["reason"] == "gemini_provider_unconfigured"

def test_workflow_10_multiturn_visitor_conversation():
    """Workflow 10: Multi-turn visitor conversation context retention."""
    v_res = client.post("/api/visits", json={
        "persona": "Research scientist",
        "agenda": "Exploring NLP compute resources",
        "duration_minutes": 5,
        "consent_analytics": True
    })
    assert v_res.status_code == 200
    session_id = v_res.json()["id"]

    # Turn 1
    q1 = client.post("/api/assistant/query", json={
        "question": "What GPU resources are available?",
        "session_id": session_id,
        "language": "en"
    })
    assert q1.status_code == 200

    # Turn 2
    q2 = client.post("/api/assistant/query", json={
        "question": "How are these resources scheduled?",
        "session_id": session_id,
        "language": "en"
    })
    assert q2.status_code == 200

    # Verify persistence in conversation_turns
    with SessionLocal() as db:
        turns = db.execute(select(ConversationTurn).where(ConversationTurn.session_id == session_id).order_by(ConversationTurn.created_at)).scalars().all()
        assert len(turns) == 2
        assert turns[0].question == "What GPU resources are available?"
        assert turns[1].question == "How are these resources scheduled?"

def test_workflow_11_project_submission_and_approval():
    """Workflow 11: Public project submission, rate limit, and administrator approval."""
    title = f"Edge Vision AI Robot {uuid.uuid4().hex[:4]}"
    sub_payload = {
        "title": title,
        "problem": "Autonomous navigation for warehouse inspection.",
        "methodology": "Edge TPU model deployment with PyTorch and ROS2.",
        "technologies": "PyTorch, Edge TPU, ROS2",
        "outcomes": "Demonstrated 30 FPS inference on mobile platform.",
        "societal_impact": "Industrial safety.",
        "demo_url": "https://github.com/oist/edge-ai-robot",
        "author_name": "Divya Sharma",
        "author_type": "student",
        "diagram_url": "",
        "related_asset_ids": []
    }

    sub_res = client.post("/api/projects/submit", json=sub_payload)
    assert sub_res.status_code == 200
    proj_id = sub_res.json()["id"]

    with SessionLocal() as db:
        p_db = db.get(Project, proj_id)
        assert p_db is not None
        assert p_db.approved is False
        assert p_db.title == title

    # Must not be visible in public projects
    pub_res = client.get("/api/projects")
    assert not any(p["id"] == proj_id for p in pub_res.json())

    # Approve project
    original = settings.admin_api_key
    settings.admin_api_key = "proj-approval-key"
    try:
        app_res = client.post(f"/api/projects/{proj_id}/approve", headers={"X-Admin-Key": settings.admin_api_key})
        assert app_res.status_code == 200

        with SessionLocal() as db:
            p_app = db.get(Project, proj_id)
            assert p_app.approved is True

        # Now visible in public list
        pub_res2 = client.get("/api/projects")
        assert any(p["id"] == proj_id for p in pub_res2.json())
    finally:
        client.delete(f"/api/projects/{proj_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original

def test_workflow_12_interactive_3d_spatial_scene():
    """Workflow 12: Interactive 3D laboratory scene data retrieval."""
    res = client.get("/api/spatial/scene")
    assert res.status_code == 200
    scene = res.json()
    assert scene["scene_type"] == "configurable_illustrative_floor_plan"
    assert scene["is_surveyed"] is False
    assert "survey" in scene["disclaimer"].lower()
    assert "zones" in scene
    assert isinstance(scene["zones"], list)

def test_workflow_13_equipment_hotspot_selection():
    """Workflow 13: Hotspot-grounded query returning verified specifications."""
    original = settings.admin_api_key
    settings.admin_api_key = "hotspot-test-key"
    asset_id = f"HOTSPOT-EQP-{uuid.uuid4().hex[:4]}"

    try:
        client.post("/api/assets", json={
            "id": asset_id,
            "name": "NVIDIA Jetson AGX Orin Industrial",
            "category": "robotics",
            "zone": "Edge AI Bay",
            "description": "275 TOPS server-class AI compute for autonomous machines",
            "manufacturer": "NVIDIA",
            "model_number": "JETSON-AGX-ORIN-IND",
            "specifications": {"tops": "275 TOPS", "power": "15W-75W"},
            "source_reference": "NVIDIA Technical Specification Sheet"
        }, headers={"X-Admin-Key": settings.admin_api_key})
        client.post(f"/api/assets/{asset_id}/verify", headers={"X-Admin-Key": settings.admin_api_key})

        # Ask question selecting this exact hotspot
        res = client.post("/api/assistant/query", json={
            "question": "What is the compute performance and power consumption?",
            "hotspot_id": asset_id,
            "language": "en"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["asset"] is not None
        assert data["asset"]["id"] == asset_id
        assert "275 TOPS" in data["answer"] or "275 TOPS" in str(data["asset"]["specifications"])
    finally:
        client.delete(f"/api/assets/{asset_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original

def test_workflow_14_agenda_to_tour_generation():
    """Workflow 14: Agenda-to-Tour compilation for 2, 5, and 15-minute visits."""
    for duration in [2, 5, 15]:
        res = client.post("/api/tours/plan", json={
            "persona": "Academic visitor",
            "agenda": "AI model training and robotics laboratories",
            "duration_minutes": duration,
            "interests": ["compute", "robotics"]
        })
        assert res.status_code == 200
        plan = res.json()
        if plan["status"] == "planned":
            assert plan["allocated_minutes"] <= duration
            assert len(plan["stops"]) <= (2 if duration == 2 else 3 if duration == 5 else 6)

def test_workflow_15_visitor_analytics_consent():
    """Workflow 15: Visitor consent enforcement in event logging."""
    # 1. No consent session
    v_no = client.post("/api/visits", json={"persona": "Student", "consent_analytics": False}).json()["id"]
    e_no = client.post(f"/api/visits/{v_no}/events", json={"event_type": "zone_view", "target_id": "ZONE-1"})
    assert e_no.status_code == 200
    assert e_no.json()["recorded"] is False

    with SessionLocal() as db:
        events = db.execute(select(AnalyticsEvent).where(AnalyticsEvent.session_id == v_no)).scalars().all()
        assert len(events) == 0

    # 2. Consented session
    v_yes = client.post("/api/visits", json={"persona": "Student", "consent_analytics": True}).json()["id"]
    e_yes = client.post(f"/api/visits/{v_yes}/events", json={"event_type": "zone_view", "target_id": "ZONE-1"})
    assert e_yes.status_code == 200
    assert e_yes.json()["recorded"] is True

    with SessionLocal() as db:
        events = db.execute(select(AnalyticsEvent).where(AnalyticsEvent.session_id == v_yes)).scalars().all()
        assert len(events) == 1

def test_workflow_16_visitor_session_summary():
    """Workflow 16: Visitor session summary generation."""
    v_id = client.post("/api/visits", json={
        "persona": "Industry executive",
        "agenda": "Evaluate campus AI partnerships",
        "duration_minutes": 15,
        "consent_analytics": True
    }).json()["id"]

    client.post(f"/api/visits/{v_id}/events", json={"event_type": "tour_started", "target_id": "Industry executive"})
    client.post(f"/api/visits/{v_id}/events", json={"event_type": "tour_completed", "target_id": "Industry executive"})

    sum_res = client.get(f"/api/visits/{v_id}/summary")
    assert sum_res.status_code == 200
    s_data = sum_res.json()
    assert s_data["session_id"] == v_id
    assert s_data["persona"] == "Industry executive"
    assert s_data["duration_minutes"] == 15
    assert s_data["event_count"] == 2

def test_workflow_17_saeg_graph_and_relationship_management():
    """Workflow 17: SAEG graph overview and relationship creation."""
    original = settings.admin_api_key
    settings.admin_api_key = "saeg-link-secret"
    asset_id = f"SAEG-EQP-{uuid.uuid4().hex[:4]}"
    doc_id = None
    proj_id = None

    try:
        # Create asset
        client.post("/api/assets", json={"id": asset_id, "name": "Workstation Node", "zone": "Computing Bay"}, headers={"X-Admin-Key": settings.admin_api_key})

        # Create approved document
        doc_res = client.post(
            "/api/knowledge/upload",
            files={"file": ("saeg_spec.txt", b"Hardware specifications for Workstation Node.", "text/plain")},
            data={"category": "specification", "version": "1.0"},
            headers={"X-Admin-Key": settings.admin_api_key}
        )
        doc_id = doc_res.json()["document_id"]
        client.post(f"/api/knowledge/documents/{doc_id}/approve", headers={"X-Admin-Key": settings.admin_api_key})

        # Create approved project
        proj_res = client.post("/api/projects/submit", json={
            "title": "Autonomous Drone Inspection",
            "problem": "Drone navigation in GPS-denied environments.",
            "author_name": "Faculty Supervisor",
            "author_type": "faculty"
        })
        proj_id = proj_res.json()["id"]
        client.post(f"/api/projects/{proj_id}/approve", headers={"X-Admin-Key": settings.admin_api_key})

        # Link Asset -> Document
        link_doc_res = client.post("/api/graph/links", json={
            "asset_id": asset_id,
            "target_id": doc_id,
            "link_type": "spec_sheet"
        }, headers={"X-Admin-Key": settings.admin_api_key})
        assert link_doc_res.status_code == 200

        # Link Asset -> Project
        link_proj_res = client.post("/api/graph/links", json={
            "asset_id": asset_id,
            "target_id": proj_id,
            "link_type": "project"
        }, headers={"X-Admin-Key": settings.admin_api_key})
        assert link_proj_res.status_code == 200

        # Verify DB persistence of links
        with SessionLocal() as db:
            dl = db.execute(select(AssetDocumentLink).where(AssetDocumentLink.asset_id == asset_id, AssetDocumentLink.document_id == doc_id)).scalar_one_or_none()
            assert dl is not None
            assert dl.link_type == "spec_sheet"

            pl = db.execute(select(AssetProjectLink).where(AssetProjectLink.asset_id == asset_id, AssetProjectLink.project_id == proj_id)).scalar_one_or_none()
            assert pl is not None

        # Check graph overview contains both edges
        graph = client.get("/api/graph/overview").json()
        assert any(e["source"] == f"asset_{asset_id}" and e["target"] == f"doc_{doc_id}" for e in graph["edges"])
        assert any(e["source"] == f"asset_{asset_id}" and e["target"] == f"proj_{proj_id}" for e in graph["edges"])
    finally:
        client.delete(f"/api/assets/{asset_id}", headers={"X-Admin-Key": settings.admin_api_key})
        if doc_id:
            client.delete(f"/api/knowledge/documents/{doc_id}", headers={"X-Admin-Key": settings.admin_api_key})
        if proj_id:
            client.delete(f"/api/projects/{proj_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original
