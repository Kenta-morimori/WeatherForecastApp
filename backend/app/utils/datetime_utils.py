from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    """テストでモック可能な now()。UTC固定で返す。"""
    return datetime.now(tz=timezone.utc)


def local_today_and_tomorrow(tz_name: str) -> tuple[date, date]:
    """UTC現在時刻から、指定タイムゾーンの「今日(D0)」「明日(D1)」を返す（DST考慮）。"""
    tz = ZoneInfo(tz_name)
    local_now = now_utc().astimezone(tz)
    d0 = local_now.date()
    d1 = date.fromordinal(d0.toordinal() + 1)
    return d0, d1
