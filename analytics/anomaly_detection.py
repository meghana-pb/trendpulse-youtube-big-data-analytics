"""
TrendPulse - Anomaly Detection (Breakout Videos)
Identifies videos with unusually high views, engagement, or trending duration.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict

logger = logging.getLogger("trendpulse.anomaly")


def _iqr_outliers(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Return boolean mask of IQR outliers (above Q3 + multiplier*IQR)."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    upper = q3 + multiplier * iqr
    return series > upper


def _zscore_outliers(series: pd.Series, threshold: float = 2.5) -> pd.Series:
    """Return boolean mask of z-score outliers."""
    z = (series - series.mean()) / series.std()
    return z.abs() > threshold


def compute_anomaly_score(df: pd.DataFrame, row_idx) -> float:
    """Score 0-100: how many std deviations above normal for key metrics."""
    row = df.loc[row_idx]
    scores = []
    for col in ["views", "engagement_rate", "trending_duration_days"]:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                z = (row[col] - mean) / std
                scores.append(min(z * 15, 50))  # cap contribution at 50
    return round(min(sum(max(s, 0) for s in scores), 100), 2)


def detect_breakout_videos(df: pd.DataFrame, max_results: int = 50) -> pd.DataFrame:
    """
    Detect anomalous/breakout videos using IQR and z-score methods.
    Returns DataFrame with anomaly info.
    """
    if len(df) < 10:
        logger.warning("Too few records for anomaly detection")
        return pd.DataFrame()

    flags = pd.DataFrame(index=df.index)
    reasons_map: Dict[int, List[str]] = {i: [] for i in df.index}

    # High views
    if "views" in df.columns:
        iqr_views = _iqr_outliers(df["views"])
        for idx in df.index[iqr_views]:
            reasons_map[idx].append("Unusually high view count")

    # High engagement rate
    if "engagement_rate" in df.columns:
        iqr_eng = _iqr_outliers(df["engagement_rate"])
        for idx in df.index[iqr_eng]:
            reasons_map[idx].append("Unusually high engagement rate")

    # Long trending duration
    if "trending_duration_days" in df.columns:
        iqr_dur = _iqr_outliers(df["trending_duration_days"])
        for idx in df.index[iqr_dur]:
            reasons_map[idx].append("Unusually long trending duration")

    # High trending despite low initial views (z-score on ratio)
    if "trending_duration_days" in df.columns and "views" in df.columns:
        ratio = df["trending_duration_days"] / df["views"].clip(lower=1) * 1e6
        z_ratio = _zscore_outliers(ratio, threshold=2.0)
        for idx in df.index[z_ratio]:
            reasons_map[idx].append("Long trending duration relative to view count")

    # High likes despite moderate views
    if "likes" in df.columns and "views" in df.columns:
        iqr_likes = _iqr_outliers(df["like_rate"] if "like_rate" in df.columns else df["likes"] / df["views"].clip(1))
        for idx in df.index[iqr_likes]:
            if "Unusually high engagement rate" not in reasons_map[idx]:
                reasons_map[idx].append("Unusually high like rate")

    # Collect anomalous videos (at least 1 reason)
    anomalous_ids = [idx for idx, reasons in reasons_map.items() if reasons]
    if not anomalous_ids:
        logger.info("No breakout videos detected")
        return pd.DataFrame()

    result_rows = []
    for idx in anomalous_ids:
        row = df.loc[idx]
        score = compute_anomaly_score(df, idx)
        result_rows.append({
            "video_id": str(row.get("video_id", "")),
            "title": str(row.get("title", "Unknown")),
            "category_name": str(row.get("category_name", "Unknown")),
            "views": int(row.get("views", 0)),
            "likes": int(row.get("likes", 0)),
            "comment_count": int(row.get("comment_count", 0)),
            "engagement_rate": float(row.get("engagement_rate", 0)),
            "trending_duration_days": int(row.get("trending_duration_days", 1)),
            "trendpulse_score": float(row.get("trendpulse_score", 0)),
            "anomaly_score": score,
            "anomaly_reasons": reasons_map[idx],
        })

    result = pd.DataFrame(result_rows)
    result = result.sort_values("anomaly_score", ascending=False).head(max_results)
    logger.info(f"Detected {len(result)} breakout videos")
    return result.reset_index(drop=True)
