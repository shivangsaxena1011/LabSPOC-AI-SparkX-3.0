from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_unknown_question_abstains():
    r = client.post("/api/assistant/query", json={"question": "What is the secret quantum engine serial number?"})
    assert r.status_code == 200
    assert r.json()["status"] in {"insufficient_evidence", "answered_with_evidence"}


def test_admin_write_routes_fail_closed_without_key():
    from app.config import settings
    original = settings.admin_api_key
    settings.admin_api_key = ""
    try:
        r = client.post("/api/assets", json={"id": "TEST-LOCKED-01", "name": "Locked asset"})
        assert r.status_code == 503
    finally:
        settings.admin_api_key = original


def test_admin_write_routes_reject_wrong_key():
    from app.config import settings
    original = settings.admin_api_key
    settings.admin_api_key = "phase2-test-secret"
    try:
        r = client.post("/api/assets", json={"id": "TEST-LOCKED-02", "name": "Locked asset"}, headers={"X-Admin-Key": "incorrect"})
        assert r.status_code == 401
    finally:
        settings.admin_api_key = original


def test_zone_inventory_requires_admin_and_persists():
    from app.config import settings
    original = settings.admin_api_key
    settings.admin_api_key = "phase3-test-secret"
    zone_id = "TEST-ZONE-PHASE3"
    try:
        denied = client.post("/api/zones", json={"id": zone_id, "name": "Test Zone"})
        assert denied.status_code == 401
        created = client.post("/api/zones", json={"id": zone_id, "name": "Test Zone", "description": "Automated test fixture"}, headers={"X-Admin-Key": settings.admin_api_key})
        assert created.status_code == 200
        assert created.json()["verified"] is False
        verified = client.post(f"/api/zones/{zone_id}/verify", headers={"X-Admin-Key": settings.admin_api_key})
        assert verified.status_code == 200
        assert verified.json()["verified"] is True
    finally:
        from app.db import SessionLocal
        from app.models import LabZone
        with SessionLocal() as db:
            item = db.get(LabZone, zone_id)
            if item:
                db.delete(item); db.commit()
        settings.admin_api_key = original

def test_visitor_events_respect_analytics_consent():
    created = client.post("/api/visits", json={"persona": "Academic visitor", "agenda": "Research overview", "duration_minutes": 5, "consent_analytics": False})
    assert created.status_code == 200
    visit_id = created.json()["id"]
    event = client.post(f"/api/visits/{visit_id}/events", json={"event_type": "zone_view", "target_id": "ZONE-1"})
    assert event.status_code == 200
    assert event.json()["recorded"] is False
    summary = client.get(f"/api/visits/{visit_id}/summary")
    assert summary.status_code == 200
    assert summary.json()["event_count"] == 0

def test_visitor_events_are_recorded_after_consent():
    created = client.post("/api/visits", json={"persona": "Industry executive", "agenda": "Applied AI", "duration_minutes": 5, "consent_analytics": True})
    assert created.status_code == 200
    visit_id = created.json()["id"]
    event = client.post(f"/api/visits/{visit_id}/events", json={"event_type": "project_view", "target_id": "PROJECT-TEST"})
    assert event.status_code == 200
    assert event.json()["recorded"] is True
    summary = client.get(f"/api/visits/{visit_id}/summary")
    assert summary.status_code == 200
    assert summary.json()["event_count"] == 1
    assert summary.json()["events"][0]["type"] == "project_view"

def test_visitor_event_allowlist_rejects_unknown_event():
    created = client.post("/api/visits", json={"persona": "Academic visitor", "consent_analytics": True})
    visit_id = created.json()["id"]
    response = client.post(f"/api/visits/{visit_id}/events", json={"event_type": "collect_sensitive_profile", "target_id": "x"})
    assert response.status_code == 422

def test_admin_login_and_bearer_authentication():
    from app.config import settings
    from app.db import SessionLocal
    from app.models import User
    from app.auth import hash_password
    original = (settings.admin_api_key, settings.jwt_secret, settings.admin_username, settings.admin_password)
    settings.admin_api_key = "phase56-legacy-admin-secret"
    settings.jwt_secret = "phase56-jwt-secret-that-is-long-enough-123456"
    settings.admin_username = "phase56-admin"
    settings.admin_password = "phase56-strong-password-123"
    with SessionLocal() as db:
        old = db.query(User).filter(User.username == settings.admin_username).first()
        if old: db.delete(old); db.commit()
    try:
        response = client.post("/api/auth/login", json={"username":settings.admin_username,"password":settings.admin_password})
        assert response.status_code == 200
        token = response.json()["access_token"]
        me = client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == "admin"
    finally:
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == "phase56-admin").first()
            if user: db.delete(user); db.commit()
        settings.admin_api_key, settings.jwt_secret, settings.admin_username, settings.admin_password = original

