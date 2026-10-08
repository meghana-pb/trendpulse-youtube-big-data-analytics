"""
TrendPulse - Trend Score Calculator
Computes the TrendPulse Score (0-100) for videos.
NOTE: Analytical score only, not a prediction guarantee.
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

logger = logging.getLogger("trendpulse.trend_score")

SCORE_WEIGHTS = {
    "engagement_rate": 0.30,
    "view_velocity": 0.25,
    "comment_rate": 0.15,
    "tag_count": 0.10,
    "like_rate": 0.15,
    "title_length": 0.05,
}


def _normalize(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.0, index=series.index)
    return (series - mn) / (mx - mn)


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add trendpulse_score (0-100) and trendpulse_label to DataFrame."""
    df = df.copy()
    if "view_velocity" not in df.columns:
        if "views" in df.columns and "trending_duration_days" in df.columns:
            df["view_velocity"] = df["views"] / df["trending_duration_days"].clip(lower=1)
        else:
            df["view_velocity"] = 0.0

    score = pd.Series(0.0, index=df.index)
    for feat, weight in SCORE_WEIGHTS.items():
        if feat in df.columns:
            norm = _normalize(pd.to_numeric(df[feat], errors="coerce").fillna(0))
            score += norm * weight

    df["trendpulse_score"] = (score * 100).clip(0, 100).round(2)
    df["trendpulse_label"] = pd.cut(
        df["trendpulse_score"],
        bins=[-0.1, 30, 60, 80, 100],
        labels=["Low", "Moderate", "High", "Very High"]
    ).astype(str)
    return df


def get_video_score(video_id: str, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Get score info for a single video."""
    if "trendpulse_score" not in df.columns:
        df = calculate_scores(df)
    row = df[df["video_id"].astype(str) == str(video_id)]
    if row.empty:
        return None
    row = row.iloc[0]
    contributions = {}
    if "view_velocity" not in df.columns:
        df["view_velocity"] = df.get("views", 0) / df.get("trending_duration_days", 1).clip(lower=1)
    for feat, weight in SCORE_WEIGHTS.items():
        if feat in df.columns:
            norm_val = _normalize(pd.to_numeric(df[feat], errors="coerce").fillna(0))
            feat_score = float(norm_val.loc[row.name]) * weight * 100
            contributions[feat] = round(feat_score, 2)
    return {
        "video_id": video_id,
        "score": float(row["trendpulse_score"]),
        "label": str(row["trendpulse_label"]),
        "contributing_factors": contributions,
        "note": "Analytical score only. Not a prediction of future trending performance.",
    }
