"""
TrendPulse - Factor Ranking
Ranks the top contributing factors for trending duration.
All rankings are data-driven, not hardcoded.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List

logger = logging.getLogger("trendpulse.factor_ranking")

FACTOR_LABELS: Dict[str, str] = {
    "engagement_rate": "Engagement Rate",
    "like_rate": "Like Rate",
    "comment_rate": "Comment Rate",
    "views": "Total Views",
    "view_velocity": "View Velocity",
    "publish_hour": "Publish Hour",
    "upload_time_bucket": "Upload Time Window",
    "category_id": "Video Category",
    "title_length": "Title Length",
    "description_length": "Description Length",
    "tag_count": "Number of Tags",
    "is_weekend": "Weekend Upload",
    "uppercase_ratio": "Uppercase Ratio in Title",
    "punctuation_count": "Punctuation in Title",
    "likes": "Total Likes",
    "comment_count": "Comment Count",
    "publish_weekday_name": "Day of Week",
    "title_length_bucket": "Title Length Category",
    "trendpulse_score": "TrendPulse Score (Composite)",
    "trending_duration_bucket": "Trending Duration Bucket",
}

INTERPRETATIONS = {
    "engagement_rate": "Higher engagement rate (likes + comments relative to views) strongly associates with longer trending periods.",
    "like_rate": "Videos with higher like rates relative to views tend to remain trending longer.",
    "comment_rate": "More comments per view indicate community engagement, which correlates with extended trending.",
    "views": "Higher total view counts are associated with extended trending duration.",
    "view_velocity": "Faster view accumulation (views per trending day) correlates with longer trending spans.",
    "publish_hour": "The hour of publication shows a statistically significant association with trending duration.",
    "upload_time_bucket": "The time-of-day window when a video is uploaded shows patterns in trending duration.",
    "category_id": "Video category has a significant group-level association with trending duration.",
    "title_length": "Title length shows a measurable relationship with how long videos stay trending.",
    "description_length": "Videos with more detailed descriptions tend to have different trending patterns.",
    "tag_count": "The number of tags is associated with content discoverability and trending duration.",
    "is_weekend": "Whether a video is uploaded on a weekend shows differences in average trending duration.",
    "uppercase_ratio": "The proportion of uppercase characters in titles shows a weak association with trending.",
    "punctuation_count": "Punctuation usage in titles has a detectable relationship with trending duration.",
    "likes": "Absolute like count is associated with broader audience engagement and trending duration.",
    "comment_count": "Absolute comment count reflects community interaction and trending persistence.",
    "publish_weekday_name": "The specific day of the week shows varying average trending durations across groups.",
    "title_length_bucket": "Videos in certain title length ranges show higher average trending durations.",
    "trendpulse_score": "The composite TrendPulse score aggregates multiple engagement signals.",
    "trending_duration_bucket": "The grouped trending duration categories capture distinct video lifecycle patterns.",
}


def _normalize_series(s: pd.Series) -> pd.Series:
    mn, mx = s.min(), s.max()
    if mx - mn == 0:
        return pd.Series(0.0, index=s.index)
    return (s - mn) / (mx - mn)


def rank_factors(corr_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Compute composite ranking score for each feature.
    Score = 0.35*|correlation_strength| + 0.25*normalized_mi +
            0.25*normalized_significance + 0.15*normalized_effect_size
    """
    if corr_df.empty:
        return pd.DataFrame()

    df = corr_df.copy()
    df["abs_corr"] = df["correlation_strength"].abs().fillna(0)
    df["mi_filled"] = df["mutual_info"].fillna(0)
    df["es_filled"] = df["effect_size"].fillna(df["abs_corr"])
    # Significance: invert p-value (lower p = higher significance)
    df["sig"] = (1 - df["p_value"].fillna(1.0)).clip(0, 1)

    df["norm_corr"] = _normalize_series(df["abs_corr"])
    df["norm_mi"] = _normalize_series(df["mi_filled"])
    df["norm_es"] = _normalize_series(df["es_filled"])
    df["norm_sig"] = _normalize_series(df["sig"])

    df["score"] = (
        0.35 * df["norm_corr"] +
        0.25 * df["norm_mi"] +
        0.25 * df["norm_sig"] +
        0.15 * df["norm_es"]
    ).round(6)

    # Exclude trivially derived features from ranking
    exclude = {"trending_duration_bucket", "trendpulse_score"}
    df = df[~df["factor"].isin(exclude)]

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank_position"] = range(1, len(df) + 1)
    df["factor_label"] = df["factor"].map(lambda f: FACTOR_LABELS.get(f, f.replace("_", " ").title()))
    df["interpretation"] = df["factor"].map(
        lambda f: INTERPRETATIONS.get(f, f"This feature shows a statistical association with trending duration."))

    result = df[["rank_position", "factor", "factor_label", "score",
                 "association_type", "pearson_r", "spearman_r", "anova_f",
                 "effect_size", "mutual_info", "p_value", "interpretation"]].head(top_n)
    logger.info(f"Top {min(5, len(result))} factors: " +
                ", ".join(result.head(5)["factor_label"].tolist()))
    return result.reset_index(drop=True)


def get_top_5(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience: compute correlations and return top 5 ranked factors."""
    from analytics.correlation_engine import compute_correlations
    corr = compute_correlations(df)
    return rank_factors(corr).head(5)
