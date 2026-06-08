#!/usr/bin/env python
"""Training script for the NIDS multi-modal Transformer model."""

import argparse
import torch
from torch.utils.data import DataLoader
from backend.models.nids_model import NIDSModel
from backend.training.dataset import NIDSDataset
from backend.training.trainer import Trainer
import mlflow


def parse_args():
    parser = argparse.ArgumentParser(description="Train NIDS Transformer model")
    parser.add_argument("--stat", required=True, help="Path to stat features .pt file")
    parser.add_argument("--payload", required=True, help="Path to payload sequences .pt file")
    parser.add_argument("--labels", required=True, help="Path to labels .pt file")
    parser.add_argument("--val-stat", required=True, help="Path to validation stat .pt")
    parser.add_argument("--val-payload", required=True, help="Path to validation payload .pt")
    parser.add_argument("--val-labels", required=True, help="Path to validation labels .pt")
    parser.add_argument("--epochs", type=int, default=100, help="Max training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--num-classes", type=int, default=8, help="Number of attack classes")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Model save directory")
    parser.add_argument("--no-mlflow", action="store_true", help="Disable MLflow logging")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Device: {args.device}")
    print(f"Loading data from: {args.stat}")

    train_ds = NIDSDataset(args.stat, args.payload, args.labels)
    val_ds = NIDSDataset(args.val_stat, args.val_payload, args.val_labels)

    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    print(f"Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")

    # Infer input dim from data
    sample_stat, _, _ = train_ds[0]
    stat_input_dim = sample_stat.shape[0]

    model = NIDSModel(
        stat_input_dim=stat_input_dim,
        payload_vocab_size=256,
        d_model=256,
        stat_layers=4,
        payload_layers=6,
        n_heads=8,
        ffn_dim=1024,
        num_classes=args.num_classes,
        dropout=0.1,
    )

    params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {params:,}")

    if not args.no_mlflow:
        mlflow.set_experiment("NIDS-Training")
        mlflow.log_params({
            "stat_input_dim": stat_input_dim,
            "d_model": 256,
            "stat_layers": 4,
            "payload_layers": 6,
            "num_classes": args.num_classes,
            "lr": args.lr,
            "batch_size": args.batch_size,
        })

    trainer = Trainer(
        model=model,
        device=args.device,
        lr=args.lr,
        patience=15,
        checkpoint_dir=args.checkpoint_dir,
    )

    trainer.fit(train_dl, val_dl, epochs=args.epochs)
    print(f"Training complete. Best model saved to {args.checkpoint_dir}/best.pt")


if __name__ == "__main__":
    main()
