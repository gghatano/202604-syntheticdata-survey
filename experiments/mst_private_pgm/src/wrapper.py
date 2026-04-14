# Research-oriented code per spec 21.2; tmlt.private_pgm is a research fork of private-pgm.
# Import path note: some forks expose MST as `mechanisms.mst.MST`; tmlt fork may use `mbi.mechanisms.mst`.
from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "shared" / "src"
sys.path.insert(0, str(ROOT))

from interface import BaseSynthesizer, FitConfig, FitResult  # noqa: E402

from mbi import Dataset, Domain  # noqa: E402
from mst import MST  # noqa: E402 (tmlt.private_pgm exposes MST at top level of its mechanisms package)


class PrivatePGMMst(BaseSynthesizer):
    def __init__(self) -> None:
        self._synth_df: pd.DataFrame | None = None
        self._columns: list[str] = []

    def fit(self, df: pd.DataFrame, config: FitConfig) -> FitResult:
        domain_dict: dict[str, int] = dict(config.domain)
        cols = list(domain_dict.keys())
        self._columns = cols
        domain = Domain(cols, [domain_dict[c] for c in cols])
        data = Dataset(df[cols].astype(int), domain)
        delta = getattr(config, "delta", 1e-9) or 1e-9

        tracemalloc.start()
        t0 = time.perf_counter()
        synth = MST(data, epsilon=config.epsilon, delta=delta)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._synth_df = synth.df.reset_index(drop=True)
        return FitResult(
            elapsed_sec=elapsed,
            peak_memory_mb=peak / (1024 * 1024),
            model_info={"n_rows": len(self._synth_df)},
        )

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        assert self._synth_df is not None, "fit() must be called first"
        rng = np.random.default_rng(seed)
        base = self._synth_df
        if n <= len(base):
            idx = rng.choice(len(base), size=n, replace=False)
        else:
            idx = rng.choice(len(base), size=n, replace=True)
        return base.iloc[idx].reset_index(drop=True)[self._columns]

    def get_metadata(self) -> dict[str, Any]:
        return {"library": "tmlt.private_pgm", "algorithm": "mst"}
