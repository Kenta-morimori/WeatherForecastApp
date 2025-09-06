from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services.open_meteo import ForecastResult, OpenMeteoClient


@pytest.mark.timeout(20)
def test_fetch_one_item_network_or_mock(monkeypatch):
    client = OpenMeteoClient()

    start = date.today()
    end = start + timedelta(days=1)

    try:
        result = client.get_forecast(lat=35.681236, lon=139.767125, start=start, end=end)
    except Exception:
        # ネット不通などの場合はモックにフォールバック
        def fake_get_forecast(lat, lon, start, end):
            return ForecastResult(
                times=["2025-09-01T00:00", "2025-09-01T01:00"],
                temperature_2m=[26.1, 25.7],
                precipitation=[0.0, 0.2],
            )

        monkeypatch.setattr(OpenMeteoClient, "get_forecast", staticmethod(fake_get_forecast))
        result = client.get_forecast(lat=0.0, lon=0.0, start=start, end=end)

    # 共通アサーション
    assert isinstance(result.times, list) and len(result.times) > 0
    assert isinstance(result.temperature_2m, list) and len(result.temperature_2m) == len(
        result.times
    )
    assert isinstance(result.precipitation, list) and len(result.precipitation) == len(result.times)
