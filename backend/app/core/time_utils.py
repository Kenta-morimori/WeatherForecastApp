from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def local_today_and_tomorrow(tz: str):
    """
    現地タイムゾーンで「今日/明日の日付」を返す。
    DST も zoneinfo で自然に考慮。
    """
    now_local = datetime.now(ZoneInfo(tz))
    today = now_local.date()
    tomorrow = today + timedelta(days=1)
    return today, tomorrow
