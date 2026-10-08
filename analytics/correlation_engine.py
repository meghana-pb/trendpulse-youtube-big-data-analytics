"""
TrendPulse - Correlation Engine
Computes statistical associations between features and trending_duration_days.
"""
import logging
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_selection import mutual_info_regression
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("trendpulse.correlation")

NUMERIC_FEATURES = [
    "views", "likes", "comment_count", "engagement_rate", "like_rate",
    "comment_rate", "title_length", "description_length", "tag_count",
    "publish_hour", "is_weekend", "uppercase_ratio", "punctuation_count",
    "view_velocity", "trendpulse_score",
]

CATEGORICAL_FEATURES = [
    "category_id", "upload_time_bucket", "publish_weekday_name",
    "title_length_bucket", "trending_duration_bucket",
]

TARGET = "trending_duration_days"


def _pearson(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    mask = x.notna() & y.notna()
    if mask.sum() < 5:
        return np.nan, np.nan
    r, p = stats.pearsonr(x[mask], y[mask])
    return round(float(r), 6), round(float(p), 10)


def _spearman(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    mask = x.notna() & y.notna()
    if mask.sum() < 5:
        return np.nan, np.nan
    r, p = stats.spearmanr(x[mask], y[mask])
    return round(float(r), 6), round(float(p), 10)


def _anova_f(groups: pd.Series, target: pd.Series) -> Tuple[float, float, float]:
    """ANOVA F-test for categorical feature. Returns (F, p_value, eta_squared)."""
    df = pd.DataFrame({"group": groups, "target": target}).dropna()
    if df["group"].nunique() < 2 or len(df) < 10:
        return np.nan, np.nan, np.nan
    group_vals = [grp["target"].values for _, grp in df.groupby("group") if len(grp) >= 2]
    if len(group_vals) < 2:
        return np.nan, np.nan, np.nan
    f, p = stats.f_oneway(*group_vals)
    # Eta-squared effect size
    grand_mean = df["target"].mean()
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in group_vals)
    ss_total = sum((df["target"] - grand_mean) ** 2)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    return round(float(f), 4), round(float(p), 10), round(float(eta_sq), 6)


def _mutual_info(x: pd.Series, y: pd.Series) -> float:
    mask = x.notna() & y.notna()
    if mask.sum() < 5:
        return np.nan
    try:
        mi = mutual_info_regression(
            x[mask].values.reshape(-1, 1), y[mask].values, random_state=42)[0]
        return round(float(mi), 6)
    except Exception:
        return np.nan


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all statistical associations with trending_duration_days."""
    if TARGET not in df.columns:
        logger.error(f"Target column '{TARGET}' not found in DataFrame")
        return pd.DataFrame()
    target = df[TARGET].astype(float)
    rows = []

    # Numeric features: Pearson + Spearman + MI
    for feat in NUMERIC_FEATURES:
        if feat not in df.columns or feat == TARGET:
            continue
        x = pd.to_numeric(df[feat], errors="coerce")
        pearson_r, pearson_p = _pearson(x, target)
        spearman_r, spearman_p = _spearman(x, target)
        mi = _mutual_info(x, target)
        rows.append({
            "factor": feat,
            "association_type": "numeric",
            "pearson_r": pearson_r,
            "spearman_r": spearman_r,
            "anova_f": np.nan,
            "effect_size": np.nan,
            "mutual_info": mi,
            "p_value": min(filter(lambda v: not np.isnan(v), [pearson_p, spearman_p, 1.0])),
            "correlation_strength": max(abs(pearson_r or 0), abs(spearman_r or 0)),
        })

    # Categorical features: ANOVA + eta-squared + MI
    for feat in CATEGORICAL_FEATURES:
        if feat not in df.columns or feat == TARGET:
            continue
        x = df[feat].astype(str)
        # Encode for MI
        encoded = pd.Categorical(x).codes
        x_enc = pd.Series(encoded, index=df.index)
        f_stat, p_val, eta_sq = _anova_f(x, target)
        mi = _mutual_info(x_enc, target)
        rows.append({
            "factor": feat,
            "association_type": "categorical",
            "pearson_r": np.nan,
            "spearman_r": np.nan,
            "anova_f": f_stat,
            "effect_size": eta_sq,
            "mutual_info": mi,
            "p_value": p_val if not np.isnan(p_val) else 1.0,
            "correlation_strength": abs(eta_sq) if not np.isnan(eta_sq) else 0.0,
        })

    result = pd.DataFrame(rows)
    result["abs_correlation"] = result["correlation_strength"].abs()
    result = result.sort_values("abs_correlation", ascending=False).reset_index(drop=True)
    logger.info(f"Correlation analysis complete: {len(result)} features evaluated")
    return result


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    df = pd.read_csv("data/processed/cleaned_videos.csv", low_memory=False)
    result = compute_correlations(df)
    print(result[["factor","association_type","pearson_r","spearman_r","anova_f","effect_size","mutual_info","p_value"]].to_string())
