import uuid
import tempfile
import os
import torch
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.schemas.detection import PcapDetectResponse, SingleDetectRequest, DetectionResult
from backend.engine.detector import Detector, CLASS_NAMES

router = APIRouter()

detector: Detector | None = None
tasks: dict[str, PcapDetectResponse] = {}


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

    return DetectionResult(
        src_ip="0.0.0.0", dst_ip="0.0.0.0",
        src_port=0, dst_port=0, protocol="TCP",
        prediction=CLASS_NAMES.get(pred, "Unknown"),
        confidence=round(probs.max().item(), 4),
    )
