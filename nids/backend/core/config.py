from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://root@localhost:3306/nids"
    model_checkpoint: str = "checkpoints/best.pt"
    host: str = "127.0.0.1"
    port: int = 8000
    batch_size: int = 64
    max_pcap_size_mb: int = 2048
    ws_cache_size: int = 200

    model_config = {"env_file": ".env"}


settings = Settings()
