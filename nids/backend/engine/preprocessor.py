from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from scapy.all import rdpcap, IP, TCP, UDP, IPv6, Raw


@dataclass
class Flow:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packets: List = field(default_factory=list)
    packet_count: int = 0
    total_bytes: int = 0
    start_time: float = 0.0
    duration: float = 0.0
    payload_bytes: bytes = b""


def _flow_key(pkt) -> Tuple[str, str, int, int, str]:
    ip = pkt.getlayer(IP) or pkt.getlayer(IPv6)
    proto = "TCP" if pkt.haslayer(TCP) else "UDP" if pkt.haslayer(UDP) else "Other"
    sport = dport = 0
    if pkt.haslayer(TCP):
        sport, dport = pkt[TCP].sport, pkt[TCP].dport
    elif pkt.haslayer(UDP):
        sport, dport = pkt[UDP].sport, pkt[UDP].dport
    return (ip.src, ip.dst, sport, dport, proto)


def reassemble_flows(pcap_path: str) -> List[Flow]:
    packets = rdpcap(pcap_path)
    flow_map: Dict[Tuple, Flow] = {}

    for pkt in packets:
        try:
            key = _flow_key(pkt)
        except Exception:
            continue

        if key not in flow_map:
            flow_map[key] = Flow(
                src_ip=key[0], dst_ip=key[1],
                src_port=key[2], dst_port=key[3],
                protocol=key[4], start_time=pkt.time,
            )

        flow = flow_map[key]
        flow.packets.append(pkt)
        flow.packet_count += 1
        flow.total_bytes += len(pkt)
        flow.duration = pkt.time - flow.start_time

        raw = pkt.getlayer(Raw)
        if raw is not None:
            flow.payload_bytes += bytes(raw.load)

    return [f for f in flow_map.values() if f.packet_count >= 2]
