from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd


class SimpleRegModel:
    """回帰モデルのラッパ（旧形式・新形式を吸収）
    - 旧: 直接 sklearn モデル
    - 新: {"pipeline": FeaturePipeline, "model": sklearn}
    """

    def __init__(self, model: Any):
        self.model = model

    @classmethod
    def load(cls, path: str) -> "SimpleRegModel":
        obj = joblib.load(path)
        return cls(model=obj)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        # 新形式（辞書形式）
        if isinstance(self.model, dict) and "model" in self.model:
            pipe = self.model.get("pipeline", None)
            reg = self.model["model"]
            if pipe is not None:
                X = pipe.transform(df)
            else:
                # パイプラインが無い場合の後方互換
                X = df[["d0_mean", "d0_min", "d0_max", "d0_prec"]]
            y = reg.predict(X)
            return np.asarray(y)

        # 旧形式（d0_* を直接入れる）
        X = df[["d0_mean", "d0_min", "d0_max", "d0_prec"]]
        return np.asarray(self.model.predict(X))
