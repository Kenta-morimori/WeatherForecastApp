from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd


class SimpleRegModel:
    """回帰モデルのラッパ
    - 新: {"pipeline": FeaturePipeline, "model": sklearn, "metadata": {...}}
      * metadata.residual=True の場合は d0 を加算して元のスケールへ戻す
    - 旧: 直接 sklearn モデル（d0_* をそのまま予測に）
    """

    def __init__(self, model: Any):
        self.model = model

    @classmethod
    def load(cls, path: str) -> "SimpleRegModel":
        return cls(model=joblib.load(path))

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        # 新形式（辞書）
        if isinstance(self.model, dict) and "model" in self.model:
            pipe = self.model.get("pipeline")
            reg = self.model["model"]
            meta = self.model.get("metadata", {}) or {}
            residual = bool(meta.get("residual", False))

            if pipe is not None:
                X = pipe.transform(df)
            else:
                X = df[["d0_mean", "d0_min", "d0_max", "d0_prec"]]

            y_hat = reg.predict(X)

            if residual:
                # df は D0 の日次。d0 を加算して元スケールへ戻す
                d0 = df[["d_mean", "d_min", "d_max", "d_prec"]].to_numpy()
                y_hat = y_hat + d0

            return np.asarray(y_hat)

        # 旧形式
        X = df[["d0_mean", "d0_min", "d0_max", "d0_prec"]]
        return np.asarray(self.model.predict(X))
