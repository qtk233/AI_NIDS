import torch
import torch.nn as nn


class LateFusionClassifier(nn.Module):
    def __init__(self, d_model: int = 256, num_classes: int = 8, dropout: float = 0.1):
        super().__init__()
        self.fusion = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.Dropout(dropout),
            nn.ReLU(),
            nn.LayerNorm(d_model),
        )
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, f_stat: torch.Tensor, f_payload: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        concat = torch.cat([f_stat, f_payload], dim=-1)
        fused = self.fusion(concat)
        logits = self.classifier(fused)
        return logits, fused
