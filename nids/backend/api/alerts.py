from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.db import crud
from backend.schemas.alert import AlertItem, AlertListResponse

router = APIRouter()


@router.get("/api/alerts", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await crud.get_alerts(db, page=page, limit=limit, search=search)
    return AlertListResponse(
        data=[
            AlertItem(
                id=r.id,
                created_at=str(r.created_at),
                src_ip=r.src_ip,
                dst_ip=r.dst_ip,
                protocol=r.protocol,
                prediction=r.prediction,
                confidence=r.confidence,
                is_unknown=r.is_unknown or False,
                is_attack=r.is_attack or False,
            )
            for r in rows
        ],
        meta={"page": page, "limit": limit, "total": total},
    )


@router.get("/api/alerts/{alert_id}")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    row = await crud.get_alert_by_id(db, alert_id)
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "success": True,
        "data": {
            k: str(v) if not isinstance(v, (int, float, bool, dict, list, type(None))) else v
            for k, v in row.__dict__.items()
            if not k.startswith("_")
        },
    }


@router.delete("/api/alerts/{alert_id}")
async def delete_alert_endpoint(alert_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_alert(db, alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "data": None}
