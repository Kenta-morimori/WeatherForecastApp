from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.baseline import SimpleRegModel
from app.scripts.train_dummy_regression import main as train_main

MODEL_PATH = Path(__file__).parents[1] / "app" / "model" / "model.joblib"


def test_train_save_load_infer_reproducibility(tmp_path):
    # 1回目学習（seed固定）
    train_main(seed=42, n_days=240)
    assert MODEL_PATH.exists()

    # 推論入力（単日でもOK：features.py が補完）
    d0 = pd.DataFrame(
        {
            "date": pd.to_datetime([datetime(2025, 1, 15)]),
            "d_mean": [10.0],
            "d_min": [7.0],
            "d_max": [14.0],
            "d_prec": [0.2],
        }
    )

    reg1 = SimpleRegModel.load(MODEL_PATH.as_posix())
    y1 = reg1.predict(d0).reshape(-1)

    # 2回目学習（同じseed）
    train_main(seed=42, n_days=240)
    reg2 = SimpleRegModel.load(MODEL_PATH.as_posix())
    y2 = reg2.predict(d0).reshape(-1)

    # 完全一致（ダミーモデル・同seedなので一致するはず）
    assert np.allclose(y1, y2)
