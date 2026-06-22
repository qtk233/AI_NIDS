import uuid
import tempfile
import os
import json
import logging
import torch
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.schemas.detection import PcapDetectResponse, SingleDetectRequest, DetectionResult, ExplainRequest, ExplainResponse
from backend.engine.detector import Detector, CLASS_NAMES
from backend.models.nids_model import NIDSModel
from backend.core.config import settings
from backend.core.database import async_session
from backend.db import crud
from backend.api.ws import manager
from backend.api.system import increment_counters

logger = logging.getLogger(__name__)

router = APIRouter()

detector: Detector | None = None
tasks: dict[str, PcapDetectResponse] = {}


def init_detector() -> Detector:
    """Create Detector from checkpoint + model config JSON."""
    checkpoint_path = settings.model_checkpoint
    config_path = os.path.join(os.path.dirname(checkpoint_path), "model_config.json")

    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
    else:
        cfg = {
            "stat_input_dim": 77, "payload_vocab_size": 256,
            "d_model": 64, "stat_layers": 2, "payload_layers": 2,
            "n_heads": 4, "ffn_dim": 128, "num_classes": 8, "dropout": 0.1,
        }

    model = NIDSModel(**cfg)
    if os.path.exists(checkpoint_path):
        model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))
    model.eval()
    return Detector(model, device="cpu", batch_size=settings.batch_size)


@router.post("/api/detect/pcap", response_model=PcapDetectResponse)
async def detect_pcap(file: UploadFile = File(...)):
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not file.filename or not file.filename.endswith(".pcap"):
        raise HTTPException(status_code=400, detail="File must be .pcap format")

    task_id = str(uuid.uuid4())
    tasks[task_id] = PcapDetectResponse(
        task_id=task_id, status="processing", total_flows=0, results=[]
    )

    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as tmp:
        tmp.write(await file.read())
        pcap_path = tmp.name

    results = detector.detect_pcap(pcap_path)
    os.unlink(pcap_path)

    detection_results = [DetectionResult(**r) for r in results]

    # ── P0: 数据管道 ──
    # 1. 批量写入 MySQL（单事务）
    try:
        async with async_session() as db:
            await crud.create_detection_logs_batch(db, [
                {
                    "src_ip": r["src_ip"],
                    "dst_ip": r["dst_ip"],
                    "src_port": r["src_port"],
                    "dst_port": r["dst_port"],
                    "protocol": r["protocol"],
                    "prediction": r["prediction"],
                    "confidence": r["confidence"],
                    "is_unknown": r.get("is_unknown", False),
                    "is_attack": r["prediction"] != "Normal",
                    "stat_features": r.get("stat_features"),
                }
                for r in results
            ])
    except Exception:
        logger.warning("Failed to write detection logs to DB", exc_info=True)

    # 2. WebSocket 广播 + 更新计数器
    for dr in detection_results:
        try:
            await manager.broadcast(dr.model_dump())
        except Exception:
            logger.warning("Failed to broadcast via WebSocket", exc_info=True)
        increment_counters(alert_count=1 if dr.prediction != "Normal" else 0)

    tasks[task_id] = PcapDetectResponse(
        task_id=task_id, status="completed",
        total_flows=len(results), results=detection_results
    )
    return tasks[task_id]


@router.get("/api/detect/task/{task_id}", response_model=PcapDetectResponse)
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@router.post("/api/detect/single", response_model=DetectionResult)
async def detect_single(req: SingleDetectRequest):
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    stat_tensor = torch.tensor(
        list(req.stat_features.values()), dtype=torch.float32
    ).unsqueeze(0)
    payload_tensor = torch.tensor(
        req.payload_bytes or [0] * 2560, dtype=torch.long
    ).unsqueeze(0)

    logits, _ = detector.model(stat_tensor, payload_tensor)
    probs = torch.softmax(logits, dim=-1)
    pred = probs.argmax(dim=-1).item()

    result = DetectionResult(
        src_ip="0.0.0.0", dst_ip="0.0.0.0",
        src_port=0, dst_port=0, protocol="TCP",
        prediction=CLASS_NAMES.get(pred, "Unknown"),
        confidence=round(probs.max().item(), 4),
    )

    # 入库 + WebSocket 广播 + 计数器
    try:
        async with async_session() as db:
            await crud.create_detection_log(db, {
                "src_ip": result.src_ip,
                "dst_ip": result.dst_ip,
                "src_port": result.src_port,
                "dst_port": result.dst_port,
                "protocol": result.protocol,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "is_unknown": result.is_unknown,
                "is_attack": result.prediction != "Normal",
                "source": "single",
            })
    except Exception:
        logger.warning("Failed to write single detection to DB", exc_info=True)

    try:
        await manager.broadcast(result.model_dump())
    except Exception:
        logger.warning("Failed to broadcast single detection", exc_info=True)

    increment_counters(alert_count=1 if result.prediction != "Normal" else 0)

    return result


@router.post("/api/detect/explain", response_model=ExplainResponse)
async def explain_detection(req: ExplainRequest):
    """Compute gradient-based feature importance and attention weights."""
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return detector.explain(dict(req.stat_features), req.payload_bytes)
