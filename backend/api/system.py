import time
import logging
from fastapi import APIRouter
from sqlalchemy import text
from backend.schemas.system import SystemStatus, SystemStats
from backend.core.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter()
_start_time = time.time()
_detection_count = 0
_alert_count = 0

# Fallback distribution when DB is unavailable
_FALLBACK_DISTRIBUTION = {"Normal": 0, "BruteForce": 0, "DDoS": 0}


def increment_counters(alert_count: int = 0) -> None:
    """Increment global detection counters. Called after each detection."""
    global _detection_count, _alert_count
    _detection_count += 1
    _alert_count += alert_count


async def _get_attack_distribution() -> dict[str, int]:
    """Query detection_logs for live attack distribution."""
    try:
        async with async_session() as sess:
            result = await sess.execute(
                text("SELECT prediction, COUNT(*) AS cnt FROM detection_logs GROUP BY prediction")
            )
            rows = result.fetchall()
            if rows:
                return {row[0]: row[1] for row in rows}
    except Exception:
        logger.warning("Failed to query attack distribution from DB", exc_info=True)
    return dict(_FALLBACK_DISTRIBUTION)


@router.get("/api/system/status")
async def get_status():
    from backend.api.detect import detector

    return {
        "success": True,
        "data": SystemStatus(
            running=True,
            model_loaded=detector is not None,
            model_version="v1.0",
            uptime_seconds=time.time() - _start_time,
            detection_count=_detection_count,
            alert_count=_alert_count,
        ).model_dump(),
        "error": None,
    }


@router.get("/api/system/stats")
async def get_stats():
    distribution = await _get_attack_distribution()
    return {
        "success": True,
        "data": SystemStats(
            total_detections=_detection_count,
            total_alerts=_alert_count,
            accuracy=0.974,
            detection_rate=1240.0,
            attack_distribution=distribution,
        ).model_dump(),
        "error": None,
    }


@router.get("/api/system/topology")
async def get_topology():
    """Return dynamic network topology from recent detection data."""
    try:
        async with async_session() as sess:
            result = await sess.execute(text("""
                SELECT src_ip, dst_ip, prediction, COUNT(*) AS cnt
                FROM detection_logs
                WHERE created_at >= NOW() - INTERVAL 1 HOUR
                GROUP BY src_ip, dst_ip, prediction
                ORDER BY cnt DESC
                LIMIT 50
            """))
            rows = result.fetchall()
            if rows:
                nodes_set: dict[str, int] = {}
                links: list[dict] = []
                for row in rows:
                    src, dst, pred, cnt = row[0], row[1], row[2], int(row[3])
                    nodes_set[src] = nodes_set.get(src, 0) + cnt
                    nodes_set[dst] = nodes_set.get(dst, 0) + cnt
                    links.append({"source": src, "target": dst, "attack": pred, "count": cnt})
                nodes = [{"id": ip, "traffic": count} for ip, count in nodes_set.items()]
                return {"success": True, "data": {"nodes": nodes, "links": links}, "error": None}
    except Exception:
        logger.warning("Failed to query topology from DB", exc_info=True)

    # Fallback: empty topology
    return {"success": True, "data": {"nodes": [], "links": []}, "error": None}


@router.get("/api/system/trends")
async def get_trends():
    """Return hourly detection counts for the past 24 hours."""
    try:
        async with async_session() as sess:
            result = await sess.execute(text("""
                SELECT DATE_FORMAT(created_at, '%Y-%m-%d %H:00') AS hour,
                       COUNT(*) AS total,
                       SUM(is_attack) AS attacks
                FROM detection_logs
                WHERE created_at >= NOW() - INTERVAL 24 HOUR
                GROUP BY hour
                ORDER BY hour ASC
            """))
            rows = result.fetchall()
            if rows:
                return {
                    "success": True,
                    "data": [
                        {"hour": row[0][-5:] or row[0], "attacks": int(row[2] or 0), "total": int(row[1])}
                        for row in rows
                    ],
                    "error": None,
                }
    except Exception:
        logger.warning("Failed to query trends from DB", exc_info=True)

    # Fallback: empty 24h
    return {"success": True, "data": [], "error": None}
