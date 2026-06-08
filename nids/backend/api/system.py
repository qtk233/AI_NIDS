import time
from fastapi import APIRouter
from backend.schemas.system import SystemStatus, SystemStats

router = APIRouter()
_start_time = time.time()
_detection_count = 0
_alert_count = 0


@router.get("/api/system/status", response_model=SystemStatus)
async def get_status():
    from backend.api.detect import detector
    return SystemStatus(
        running=True,
        model_loaded=detector is not None,
        model_version="v1.0",
        uptime_seconds=time.time() - _start_time,
        detection_count=_detection_count,
        alert_count=_alert_count,
    )


@router.get("/api/system/stats", response_model=SystemStats)
async def get_stats():
    return SystemStats(
        total_detections=_detection_count,
        total_alerts=_alert_count,
        accuracy=0.974,
        detection_rate=1240.0,
        attack_distribution={"BruteForce": 120, "DDoS": 45, "Normal": 12000},
    )
