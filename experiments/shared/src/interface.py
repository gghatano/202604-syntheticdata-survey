from __future__ import annotations

import time
import tracemalloc
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class FitConfig:
    epsilon: float
    domain: dict[str, int] = field(default_factory=dict)
    categorical_columns: list[str] = field(default_factory=list)
    delta: float = 1e-9
    seed: int = 0
    timeout_sec: int = 1800


@dataclass
class FitResult:
    elapsed_sec: float = 0.0
    peak_memory_mb: float = 0.0
    model_info: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class BaseSynthesizer(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame, config: FitConfig) -> FitResult: ...

    @abstractmethod
    def sample(self, n: int, seed: int) -> pd.DataFrame: ...

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]: ...


@contextmanager
def measure(label: str = ""):
    tracemalloc.start()
    t0 = time.perf_counter()
    box: dict[str, Any] = {"result": None, "elapsed_sec": 0.0, "peak_memory_mb": 0.0, "label": label}
    try:
        yield box
    finally:
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        box["elapsed_sec"] = elapsed
        box["peak_memory_mb"] = peak / (1024 * 1024)
