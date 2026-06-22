import pytest
import torch
from backend.training.dataset import NIDSDataset
import numpy as np
import tempfile
import os


class TestNIDSDataset:
    @pytest.fixture
    def dataset_files(self):
        n = 32
        stat = np.random.randn(n, 60).astype(np.float32)
        payload = np.random.randint(0, 256, (n, 2560)).astype(np.uint8)
        labels = np.random.randint(0, 8, n).astype(np.int64)
        tmp = tempfile.mkdtemp()
        stat_f = os.path.join(tmp, "stat.pt")
        payl_f = os.path.join(tmp, "payload.pt")
        label_f = os.path.join(tmp, "labels.pt")
        torch.save(torch.from_numpy(stat), stat_f)
        torch.save(torch.from_numpy(payload), payl_f)
        torch.save(torch.from_numpy(labels), label_f)
        return stat_f, payl_f, label_f, n, tmp

    def test_len(self, dataset_files):
        stat_f, payl_f, label_f, n, tmp = dataset_files
        ds = NIDSDataset(stat_f, payl_f, label_f)
        assert len(ds) == n

    def test_getitem_shapes(self, dataset_files):
        stat_f, payl_f, label_f, n, tmp = dataset_files
        ds = NIDSDataset(stat_f, payl_f, label_f)
        stat, payload, label = ds[0]
        assert stat.shape == (60,)
        assert payload.shape == (2560,)
        assert isinstance(label.item(), int)

    def test_getitem_types(self, dataset_files):
        stat_f, payl_f, label_f, n, tmp = dataset_files
        ds = NIDSDataset(stat_f, payl_f, label_f)
        stat, payload, label = ds[0]
        assert stat.dtype == torch.float32
        assert payload.dtype == torch.int64
        assert label.dtype == torch.int64
