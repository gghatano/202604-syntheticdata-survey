from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import OneHotEncoder


def _hist(series: pd.Series, k: int) -> np.ndarray:
    counts = np.bincount(series.astype(int).to_numpy(), minlength=k).astype(float)
    s = counts.sum()
    return counts / s if s > 0 else counts


def univariate_tvd(real: pd.DataFrame, synth: pd.DataFrame, domain: dict[str, int]) -> pd.Series:
    out = {}
    for col, k in domain.items():
        if col not in real.columns or col not in synth.columns:
            continue
        p = _hist(real[col], k)
        q = _hist(synth[col], k)
        out[col] = 0.5 * float(np.abs(p - q).sum())
    return pd.Series(out, name="tvd")


def univariate_js(real: pd.DataFrame, synth: pd.DataFrame, domain: dict[str, int]) -> pd.Series:
    out = {}
    for col, k in domain.items():
        if col not in real.columns or col not in synth.columns:
            continue
        p = _hist(real[col], k)
        q = _hist(synth[col], k)
        m = 0.5 * (p + q)
        def _kl(a, b):
            mask = (a > 0) & (b > 0)
            return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))
        out[col] = 0.5 * _kl(p, m) + 0.5 * _kl(q, m)
    return pd.Series(out, name="js")


def _joint_hist(df: pd.DataFrame, a: str, b: str, ka: int, kb: int) -> np.ndarray:
    idx = df[a].astype(int).to_numpy() * kb + df[b].astype(int).to_numpy()
    counts = np.bincount(idx, minlength=ka * kb).astype(float)
    s = counts.sum()
    return counts / s if s > 0 else counts


def bivariate_tvd(real: pd.DataFrame, synth: pd.DataFrame, domain: dict[str, int]) -> dict[str, Any]:
    cols = [c for c in domain if c in real.columns and c in synth.columns]
    vals = []
    pairs = {}
    for a, b in combinations(cols, 2):
        ka, kb = domain[a], domain[b]
        p = _joint_hist(real, a, b, ka, kb)
        q = _joint_hist(synth, a, b, ka, kb)
        v = 0.5 * float(np.abs(p - q).sum())
        vals.append(v)
        pairs[f"{a}|{b}"] = v
    arr = np.array(vals) if vals else np.array([0.0])
    return {"mean": float(arr.mean()), "max": float(arr.max()), "pairs": pairs}


def _mi_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    n = len(df)
    mat = pd.DataFrame(0.0, index=cols, columns=cols)
    for a, b in combinations(cols, 2):
        ka = int(df[a].max()) + 1
        kb = int(df[b].max()) + 1
        joint = np.zeros((ka, kb), dtype=float)
        for x, y in zip(df[a].astype(int).to_numpy(), df[b].astype(int).to_numpy()):
            joint[x, y] += 1.0
        joint /= max(n, 1)
        px = joint.sum(axis=1, keepdims=True)
        py = joint.sum(axis=0, keepdims=True)
        denom = px @ py
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where((joint > 0) & (denom > 0), joint / denom, 1.0)
            mi = float(np.sum(np.where(joint > 0, joint * np.log2(ratio), 0.0)))
        mat.loc[a, b] = mi
        mat.loc[b, a] = mi
    return mat


def mutual_information_diff(real: pd.DataFrame, synth: pd.DataFrame) -> pd.DataFrame:
    common = [c for c in real.columns if c in synth.columns]
    r = _mi_matrix(real[common])
    s = _mi_matrix(synth[common])
    return (r - s).abs()


def _prep_xy(df: pd.DataFrame, target_col: str):
    y = df[target_col].astype(int).to_numpy()
    X = df.drop(columns=[target_col])
    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    Xe = enc.fit_transform(X.astype(int))
    return Xe, y, enc


def downstream_task(
    real_train: pd.DataFrame,
    synth_train: pd.DataFrame,
    real_holdout: pd.DataFrame,
    target_col: str,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, train_df in [("real", real_train), ("synth", synth_train)]:
        Xtr, ytr, enc = _prep_xy(train_df, target_col)
        Xh = enc.transform(real_holdout.drop(columns=[target_col]).astype(int))
        yh = real_holdout[target_col].astype(int).to_numpy()
        if len(np.unique(ytr)) < 2:
            results[name] = {"accuracy": float("nan"), "macro_f1": float("nan"), "auc": float("nan")}
            continue
        clf = LogisticRegression(max_iter=500, n_jobs=1)
        clf.fit(Xtr, ytr)
        pred = clf.predict(Xh)
        try:
            proba = clf.predict_proba(Xh)
            if proba.shape[1] == 2:
                auc = float(roc_auc_score(yh, proba[:, 1]))
            else:
                auc = float(roc_auc_score(yh, proba, multi_class="ovr"))
        except ValueError:
            auc = float("nan")
        results[name] = {
            "accuracy": float(accuracy_score(yh, pred)),
            "macro_f1": float(f1_score(yh, pred, average="macro")),
            "auc": auc,
        }
    return results


def diversity(real: pd.DataFrame, synth: pd.DataFrame) -> dict[str, float]:
    n = max(len(synth), 1)
    uniq_synth = synth.drop_duplicates()
    unique_rate = len(uniq_synth) / n
    merged = synth.merge(real.drop_duplicates(), how="inner", on=list(real.columns))
    duplicate_rate = len(merged) / n
    real_unique = real.drop_duplicates()
    if len(real_unique) == 0:
        coverage = 0.0
    else:
        covered = real_unique.merge(uniq_synth, how="inner", on=list(real.columns))
        coverage = len(covered) / len(real_unique)
    return {
        "unique_rate": float(unique_rate),
        "duplicate_rate": float(duplicate_rate),
        "coverage": float(coverage),
    }
