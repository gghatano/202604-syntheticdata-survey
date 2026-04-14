from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ADULT_COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country", "income",
]


def load_raw(name: str, data_dir: Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    if name == "adult":
        csv_path = data_dir / "raw" / "adult.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Adult CSV not found at {csv_path}. "
                "Download from UCI (https://archive.ics.uci.edu/dataset/2/adult) "
                f"and place it at {csv_path}. See experiments/shared/data/README.md."
            )
        df = pd.read_csv(csv_path, skipinitialspace=True, na_values=["?"])
        if list(df.columns) != ADULT_COLUMNS and df.shape[1] == len(ADULT_COLUMNS):
            df.columns = ADULT_COLUMNS
        return df
    raise FileNotFoundError(f"Unknown dataset '{name}'. Only 'adult' is supported.")


@dataclass
class PreprocessRules:
    drop_cols: list[str] = field(default_factory=list)
    categorical_cols: list[str] = field(default_factory=list)
    numeric_cols: list[str] = field(default_factory=list)
    bins: dict[str, int] = field(default_factory=dict)
    top_k: dict[str, int] = field(default_factory=dict)
    missing_token: str = "__NA__"


def preprocess(
    df: pd.DataFrame, rules: PreprocessRules
) -> tuple[pd.DataFrame, dict[str, int], dict[str, Any]]:
    df = df.copy()
    for c in rules.drop_cols:
        if c in df.columns:
            df = df.drop(columns=[c])

    encoders: dict[str, Any] = {}
    domain: dict[str, int] = {}

    for col in rules.numeric_cols:
        if col not in df.columns:
            continue
        n_bins = rules.bins.get(col, 10)
        series = pd.to_numeric(df[col], errors="coerce")
        try:
            binned, edges = pd.qcut(series, q=n_bins, labels=False, retbins=True, duplicates="drop")
        except ValueError:
            binned, edges = pd.cut(series, bins=n_bins, labels=False, retbins=True)
        binned = binned.astype("Float64")
        na_code = int(np.nanmax(binned.to_numpy(dtype=float, na_value=-1)) + 1) if binned.notna().any() else 0
        filled = binned.fillna(na_code).astype(int)
        df[col] = filled
        encoders[col] = {"type": "numeric_bin", "edges": list(edges), "na_code": na_code}
        domain[col] = int(filled.max() + 1)

    for col in rules.categorical_cols:
        if col not in df.columns:
            continue
        s = df[col].astype("object").where(df[col].notna(), rules.missing_token)
        s = s.astype(str)
        if col in rules.top_k:
            k = rules.top_k[col]
            top = s.value_counts().nlargest(k).index
            s = s.where(s.isin(top), "OTHER")
        categories = sorted(s.unique().tolist())
        mapping = {v: i for i, v in enumerate(categories)}
        codes = s.map(mapping).astype(int)
        df[col] = codes
        encoders[col] = {"type": "categorical", "categories": categories}
        domain[col] = len(categories)

    df = df[[c for c in df.columns if c in domain]]
    return df, domain, encoders


def split_train_holdout(
    df: pd.DataFrame, holdout_frac: float = 0.2, seed: int = 0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    rng.shuffle(idx)
    cut = int(len(df) * (1 - holdout_frac))
    train_idx = idx[:cut]
    holdout_idx = idx[cut:]
    return df.iloc[train_idx].reset_index(drop=True), df.iloc[holdout_idx].reset_index(drop=True)
