# backend/app/ml/baseline.py
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.utils import check_random_state

from app.services.open_meteo import ForecastResult, OpenMeteoClient


def set_seed(seed: int = 42) -> np.random.RandomState:
    """乱数シード固定（学習の再現性確保）"""
    return check_random_state(seed)


# === 1) Persistence baseline ===
@dataclass(frozen=True)
class PersistenceOutput:
    temp_mean_c: float
    temp_min_c: float
    temp_max_c: float
    precip_mm: float


def _day_slice(times_iso: List[str], arr: List[float], day: date) -> List[float]:
    """times/values から day(UTC/ローカル自動) のデータを抽出"""
    s = f"{day.isoformat()}T"
    return [v for t, v in zip(times_iso, arr) if t.startswith(s)]


def persistence_from_series(fc: ForecastResult, target_date: date) -> PersistenceOutput:
    """D+1 の予測を D0（前日）そのまま使う単純ベースライン"""
    d0 = target_date - timedelta(days=1)
    # 前日（D0）の時系列を切り出し
    temps = _day_slice(fc.times, fc.temperature_2m, d0)
    precs = _day_slice(fc.times, fc.precipitation, d0)
    if not temps:
        # データ穴埋め：全期間から代用
        temps = fc.temperature_2m
    if not precs:
        precs = fc.precipitation

    t_mean = float(np.mean(temps)) if temps else math.nan
    t_min = float(np.min(temps)) if temps else math.nan
    t_max = float(np.max(temps)) if temps else math.nan
    p_sum = float(np.sum(precs)) if precs else math.nan
    return PersistenceOutput(t_mean, t_min, t_max, p_sum)


# === 2) 単純回帰 baseline（学習/保存I/Oつき） ===
@dataclass
class SimpleRegModel:
    """D0の集約統計 → D+1（平均/最小/最大/降水）を予測する多出力回帰"""

    model: LinearRegression

    @staticmethod
    def build_training_frame(
        rows: Iterable[Tuple[float, float, float, float, float, float, float, float]],
    ) -> pd.DataFrame:
        """
        rows: 1行が (d0_mean, d0_min, d0_max, d0_prec, d1_mean, d1_min, d1_max, d1_prec)
        """
        cols = ["d0_mean", "d0_min", "d0_max", "d0_prec", "d1_mean", "d1_min", "d1_max", "d1_prec"]
        return pd.DataFrame(list(rows), columns=cols)

    @classmethod
    def train(cls, df: pd.DataFrame, random_state: int = 42) -> "SimpleRegModel":
        X = df[["d0_mean", "d0_min", "d0_max", "d0_prec"]].to_numpy()
        y = df[["d1_mean", "d1_min", "d1_max", "d1_prec"]].to_numpy()
        # 線形回帰（多出力）
        model = LinearRegression()
        model.fit(X, y)
        return cls(model=model)

    def predict(
        self, d0_mean: float, d0_min: float, d0_max: float, d0_prec: float
    ) -> PersistenceOutput:
        pred = self.model.predict(np.array([[d0_mean, d0_min, d0_max, d0_prec]]))[0]
        return PersistenceOutput(float(pred[0]), float(pred[1]), float(pred[2]), float(pred[3]))

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str) -> "SimpleRegModel":
        model = joblib.load(path)
        return cls(model=model)


# === 3) /predict 用ユーティリティ ===
def aggregate_day_stats(fc: ForecastResult, day: date) -> Tuple[float, float, float, float]:
    """指定日の集約統計（平均/最小/最大/降水合計）"""
    temps = _day_slice(fc.times, fc.temperature_2m, day)
    precs = _day_slice(fc.times, fc.precipitation, day)
    t_mean = float(np.mean(temps)) if temps else math.nan
    t_min = float(np.min(temps)) if temps else math.nan
    t_max = float(np.max(temps)) if temps else math.nan
    p_sum = float(np.sum(precs)) if precs else math.nan
    return t_mean, t_min, t_max, p_sum


def predict_with_backend(
    lat: float,
    lon: float,
    target_date: date,
    backend: str = "persistence",
    model_path: str | None = None,
    client: OpenMeteoClient | None = None,
) -> Tuple[PersistenceOutput, Dict[str, str]]:
    """
    backend:
      - "persistence": 前日そのまま
      - "regression":  保存済み線形回帰モデルを使う
    """
    client = client or OpenMeteoClient()
    # target_date の前日/当日の hourly を取得（安全側に 2日分）
    start = target_date - timedelta(days=1)
    end = target_date
    fc = client.get_forecast(lat=lat, lon=lon, start=start, end=end)

    # D0 集約を計算
    d0_mean, d0_min, d0_max, d0_prec = aggregate_day_stats(fc, start)

    if backend == "regression" and model_path and os.path.exists(model_path):
        model = SimpleRegModel.load(model_path)
        out = model.predict(d0_mean, d0_min, d0_max, d0_prec)
        explain = {
            "backend": "regression",
            "features_used": "d0_mean,d0_min,d0_max,d0_prec",
            "notes": f"seed fixed; model={os.path.basename(model_path)}",
        }
        return out, explain

    # fallback: persistence
    out = persistence_from_series(fc, target_date)
    explain = {
        "backend": "persistence",
        "features_used": "prev_day(hourly)→mean/min/max,sum(precip)",
        "notes": "D0をそのままD+1に用いる単純ベースライン",
    }
    return out, explain
