from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import DetectionLog
from typing import Optional, List
import uuid


async def create_detection_log(db: AsyncSession, data: dict) -> DetectionLog:
    log = DetectionLog(id=str(uuid.uuid4()), **data)
    db.add(log)
    await db.commit()
    return log


async def create_detection_logs_batch(db: AsyncSession, records: list[dict]) -> list[DetectionLog]:
    """Batch insert detection logs in a single transaction."""
    logs = [DetectionLog(id=str(uuid.uuid4()), **r) for r in records]
    db.add_all(logs)
    await db.commit()
    return logs


async def get_alerts(
    db: AsyncSession,
    page: int = 1,
    limit: int = 50,
    attack_only: bool = False,
    search: Optional[str] = None
) -> tuple[List[DetectionLog], int]:
    query = select(DetectionLog)
    if attack_only:
        query = query.where(DetectionLog.is_attack == True)
    if search:
        query = query.where(
            (DetectionLog.src_ip.contains(search)) |
            (DetectionLog.dst_ip.contains(search))
        )
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(DetectionLog.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit)
    rows = (await db.execute(query)).scalars().all()
    return list(rows), int(total)


async def get_alert_by_id(db: AsyncSession, alert_id: str) -> Optional[DetectionLog]:
    result = await db.execute(select(DetectionLog).where(DetectionLog.id == alert_id))
    return result.scalar_one_or_none()


async def delete_alert(db: AsyncSession, alert_id: str) -> bool:
    result = await db.execute(delete(DetectionLog).where(DetectionLog.id == alert_id))
    await db.commit()
    return result.rowcount > 0
