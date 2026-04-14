# T02 共通 I/F 設計

## 目的
3 実装を同一条件で呼び出すための共通 Synthesizer インターフェースを定義する。

## 成果物
- `experiments/shared/src/interface.py` (型定義・ABC)
- `docs/tasks/notes/02_interface.md` (設計判断メモ)

## 必須 API
```python
class BaseSynthesizer(ABC):
    def fit(self, df: pd.DataFrame, config: FitConfig) -> FitResult: ...
    def sample(self, n: int, seed: int) -> pd.DataFrame: ...
    def get_metadata(self) -> dict: ...
```

- `FitConfig`: epsilon, delta, domain(dict[col->cardinality]), categorical_columns, seed, timeout_sec
- `FitResult`: elapsed_sec, peak_memory_mb, model_info, warnings
- 時間計測・メモリ計測・タイムアウトは base 側で共通化

## 完了条件
- ABC と dataclass が書かれている
- 3 runner から import 可能
- docstring に期待挙動が記載されている
