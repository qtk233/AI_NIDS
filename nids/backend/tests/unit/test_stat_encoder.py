import pytest
import torch
from backend.models.stat_encoder import StatEncoder, PositionalEncoding


class TestPositionalEncoding:
    def test_output_shape(self):
        pe = PositionalEncoding(d_model=256, max_len=100, dropout=0.0)
        x = torch.randn(4, 10, 256)
        out = pe(x)
        assert out.shape == (4, 10, 256)

    def test_no_all_zeros(self):
        pe = PositionalEncoding(d_model=256, max_len=100, dropout=0.0)
        x = torch.zeros(1, 5, 256)
        out = pe(x)
        assert not torch.allclose(out, torch.zeros_like(out))


class TestStatEncoder:
    @pytest.fixture
    def encoder(self):
        return StatEncoder(input_dim=60, d_model=256, n_layers=2, n_heads=8, ffn_dim=512, dropout=0.1)

    def test_forward_single(self, encoder):
        x = torch.randn(1, 60)
        out = encoder(x)
        assert out.shape == (1, 256)

    def test_forward_batch(self, encoder):
        x = torch.randn(16, 60)
        out = encoder(x)
        assert out.shape == (16, 256)

    def test_forward_grad(self, encoder):
        x = torch.randn(4, 60, requires_grad=False)
        out = encoder(x)
        loss = out.sum()
        loss.backward()
        assert encoder.input_proj.weight.grad is not None

    def test_eval_mode_deterministic(self, encoder):
        encoder.eval()
        x = torch.randn(4, 60)
        with torch.no_grad():
            out1 = encoder(x)
            out2 = encoder(x)
        assert torch.allclose(out1, out2)
