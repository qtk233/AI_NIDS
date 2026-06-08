import torch.nn as nn
from backend.models.stat_encoder import StatEncoder
from backend.models.payload_encoder import PayloadEncoder
from backend.models.fusion import LateFusionClassifier


class NIDSModel(nn.Module):
    def __init__(self, stat_input_dim: int = 80, payload_vocab_size: int = 256,
                 d_model: int = 256, stat_layers: int = 4, payload_layers: int = 6,
                 n_heads: int = 8, ffn_dim: int = 1024, num_classes: int = 8,
                 dropout: float = 0.1):
        super().__init__()
        self.stat_encoder = StatEncoder(stat_input_dim, d_model, stat_layers, n_heads, ffn_dim, dropout)
        self.payload_encoder = PayloadEncoder(payload_vocab_size, d_model, payload_layers, n_heads, ffn_dim, max_len=2560, dropout=dropout)
        self.fusion = LateFusionClassifier(d_model, num_classes, dropout)

    def forward(self, stat_features, payload_seq):
        f_stat = self.stat_encoder(stat_features)
        f_payload = self.payload_encoder(payload_seq)
        logits, fused = self.fusion(f_stat, f_payload)
        return logits, fused
