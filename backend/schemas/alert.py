from pydantic import BaseModel
from typing import Optional, List


class AlertItem(BaseModel):
    id: str
    created_at: str
    src_ip: str
    dst_ip: str
    protocol: str
    prediction: str
    confidence: float
    is_unknown: bool
    is_attack: bool


class AlertListResponse(BaseModel):
    success: bool = True
    data: List[AlertItem]
    meta: dict
