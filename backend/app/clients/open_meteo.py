from __future__ import annotations
from dataclasses import dataclass

@dataclass
class OpenMeteoClient:
    timeout: float = 10.0

    # ここは後で本実装に差し替え。
    # routes 側でモック差替え（テスト）もしやすいよう、メソッド名は固定で用意。
    def fetch_recent_daily(self, lat: float, lon: float, tz: str, days: int = 14):
        """
        直近 days 日のサマリー（日次）のダミーデータを返す。
        実装を後で Open-Meteo 叩く形に差し替える前提。
        """
        # ダミー：最低限の形だけ返す
        return {
            "lat": lat,
            "lon": lon,
            "tz": tz,
            "days": days,
            "daily": []  # 後で [ {date: 'YYYY-MM-DD', tmax:..., tmin:..., precip:...}, ... ] などに
        }
