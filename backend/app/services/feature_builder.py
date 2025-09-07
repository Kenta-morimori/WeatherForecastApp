from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class D0Features:
    d0_mean: float
    d0_min: float
    d0_max: float
    d0_prec: float

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(self)])


def _as_aware_dt(d: date, tz: str = "Asia/Tokyo") -> tuple[datetime, datetime]:
    z = ZoneInfo(tz)
    start = datetime.combine(d, time.min).replace(tzinfo=z)
    end = datetime.combine(d, time.max).replace(tzinfo=z)
    return start, end


def build_d0_features_from_series(
    temp_series: Sequence[float], precip_series: Sequence[float]
) -> D0Features:
    """時間解像度の配列から D0 特徴量を構築する（平均/最小/最大/降水合計）"""
    t = np.asarray(temp_series, dtype=float)
    p = np.asarray(precip_series, dtype=float)
    if t.size == 0:
        raise ValueError("temperature series is empty")
    return D0Features(
        d0_mean=float(np.nanmean(t)),
        d0_min=float(np.nanmin(t)),
        d0_max=float(np.nanmax(t)),
        d0_prec=float(np.nansum(p)) if p.size else 0.0,
    )


def build_d0_features_via_client(
    lat: float,
    lon: float,
    target_date: date,
    client: Any,
    tz: str = "Asia/Tokyo",
) -> D0Features:
    """Open-Meteoクライアント経由で対象日の hourly を取得し D0 特徴量を返す。
    クライアントは `fetch_hourly` or `get_hourly` を持つ想定（なければ ValueError）。
    """
    start, end = _as_aware_dt(target_date, tz=tz)

    kwargs = dict(
        lat=lat,
        lon=lon,
        start=start,
        end=end,
        hourly=["temperature_2m", "precipitation"],
        timezone=tz,
    )

    if hasattr(client, "fetch_hourly"):
        data: Mapping[str, Any] = client.fetch_hourly(**kwargs)
    elif hasattr(client, "get_hourly"):
        data = client.get_hourly(**kwargs)
    else:
        raise ValueError("OpenMeteo client must expose fetch_hourly or get_hourly")

    # 期待形: {"hourly": {"temperature_2m": [...], "precipitation": [...]} }
    hourly: Mapping[str, Any] = data["hourly"]
    temps: Sequence[float] = hourly["temperature_2m"]
    precs: Sequence[float] = hourly.get("precipitation", hourly.get("precipitation_sum", []))
    return build_d0_features_from_series(temps, precs)
