from backend.engine.preprocessor import Flow
from typing import Dict, List
import numpy as np

MAX_PACKETS = 20
BYTES_PER_PACKET = 128
PAYLOAD_SEQ_LEN = MAX_PACKETS * BYTES_PER_PACKET  # 2560


def extract_stat_features(flow: Flow) -> Dict[str, float]:
    duration = flow.duration if flow.duration > 0 else 1e-6
    return {
        "packet_count": float(flow.packet_count),
        "total_bytes": float(flow.total_bytes),
        "duration": float(flow.duration),
        "bytes_per_second": flow.total_bytes / duration,
        "packets_per_second": flow.packet_count / duration,
        "avg_packet_size": flow.total_bytes / max(flow.packet_count, 1),
        "src_port": float(flow.src_port),
        "dst_port": float(flow.dst_port),
    }


def extract_payload_sequence(flow: Flow) -> List[int]:
    result: List[int] = []
    ptr = 0
    for _ in range(MAX_PACKETS):
        chunk = flow.payload_bytes[ptr:ptr + BYTES_PER_PACKET]
        result.extend(list(chunk))
        result.extend([0] * (BYTES_PER_PACKET - len(chunk)))
        ptr += BYTES_PER_PACKET
        if ptr >= len(flow.payload_bytes):
            break

    while len(result) < PAYLOAD_SEQ_LEN:
        result.append(0)
    return result[:PAYLOAD_SEQ_LEN]
