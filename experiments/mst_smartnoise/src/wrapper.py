from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "shared" / "src"
sys.path.insert(0, str(ROOT))

from interface import BaseSynthesizer, FitConfig, FitResult  # noqa: E402
from snsynth import Synthesizer  # noqa: E402


class SmartNoiseMST(BaseSynthesizer):
    """MST wrapper using snsynth.Synthesizer.create("mst", ...)."""

    def __init__(self) -> None:
        self._model = None
        self._columns: list[str] | None = None
        self._config: FitConfig | None = None

    def fit(self, df: pd.DataFrame, config: FitConfig) -> FitResult:
        self._columns = list(df.columns)
        self._config = config
        cat_cols = list(config.categorical_columns) if config.categorical_columns else list(df.columns)

        tracemalloc.start()
        t0 = time.perf_counter()
        # snsynth MST uses Private-PGM internally; epsilon/delta passed at create time.
        self._model = Synthesizer.create("mst", epsilon=config.epsilon, delta=config.delta)
        # snsynth infers domain from data; preprocessed ints are treated as categorical via categorical_columns.
        self._model.fit(df, categorical_columns=cat_cols, preprocessor_eps=0.0)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return FitResult(
            elapsed_sec=elapsed,
            peak_memory_mb=peak / (1024 * 1024),
            model_info={"algorithm": "mst", "epsilon": config.epsilon, "delta": config.delta},
            warnings=[],
        )

    def sample(self, n: int, seed: int) -> pd.DataFrame:
        if self._model is None or self._columns is None:
            raise RuntimeError("fit() must be called before sample().")
        np.random.seed(seed)
        import random
        random.seed(seed)
        out = self._model.sample(n)
        if not isinstance(out, pd.DataFrame):
            out = pd.DataFrame(out, columns=self._columns)
        return out[self._columns]

    def get_metadata(self) -> dict:
        return {"library": "smartnoise-synth", "algorithm": "mst"}
