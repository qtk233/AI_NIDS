from pydantic import BaseModel
from typing import Optional


class SystemStatus(BaseModel):
    running: bool
    model_loaded: bool
    model_version: str
    uptime_seconds: float
    detection_count: int
    alert_count: int


class SystemStats(BaseModel):
    total_detections: int
    total_alerts: int
    accuracy: float
    detection_rate: float
    attack_distribution: dict[str, int]
