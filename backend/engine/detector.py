import torch
from typing import List, Dict
from backend.engine.preprocessor import reassemble_flows
from backend.engine.feature_extractor import extract_stat_features, extract_payload_sequence
from backend.models.nids_model import NIDSModel


CLASS_NAMES = {
    0: "Normal", 1: "DoS", 2: "DDoS", 3: "BruteForce",
    4: "Botnet", 5: "WebAttack", 6: "PortScan", 7: "Infiltration"
}

# Feature names for the 77-dim stat vector (first 77 of 80 dims)
_FEATURE_NAMES = [
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

    def explain(self, stat_features: dict[str, float], payload_seq: list[int] | None = None) -> dict:
        """
        Compute gradient-based feature importance and attention weights.

        Returns dict with:
          - shap_values: [{feature, value, importance}] sorted descending
          - attention: list of (layer, head, weights) for heatmap rendering
          - prediction: str
          - confidence: float
        """
        self.model.eval()

        # Prepare inputs with gradient tracking on stat features
        stat_vals = list(stat_features.values())
        stat_tensor = torch.tensor([stat_vals], dtype=torch.float32, device=self.device)
        stat_tensor.requires_grad_(True)

        if payload_seq is None:
            payload_seq = [0] * 2560
        payload_tensor = torch.tensor([payload_seq], dtype=torch.long, device=self.device)

        # ── Capture attention weights via hooks ──
        captured_attn: list[dict] = []
        hooks = []

        def make_hook(layer_idx: int):
            def hook_fn(module, _input, _output):
                # _output from MultiheadAttention.forward(batch_first=True) is a tuple
                # when need_weights=True: (attn_output, attn_weights)
                if isinstance(_output, tuple) and len(_output) == 2:
                    attn_weights = _output[1]  # (B, n_heads, L, L) or (B, n_heads, L, S)
                    if attn_weights is not None:
                        captured_attn.append({
                            "layer": layer_idx,
                            "weights": attn_weights.detach().cpu().tolist(),
                        })
            return hook_fn

        # Register hooks on payload encoder's self-attention layers
        for i, layer in enumerate(self.model.payload_encoder.transformer.layers):
            h = layer.self_attn.register_forward_hook(make_hook(i))
            hooks.append(h)

        # ── Forward pass ──
        logits, _ = self.model(stat_tensor, payload_tensor)
        probs = torch.softmax(logits, dim=-1)
        pred_class = probs.argmax(dim=-1).item()
        confidence = probs.max(dim=-1).item()

        # ── Gradient-based feature importance ──
        self.model.zero_grad()
        logits[0, pred_class].backward()

        grad = stat_tensor.grad.detach().abs().squeeze().cpu().tolist()
        inp = stat_tensor.detach().abs().squeeze().cpu().tolist()
        importance = [g * v for g, v in zip(grad, inp)]

        feature_keys = list(stat_features.keys())
        shap_values = []
        for i in range(len(importance)):
            name = _FEATURE_NAMES[i] if i < len(_FEATURE_NAMES) else feature_keys[i] if i < len(feature_keys) else f"feat_{i}"
            shap_values.append({
                "feature": name,
                "value": round(stat_vals[i], 4) if i < len(stat_vals) else 0,
                "importance": round(importance[i], 6),
            })
        shap_values.sort(key=lambda x: x["importance"], reverse=True)

        # ── Cleanup hooks ──
        for h in hooks:
            h.remove()

        # ── Build attention heatmap data ──
        attention_data = []
        for entry in captured_attn:
            layer_weights = entry["weights"]  # (1, n_heads, L, L)
            attention_data.append({
                "layer": entry["layer"],
                "weights": layer_weights[0],  # first batch item: (n_heads, L, L)
            })

        return {
            "shap_values": shap_values[:10],
            "attention": attention_data,
            "prediction": CLASS_NAMES.get(pred_class, "Unknown"),
            "confidence": round(confidence, 4),
        }

    def load_model(self, checkpoint_path: str):
        self.model.load_state_dict(
            torch.load(checkpoint_path, map_location=self.device)
        )
        self.model.eval()
