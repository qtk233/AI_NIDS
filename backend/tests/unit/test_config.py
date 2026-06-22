import pytest
from backend.core.config import Settings


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.database_url == "mysql+aiomysql://root@localhost:3306/nids"
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000
        assert settings.batch_size == 64
        assert settings.max_pcap_size_mb == 2048
        assert settings.ws_cache_size == 200

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://user:pass@remote:3306/mydb")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("BATCH_SIZE", "128")
        settings = Settings()
        assert settings.database_url == "mysql+aiomysql://user:pass@remote:3306/mydb"
        assert settings.port == 9000
        assert settings.batch_size == 128
