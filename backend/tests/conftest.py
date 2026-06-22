import pytest
import torch
from backend.models.nids_model import NIDSModel
from backend.engine.detector import Detector


@pytest.fixture
def nids_model():
    model = NIDSModel(
        stat_input_dim=60, d_model=128, stat_layers=2, payload_layers=2,
        n_heads=4, ffn_dim=256, num_classes=8, dropout=0.1
    )
    model.eval()
    return model


@pytest.fixture
def detector(nids_model):
    return Detector(nids_model, device="cpu")
