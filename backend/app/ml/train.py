from __future__ import annotations

import argparse
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.multioutput import MultiOutputRegressor

from .features import FeaturePipeline, FeaturePipelineConfig

# --------------------------- データ生成（暫定: 合成） ---------------------------


def make_synthetic_daily(seed: int = 42, n_days: int = 365 * 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = datetime(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n_days)]
    t = np.arange(n_days)

    base = 20 + 10 * np.sin(2 * np.pi * t / 365.25)
    noise = rng.normal(0, 2, size=n_days)
    d_mean = base + noise
    d_min = d_mean - rng.uniform(1, 5, size=n_days)
    d_max = d_mean + rng.uniform(1, 5, size=n_days)
    d_prec = rng.gamma(shape=1.2, scale=1.0, size=n_days) * (rng.random(n_days) < 0.4)

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "d_mean": d_mean,
            "d_min": d_min,
            "d_max": d_max,
            "d_prec": d_prec,
        }
    )
    y = df[["d_mean", "d_min", "d_max", "d_prec"]].shift(-1)
    y.columns = ["d1_mean", "d1_min", "d1_max", "d1_prec"]
    df = df.iloc[:-1].reset_index(drop=True)
    y = y.iloc[:-1].reset_index(drop=True)
    return df, y


# --------------------------- メトリクス ----------------------------------------


@dataclass
class FoldMetrics:
    mae: Dict[str, float]
    rmse: Dict[str, float]
    mae_macro: float
    rmse_macro: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mae": self.mae,
            "rmse": self.rmse,
            "mae_macro": self.mae_macro,
            "rmse_macro": self.rmse_macro,
        }


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, target_names: List[str]) -> FoldMetrics:
    mae = {}
    rmse = {}
    for i, name in enumerate(target_names):
        mae[name] = float(mean_absolute_error(y_true[:, i], y_pred[:, i]))
        rmse[name] = float(root_mean_squared_error(y_true[:, i], y_pred[:, i]))
    mae_macro = float(np.mean(list(mae.values())))
    rmse_macro = float(np.mean(list(rmse.values())))
    return FoldMetrics(mae=mae, rmse=rmse, mae_macro=mae_macro, rmse_macro=rmse_macro)


# --------------------------- 学習ロジック --------------------------------------


def _make_model(seed: int) -> MultiOutputRegressor:
    # 少し強め＆汎化寄りの初期値（過学習しにくく、残差を拾いやすい）
    base = HistGradientBoostingRegressor(
        learning_rate=0.08,
        max_iter=800,
        max_depth=3,
        min_samples_leaf=20,
        l2_regularization=0.1,
        early_stopping=True,
        random_state=seed,
    )
    return MultiOutputRegressor(base)


