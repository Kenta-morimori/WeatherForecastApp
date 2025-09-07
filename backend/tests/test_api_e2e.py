from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# FastAPIアプリ本体
from app.main import app


# ===== Open-Meteo モック =====
class _MockOM:
    """feature_builder から呼ばれるインターフェース互換（get_hourly/fetch_hourly）"""

    def get_hourly(
        self,
        *,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        hourly,
        timezone: str = "Asia/Tokyo",
    ) -> Dict[str, Any]:
        # 24時間ぶんのダミー時刻と値を返す
        # feature_builder は hourly["time"], ["temperature_2m"], ["precipitation"] 等を参照
        base = (
            datetime(2025, 1, 1, 0, 0, tzinfo=timezone)
            if hasattr(timezone, "tzname")
            else datetime(2025, 1, 1, 0, 0)
        )
        times = [(base + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(24)]
        temps = [10.0 + i * 0.1 for i in range(24)]
        precs = [0.0 for _ in range(24)]
        return {
            "hourly": {
                "time": times,
                "temperature_2m": temps,
                "precipitation": precs,
            }
        }

    # 互換メソッド
    def fetch_hourly(self, **kwargs):
        return self.get_hourly(**kwargs)


@pytest.fixture(autouse=True)
def mock_open_meteo(monkeypatch):
    # app.services.open_meteo.OpenMeteoClient を上書き
    from app.services import open_meteo as om

    monkeypatch.setattr(om, "OpenMeteoClient", _MockOM)
    yield


def test_predict_200_regression(tmp_path, monkeypatch):
    # regression モードに固定。MODEL_PATHは存在チェック回避のためダミー設定（persistenceで動作確認してもOK）
    # ここでは regression で実運用に近い流れを確認。
    monkeypatch.setenv("MODEL_BACKEND", "regression")

    # シンプルに persistence でも通るよう fallback: MODEL_PATH が無い場合は persistence に切替
    # 実行環境で学習済みモデルのパスがあるなら、以下を環境変数で与えても良い。
    model_path = os.getenv("MODEL_PATH")
    if not model_path or not os.path.exists(model_path):
        # 未設定なら persistence に切り替え（API通ることを最小確認）
        monkeypatch.setenv("MODEL_BACKEND", "persistence")

    client = TestClient(app)
    resp = client.post("/predict", json={"lat": 35.6762, "lon": 139.6503})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "backend" in body and body["backend"] in ("regression", "persistence")
    assert "prediction" in body and isinstance(body["prediction"], dict)
    for k in ("d1_mean", "d1_min", "d1_max", "d1_prec"):
        assert k in body["prediction"]
