from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def load_scores(yaml_path: Path) -> pd.DataFrame:
    yaml_path = Path(yaml_path)
    data = yaml.safe_load(yaml_path.read_text())
    rows: list[dict] = []
    if isinstance(data, dict):
        for impl, scores in data.items():
            if isinstance(scores, dict):
                row = {"implementation": impl, **scores}
            else:
                row = {"implementation": impl, "score": scores}
            rows.append(row)
    elif isinstance(data, list):
        rows = list(data)
    return pd.DataFrame(rows)


def to_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
