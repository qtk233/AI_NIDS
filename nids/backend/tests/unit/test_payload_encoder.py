import pytest
import torch
from backend.models.payload_encoder import PayloadEncoder


class TestPayloadEncoder:
    @pytest.fixture
    def encoder(self):
        return PayloadEncoder(
            vocab_size=256, d_model=256, n_layers=2,
            n_heads=8, ffn_dim=512, max_len=2560, dropout=0.1
        )

    def test_forward_single(self, encoder):
        x = torch.randint(0, 256, (1, 2560))
        out = encoder(x)
        assert out.shape == (1, 256)

    def test_forward_batch(self, encoder):
        x = torch.randint(0, 256, (8, 2560))
        out = encoder(x)
        assert out.shape == (8, 256)

    def test_handles_padding(self, encoder):
        x = torch.zeros(4, 2560, dtype=torch.long)
        out = encoder(x)
        assert not torch.isnan(out).any()

    def test_cls_token_exists(self, encoder):
        assert encoder.cls_token.shape == (1, 1, 256)
        assert encoder.cls_token.requires_grad

    def test_forward_grad(self, encoder):
        x = torch.randint(0, 256, (4, 2560))
        out = encoder(x)
        loss = out.sum()
        loss.backward()
        assert encoder.embedding.weight.grad is not None
