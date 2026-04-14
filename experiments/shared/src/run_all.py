from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


RUNNER_PATHS = {
    "smartnoise": "experiments/mst_smartnoise/src/runner.py",
    "private_pgm": "experiments/mst_private_pgm/src/runner.py",
    "dpmm": "experiments/mst_dpmm/src/runner.py",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(Path(path).read_text())


def run_one(
    impl: str,
    epsilon: float,
    seed: int,
    repo_root: Path,
    output_dir: Path,
    timeout: int,
    dry_run: bool,
) -> dict:
    out_json = output_dir / "raw" / f"{impl}_eps{epsilon}_seed{seed}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "implementation": impl,
        "epsilon": epsilon,
        "seed": seed,
        "output_json": str(out_json),
    }
    if dry_run:
        stub = {
            **record,
            "status": "ok",
            "elapsed_fit_sec": 0.0,
            "elapsed_sample_sec": 0.0,
            "peak_memory_mb": 0.0,
            "utility_tvd_mean": 0.0,
            "privacy_dcr_mean": 0.0,
        }
        out_json.write_text(json.dumps(stub))
        return stub
    runner_rel = RUNNER_PATHS.get(impl)
    if runner_rel is None:
        return {**record, "status": "error", "error": f"unknown impl {impl}"}
    runner_path = repo_root / runner_rel
    cmd = [
        sys.executable, str(runner_path),
        "--epsilon", str(epsilon),
        "--seed", str(seed),
        "--output", str(out_json),
    ]
    try:
        subprocess.run(cmd, timeout=timeout, check=True)
        data = json.loads(out_json.read_text())
        return {**record, **data}
    except subprocess.TimeoutExpired:
        return {**record, "status": "timeout", "error": f"timeout after {timeout}s"}
    except subprocess.CalledProcessError as e:
        return {**record, "status": "error", "error": f"exit {e.returncode}"}
    except FileNotFoundError as e:
        return {**record, "status": "error", "error": str(e)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, default=Path("experiments/shared/configs/experiment_base.yaml"))
    ap.add_argument("--epsilons", type=Path, default=Path("experiments/shared/configs/epsilon_grid.yaml"))
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = load_yaml(args.base)
    eps_cfg = load_yaml(args.epsilons)
    epsilons = eps_cfg["epsilons"] if isinstance(eps_cfg, dict) else eps_cfg
    impls = base.get("implementations", list(RUNNER_PATHS.keys()))
    repeats = int(base.get("repeats", 5))
    timeout = int(base.get("timeout_fit_sec", 1800))
    output_dir = Path(base.get("output_dir", "results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    failures: list[dict] = []
    for impl in impls:
        for eps in epsilons:
            for seed in range(repeats):
                rec = run_one(impl, float(eps), seed, args.repo_root, output_dir, timeout, args.dry_run)
                records.append(rec)
                if rec.get("status") not in (None, "ok", "success"):
                    failures.append(rec)

    df = pd.DataFrame(records)
    df.to_csv(output_dir / "summary.csv", index=False)

    for metric_prefix in ["utility_", "privacy_", "elapsed_", "peak_"]:
        cols = [c for c in df.columns if c.startswith(metric_prefix)]
        if cols:
            sub = df[["implementation", "epsilon", "seed", *cols]]
            sub.to_csv(output_dir / f"metrics_{metric_prefix.rstrip('_')}.csv", index=False)

    pd.DataFrame(failures).to_csv(output_dir / "failures.csv", index=False)
    print(f"wrote {len(records)} rows to {output_dir/'summary.csv'} ({len(failures)} failures)")


if __name__ == "__main__":
    main()
