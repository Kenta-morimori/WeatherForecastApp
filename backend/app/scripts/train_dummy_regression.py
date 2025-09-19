from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from ..ml.features import FeaturePipeline, FeaturePipelineConfig


def main(seed: int = 42, n_days: int = 240) -> None:
    rng = np.random.default_rng(seed)

    # ==== 合成日次データ ====
    start = datetime(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n_days)]
    t = np.arange(n_days)

    base = 20 + 10 * np.sin(2 * np.pi * t / 365.25)  # 年周
    noise = rng.normal(0, 2, size=n_days)

    d_mean = base + noise
    d_min = d_mean - rng.uniform(1, 5, size=n_days)
    d_max = d_mean + rng.uniform(1, 5, size=n_days)
    d_prec = rng.gamma(shape=1.2, scale=1.0, size=n_days) * (rng.random(n_days) < 0.4)

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "d_mean": d_mean,
            "d_min": d_min,
            "d_max": d_max,
            "d_prec": d_prec,
        }
    )

    # 教師信号（翌日）
    y = df[["d_mean", "d_min", "d_max", "d_prec"]].shift(-1)
    y.columns = ["d1_mean", "d1_min", "d1_max", "d1_prec"]

    # 最終行はターゲットがないので除外
    df = df.iloc[:-1].reset_index(drop=True)
    y = y.iloc[:-1].reset_index(drop=True)

    # ==== 特徴量パイプライン ====
    pipe = FeaturePipeline(FeaturePipelineConfig())
    X = pipe.fit(df).transform(df)

    # ==== ダミー回帰 ====
    model = LinearRegression().fit(X, y)

    # ==== 保存（ファイル位置基準で固定）====
    # このスクリプトは backend/app/scripts/ 配下 → 親(1)=app, 親(2)=backend
    script_path = Path(__file__).resolve()
    app_dir = script_path.parents[1]  # .../backend/app
    save_path = app_dir / "model" / "model.joblib"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump({"pipeline": pipe, "model": model, "version": 1}, save_path.as_posix())
    print(f"saved to {save_path.as_posix()}")


if __name__ == "__main__":
    main()
