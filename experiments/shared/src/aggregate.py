"""Aggregate per-run synthetic CSVs across implementations and compute evaluation metrics.

Reads:
  experiments/mst_*/results/synth_*.csv
  experiments/mst_*/results/run_*.json
Writes:
  results/summary.csv (one row per run)
  results/utility_metrics.csv
  results/privacy_metrics.csv
  results/performance_metrics.csv
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
SHARED_SRC = ROOT / "experiments" / "shared" / "src"
sys.path.insert(0, str(SHARED_SRC))

from preprocessing import PreprocessRules, preprocess, split_train_holdout  # noqa: E402

sys.path.insert(0, str(ROOT / "experiments" / "shared"))
import importlib.util
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
_util = _load("eval_utility", ROOT / "experiments/shared/evaluation/utility.py")
_priv = _load("eval_privacy", ROOT / "experiments/shared/evaluation/privacy.py")
univariate_tvd = _util.univariate_tvd
univariate_js = _util.univariate_js
bivariate_tvd = _util.bivariate_tvd
downstream_task = _util.downstream_task
diversity = _util.diversity
dcr_nndr = _priv.dcr_nndr
exact_match = _priv.exact_match
nearest_neighbor_mia = _priv.nearest_neighbor_mia


RUN_RE = re.compile(r"run_(mst_[a-z_]+)_([0-9.]+)_(\d+)\.json")
IMPLS = ["mst_smartnoise", "mst_private_pgm", "mst_dpmm"]


def load_real() -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame, pd.DataFrame, str]:
    cfg = yaml.safe_load((ROOT / "experiments/shared/configs/preprocessing.yaml").read_text())["adult"]
    rules = PreprocessRules(
        drop_cols=cfg.get("drop_cols", []),
        categorical_cols=cfg.get("categorical_cols", []),
        numeric_cols=cfg.get("numeric_cols", []),
        bins=cfg.get("bins", {}),
        top_k=cfg.get("top_k", {}),
    )
    df_raw = pd.read_csv(ROOT / "experiments/shared/data/raw/adult_5k.csv")
    df_proc, domain, _ = preprocess(df_raw, rules)
    train, holdout = split_train_holdout(df_proc, holdout_frac=0.2, seed=42)
    return df_proc, domain, train, holdout, cfg.get("target_col", "income")


def collect_runs() -> list[dict]:
    rows: list[dict] = []
    for impl in IMPLS:
        res_dir = ROOT / "experiments" / impl / "results"
        if not res_dir.exists():
            continue
        for jf in sorted(res_dir.glob("run_*.json")):
            m = RUN_RE.match(jf.name)
            if not m:
                continue
            rec = json.loads(jf.read_text())
            rec["json_file"] = str(jf)
            rec["synth_file"] = str(res_dir / jf.name.replace("run_", "synth_").replace(".json", ".csv"))
            rows.append(rec)
    return rows


def main() -> None:
    real_full, domain, train, holdout, target = load_real()
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)

    summary: list[dict] = []
    utility_rows: list[dict] = []
    privacy_rows: list[dict] = []
    perf_rows: list[dict] = []

    for rec in collect_runs():
        impl = rec["impl"]
        eps = rec["epsilon"]
        seed = rec["seed"]
        base = {"impl": impl, "epsilon": eps, "seed": seed}
        perf_rows.append({
            **base,
            "elapsed_fit": rec.get("elapsed_fit"),
            "elapsed_sample": rec.get("elapsed_sample"),
            "peak_mem_mb": rec.get("peak_mem_mb"),
            "status": rec.get("status"),
        })
        if rec.get("status") != "ok":
            summary.append({**base, "status": rec.get("status"), "error": rec.get("error", "")[:200]})
            continue
        synth_path = Path(rec["synth_file"])
        if not synth_path.exists():
            continue
        synth = pd.read_csv(synth_path)
        synth = synth[[c for c in real_full.columns if c in synth.columns]].astype(int)

        tvd = univariate_tvd(real_full, synth, domain)
        js = univariate_js(real_full, synth, domain)
        biv = bivariate_tvd(real_full, synth, domain)
        div = diversity(real_full, synth)
        try:
            down = downstream_task(train, synth, holdout, target)
        except Exception as e:  # noqa: BLE001
            down = {"real": {"accuracy": float("nan")}, "synth": {"accuracy": float("nan"), "error": str(e)}}

        utility_rows.append({
            **base,
            "tvd_mean": float(tvd.mean()),
            "tvd_max": float(tvd.max()),
            "js_mean": float(js.mean()),
            "bivariate_tvd_mean": biv["mean"],
            "bivariate_tvd_max": biv["max"],
            "downstream_acc_real": down["real"]["accuracy"],
            "downstream_acc_synth": down["synth"]["accuracy"],
            "downstream_f1_synth": down["synth"].get("macro_f1"),
            "unique_rate": div["unique_rate"],
            "duplicate_rate": div["duplicate_rate"],
            "coverage": div["coverage"],
        })

        dcr = dcr_nndr(real_full, synth)
        ex = exact_match(real_full, synth)
        mia = nearest_neighbor_mia(train, holdout, synth)
        privacy_rows.append({
            **base,
            "dcr_mean": dcr["dcr_mean"],
            "dcr_min": dcr["dcr_min"],
            "nndr_mean": dcr["nndr_mean"],
            "exact_match_count": ex["count"],
            "exact_match_rate": ex["rate"],
            "mia_auc": mia["roc_auc"],
            "mia_advantage": mia["advantage"],
        })

        summary.append({
            **base,
            "status": "ok",
            "tvd_mean": float(tvd.mean()),
            "bivariate_tvd_mean": biv["mean"],
            "dcr_mean": dcr["dcr_mean"],
            "mia_auc": mia["roc_auc"],
            "elapsed_fit": rec.get("elapsed_fit"),
            "elapsed_sample": rec.get("elapsed_sample"),
        })

    pd.DataFrame(summary).to_csv(out_dir / "summary.csv", index=False)
    pd.DataFrame(utility_rows).to_csv(out_dir / "utility_metrics.csv", index=False)
    pd.DataFrame(privacy_rows).to_csv(out_dir / "privacy_metrics.csv", index=False)
    pd.DataFrame(perf_rows).to_csv(out_dir / "performance_metrics.csv", index=False)
    print(f"wrote {len(summary)} summary rows, {len(utility_rows)} utility, {len(privacy_rows)} privacy to {out_dir}")


if __name__ == "__main__":
    main()
