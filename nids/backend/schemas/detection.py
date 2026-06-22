from pydantic import BaseModel
from typing import Optional, List, Dict


class DetectionResult(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    prediction: str
    confidence: float
    is_unknown: bool = False
    top_features: Optional[List[Dict]] = None


class PcapDetectResponse(BaseModel):
    task_id: str
    status: str
    total_flows: int
    results: List[DetectionResult] = []


class SingleDetectRequest(BaseModel):
    stat_features: Dict[str, float]
    payload_bytes: Optional[List[int]] = None


class ExplainRequest(BaseModel):
    stat_features: Dict[str, float]
    payload_bytes: Optional[List[int]] = None


class ShapItem(BaseModel):
    feature: str
    value: float
    importance: float


class AttentionLayer(BaseModel):
    layer: int
    weights: List[List[List[float]]]  # (n_heads, L, L)


class ExplainResponse(BaseModel):
    shap_values: List[ShapItem]
    attention: List[AttentionLayer]
    prediction: str
    confidence: float
