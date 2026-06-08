import pytest
import torch
import numpy as np
from backend.training.metrics import compute_metrics


class TestComputeMetrics:
    def test_perfect_prediction(self):
        logits = torch.tensor([
            [10.0, 0.0, 0.0],
            [0.0, 10.0, 0.0],
            [0.0, 0.0, 10.0],
        ])
        labels = torch.tensor([0, 1, 2])
        m = compute_metrics(logits, labels)
        assert m["accuracy"] == 1.0
        assert m["macro_f1"] == 1.0

    def test_worst_prediction(self):
        logits = torch.tensor([
            [10.0, 0.0],
            [10.0, 0.0],
            [10.0, 0.0],
        ])
        labels = torch.tensor([1, 1, 1])
        m = compute_metrics(logits, labels)
        assert m["accuracy"] == 0.0

    def test_returns_all_keys(self):
        logits = torch.randn(8, 3)
        labels = torch.randint(0, 3, (8,))
        m = compute_metrics(logits, labels)
        for k in ["accuracy", "macro_f1", "weighted_f1", "macro_precision", "macro_recall"]:
            assert k in m, f"Missing key: {k}"
