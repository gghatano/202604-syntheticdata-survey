from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _line(df: pd.DataFrame, y: str, title: str, ylabel: str, out: Path, lower_better: bool = True) -> None:
    if y not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    for impl, sub in df.groupby("impl"):
        g = sub.groupby("epsilon")[y].mean().reset_index().sort_values("epsilon")
        ax.plot(g["epsilon"], g[y], marker="o", label=impl)
    ax.set_xscale("log")
    ax.set_xlabel("epsilon")
    ax.set_ylabel(ylabel + (" (lower=better)" if lower_better else " (higher=better)"))
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _bar(df: pd.DataFrame, y: str, title: str, ylabel: str, out: Path) -> None:
    if y not in df.columns:
        return
    agg = df.groupby("impl")[y].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(agg["impl"], agg["mean"], yerr=agg["std"].fillna(0), capsize=4)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _scatter_util_priv(util: pd.DataFrame, priv: pd.DataFrame, out: Path) -> None:
    merged = util.merge(priv, on=["impl", "epsilon", "seed"])
    if merged.empty:
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    for impl, sub in merged.groupby("impl"):
        ax.scatter(sub["tvd_mean"], sub["dcr_mean"], label=impl, s=60, alpha=0.75)
    ax.set_xlabel("utility TVD mean (lower=better utility)")
    ax.set_ylabel("DCR mean (higher=safer)")
    ax.set_title("Utility vs Privacy")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _radar(summary: pd.DataFrame, out: Path) -> None:
    cols = ["tvd_mean", "bivariate_tvd_mean", "elapsed_fit", "mia_auc"]
    labels = ["utility (1-TVD)", "bivariate utility", "fit speed", "privacy (1-MIA)"]
    if not all(c in summary.columns for c in cols):
        return
    agg = summary.groupby("impl")[cols].mean(numeric_only=True)
    scores = pd.DataFrame(index=agg.index)
    scores["utility"] = 1 - agg["tvd_mean"].clip(0, 1)
    scores["biv_utility"] = 1 - agg["bivariate_tvd_mean"].clip(0, 1)
    max_fit = max(agg["elapsed_fit"].max(), 1.0)
    scores["fit_speed"] = 1 - (agg["elapsed_fit"] / max_fit)
    scores["privacy"] = 1 - (agg["mia_auc"] - 0.5).clip(0, 0.5) * 2

    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    for impl, row in scores.iterrows():
        vals = row.tolist() + [row.iloc[0]]
        ax.plot(angles, vals, marker="o", label=impl)
        ax.fill(angles, vals, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_title("Overall (higher=better)")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, default=Path("results"))
    args = ap.parse_args()
    rd = args.results_dir
    out_dir = rd / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(rd / "summary.csv")
    utility = pd.read_csv(rd / "utility_metrics.csv")
    privacy = pd.read_csv(rd / "privacy_metrics.csv")
    perf = pd.read_csv(rd / "performance_metrics.csv")

    ok = summary[summary["status"] == "ok"].copy()

    _line(utility, "tvd_mean", "Utility (univariate TVD) vs epsilon", "TVD mean", out_dir / "utility_vs_epsilon.png", lower_better=True)
    _line(utility, "bivariate_tvd_mean", "Bivariate TVD vs epsilon", "biv TVD mean", out_dir / "bivariate_vs_epsilon.png", lower_better=True)
    _line(privacy, "dcr_mean", "Privacy DCR vs epsilon", "DCR mean", out_dir / "privacy_dcr_vs_epsilon.png", lower_better=False)
    _line(privacy, "mia_auc", "MIA AUC vs epsilon", "AUC (0.5=safe)", out_dir / "privacy_mia_vs_epsilon.png", lower_better=True)
    _bar(perf, "elapsed_fit", "Fit time", "sec", out_dir / "fit_time.png")
    _bar(perf, "elapsed_sample", "Sample time", "sec", out_dir / "sample_time.png")
    _bar(perf, "peak_mem_mb", "Peak memory (tracemalloc)", "MB", out_dir / "peak_memory.png")
    _scatter_util_priv(utility, privacy, out_dir / "utility_vs_privacy.png")
    _radar(ok, out_dir / "radar_overall.png")

    # downstream task bar
    if "downstream_acc_synth" in utility.columns:
        _bar(utility, "downstream_acc_synth", "Downstream accuracy (synth→holdout)", "accuracy", out_dir / "downstream_acc.png")

    print(f"plots → {out_dir}")


if __name__ == "__main__":
    main()
