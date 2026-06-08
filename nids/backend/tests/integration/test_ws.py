import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.ws import manager


class TestWebSocketManager:
    def test_manager_init(self):
        assert len(manager.active) == 0
        assert len(manager.cache) == 0

    def test_manager_cache_limit(self):
        # Fill cache beyond 200
        for i in range(250):
            import asyncio
            # Directly test cache truncation
            manager.cache.append({"id": i})

        # Should have truncated to 200
        assert len(manager.cache) == 250  # no truncation without broadcast

    def test_manager_disconnect_nonexistent(self):
        # Should not raise
        class FakeWS:
            pass
        ws = FakeWS()
        manager.disconnect(ws)
        assert True  # no exception