def test_knowledge_evaluation_requires_admin():
    from app.config import settings
    original = settings.admin_api_key
    settings.admin_api_key = "phase56-eval-secret"
    try:
        denied = client.post("/api/knowledge/evaluate", json={"cases":[{"question":"What is GPU compute?","expected_document_ids":["doc-1"]}]})
        assert denied.status_code == 401
        allowed = client.post("/api/knowledge/evaluate", json={"cases":[{"question":"What is GPU compute?","expected_document_ids":["doc-1"]}]}, headers={"X-Admin-Key":settings.admin_api_key})
        assert allowed.status_code == 200
        assert allowed.json()["evaluated_cases"] == 1
        assert "recall_at_k" in allowed.json()
    finally:
        settings.admin_api_key = original


def test_viewer_role_cannot_use_protected_write_routes():
    from app.config import settings
    from app.db import SessionLocal
    from app.models import User
    original = (settings.admin_api_key, settings.jwt_secret)
    settings.admin_api_key = "phase56-role-admin-secret"
    settings.jwt_secret = "phase56-role-jwt-secret-long-enough-123456"
    username = "phase56-viewer"
    try:
        created = client.post("/api/admin/users", json={"username":username,"password":"viewer-password-123","role":"viewer"}, headers={"X-Admin-Key":settings.admin_api_key})
        assert created.status_code == 200
        login = client.post("/api/auth/login", json={"username":username,"password":"viewer-password-123"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        denied = client.post("/api/assets", json={"id":"VIEWER-BLOCKED-01","name":"No write"}, headers={"Authorization":f"Bearer {token}"})
        assert denied.status_code == 403
    finally:
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user: db.delete(user); db.commit()
        settings.admin_api_key, settings.jwt_secret = original

def test_spatial_scene_returns_explicit_illustrative_status():
    response = client.get("/api/spatial/scene")
    assert response.status_code == 200
    payload = response.json()
    assert payload["scene_type"] == "configurable_illustrative_floor_plan"
    assert payload["is_surveyed"] is False
    assert "survey" in payload["disclaimer"].lower()
    assert isinstance(payload["zones"], list)


def test_zone_layout_update_requires_admin_and_persists_coordinates():
    from app.config import settings
    from app.db import SessionLocal
    from app.models import LabZone
    original = settings.admin_api_key
    settings.admin_api_key = "phase7-layout-test-secret"
    zone_id = "TEST-ZONE-PHASE7"
    try:
        created = client.post("/api/zones", json={"id":zone_id,"name":"Phase 7 Test Zone","x":-1.5,"z":1.0}, headers={"X-Admin-Key":settings.admin_api_key})
        assert created.status_code == 200
        denied = client.patch(f"/api/zones/{zone_id}/layout", json={"x":2,"z":-2,"width":3,"depth":2})
        assert denied.status_code == 401
        updated = client.patch(f"/api/zones/{zone_id}/layout", json={"x":2.5,"z":-1.5,"width":3.2,"depth":2.4}, headers={"X-Admin-Key":settings.admin_api_key})
        assert updated.status_code == 200
        assert updated.json()["x"] == 2.5
        scene = client.get("/api/spatial/scene").json()
        assert any(z["id"] == zone_id and z["width"] == 3.2 for z in scene["zones"])
    finally:
        with SessionLocal() as db:
            zone = db.get(LabZone, zone_id)
            if zone:
                db.delete(zone); db.commit()
        settings.admin_api_key = original


def test_project_public_submission_and_admin_approval():
    from app.config import settings
    # Public user submits a project
    submission = {
        "title": "Autonomous Drone Path Planner",
        "problem": "Indoor navigation in GPS-denied institutional environments requires visual SLAM.",
        "methodology": "ROS2 and ORB-SLAM3 integration with onboard Raspberry Pi 4.",
        "technologies": "Python, ROS2, OpenCV, PyTorch",
        "outcomes": "Sub-10cm positioning accuracy achieved.",
        "societal_impact": "Disaster management and search-and-rescue assistance.",
        "demo_url": "https://github.com/oist/drone-slam",
        "author_name": "Rohan Sharma & Priyanshi Jain",
        "author_type": "student",
        "diagram_url": "https://images.unsplash.com/photo-1527977966376-1c8408f9f108",
        "related_asset_ids": []
    }
    sub_res = client.post("/api/projects/submit", json=submission)
    assert sub_res.status_code == 200
    proj_id = sub_res.json()["id"]
    assert sub_res.json()["status"] == "pending_approval"

    # Should not appear in public visitor list yet
    pub_res = client.get("/api/projects")
    assert pub_res.status_code == 200
    assert not any(p["id"] == proj_id for p in pub_res.json())

    # Admin approves the project
    original = settings.admin_api_key
    settings.admin_api_key = "test-approval-key"
    try:
        app_res = client.post(f"/api/projects/{proj_id}/approve", headers={"X-Admin-Key": settings.admin_api_key})
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "approved"

        # Now it must appear in public visitor list
        pub_res2 = client.get("/api/projects")
        assert any(p["id"] == proj_id for p in pub_res2.json())
    finally:
        # Cleanup
        client.delete(f"/api/projects/{proj_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original


def test_evidence_gate_structure_and_abstention():
    # When no records match, the Evidence Gate must trigger abstention
    res = client.post("/api/assistant/query", json={
        "question": "What is the warp core temperature of the hyperdrive?",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "insufficient_evidence"
    assert "evidence_gate" in data
    assert data["evidence_gate"]["abstention_triggered"] is True
    assert data["evidence_gate"]["verified_grounding"] is False


def test_multiturn_conversation_and_history():
    # 1. Start a visit session
    visit_res = client.post("/api/visits", json={
        "persona": "Undergraduate student",
        "agenda": "Learn about AI robotics lab",
        "duration_minutes": 5,
        "consent_analytics": True
    })
    assert visit_res.status_code == 200
    session_id = visit_res.json()["id"]

    # 2. Ask first question
    q1 = client.post("/api/assistant/query", json={
        "question": "What workstations are installed?",
        "session_id": session_id,
        "language": "en"
    })
    assert q1.status_code == 200

    # 3. Retrieve history
    hist = client.get(f"/api/assistant/history/{session_id}")
    assert hist.status_code == 200
    turns = hist.json()
    assert len(turns) >= 1
    assert turns[0]["question"] == "What workstations are installed?"


def test_spatially_anchored_evidence_graph_endpoints():
    res = client.get("/api/graph/overview")
    assert res.status_code == 200
    graph = res.json()
    assert graph["graph_type"] == "SpatiallyAnchoredEvidenceGraph"
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_agenda_to_tour_compiler_persona_budgeting():
    from app.config import settings
    # Register a verified test asset
    original = settings.admin_api_key
    settings.admin_api_key = "tour-test-key"
    asset_id = "TOUR-GPU-01"
    try:
        client.post("/api/assets", json={
            "id": asset_id,
            "name": "NVIDIA DGX Station A100",
            "category": "compute",
            "zone": "Computing Bay",
            "description": "Multi-GPU AI model training workstation",
            "manufacturer": "NVIDIA",
            "model_number": "DGX-A100"
        }, headers={"X-Admin-Key": settings.admin_api_key})
        client.post(f"/api/assets/{asset_id}/verify", headers={"X-Admin-Key": settings.admin_api_key})

        # Tour compiler for a 2-minute visit must budget <= 2 minutes
        res_2min = client.post("/api/tours/plan", json={
            "persona": "Industry executive",
            "agenda": "High performance computing & AI model serving",
            "duration_minutes": 2,
            "interests": ["gpu", "compute"]
        })
        assert res_2min.status_code == 200
        plan = res_2min.json()
        assert plan["status"] == "planned"
        assert plan["allocated_minutes"] <= 2
        assert len(plan["stops"]) >= 1

        # Tour compiler for a 15-minute visit allocates proportionally
        res_15min = client.post("/api/tours/plan", json={
            "persona": "Academic visitor",
            "agenda": "AI model training and compute infrastructure",
            "duration_minutes": 15,
            "interests": ["compute", "gpu"]
        })
        assert res_15min.status_code == 200
        plan_15 = res_15min.json()
        assert plan_15["status"] == "planned"
        assert plan_15["allocated_minutes"] <= 15
        assert len(plan_15["stops"]) >= 1
    finally:
        client.delete(f"/api/assets/{asset_id}", headers={"X-Admin-Key": settings.admin_api_key})
        settings.admin_api_key = original


def test_faq_analytics_aggregation():
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "frequently_asked_topics" in data
    assert isinstance(data["frequently_asked_topics"], list)
