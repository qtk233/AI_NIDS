import pytest
import torch
from backend.models.fusion import LateFusionClassifier


class TestLateFusionClassifier:
    @pytest.fixture
    def model(self):
        return LateFusionClassifier(d_model=256, num_classes=8, dropout=0.1)

    def test_output_shapes(self, model):
        f_stat = torch.randn(4, 256)
        f_payload = torch.randn(4, 256)
        logits, fused = model(f_stat, f_payload)
        assert logits.shape == (4, 8)
        assert fused.shape == (4, 256)

    def test_no_nan(self, model):
        f_stat = torch.randn(16, 256)
        f_payload = torch.randn(16, 256)
        logits, fused = model(f_stat, f_payload)
        assert not torch.isnan(logits).any()
        assert not torch.isnan(fused).any()

    def test_gradient_flow(self, model):
        f_stat = torch.randn(4, 256)
        f_payload = torch.randn(4, 256)
        logits, _ = model(f_stat, f_payload)
        loss = logits.sum()
        loss.backward()
        for name, p in model.named_parameters():
            assert p.grad is not None, f"Gradient missing for {name}"

    def test_different_inputs_different_outputs(self, model):
        f_stat = torch.randn(4, 256)
        f_payload = torch.randn(4, 256)
        logits1, _ = model(f_stat, f_payload)
        logits2, _ = model(f_stat + 1.0, f_payload)
        assert not torch.allclose(logits1, logits2)
