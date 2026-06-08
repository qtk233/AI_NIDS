import torch
import torch.nn as nn
import numpy as np
from scipy.stats import weibull_min


class OpenMax(nn.Module):
    def __init__(self, num_known_classes: int, feature_dim: int, tail_size: int = 20):
        super().__init__()
        self.num_known = num_known_classes
        self.tail_size = tail_size
        self.feature_dim = feature_dim
        self.classifier = nn.Linear(feature_dim, num_known_classes)
        self.register_buffer("weibull_params", torch.zeros(num_known_classes, 2))
        self.register_buffer("class_means", torch.zeros(num_known_classes, feature_dim))
        self.fitted = False

    def fit_weibull(self, activations: torch.Tensor, labels: torch.Tensor):
        self.class_means = torch.zeros(self.num_known, self.feature_dim)
        params = torch.zeros(self.num_known, 2)
        for k in range(self.num_known):
            mask = labels == k
            if mask.sum() == 0:
                params[k] = torch.tensor([1.0, 1.0])
                continue
            class_acts = activations[mask]
            self.class_means[k] = class_acts.mean(dim=0)
            dists = torch.norm(class_acts - self.class_means[k], dim=1)
            tail = dists.sort().values[-self.tail_size:]
            if len(tail) > 1:
                shape, loc, scale = weibull_min.fit(tail.numpy(), floc=0)
                params[k] = torch.tensor([shape, scale])
            else:
                params[k] = torch.tensor([1.0, 1.0])
        self.weibull_params = params
        self.fitted = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.classifier(x)
        if not self.fitted:
            return torch.softmax(logits, dim=-1)
        scores = torch.softmax(logits, dim=-1)
        dists = torch.norm(x.unsqueeze(1) - self.class_means.unsqueeze(0), dim=-1)
        weibull_probs = torch.zeros_like(scores)
        for k in range(self.num_known):
            shape, scale = self.weibull_params[k]
            if shape <= 0 or scale <= 0:
                weibull_probs[:, k] = 1.0
            else:
                w = weibull_min.cdf(dists[:, k].numpy(), shape.item(), scale=scale.item())
                weibull_probs[:, k] = torch.from_numpy(w).float()
        recalibrated = scores * weibull_probs
        unknown_score = scores * (1 - weibull_probs)
        unknown_prob = unknown_score.sum(dim=-1, keepdim=True)
        recalibrated = torch.cat([recalibrated, unknown_prob], dim=-1)
        return recalibrated / recalibrated.sum(dim=-1, keepdim=True)
