import torch
from torch.utils.data import Dataset


class NIDSDataset(Dataset):
    def __init__(self, stat_path: str, payload_path: str, label_path: str):
        self.stat_data = torch.load(stat_path)
        self.payload_data = torch.load(payload_path)
        self.labels = torch.load(label_path)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (
            self.stat_data[idx].float(),
            self.payload_data[idx].long(),
            self.labels[idx],
        )
