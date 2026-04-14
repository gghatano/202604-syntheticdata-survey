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

from dpmm.pipelines.mst import MSTPipeline  # noqa: E402


class DpmmMST(BaseSynthesizer):
    def __init__(self) -> None:
        self._model: MSTPipeline | None = None
        self._columns: list[str] = []

    def fit(self, df: pd.DataFrame, config: FitConfig) -> FitResult:
        self._columns = list(df.columns)
        domain = {c: int(config.domain[c]) for c in self._columns}

        tracemalloc.start()
        t0 = time.perf_counter()
        # disable_processing=True: data is already preprocessed and integer-encoded.
        self._model = MSTPipeline(
            epsilon=config.epsilon,
            delta=config.delta,
            disable_processing=True,
            n_jobs=1,
        )
        self._model.fit(df.astype(int), domain=domain, random_state=config.seed)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return FitResult(
            elapsed_sec=elapsed,
            peak_memory_mb=peak / (1024 * 1024),
            model_info={"algorithm": "mst", "library": "dpmm"},
        )

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        assert self._model is not None, "fit() must be called first"
        out = self._model.generate(n_records=n, random_state=seed)
        return out[self._columns]

    def get_metadata(self) -> dict[str, Any]:
        return {"library": "dpmm", "algorithm": "mst"}
