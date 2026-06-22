import torch
from sklearn.metrics import f1_score, precision_score, recall_score
import numpy as np


def compute_metrics(logits: torch.Tensor, labels: torch.Tensor) -> dict:
    preds = logits.argmax(dim=-1).cpu().numpy()
    labels_np = labels.cpu().numpy()
    return {
        "accuracy": (preds == labels_np).mean(),
        "macro_f1": f1_score(labels_np, preds, average="macro", zero_division=0),
        "weighted_f1": f1_score(labels_np, preds, average="weighted", zero_division=0),
        "macro_precision": precision_score(labels_np, preds, average="macro", zero_division=0),
        "macro_recall": recall_score(labels_np, preds, average="macro", zero_division=0),
    }
