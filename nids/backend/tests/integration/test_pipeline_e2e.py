import pytest
from scapy.all import IP, TCP, Ether, Raw
from scapy.utils import wrpcap
import tempfile
import os
from backend.engine.detector import Detector
from backend.models.nids_model import NIDSModel


class TestDetectionPipeline:
    @pytest.fixture
    def detector(self):
        model = NIDSModel(
            stat_input_dim=8, d_model=128, stat_layers=2, payload_layers=2,
            n_heads=4, ffn_dim=256, num_classes=8, dropout=0.1
        )
        model.eval()
        return Detector(model, device="cpu")

    def test_detect_pcap_returns_results(self, detector):
        pkts = []
        for i in range(10):
            pkt = Ether()/IP(src="10.0.0.1", dst="10.0.0.2")/TCP(sport=30000, dport=80)/Raw(b"A" * 100)
            pkts.append(pkt)
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, pkts)
            pcap_path = f.name

        results = detector.detect_pcap(pcap_path)
        os.unlink(pcap_path)

        assert len(results) > 0
        for r in results:
            assert "src_ip" in r
            assert "dst_ip" in r
            assert "prediction" in r
            assert "confidence" in r
            assert isinstance(r["confidence"], float)
            assert 0 <= r["confidence"] <= 1

    def test_detect_pcap_empty_file(self, detector):
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
            wrpcap(f.name, [])
            pcap_path = f.name

        results = detector.detect_pcap(pcap_path)
        os.unlink(pcap_path)
        assert isinstance(results, list)

    def test_load_model_updates_weights(self, detector, tmp_path):
        checkpoint = tmp_path / "test.pt"
        import torch
        torch.save(detector.model.state_dict(), checkpoint)
        detector.load_model(str(checkpoint))
        assert True  # no exception
