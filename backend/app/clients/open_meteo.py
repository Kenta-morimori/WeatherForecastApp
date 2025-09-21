from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from ..observability import record_ext_api_call


@dataclass
class OpenMeteoClient:
    timeout: float = 10.0

    async def fetch_recent_daily(
        self, lat: float, lon: float, tz: str, days: int = 14
    ) -> Dict[str, Any]:
        """
        Open-Meteo の日次サマリー（直近 days 日相当）を取得する簡易実装。
        - 可観測性: 外部API呼び出しは record_ext_api_call() で必ず記録する。
        - 注意: API仕様は将来変わり得るため、必要に応じて調整すること。
        """
        url = "https://api.open-meteo.com/v1/forecast"
        # 代表的な日次指標（必要に応じて増減）
        daily = "temperature_2m_max,temperature_2m_min,precipitation_sum"
        # Open-Meteoは過去データの取得に past_days を使う（安全のため上限を設ける）
        past_days = max(0, min(int(days), 92))

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": daily,
            "timezone": tz,
            "past_days": past_days,
        }

        t0 = time.perf_counter()
        status = 599
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                status = resp.status_code
                resp.raise_for_status()
                return resp.json()
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            record_ext_api_call(url=url, status=status, duration_ms=dt_ms)
