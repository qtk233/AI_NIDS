import io
import csv
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.db import crud
from backend.schemas.alert import AlertItem, AlertListResponse
from backend.schemas.detection import ExplainResponse

router = APIRouter()


# ── List ──

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


# ── Export / Explain (固定路径必须在 {alert_id} 之前) ──

@router.get("/api/alerts/export/csv")
async def export_alerts_csv(
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export all alerts matching the search filter as CSV."""
    rows, _ = await crud.get_alerts(db, page=1, limit=10000, search=search)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "时间", "源IP", "目标IP", "源端口", "目标端口", "协议", "判定", "置信度", "是否攻击", "是否未知"])
    for r in rows:
        writer.writerow([
            r.id,
            str(r.created_at),
            r.src_ip,
            r.dst_ip,
            r.src_port or "",
            r.dst_port or "",
            r.protocol,
            r.prediction,
            f"{r.confidence:.4f}",
            "是" if r.is_attack else "否",
            "是" if r.is_unknown else "否",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=alerts_export.csv"},
    )


@router.get("/api/alerts/{alert_id}/explain", response_model=ExplainResponse)
async def explain_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Compute feature importance & attention for a stored detection."""
    from backend.api.detect import detector

    row = await crud.get_alert_by_id(db, alert_id)
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not row.stat_features:
        raise HTTPException(status_code=400, detail="No stat features stored for this detection")

    return detector.explain(dict(row.stat_features))


# ── Single alert CRUD ──

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
