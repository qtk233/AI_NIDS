import pytest
import torch
from backend.models.openmax import OpenMax


class TestOpenMax:
    @pytest.fixture
    def activations_and_labels(self):
        torch.manual_seed(42)
        activations = torch.randn(500, 256)
        labels = torch.randint(0, 5, (500,))
        return activations, labels

    @pytest.fixture
    def fitted_openmax(self, activations_and_labels):
        acts, labels = activations_and_labels
        om = OpenMax(num_known_classes=5, feature_dim=256)
        om.fit_weibull(acts, labels)
        return om

    def test_unfitted_returns_softmax(self):
        om = OpenMax(num_known_classes=5, feature_dim=256)
        x = torch.randn(4, 256)
        probs = om(x)
        assert probs.shape == (4, 5)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(4), atol=1e-5)

    def test_fit_weibull_shapes(self, activations_and_labels):
        acts, labels = activations_and_labels
        om = OpenMax(num_known_classes=5, feature_dim=256)
        om.fit_weibull(acts, labels)
        assert om.weibull_params.shape == (5, 2)
        assert om.class_means.shape == (5, 256)
        assert om.fitted

    def test_fitted_forward_shape(self, fitted_openmax):
        x = torch.randn(4, 256)
        probs = fitted_openmax(x)
        assert probs.shape == (4, 6)  # 5 known + 1 unknown

    def test_probs_sum_to_one(self, fitted_openmax):
        x = torch.randn(4, 256)
        probs = fitted_openmax(x)
        assert torch.allclose(probs.sum(dim=-1), torch.ones(4), atol=1e-5)

    def test_unknown_prob_nonzero(self, fitted_openmax):
        far = torch.randn(4, 256) * 10 + 50  # far from any class mean
        probs = fitted_openmax(far)
        # Unknown probability should be > 0 for all samples
        assert (probs[:, -1] >= 0).all()

