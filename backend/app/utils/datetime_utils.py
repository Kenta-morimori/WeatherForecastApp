from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = ["now_utc", "local_today_and_tomorrow"]


def now_utc() -> datetime:
    """Patchable current time in UTC (pytest から monkeypatch される想定)。"""
    return datetime.now(timezone.utc)


def local_today_and_tomorrow(tz_name: str) -> tuple[date, date]:
    """
    指定 IANA タイムゾーンの「今日(D0)」「明日(D1)」を返す。
    現在時刻は now_utc() を経由して取得する（テストで固定可能）。
    """
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")

    local_now = now_utc().astimezone(tz)
    d0 = local_now.date()
    d1 = d0 + timedelta(days=1)
    return d0, d1
