from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2] / "shared" / "src"
sys.path.insert(0, str(ROOT))

from interface import FitConfig  # noqa: E402
from preprocessing import PreprocessRules, preprocess  # noqa: E402

from wrapper import SmartNoiseMST  # noqa: E402

IMPL = "mst_smartnoise"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--preprocessing-config", type=Path, required=True)
    p.add_argument("--epsilon", type=float, required=True)
    p.add_argument("--delta", type=float, default=1e-9)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--n-synth", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dataset", type=str, default="adult")
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    tag = f"{IMPL}_{args.epsilon}_{args.seed}"
    synth_path = args.out / f"synth_{tag}.csv"
    run_path = args.out / f"run_{tag}.json"

    record: dict = {
        "impl": IMPL,
        "epsilon": args.epsilon,
        "seed": args.seed,
        "n_synth": args.n_synth,
        "elapsed_fit": None,
        "elapsed_sample": None,
        "peak_mem_mb": None,
        "status": "ok",
    }

    try:
        df_raw = pd.read_csv(args.data)
        all_rules = yaml.safe_load(args.preprocessing_config.read_text())
        raw_rules = all_rules[args.dataset]
        rules = PreprocessRules(
            drop_cols=raw_rules.get("drop_cols", []),
            categorical_cols=raw_rules.get("categorical_cols", []),
            numeric_cols=raw_rules.get("numeric_cols", []),
            bins=raw_rules.get("bins", {}),
            top_k=raw_rules.get("top_k", {}),
            missing_token=raw_rules.get("missing_token", "__NA__"),
        )
        df_proc, domain, _encoders = preprocess(df_raw, rules)

        cfg = FitConfig(
            epsilon=args.epsilon,
            delta=args.delta,
            domain=domain,
            categorical_columns=list(df_proc.columns),
            seed=args.seed,
            timeout_sec=1800,
        )

        model = SmartNoiseMST()
        fit_res = model.fit(df_proc, cfg)
        record["elapsed_fit"] = fit_res.elapsed_sec
        record["peak_mem_mb"] = fit_res.peak_memory_mb

        t0 = time.perf_counter()
        df_synth = model.sample(args.n_synth, seed=args.seed)
        record["elapsed_sample"] = time.perf_counter() - t0

        df_synth.to_csv(synth_path, index=False)
    except Exception as e:  # noqa: BLE001
        record["status"] = "failed"
        record["error"] = f"{type(e).__name__}: {e}"
        record["traceback"] = traceback.format_exc()

    run_path.write_text(json.dumps(record, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
