import asyncio
import logging
import random
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Simulated source IPs for traffic generation
_SRC_IPS = ["192.168.1.100", "192.168.1.101", "10.0.0.15", "172.16.0.50", "192.168.1.200"]
_DST_IPS = ["10.0.0.1", "10.0.0.2", "192.168.1.1", "172.16.0.1"]
_PROTOCOLS = ["TCP", "UDP", "ICMP"]
_ATTACK_TYPES = ["Normal", "DoS", "DDoS", "BruteForce", "Botnet", "WebAttack", "PortScan", "Infiltration"]


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self.cache: list[dict] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        for msg in self.cache[-50:]:
            await ws.send_json(msg)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict):
        self.cache.append(message)
        if len(self.cache) > 200:
            self.cache = self.cache[-200:]
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


_STAT_FEATURE_NAMES = [
    "Flow Duration", "Total Fwd Packets", "Total Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Total", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Fwd PSH Flags", "Bwd PSH Flags", "Fwd URG Flags", "Bwd URG Flags",
    "Fwd Header Len", "Bwd Header Len", "Fwd Packets/s", "Bwd Packets/s",
    "Packet Len Min", "Packet Len Max", "Packet Len Mean", "Packet Len Std", "Packet Len Var",
    "FIN Count", "SYN Count", "RST Count", "PSH Count", "ACK Count", "URG Count",
    "CWE Count", "ECE Count", "Down/Up Ratio", "Avg Packet Size",
    "Avg Fwd Segment Size", "Avg Bwd Segment Size",
    "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets", "Subflow Fwd Bytes", "Subflow Bwd Packets", "Subflow Bwd Bytes",
    "Init_Win_bytes_fwd", "Init_Win_bytes_bwd", "act_data_pkt_fwd",
    "min_seg_size_fwd", "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min",
    "Fwd Segment Size Avg", "Bwd Segment Size Avg",
    "Fwd Bytes/Bulk Avg", "Fwd Packets/Bulk Avg",
    "Bwd Bytes/Bulk Avg", "Bwd Packets/Bulk Avg",
    "Fwd Blk Rate Avg", "Bwd Blk Rate Avg",
]


def _random_detection() -> dict:
    """Generate a single simulated detection result."""
    attack_type = random.choices(
        _ATTACK_TYPES,
        weights=[70, 8, 5, 7, 3, 4, 2, 1],
        k=1,
    )[0]

    # Generate plausible fake stat features (77-dim vector)
    stat_features = {}
    for name in _STAT_FEATURE_NAMES:
        # Different attack types have different feature distributions
        if attack_type == "Normal":
            stat_features[name] = round(random.uniform(0, 100), 4)
        elif attack_type in ("DoS", "DDoS"):
            stat_features[name] = round(random.uniform(100, 10000), 4)
        elif attack_type == "PortScan":
            stat_features[name] = round(random.uniform(10, 500), 4)
        else:
            stat_features[name] = round(random.uniform(0, 1000), 4)

    return {
        "src_ip": random.choice(_SRC_IPS),
        "dst_ip": random.choice(_DST_IPS),
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([22, 80, 443, 3306, 8080, 8443]),
        "protocol": random.choice(_PROTOCOLS),
        "prediction": attack_type,
        "confidence": round(random.uniform(0.75, 0.99), 4),
        "is_unknown": attack_type == "Infiltration",
        "stat_features": stat_features,
    }


async def run_simulator(interval: float = 3.0):
    """
    Background task: periodically generate simulated detection data.
    Broadcasts via WebSocket and writes to DB.
    """
    from backend.api.system import increment_counters
    from backend.core.database import async_session
    from backend.db.crud import create_detection_log

    logger.info("Traffic simulator started (interval=%.1fs)", interval)
    while True:
        try:
            detection = _random_detection()
            await manager.broadcast(detection)
            increment_counters(alert_count=1 if detection["prediction"] != "Normal" else 0)

            # Write to DB so history/trends work
            try:
                async with async_session() as db:
                    await create_detection_log(db, {
                        "src_ip": detection["src_ip"],
                        "dst_ip": detection["dst_ip"],
                        "src_port": detection["src_port"],
                        "dst_port": detection["dst_port"],
                        "protocol": detection["protocol"],
                        "prediction": detection["prediction"],
                        "confidence": detection["confidence"],
                        "is_unknown": detection.get("is_unknown", False),
                        "is_attack": detection["prediction"] != "Normal",
                        "stat_features": detection.get("stat_features"),
                        "source": "simulator",
                    })
            except Exception:
                logger.warning("Simulator: failed to write to DB", exc_info=True)
        except Exception:
            logger.warning("Simulator error", exc_info=True)

        await asyncio.sleep(interval)


@router.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
