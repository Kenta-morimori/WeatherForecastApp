from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils import datetime_utils as dtmod


# ---- Open-Meteo モック（ネット非依存） ----
class _MockOM:
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
        # 24hダミー
        base = datetime(2025, 1, 1, 0, 0)
        times = [(base + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(24)]
        temps = [10.0] * 24
        precs = [0.0] * 24
        return {"hourly": {"time": times, "temperature_2m": temps, "precipitation": precs}}

    def fetch_hourly(self, **kwargs):
        return self.get_hourly(**kwargs)


@pytest.fixture(autouse=True)
def mock_open_meteo(monkeypatch):
    # routes が保持している参照自体を差し替える（ここが重要）
    from app.api import routes as routes_mod

    monkeypatch.setattr(routes_mod, "OpenMeteoClient", _MockOM)
    yield


def test_local_today_and_tomorrow_around_utc_midnight(monkeypatch):
    fixed = datetime(2025, 1, 1, 23, 59, tzinfo=timezone.utc)
    monkeypatch.setattr(dtmod, "now_utc", lambda: fixed)
    d0, d1 = dtmod.local_today_and_tomorrow("Etc/UTC")
    assert str(d0) == "2025-01-01"
    assert str(d1) == "2025-01-02"

    fixed2 = datetime(2025, 1, 2, 0, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(dtmod, "now_utc", lambda: fixed2)
    d0b, d1b = dtmod.local_today_and_tomorrow("Etc/UTC")
    assert str(d0b) == "2025-01-02"
    assert str(d1b) == "2025-01-03"


def test_predict_uses_tz_for_d0_d1(monkeypatch):
    # CI安定のためデフォは persistence でもOK。今回は 200 応答の確認が目的
    monkeypatch.setenv("MODEL_BACKEND", "persistence")

    # UTC 23:59 を固定し tz=Etc/UTC を指定 → date 未指定で D0=その日
    monkeypatch.setattr(dtmod, "now_utc", lambda: datetime(2025, 1, 1, 23, 59, tzinfo=timezone.utc))

    client = TestClient(app)
    resp = client.post("/predict", json={"lat": 35.0, "lon": 139.0, "tz": "Etc/UTC"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["date_d0"] == "2025-01-01"
    assert body["date_d1"] == "2025-01-02"
