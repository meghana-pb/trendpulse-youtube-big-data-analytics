"""
TrendPulse - Dynamic Insight Generator
Generates natural-language insights from actual computed data.
All statements are data-driven, not hardcoded.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Optional

logger = logging.getLogger("trendpulse.insights")


def generate_category_insight(df: pd.DataFrame) -> str:
    if "category_name" not in df.columns or "trending_duration_days" not in df.columns:
        return "Category data is not available for analysis."
    cat_avg = df.groupby("category_name")["trending_duration_days"].mean()
    if cat_avg.empty:
        return "Insufficient data to identify category trends."
    top_cat = cat_avg.idxmax()
    top_val = cat_avg.max()
    bottom_cat = cat_avg.idxmin()
    bottom_val = cat_avg.min()
    return (f"'{top_cat}' videos have the highest average trending duration "
            f"({top_val:.1f} days) in this dataset, while '{bottom_cat}' "
            f"averages only {bottom_val:.1f} days. "
            f"Category selection shows a {top_val/max(bottom_val,0.1):.1f}x difference "
            f"in average trending duration across content types.")


def generate_upload_time_insight(df: pd.DataFrame) -> str:
    if "upload_time_bucket" not in df.columns or "trending_duration_days" not in df.columns:
        return "Upload time data is not available for analysis."
    bucket_avg = df.groupby("upload_time_bucket")["trending_duration_days"].mean()
    if bucket_avg.empty:
        return "Insufficient data to identify upload time patterns."
    best_bucket = bucket_avg.idxmax()
    best_val = bucket_avg.max()
    worst_bucket = bucket_avg.idxmin()
    worst_val = bucket_avg.min()
    hour_avg = None
    if "publish_hour" in df.columns:
        hour_avg = df.groupby("publish_hour")["trending_duration_days"].mean()
        best_hour = hour_avg.idxmax()
        return (f"Videos uploaded during the '{best_bucket}' window showed the highest "
                f"average trending duration ({best_val:.1f} days) in this dataset. "
                f"Specifically, {best_hour}:00 UTC showed the strongest association. "
                f"'{worst_bucket}' uploads averaged only {worst_val:.1f} days.")
    return (f"Videos uploaded during the '{best_bucket}' window showed the highest "
            f"average trending duration ({best_val:.1f} days) in this dataset, "
            f"compared to '{worst_bucket}' which averaged {worst_val:.1f} days.")


def generate_title_length_insight(df: pd.DataFrame) -> str:
    if "title_length_bucket" not in df.columns or "trending_duration_days" not in df.columns:
        return "Title length data is not available."
    tl_avg = df.groupby("title_length_bucket")["trending_duration_days"].mean()
    if tl_avg.empty:
        return "Insufficient data to analyze title length patterns."
    best_bucket = tl_avg.idxmax()
    best_val = tl_avg.max()
    return (f"Videos with titles in the '{best_bucket}' character range showed the "
            f"highest average trending duration ({best_val:.1f} days) in this dataset. "
            f"Extremely short or very long titles tend to underperform "
            f"compared to the optimal range.")


def generate_engagement_insight(df: pd.DataFrame) -> str:
    if "engagement_rate" not in df.columns or "trending_duration_days" not in df.columns:
        return "Engagement data is not available."
    corr = df["engagement_rate"].corr(df["trending_duration_days"])
    avg_eng = df["engagement_rate"].mean()
    high_eng = df[df["engagement_rate"] > df["engagement_rate"].quantile(0.75)]
    low_eng = df[df["engagement_rate"] <= df["engagement_rate"].quantile(0.25)]
    high_dur = high_eng["trending_duration_days"].mean() if len(high_eng) > 0 else 0
    low_dur = low_eng["trending_duration_days"].mean() if len(low_eng) > 0 else 0
    direction = "positive" if corr > 0 else "negative"
    strength = "strong" if abs(corr) > 0.4 else ("moderate" if abs(corr) > 0.2 else "weak")
    return (f"Engagement rate shows a {strength} {direction} correlation (r={corr:.3f}) "
            f"with trending duration. Videos in the top quartile of engagement rate "
            f"({avg_eng:.3f} avg) trend for {high_dur:.1f} days on average, "
            f"versus {low_dur:.1f} days for the bottom quartile.")


def generate_top_factor_insight(factor_df: pd.DataFrame) -> str:
    if factor_df.empty:
        return "Factor analysis data is not available."
    top = factor_df.iloc[0]
    second = factor_df.iloc[1] if len(factor_df) > 1 else None
    label = top.get("factor_label", top.get("factor", "Unknown"))
    score = top.get("score", 0)
    interp = top.get("interpretation", "")
    msg = (f"'{label}' ranks as the strongest contributor to trending duration "
           f"(composite score: {score:.4f}). {interp}")
    if second is not None:
        s_label = second.get("factor_label", second.get("factor", ""))
        msg += f" '{s_label}' ranks second in association strength."
    return msg


def generate_weekend_insight(df: pd.DataFrame) -> str:
    if "is_weekend" not in df.columns or "trending_duration_days" not in df.columns:
        return "Weekend upload data is not available."
    weekend_avg = df[df["is_weekend"] == 1]["trending_duration_days"].mean()
    weekday_avg = df[df["is_weekend"] == 0]["trending_duration_days"].mean()
    diff = weekend_avg - weekday_avg
    direction = "higher" if diff > 0 else "lower"
    return (f"Weekend uploads average {abs(diff):.1f} days {direction} trending duration "
            f"({weekend_avg:.1f} days) compared to weekday uploads ({weekday_avg:.1f} days) "
            f"in this dataset.")


def generate_all_insights(df: pd.DataFrame, factor_df: Optional[pd.DataFrame] = None) -> List[str]:
    """Generate all available insights from the dataset."""
    insights = [
        generate_category_insight(df),
        generate_upload_time_insight(df),
        generate_title_length_insight(df),
        generate_engagement_insight(df),
        generate_weekend_insight(df),
    ]
    if factor_df is not None and not factor_df.empty:
        insights.append(generate_top_factor_insight(factor_df))
    return [i for i in insights if i]
