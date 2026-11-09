import pytest
import os
from sqlalchemy import select
from starlette.testclient import TestClient
from app.main import app
from app.storage import LocalStorageAdapter, S3StorageAdapter, get_storage

client = TestClient(app)

def test_readiness_probe():
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["storage"]["status"] == "ok"
    assert "ai_engine" in data["checks"]

def test_correlation_id_and_timing_headers():
    custom_id = "test-corr-id-12345"
    res = client.get("/api/health", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_id
    assert "X-Response-Time-MS" in res.headers
    assert float(res.headers["X-Response-Time-MS"]) >= 0.0

def test_auto_generated_correlation_id():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert len(res.headers["X-Request-ID"]) >= 8

def test_admin_system_metrics():
    from app.db import SessionLocal
    from app.models import User
    from app.auth import hash_password, issue_token
    
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.username == "test_metrics_admin")).scalar_one_or_none()
        if not user:
            user = User(
                id="test-metrics-admin-id",
                username="test_metrics_admin",
                password_hash=hash_password("admin_secret_123"),
                role="admin",
                active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = issue_token(user)
        headers = {"Authorization": f"Bearer {token}"}
        metrics_res = client.get("/api/admin/system/metrics", headers=headers)
        assert metrics_res.status_code == 200
        data = metrics_res.json()
        assert "inventory_metrics" in data
        assert "uptime_seconds" in data
        assert "database_engine" in data
        assert "storage_backend" in data
    finally:
        db.close()

def test_local_storage_adapter(tmp_path):
    adapter = LocalStorageAdapter(base_dir=tmp_path)
    
    # Save file
    test_bytes = b"Hello LabSPOC AI Storage"
    saved_key = adapter.save("test_docs/sample.txt", test_bytes, "text/plain")
    assert adapter.exists("test_docs/sample.txt")
    
    # Load file
    loaded = adapter.load("test_docs/sample.txt")
    assert loaded == test_bytes
    
    # URL generation
    url = adapter.get_url("test_docs/sample.txt")
    assert "test_docs/sample.txt" in url
    
    # Health check
    hc = adapter.health_check()
    assert hc["status"] == "ok"
    assert hc["writable"] is True
    
    # Path traversal rejection
    with pytest.raises(ValueError):
        adapter.save("../outside.txt", b"evil payload")

    # Delete
    assert adapter.delete("test_docs/sample.txt")
    assert not adapter.exists("test_docs/sample.txt")

def test_s3_storage_adapter_interface():
    # Verify contract without live credentials
    s3 = S3StorageAdapter(
        bucket_name="labspoc-test-bucket",
        endpoint_url="https://fake-s3.example.com",
        access_key_id="fake_key",
        secret_access_key="fake_secret",
        region_name="ap-south-1",
        public_url_prefix="https://cdn.labspoc.oist.edu"
    )
    url = s3.get_url("documents/dgx1_sop.pdf")
    assert url == "https://cdn.labspoc.oist.edu/documents/dgx1_sop.pdf"
