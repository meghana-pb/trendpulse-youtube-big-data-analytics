"""
TrendPulse - Advanced Feature Engineering
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

logger = logging.getLogger("trendpulse.feature_engineering")


def add_trend_buckets(df: pd.DataFrame) -> pd.DataFrame:
    def bucket(d):
        if d <= 1: return "1_day"
        elif d <= 3: return "2-3_days"
        elif d <= 7: return "4-7_days"
        elif d <= 14: return "8-14_days"
        else: return "15+_days"
    if "trending_duration_days" in df.columns:
        df["trending_duration_bucket"] = df["trending_duration_days"].apply(bucket)
    return df


def add_view_velocity(df: pd.DataFrame) -> pd.DataFrame:
    if "views" in df.columns and "trending_duration_days" in df.columns:
        df["view_velocity"] = (df["views"] / df["trending_duration_days"].clip(lower=1)).round(0)
    return df


def add_normalized_features(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            col_min = df[col].min()
            col_max = df[col].max()
            denom = col_max - col_min
            if denom > 0:
                df[f"{col}_norm"] = ((df[col] - col_min) / denom).round(6)
            else:
                df[f"{col}_norm"] = 0.0
    return df


def add_log_transforms(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[f"{col}_log"] = np.log1p(df[col].fillna(0).clip(lower=0))
    return df


def compute_trendpulse_score(df: pd.DataFrame, weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    TrendPulse Score (0-100): analytical score based on normalized engagement and reach.
    NOTE: This is an analytical score, not a prediction of future trending.
    """
    default_weights = {
        "engagement_rate_norm": 0.30,
        "view_velocity_norm": 0.25,
        "comment_rate_norm": 0.15,
        "tag_count_norm": 0.10,
        "like_rate_norm": 0.15,
        "title_length_norm": 0.05,
    }
    if weights is None:
        weights = default_weights
    norm_cols = [c.replace("_norm", "") for c in weights.keys()]
    df = add_view_velocity(df)
    df = add_normalized_features(df, norm_cols + ["view_velocity"])
    score = pd.Series(0.0, index=df.index)
    for feat, weight in weights.items():
        if feat in df.columns:
            score += df[feat].fillna(0) * weight
    df["trendpulse_score"] = (score * 100).clip(0, 100).round(2)
    df["trendpulse_label"] = pd.cut(
        df["trendpulse_score"], bins=[-0.1, 30, 60, 80, 100],
        labels=["Low", "Moderate", "High", "Very High"])
    return df


def run_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = add_trend_buckets(df)
    df = add_view_velocity(df)
    df = add_log_transforms(df, ["views", "likes", "comment_count", "engagement_rate"])
    df = add_normalized_features(df, [
        "views", "likes", "comment_count", "engagement_rate",
        "tag_count", "title_length", "like_rate", "comment_rate"])
    df = compute_trendpulse_score(df)
    logger.info(f"Feature engineering complete. Shape: {df.shape}")
    return df
