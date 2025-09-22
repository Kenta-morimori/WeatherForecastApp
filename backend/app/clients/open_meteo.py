# app/clients/open_meteo.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Sequence, Union

import httpx

# QueryParams 互換の型（mypy対策）
QPAtom = Union[str, int, float, bool, None]
QP = Union[QPAtom, Sequence[QPAtom]]

# 可観測性: 存在しない環境でも動くように no-op フォールバック
try:
    from ..observability import record_ext_api_call  # type: ignore
except Exception:  # pragma: no cover

    def record_ext_api_call(url: str, status: int, duration_ms: float) -> None:  # type: ignore
        return


@dataclass
class OpenMeteoClient:
    timeout: float = 10.0
    base_url: str = "https://api.open-meteo.com/v1/forecast"
    user_agent: str = (
        "WeatherForecastApp/0.1 (+https://github.com/Kenta-morimori/WeatherForecastApp)"
    )

    async def fetch_recent_daily(
        self, lat: float, lon: float, tz: str, days: int = 14
    ) -> Dict[str, Any]:
        """
        Open-Meteo の日次サマリー（直近 days 日）を取得。
        - 可観測性: 外部呼び出しは record_ext_api_call() で必ず記録。
        """
        daily = "temperature_2m_max,temperature_2m_min,precipitation_sum"
        # Open-Meteo は過去データに past_days を利用（上限 92）
        past_days = max(1, min(int(days), 92))

        params: Dict[str, QP] = {
            "latitude": lat,
            "longitude": lon,
            "daily": daily,
            "timezone": tz,
            "past_days": past_days,
        }
        headers: Dict[str, str] = {"User-Agent": self.user_agent}

        t0 = time.perf_counter()
        status = 599
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                # mypy が受け入れるように QueryParams でラップ
                resp = await client.get(self.base_url, params=httpx.QueryParams(params))
                status = resp.status_code
                resp.raise_for_status()
                return resp.json()
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            record_ext_api_call(url=self.base_url, status=status, duration_ms=dt_ms)
