import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestDetectEndpoints:
    def test_single_detect_model_not_loaded(self):
        resp = client.post("/api/detect/single", json={
            "stat_features": {"packet_count": 10.0, "total_bytes": 5000.0},
        })
        assert resp.status_code == 503

    def test_upload_non_pcap_rejected(self):
        resp = client.post("/api/detect/pcap", files={"file": ("test.txt", b"not a pcap", "text/plain")})
        assert resp.status_code == 503  # model not loaded first, format check after
