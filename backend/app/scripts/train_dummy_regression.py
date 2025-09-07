# backend/app/scripts/train_dummy_regression.py
from __future__ import annotations

from pathlib import Path

import numpy as np

from app.ml.baseline import SimpleRegModel, set_seed


def main():
    rng = set_seed(42)
    n = 200
    d0_mean = rng.normal(20, 5, n)
    d0_min = d0_mean - rng.normal(2, 1, n)
    d0_max = d0_mean + rng.normal(3, 1, n)
    d0_prec = np.clip(rng.exponential(1.0, n), 0, 20)

    d1_mean = d0_mean + rng.normal(0, 0.3, n)
    d1_min = d0_min + rng.normal(0, 0.3, n)
    d1_max = d0_max + rng.normal(0, 0.3, n)
    d1_prec = np.clip(d0_prec + rng.normal(0, 0.3, n), 0, None)

    df = SimpleRegModel.build_training_frame(
        zip(d0_mean, d0_min, d0_max, d0_prec, d1_mean, d1_min, d1_max, d1_prec)
    )
    model = SimpleRegModel.train(df, random_state=42)

    # backend/app/model/model.joblib に保存（スクリプト位置起点）
    model_path = Path(__file__).resolve().parents[1] / "model" / "model.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))
    print(f"saved: {model_path}")


if __name__ == "__main__":
    main()
