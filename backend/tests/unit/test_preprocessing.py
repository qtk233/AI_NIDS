import pytest
import torch
from scapy.all import IP, TCP, Ether, Raw
from scapy.utils import wrpcap
import tempfile
import os
from backend.engine.preprocessor import reassemble_flows, Flow


class TestFlow:
    def test_flow_dataclass(self):
        f = Flow(src_ip="1.1.1.1", dst_ip="2.2.2.2", src_port=80, dst_port=443, protocol="TCP")
        assert f.packet_count == 0
        assert f.total_bytes == 0
        assert f.payload_bytes == b""


class TestReassembleFlows:
    def test_basic_flows(self):
        pkts = []
        for i in range(5):
            pkt = Ether()/IP(src="10.0.0.1", dst="10.0.0.2")/TCP(sport=30000, dport=80)/Raw(f"GET /{i}")
            pkts.append(pkt)
        for i in range(3):
            pkt = Ether()/IP(src="10.0.0.3", dst="10.0.0.4")/TCP(sport=50000, dport=443)/Raw(f"TLS-{i}")
            pkts.append(pkt)

        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, pkts)
            pcap_path = f.name

        flows = reassemble_flows(pcap_path)
        os.unlink(pcap_path)

        assert len(flows) == 2
        f1 = next(f for f in flows if f.src_ip == "10.0.0.1")
        assert f1.dst_ip == "10.0.0.2"
        assert f1.src_port == 30000
        assert f1.dst_port == 80
        assert f1.protocol == "TCP"
        assert f1.packet_count == 5

    def test_empty_pcap(self):
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, [])
            pcap_path = f.name

        flows = reassemble_flows(pcap_path)
        os.unlink(pcap_path)
        assert len(flows) == 0

    def test_single_packet_flow_filtered(self):
        pkts = [Ether()/IP(src="1.1.1.1", dst="2.2.2.2")/TCP(sport=1, dport=1)]
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, pkts)
            pcap_path = f.name

        flows = reassemble_flows(pcap_path)
        os.unlink(pcap_path)
        assert len(flows) == 0  # filtered: < 2 packets

    def test_payload_extraction(self):
        pkts = []
        for i in range(3):
            pkts.append(Ether()/IP(src="1.1.1.1", dst="2.2.2.2")/TCP(sport=80, dport=80)/Raw(b"HELLO"))
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, pkts)
            pcap_path = f.name

        flows = reassemble_flows(pcap_path)
        os.unlink(pcap_path)
        assert len(flows) == 1
        assert b"HELLO" in flows[0].payload_bytes
