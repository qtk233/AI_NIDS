import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from backend.training.metrics import compute_metrics
import mlflow


class Trainer:
    def __init__(self, model: nn.Module, device: str = "cuda",
                 lr: float = 1e-4, weight_decay: float = 0.01,
                 label_smoothing: float = 0.1, patience: int = 15,
                 checkpoint_dir: str = "checkpoints"):
        self.model = model.to(device)
        self.device = device
        self.criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)
        self.optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = CosineAnnealingWarmRestarts(self.optimizer, T_0=10)
        self.patience = patience
        self.checkpoint_dir = checkpoint_dir
        self.best_val_f1 = 0.0
        self.best_epoch = 0
        self.epochs_no_improve = 0

    def train_epoch(self, dataloader: DataLoader) -> dict:
        self.model.train()
        total_loss, all_logits, all_labels = 0.0, [], []
        for stat, payload, labels in dataloader:
            stat, payload, labels = stat.to(self.device), payload.to(self.device), labels.to(self.device)
            self.optimizer.zero_grad()
            logits, _ = self.model(stat, payload)
            loss = self.criterion(logits, labels)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            all_logits.append(logits.detach())
            all_labels.append(labels)
        self.scheduler.step()
        metrics = compute_metrics(torch.cat(all_logits), torch.cat(all_labels))
        metrics["loss"] = total_loss / len(dataloader)
        return metrics

    @torch.no_grad()
    def validate_epoch(self, dataloader: DataLoader) -> dict:
        self.model.eval()
        total_loss, all_logits, all_labels = 0.0, [], []
        for stat, payload, labels in dataloader:
            stat, payload, labels = stat.to(self.device), payload.to(self.device), labels.to(self.device)
            logits, _ = self.model(stat, payload)
            loss = self.criterion(logits, labels)
            total_loss += loss.item()
            all_logits.append(logits)
            all_labels.append(labels)
        metrics = compute_metrics(torch.cat(all_logits), torch.cat(all_labels))
        metrics["loss"] = total_loss / len(dataloader)
        return metrics

    def fit(self, train_dl: DataLoader, val_dl: DataLoader, epochs: int = 100,
            use_mlflow: bool = True):
        for epoch in range(1, epochs + 1):
            train_m = self.train_epoch(train_dl)
            val_m = self.validate_epoch(val_dl)
            print(f"Epoch {epoch:3d} | train_loss={train_m['loss']:.4f} acc={train_m['accuracy']:.4f} "
                  f"| val_loss={val_m['loss']:.4f} acc={val_m['accuracy']:.4f} f1={val_m['macro_f1']:.4f}")
            if use_mlflow:
                mlflow.log_metrics({f"train_{k}": v for k, v in train_m.items()}, step=epoch)
                mlflow.log_metrics({f"val_{k}": v for k, v in val_m.items()}, step=epoch)
            if val_m["macro_f1"] > self.best_val_f1:
                self.best_val_f1 = val_m["macro_f1"]
                self.best_epoch = epoch
                self.epochs_no_improve = 0
                torch.save(self.model.state_dict(), f"{self.checkpoint_dir}/best.pt")
            else:
                self.epochs_no_improve += 1
            if self.epochs_no_improve >= self.patience:
                print(f"Early stopping at epoch {epoch}")
                break
        print(f"Best val F1: {self.best_val_f1:.4f} at epoch {self.best_epoch}")