def time_series_cv_train(
    df: pd.DataFrame,
    y: pd.DataFrame,
    seed: int,
    n_splits: int,
    residual: bool,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    TimeSeriesSplit で CV。train で fit、valid で評価。
    residual=True の場合は（y - d0）を学習し、予測時に d0 を加算。
    """
    target_names = list(y.columns)
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_reports: List[Dict[str, Any]] = []

    best_bundle: Dict[str, Any] | None = None
    best_score = math.inf

    d0_all = df[["d_mean", "d_min", "d_max", "d_prec"]].to_numpy()
    y_all = y.to_numpy()

    for fold, (tr_idx, va_idx) in enumerate(tscv.split(df), start=1):
        df_tr, df_va = df.iloc[tr_idx].copy(), df.iloc[va_idx].copy()
        y_tr, y_va = y_all[tr_idx], y_all[va_idx]
        d0_tr, d0_va = d0_all[tr_idx], d0_all[va_idx]

        # pipeline
        pipe = FeaturePipeline(FeaturePipelineConfig())
        X_tr = pipe.fit(df_tr).transform(df_tr)
        X_va = pipe.transform(df_va)

        # 目的変数（残差 or 直接）
        y_tr_fit = (y_tr - d0_tr) if residual else y_tr

        model = _make_model(seed)
        model.fit(X_tr, y_tr_fit)

        # 予測（残差なら戻す）
        y_hat = model.predict(X_va)
        if residual:
            y_hat = y_hat + d0_va

        metrics = compute_metrics(y_va, y_hat, target_names)

        # Baseline（persistence）
        baseline_metrics = compute_metrics(y_va, d0_va, target_names)

        fold_reports.append(
            {
                "fold": fold,
                "n_train": int(len(tr_idx)),
                "n_valid": int(len(va_idx)),
                "model_metrics": metrics.to_dict(),
                "baseline_metrics": baseline_metrics.to_dict(),
            }
        )

        if metrics.rmse_macro < best_score:
            best_score = metrics.rmse_macro
            best_bundle = {"pipeline": pipe, "model": model, "residual": residual}

    assert best_bundle is not None
    cv_report = {"folds": fold_reports}
    return best_bundle, cv_report


def refit_full_and_save(
    df: pd.DataFrame,
    y: pd.DataFrame,
    bundle: Dict[str, Any],
    cv_report: Dict[str, Any],
    out_dir: Path,
    seed: int,
    require_improve_ratio: float,
) -> Path:
    """全データで再学習 → /models に保存（{YYYYMMDD}_{gitSHA}_gbdt.joblib）"""
    residual = bool(bundle.get("residual", False))
    pipeline = FeaturePipeline(FeaturePipelineConfig())
    X_all = pipeline.fit(df).transform(df)

    d0_all = df[["d_mean", "d_min", "d_max", "d_prec"]].to_numpy()
    y_all = y.to_numpy()
    y_all_fit = (y_all - d0_all) if residual else y_all

    model = _make_model(seed)
    model.fit(X_all, y_all_fit)

    # CV集計 & baseline
    folds = cv_report["folds"]
    rmse_macro = float(np.mean([f["model_metrics"]["rmse_macro"] for f in folds]))
    rmse_macro_baseline = float(np.mean([f["baseline_metrics"]["rmse_macro"] for f in folds]))

    if rmse_macro > rmse_macro_baseline * require_improve_ratio:
        raise SystemExit(
            f"DoD failed: rmse_macro={rmse_macro:.4f} baseline={rmse_macro_baseline:.4f} "
            f"(require ratio <= {require_improve_ratio})"
        )

    # 保存名
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_sha = "nogit"
    datestamp = datetime.now().strftime("%Y%m%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    save_path = out_dir / f"{datestamp}_{git_sha}_gbdt.joblib"

    artifact = {
        "version": 3,
        "algo": "HistGradientBoostingRegressor",
        "pipeline": pipeline,
        "model": model,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "git_sha": git_sha,
            "cv": cv_report,
            "rmse_macro": rmse_macro,
            "rmse_macro_baseline": rmse_macro_baseline,
            "feature_config": asdict(FeaturePipelineConfig()),
            "seed": seed,
            "residual": residual,
        },
    }
    joblib.dump(artifact, save_path.as_posix())
    return save_path


# --------------------------- CLI ---------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Train GBDT model with shared feature pipeline")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-days", type=int, default=365 * 2)
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--models-dir", type=str, default="models")
    parser.add_argument("--require-improve", type=float, default=0.99)
    parser.add_argument("--residual", action="store_true", help="learn residual (y - persistence)")
    args = parser.parse_args()

    df, y = make_synthetic_daily(seed=args.seed, n_days=args.n_days)
    best_bundle, cv_report = time_series_cv_train(
        df, y, seed=args.seed, n_splits=args.splits, residual=args.residual
    )
    out_path = refit_full_and_save(
        df=df,
        y=y,
        bundle=best_bundle,
        cv_report=cv_report,
        out_dir=Path(args.models_dir),
        seed=args.seed,
        require_improve_ratio=args.require_improve,
    )
    print(json.dumps({"saved_to": out_path.as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
