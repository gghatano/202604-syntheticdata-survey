from __future__ import annotations

import pandas as pd


def aggregate_runs(run_records: list[dict]) -> pd.DataFrame:
    if not run_records:
        return pd.DataFrame()
    df = pd.DataFrame(run_records)
    group_cols = [c for c in ["implementation", "epsilon"] if c in df.columns]
    metric_cols = [c for c in df.columns if c not in group_cols + ["seed", "status", "error"]]
    numeric = df[metric_cols].apply(pd.to_numeric, errors="coerce")
    df2 = pd.concat([df[group_cols], numeric], axis=1)
    if not group_cols:
        return df2.agg(["mean", "std", "median"]).reset_index()
    agg = df2.groupby(group_cols).agg(["mean", "std", "median"]).reset_index()
    return agg


def failure_rate(run_records: list[dict]) -> float:
    if not run_records:
        return 0.0
    fails = sum(1 for r in run_records if r.get("status") not in (None, "ok", "success"))
    return fails / len(run_records)
