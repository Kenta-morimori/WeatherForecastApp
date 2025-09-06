# backend/app/services/open_meteo.py
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Tuple

import httpx

DEFAULT_BASE = os.getenv("OPEN_METEO_BASE", "https://api.open-meteo.com")
USER_AGENT = os.getenv(
    "OPEN_METEO_UA",
    "WeatherForecastApp/0.1 (+https://github.com/Kenta-morimori/WeatherForecastApp)",
)


# ---- 簡易メモリキャッシュ（TTL秒） ----
class _TTLCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        now = time.time()
        hit = self._store.get(key)
        if not hit:
            return None
        ts, value = hit
        if now - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)


_cache = _TTLCache(ttl_seconds=int(os.getenv("OPEN_METEO_CACHE_TTL", "300")))


@dataclass(frozen=True)
class ForecastResult:
    """明日予測に必要な配列（時系列）"""

    times: List[str]  # ISO8601 (hourly)
    temperature_2m: List[float]
    precipitation: List[float]


class OpenMeteoClient:
    """Open-Meteo forecast client with timeout/retry and simple cache"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE,
        timeout: float = 10.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff_factor

    def _cache_key(self, lat: float, lon: float, start: date, end: date) -> str:
        return f"{lat:.4f}:{lon:.4f}:{start.isoformat()}:{end.isoformat()}"

    def get_forecast(self, lat: float, lon: float, start: date, end: date) -> ForecastResult:
        """
        Args:
            lat, lon: 緯度経度
            start, end: 取得期間（閉区間。Open-Meteoは日付境界で扱う）
        Returns:
            ForecastResult（時刻、2m気温、降水量の配列）
        """
        key = self._cache_key(lat, lon, start, end)
        cached = _cache.get(key)
        if cached:
            return cached

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": "temperature_2m,precipitation",
            "timezone": "auto",
        }
        headers = {"User-Agent": USER_AGENT}

        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, headers=headers) as client:
                    resp = client.get(f"{self.base_url}/v1/forecast", params=params)
                    resp.raise_for_status()
                    data = resp.json()
                result = self._parse(data)
                _cache.set(key, result)
                return result
            except Exception as e:  # noqa: BLE001（シンプルにまとめる）
                last_err = e
                # 簡易エクスポネンシャルバックオフ
                time.sleep(self.backoff * (2 ** (attempt - 1)))
        # すべて失敗したら例外
        assert last_err is not None
        raise last_err

    @staticmethod
    def _parse(payload: Dict[str, Any]) -> ForecastResult:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        temp = hourly.get("temperature_2m") or []
        precip = hourly.get("precipitation") or []
        # 正規化：長さを揃える（不足分は切り詰め）
        n = min(len(times), len(temp), len(precip))
        return ForecastResult(
            times=list(times[:n]),
            temperature_2m=list(map(float, temp[:n])),
            precipitation=list(map(float, precip[:n])),
        )


# --- ファイルキャッシュの簡易例（任意で使いたい時だけ） ---
def dump_cache_to_file(result: ForecastResult, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "times": result.times,
                "temperature_2m": result.temperature_2m,
                "precipitation": result.precipitation,
            },
            f,
            ensure_ascii=False,
        )


def load_cache_from_file(path: str) -> ForecastResult | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ForecastResult(
        times=list(data["times"]),
        temperature_2m=list(map(float, data["temperature_2m"])),
        precipitation=list(map(float, data["precipitation"])),
    )
