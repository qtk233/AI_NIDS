#!/usr/bin/env python
"""Preprocess CIC-IDS-2017 Parquet files into .pt tensors for NIDS training."""

import argparse
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# File → class ID mapping (matching backend/engine/detector.py CLASS_NAMES)
FILE_CLASS_MAP = {
    "Benign-Monday-no-metadata.parquet": 0,   # Normal
    "DoS-Wednesday-no-metadata.parquet": 1,    # DoS
    "DDoS-Friday-no-metadata.parquet": 2,      # DDoS
    "Bruteforce-Tuesday-no-metadata.parquet": 3,  # BruteForce
    "Botnet-Friday-no-metadata.parquet": 4,    # Botnet
    "WebAttacks-Thursday-no-metadata.parquet": 5,  # WebAttack
    "Portscan-Friday-no-metadata.parquet": 6,  # PortScan
    "Infiltration-Thursday-no-metadata.parquet": 7,  # Infiltration
}

PAYLOAD_SEQ_LEN = 2560


def load_and_label(data_dir: str, file_name: str, class_id: int):
    """Load a parquet file, keep only attack rows, assign class label."""
    df = pd.read_parquet(f"{data_dir}/{file_name}")
    if class_id == 0:
        # Benign file: keep all rows
        df = df[df["Label"] == "Benign"]
    else:
        # Attack files: drop Benign rows, assign class_id
        df = df[df["Label"] != "Benign"]
    if df.empty:
        return None, None, None

    # Drop Label column, keep all numeric features
    feature_df = df.drop(columns=["Label"]).select_dtypes(include=[np.number])
    feature_arr = feature_df.values.astype(np.float32)

    labels = np.full(len(feature_arr), class_id, dtype=np.int64)
    return feature_arr, labels


def main():
    parser = argparse.ArgumentParser(description="Preprocess CIC-IDS-2017 parquet files")
    parser.add_argument("--data-dir", default="data", help="Directory with .parquet files")
    parser.add_argument("--output-dir", default="processed", help="Output directory for .pt files")
    parser.add_argument("--test-split", type=float, default=0.2, help="Validation split ratio")
    args = parser.parse_args()

    import os
    os.makedirs(args.output_dir, exist_ok=True)

    all_features = []
    all_labels = []

    for file_name, class_id in FILE_CLASS_MAP.items():
        feat, lbl = load_and_label(args.data_dir, file_name, class_id)
        if feat is None:
            print(f"WARNING: {file_name} not found or empty, skipping")
            continue
        all_features.append(feat)
        all_labels.append(lbl)
        print(f"  {file_name}: {feat.shape[0]} samples, class={class_id}")

    X = np.concatenate(all_features, axis=0)
    y = np.concatenate(all_labels, axis=0)
    print(f"\nTotal samples: {X.shape[0]}, features: {X.shape[1]}")

    # Normalize features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Train/val split (stratified)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=args.test_split, stratify=y, random_state=42
    )
    print(f"Train: {X_train.shape[0]}, Val: {X_val.shape[0]}")

    # Create synthetic payload tensors
    # (Parquet data has no raw payload bytes; we use random byte sequences
    #  as placeholders — the model learns mainly from stat features)
    def make_payload(n_samples: int) -> torch.Tensor:
        return torch.randint(0, 256, (n_samples, PAYLOAD_SEQ_LEN), dtype=torch.long)

    # Convert to tensors
    train_stat = torch.tensor(X_train, dtype=torch.float32)
    val_stat = torch.tensor(X_val, dtype=torch.float32)
    train_labels = torch.tensor(y_train, dtype=torch.long)
    val_labels = torch.tensor(y_val, dtype=torch.long)
    train_payload = make_payload(len(X_train))
    val_payload = make_payload(len(X_val))

    # Save
    torch.save(train_stat, f"{args.output_dir}/train_stat.pt")
    torch.save(train_payload, f"{args.output_dir}/train_payload.pt")
    torch.save(train_labels, f"{args.output_dir}/train_labels.pt")
    torch.save(val_stat, f"{args.output_dir}/val_stat.pt")
    torch.save(val_payload, f"{args.output_dir}/val_payload.pt")
    torch.save(val_labels, f"{args.output_dir}/val_labels.pt")

    print(f"\nSaved to {args.output_dir}/:")
    print(f"  train_stat.pt     {train_stat.shape}")
    print(f"  train_payload.pt   {train_payload.shape}")
    print(f"  train_labels.pt    {train_labels.shape}")
    print(f"  val_stat.pt        {val_stat.shape}")
    print(f"  val_payload.pt     {val_payload.shape}")
    print(f"  val_labels.pt       {val_labels.shape}")


if __name__ == "__main__":
    main()
