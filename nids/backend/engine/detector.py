import torch
from typing import List, Dict
from backend.engine.preprocessor import reassemble_flows
from backend.engine.feature_extractor import extract_stat_features, extract_payload_sequence
from backend.models.nids_model import NIDSModel


CLASS_NAMES = {
    0: "Normal", 1: "DoS", 2: "DDoS", 3: "BruteForce",
    4: "Botnet", 5: "WebAttack", 6: "PortScan", 7: "Infiltration"
}


class Detector:
    def __init__(self, model: NIDSModel, device: str = "cpu", batch_size: int = 64):
        self.model = model.to(device)
        self.device = device
        self.batch_size = batch_size
        self.model.eval()

    @torch.no_grad()
    def detect_pcap(self, pcap_path: str) -> List[Dict]:
        flows = reassemble_flows(pcap_path)
        results = []
        for flow in flows:
            stat_dict = extract_stat_features(flow)
            payload_seq = extract_payload_sequence(flow)
            stat_tensor = torch.tensor(
                list(stat_dict.values()), dtype=torch.float32
            ).unsqueeze(0).to(self.device)
            payload_tensor = torch.tensor(
                payload_seq, dtype=torch.long
            ).unsqueeze(0).to(self.device)
            logits, _ = self.model(stat_tensor, payload_tensor)
            probs = torch.softmax(logits, dim=-1)
            pred_class = probs.argmax(dim=-1).item()
            confidence = probs.max(dim=-1).values.item()
            results.append({
                "src_ip": flow.src_ip,
                "dst_ip": flow.dst_ip,
                "src_port": flow.src_port,
                "dst_port": flow.dst_port,
                "protocol": flow.protocol,
                "prediction": CLASS_NAMES.get(pred_class, "Unknown"),
                "confidence": round(confidence, 4),
                "is_unknown": False,
                "stat_features": stat_dict,
            })
        return results

    def load_model(self, checkpoint_path: str):
        self.model.load_state_dict(
            torch.load(checkpoint_path, map_location=self.device)
        )
        self.model.eval()
