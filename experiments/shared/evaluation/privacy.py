from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors


def _nn(real: pd.DataFrame, metric: str = "hamming") -> NearestNeighbors:
    nn = NearestNeighbors(n_neighbors=2, metric=metric)
    nn.fit(real.to_numpy())
    return nn


def dcr_nndr(real: pd.DataFrame, synth: pd.DataFrame) -> dict[str, Any]:
    cols = [c for c in real.columns if c in synth.columns]
    if not cols:
        return {"dcr_mean": float("nan"), "dcr_min": float("nan"), "nndr_mean": float("nan")}
    nn = _nn(real[cols])
    dists, _ = nn.kneighbors(synth[cols].to_numpy())
    d1 = dists[:, 0]
    d2 = dists[:, 1]
    nndr = np.where(d2 > 0, d1 / d2, 0.0)
    return {
        "dcr_mean": float(d1.mean()),
        "dcr_min": float(d1.min()),
        "dcr_p05": float(np.quantile(d1, 0.05)),
        "nndr_mean": float(nndr.mean()),
    }


def exact_match(real: pd.DataFrame, synth: pd.DataFrame) -> dict[str, Any]:
    cols = [c for c in real.columns if c in synth.columns]
    if not cols:
        return {"count": 0, "rate": 0.0}
    merged = synth[cols].merge(real[cols].drop_duplicates(), how="inner", on=cols)
    cnt = len(merged)
    rate = cnt / max(len(synth), 1)
    return {"count": int(cnt), "rate": float(rate)}


def nearest_neighbor_mia(
    real_train: pd.DataFrame, real_holdout: pd.DataFrame, synth: pd.DataFrame
) -> dict[str, Any]:
    cols = [c for c in real_train.columns if c in synth.columns]
    nn = NearestNeighbors(n_neighbors=1, metric="hamming")
    nn.fit(synth[cols].to_numpy())
    d_in, _ = nn.kneighbors(real_train[cols].to_numpy())
    d_out, _ = nn.kneighbors(real_holdout[cols].to_numpy())
    y = np.concatenate([np.ones(len(d_in)), np.zeros(len(d_out))])
    scores = -np.concatenate([d_in[:, 0], d_out[:, 0]])
    try:
        auc = float(roc_auc_score(y, scores))
    except ValueError:
        auc = 0.5
    return {"roc_auc": auc, "advantage": float(2.0 * (auc - 0.5))}


def attribute_inference(
    real: pd.DataFrame, synth: pd.DataFrame, known_cols: list[str], target_col: str
) -> dict[str, Any]:
    known = [c for c in known_cols if c in synth.columns and c in real.columns]
    if not known or target_col not in synth.columns or target_col not in real.columns:
        return {"accuracy": float("nan"), "baseline": float("nan"), "advantage": float("nan")}
    nn = NearestNeighbors(n_neighbors=1, metric="hamming")
    nn.fit(synth[known].to_numpy())
    _, idx = nn.kneighbors(real[known].to_numpy())
    pred = synth[target_col].to_numpy()[idx[:, 0]]
    truth = real[target_col].to_numpy()
    acc = float((pred == truth).mean())
    counts = real[target_col].value_counts(normalize=True)
    baseline = float(counts.max()) if len(counts) else 0.0
    return {"accuracy": acc, "baseline": baseline, "advantage": acc - baseline}
