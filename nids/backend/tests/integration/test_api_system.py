import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestSystemEndpoints:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["service"] == "NIDS API"

    def test_status(self):
        resp = client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is True
        assert "model_loaded" in data
        assert "uptime_seconds" in data

    def test_stats(self):
        resp = client.get("/api/system/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_detections" in data
        assert "accuracy" in data
        assert "attack_distribution" in data


class TestModelEndpoints:
    def test_model_info(self):
        resp = client.get("/api/model/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["version"] == "v1.0"
        assert data["data"]["params_count"] == 4200000

    def test_model_metrics(self):
        resp = client.get("/api/model/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "accuracy" in data["data"]
        assert "confusion_matrix" in data["data"]
        assert "class_names" in data["data"]

    def test_model_reload(self):
        resp = client.post("/api/model/reload")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
