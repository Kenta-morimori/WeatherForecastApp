# backend/app/services/open_meteo.py
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Union

import httpx

# --- 追加：QueryParam互換の型エイリアス ---
QPAtom = Union[str, int, float, bool, None]
QP = Union[QPAtom, Sequence[QPAtom]]
# --------------------------------------

# --- 可観測性（存在しない環境でも動くように no-op フォールバック） ---
try:
    from app.observability import record_ext_api_call  # type: ignore
except Exception:  # pragma: no cover

    def record_ext_api_call(url: str, status: int, duration_ms: float) -> None:  # type: ignore
        return


DEFAULT_BASE = os.getenv("OPEN_METEO_BASE", "https://api.open-meteo.com")
USER_AGENT = os.getenv(
    "OPEN_METEO_UA",
    "WeatherForecastApp/0.1 (+https://github.com/Kenta-morimori/WeatherForecastApp)",
)

ParamAtom = Union[str, int, float, bool, None]
ParamSeq = Sequence[ParamAtom]
ParamValue = Union[ParamAtom, ParamSeq]


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

# /forecast（日次）専用のTTLキャッシュ（独立設定可能）
_daily_cache = _TTLCache(ttl_seconds=int(os.getenv("OPEN_METEO_DAILY_CACHE_TTL", "300")))


def _daily_cache_key(lat: float, lon: float, tz: str, days: int) -> str:
    return f"daily:{lat:.4f}:{lon:.4f}:{tz}:{int(days)}"


# AsyncClient の再利用（DNS/TLS再確立を回避してレイテンシ低減）
_async_client: httpx.AsyncClient | None = None


def _get_async_client(timeout: float, headers: Dict[str, str]) -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=timeout, headers=headers)
    return _async_client


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

    # ===== 既存インターフェース（後方互換）====================================

    def _cache_key(
        self,
        lat: float,
        lon: float,
        start: date,
        end: date,
        *,
        hourly: str = "temperature_2m,precipitation",
        tz: str = "auto",
    ) -> str:
        return f"{lat:.4f}:{lon:.4f}:{start.isoformat()}:{end.isoformat()}:{hourly}:{tz}"

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

        params: Dict[str, ParamValue] = {
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
                    resp = client.get(
                        f"{self.base_url}/v1/forecast", params=httpx.QueryParams(params)
                    )
                    resp.raise_for_status()
                    data = resp.json()
                result = self._parse(data)
                _cache.set(key, result)
                return result
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(self.backoff * (2 ** (attempt - 1)))
        assert last_err is not None
        raise last_err

    @staticmethod
    def _parse(payload: Dict[str, Any]) -> ForecastResult:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        temp = hourly.get("temperature_2m") or []
        precip = hourly.get("precipitation") or []
        n = min(len(times), len(temp), len(precip))
        return ForecastResult(
            times=list(times[:n]),
            temperature_2m=list(map(float, temp[:n])),
            precipitation=list(map(float, precip[:n])),
        )

    # ===== feature_builder 向けの新インターフェース ============================

    def get_hourly(
        self,
        *,
        lat: float,
        lon: float,
        start: date | datetime,
        end: date | datetime,
        hourly: Iterable[str],
        timezone: str = "Asia/Tokyo",
    ) -> Mapping[str, Any]:
        """
        feature_builder 用の hourly 取得（生の Open-Meteo 形式を返す）
        返り値: {"hourly": {...}, "hourly_units": {...}, ...}
        """
        start_date = start.date() if isinstance(start, datetime) else start
        end_date = end.date() if isinstance(end, datetime) else end

        hourly_param = ",".join(hourly)
        key = self._cache_key(lat, lon, start_date, end_date, hourly=hourly_param, tz=timezone)
        cached = _cache.get(key)
        if cached:
            return cached  # type: ignore[return-value]

        params: Dict[str, ParamValue] = {
            "latitude": f"{lat}",
            "longitude": f"{lon}",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": hourly_param,
            "timezone": timezone,
        }
        headers = {"User-Agent": USER_AGENT}

        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, headers=headers) as client:
                    resp = client.get(
                        f"{self.base_url}/v1/forecast", params=httpx.QueryParams(params)
                    )
                    resp.raise_for_status()
                    data = resp.json()
                _cache.set(key, data)
                return data
            except Exception as e:
                last_err = e
                time.sleep(self.backoff * (2 ** (attempt - 1)))
        assert last_err is not None
        raise last_err

    def fetch_hourly(self, **kwargs) -> Mapping[str, Any]:
        return self.get_hourly(**kwargs)

    # ===== 追加: /forecast 用（非同期・日次サマリー）==========================

    async def fetch_recent_daily(
        self,
        lat: float,
        lon: float,
        tz: str,
        days: int = 14,
    ) -> Dict[str, Any]:
        """
        直近 `days` 日の **日次サマリー** を取得（最高/最低気温・降水量）。
        - Open-Meteoでは過去データ取得に `past_days` を利用（上限 92）
        - 返り値は Open-Meteo の **生JSON** を返す（routes 側で整形）
        - 可観測性: 各試行ごとに record_ext_api_call(...) を記録
        - 最適化: 5分TTLキャッシュ, AsyncClient再利用
        """
        past_days = max(1, min(int(days), 92))
        key = _daily_cache_key(lat, lon, tz, past_days)
        cached = _daily_cache.get(key)
        if cached:
            return cached  # type: ignore[return-value]

        params: Dict[str, ParamValue] = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": tz,
            "past_days": past_days,
        }
        headers = {"User-Agent": USER_AGENT}
        url = f"{self.base_url}/v1/forecast"

        client = _get_async_client(self.timeout, headers)

        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            status = 599
            t1 = time.perf_counter()
            try:
                resp = await client.get(url, params=httpx.QueryParams(params))
                status = resp.status_code
                resp.raise_for_status()
                data = resp.json()
                # 観測記録（成功試行）
                dt_ms = (time.perf_counter() - t1) * 1000.0
                record_ext_api_call(url=url, status=status, duration_ms=dt_ms)
                _daily_cache.set(key, data)
                return data
            except Exception as e:
                # 観測記録（失敗試行）
                dt_ms = (time.perf_counter() - t1) * 1000.0
                record_ext_api_call(url=url, status=status, duration_ms=dt_ms)
                last_err = e
                if attempt < self.retries:
                    await asyncio.sleep(self.backoff * (2 ** (attempt - 1)))
                else:
                    break

        assert last_err is not None
        raise last_err


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
