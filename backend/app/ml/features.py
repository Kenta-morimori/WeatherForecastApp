from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


@dataclass
class FeaturePipelineConfig:
    # 学習/推論双方で固定できるハイパラ
    base_cols: Tuple[str, ...] = ("d_mean", "d_min", "d_max", "d_prec")
    date_col: str = "date"
    group_cols: Tuple[str, ...] = ()  # 位置情報があれば ("lat","lon") 等
    ma_windows: Tuple[int, ...] = (3, 7)
    seasonal: bool = True
    clip_quantiles: Tuple[float, float] = (0.001, 0.999)  # 外れ値ガード
    min_periods_ratio: float = 0.5  # MAの最小有効サンプル比（0.5なら⌈w/2⌉）


@dataclass
class FeaturePipeline:
    """日次系列 -> 学習用特徴量へ変換するパイプライン（fit/transform互換）"""

    config: FeaturePipelineConfig = field(default_factory=FeaturePipelineConfig)
    # 学習後に確定する属性
    medians_: Dict[str, float] = field(default_factory=dict)
    clip_bounds_: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    feature_cols_: List[str] = field(default_factory=list)
    is_fit_: bool = False

    # ---- public API ---------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "FeaturePipeline":
        df = self._validate_and_copy(df)
        feat = self._add_features(df)
        # 学習データの統計量を記録（欠損/外れ値対策）
        self.medians_ = {
            c: float(
                np.nanmedian(
                    # ExtensionArray を避け、必ず float ndarray に統一
                    pd.to_numeric(feat[c], errors="coerce").to_numpy(dtype=float, copy=False)
                )
            )
            for c in feat.columns
            if c not in self._id_cols
        }
        loq, hiq = self.config.clip_quantiles
        self.clip_bounds_ = {
            c: (
                float(np.nanquantile(feat[c].values, loq)),
                float(np.nanquantile(feat[c].values, hiq)),
            )
            for c in feat.columns
            if c not in self._id_cols
        }
        # 学習時に使用する最終列集合（ID列を除く）
        self.feature_cols_ = [c for c in feat.columns if c not in self._id_cols]
        self.is_fit_ = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fit_:
            raise RuntimeError("FeaturePipeline is not fit yet. Call fit() first.")
        df = self._validate_and_copy(df)
        feat = self._add_features(df)

        # 1) 欠損埋め（学習時中央値）
        for c, m in self.medians_.items():
            if c in feat.columns:
                feat[c] = feat[c].fillna(m)

        # 2) 外れ値クリップ（学習時分位）
        for c, (lo, hi) in self.clip_bounds_.items():
            if c in feat.columns:
                feat[c] = feat[c].clip(lower=lo, upper=hi)

        # 学習時と同じ列順へ（不足列は作成、余剰列は削除）
        for c in self.feature_cols_:
            if c not in feat.columns:
                # あり得ないが堅牢性確保：欠損列は中央値で追加
                feat[c] = self.medians_.get(c, 0.0)
        feat = feat[self.feature_cols_].copy()

        # 数値化の最終チェック
        for c in feat.columns:
            feat[c] = pd.to_numeric(feat[c], errors="coerce").fillna(self.medians_.get(c, 0.0))

        return feat

    # ---- helpers ------------------------------------------------------------
    @property
    def _id_cols(self) -> Tuple[str, ...]:
        return (self.config.date_col,) + self.config.group_cols

    def required_history_days(self) -> int:
        """推論で必要な最小履歴（MAのため）。例: max(ma)+1（lag1ぶん）"""
        return (max(self.config.ma_windows) if self.config.ma_windows else 0) + 1

    def _validate_and_copy(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        miss = [c for c in (self._id_cols + self.config.base_cols) if c not in df.columns]
        if miss:
            raise ValueError(f"missing columns: {miss}")
        # 型・並び
        # pandas の dtype 判定APIは ExtensionDtype も安全に扱える
        if not is_datetime64_any_dtype(df[self.config.date_col]):
            df[self.config.date_col] = pd.to_datetime(df[self.config.date_col], errors="coerce")
        if df[self.config.date_col].isna().any():
            raise ValueError("date column contains NaT after parsing")
        # 並び順（リーク防止のため古い→新しい）
        sort_keys = list(self._id_cols)
        df = df.sort_values(sort_keys, kind="mergesort").reset_index(drop=True)
        return df

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        gcols = list(cfg.group_cols)
        out = df[[cfg.date_col, *gcols, *cfg.base_cols]].copy()

        # lag1, diff1, moving average（shift(1)で当日リーク防止）
        for col in cfg.base_cols:
            # groupby対応（位置単位で系列特徴を作る）
            if gcols:
                lag1 = out.groupby(gcols, group_keys=False)[col].shift(1)
                out[f"{col}_lag1"] = lag1
                out[f"{col}_diff1"] = out[col] - lag1
                for w in cfg.ma_windows:
                    mp = max(1, int(np.ceil(w * cfg.min_periods_ratio)))
                    out[f"{col}_ma{w}"] = (
                        out.groupby(gcols, group_keys=False)[col]
                        .shift(1)
                        .rolling(window=w, min_periods=mp)
                        .mean()
                    )
            else:
                lag1 = out[col].shift(1)
                out[f"{col}_lag1"] = lag1
                out[f"{col}_diff1"] = out[col] - lag1
                for w in cfg.ma_windows:
                    mp = max(1, int(np.ceil(w * cfg.min_periods_ratio)))
                    out[f"{col}_ma{w}"] = out[col].shift(1).rolling(window=w, min_periods=mp).mean()

        # 季節性（年サイクル）
        if cfg.seasonal:
            doy = out[cfg.date_col].dt.dayofyear.astype(float)
            two_pi = 2.0 * np.pi
            out["season_sin"] = np.sin(two_pi * doy / 365.25)
            out["season_cos"] = np.cos(two_pi * doy / 365.25)

        return out
