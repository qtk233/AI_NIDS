import torch
import torch.nn as nn
from backend.models.stat_encoder import PositionalEncoding


class PayloadEncoder(nn.Module):
    def __init__(self, vocab_size: int = 256, d_model: int = 256, n_layers: int = 6,
                 n_heads: int = 8, ffn_dim: int = 1024, max_len: int = 2560,
                 dropout: float = 0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_encoding = PositionalEncoding(d_model, max_len=max_len + 1, dropout=dropout)  # +1 for CLS token
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=ffn_dim,
            dropout=dropout, activation="gelu", batch_first=True, norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.embedding(x)
        cls_tokens = self.cls_token.expand(x.size(0), -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = self.pos_encoding(x)
        x = self.transformer(x)
        x = x[:, 0, :]
        x = self.norm(x)
        return x
