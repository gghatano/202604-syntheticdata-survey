"""Compute real↔real baselines for safety-metric interpretation.

前処理済み実データの「自己重複率」「holdout↔train exact match」「DCR」を算出する。
これらは §2.4 の比較基準となるため、毎実験で計測しておく。

Usage:
    python3 experiments/shared/src/baseline.py --dataset adult
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocessing import PreprocessRules, preprocess, split_train_holdout  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="adult")
    ap.add_argument("--data-file", type=Path, default=None,
                    help="default: experiments/shared/data/raw/{dataset}_5k.csv")
    ap.add_argument("--holdout-frac", type=float, default=0.2)
    ap.add_argument("--split-seed", type=int, default=42)
    args = ap.parse_args()

    data_file = args.data_file or ROOT / f"experiments/shared/data/raw/{args.dataset}_5k.csv"
    cfg = yaml.safe_load((ROOT / "experiments/shared/configs/preprocessing.yaml").read_text())[args.dataset]
    rules = PreprocessRules(
        drop_cols=cfg.get("drop_cols", []),
        categorical_cols=cfg.get("categorical_cols", []),
        numeric_cols=cfg.get("numeric_cols", []),
        bins=cfg.get("bins", {}),
        top_k=cfg.get("top_k", {}),
    )
    df_raw = pd.read_csv(data_file)
    df_proc, domain, _ = preprocess(df_raw, rules)
    train, holdout = split_train_holdout(df_proc, holdout_frac=args.holdout_frac, seed=args.split_seed)

    # holdout rows exactly present in train
    merged = holdout.merge(train.drop_duplicates(), how="inner", on=list(train.columns))
    exact_holdout_in_train = len(merged) / len(holdout)

    # duplicate rate within train
    dup_rate = float(train.duplicated().mean())

    # DCR holdout -> train (hamming)
    nn = NearestNeighbors(n_neighbors=1, metric="hamming")
    nn.fit(train.to_numpy())
    d, _ = nn.kneighbors(holdout.to_numpy())
    dcr_mean = float(d[:, 0].mean())
    dcr_p05 = float(pd.Series(d[:, 0]).quantile(0.05))

    print(f"dataset: {args.dataset}")
    print(f"  n_train: {len(train)}  n_holdout: {len(holdout)}")
    print(f"  domain sum: {sum(domain.values())}  domain product: ~{float(pd.Series(list(domain.values())).prod()):.2e}")
    print()
    print("real↔real baselines (use these as reference when interpreting synth privacy metrics):")
    print(f"  exact match rate (holdout in train): {exact_holdout_in_train:.4f}")
    print(f"  train internal duplicate rate:       {dup_rate:.4f}")
    print(f"  DCR mean (holdout→train, hamming):   {dcr_mean:.4f}")
    print(f"  DCR p05:                             {dcr_p05:.4f}")


if __name__ == "__main__":
    main()
