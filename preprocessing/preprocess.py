"""
TrendPulse - Data Preprocessing Pipeline
Handles YouTube Trending Video Statistics dataset preprocessing.
Supports multiple CSV schemas gracefully.
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "preprocess.log", mode="a"),
    ],
)
logger = logging.getLogger("trendpulse.preprocess")

UPLOAD_TIME_BUCKETS = [
    (0, 5, "Early Morning"),
    (5, 9, "Morning"),
    (9, 12, "Late Morning"),
    (12, 17, "Afternoon"),
    (17, 20, "Evening"),
    (20, 24, "Night"),
]

TITLE_LENGTH_BUCKETS = [
    (0, 20, "0-20"),
    (21, 40, "21-40"),
    (41, 60, "41-60"),
    (61, 80, "61-80"),
    (81, 100, "81-100"),
    (101, 9999, "100+"),
]

COLUMN_ALIASES: Dict[str, List[str]] = {
    "video_id": ["video_id", "videoid", "id"],
    "title": ["title", "video_title", "name"],
    "channel_title": ["channel_title", "channeltitle", "channel_name", "channel"],
    "category_id": ["category_id", "categoryid", "category"],
    "publish_time": ["publish_time", "publishedat", "published_at", "publish_date"],
    "tags": ["tags", "video_tags", "tag_list"],
    "views": ["views", "view_count", "viewcount"],
    "likes": ["likes", "like_count", "likecount"],
    "dislikes": ["dislikes", "dislike_count", "dislikecount"],
    "comment_count": ["comment_count", "commentcount", "comments"],
    "trending_date": ["trending_date", "trendingdate", "trending_on"],
    "description": ["description", "video_description", "desc"],
    "comments_disabled": ["comments_disabled", "commentsdisabled"],
    "ratings_disabled": ["ratings_disabled", "ratingsdisabled"],
    "video_error_or_removed": ["video_error_or_removed", "videoerrororremoved", "removed"],
    "thumbnail_link": ["thumbnail_link", "thumbnaillink", "thumbnail"],
}


class YouTubePreprocessor:
    """Main preprocessing class for YouTube trending video data."""

    def __init__(self, dataset_path: str, category_json_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path)
        self.category_json_path = Path(category_json_path) if category_json_path else None
        self.category_map: Dict[int, str] = {}
        self.stats: Dict[str, Any] = {}
        self._validate_paths()
        self._load_category_map()

    def _validate_paths(self):
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        logger.info(f"Dataset found: {self.dataset_path} ({self.dataset_path.stat().st_size / 1024:.1f} KB)")

    def _load_category_map(self):
        if self.category_json_path and self.category_json_path.exists():
            try:
                with open(self.category_json_path, "r") as f:
                    data = json.load(f)
                for item in data.get("items", []):
                    cat_id = int(item["id"])
                    cat_name = item["snippet"]["title"]
                    self.category_map[cat_id] = cat_name
                logger.info(f"Loaded {len(self.category_map)} categories from JSON")
            except Exception as e:
                logger.warning(f"Could not load category JSON: {e}")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        col_map = {}
        df_cols_lower = {c.lower().strip(): c for c in df.columns}
        for standard, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias.lower() in df_cols_lower:
                    original = df_cols_lower[alias.lower()]
                    if original != standard:
                        col_map[original] = standard
                    break
        if col_map:
            logger.info(f"Column remapping: {col_map}")
            df = df.rename(columns=col_map)
        return df

    def load_dataset(self, encoding: str = "utf-8") -> pd.DataFrame:
        for enc in [encoding, "latin-1", "cp1252", "iso-8859-1"]:
            try:
                df = pd.read_csv(self.dataset_path, encoding=enc, low_memory=False)
                logger.info(f"Loaded {len(df)} rows with encoding '{enc}'")
                df = self._normalize_columns(df)
                self.stats["raw_rows"] = len(df)
                self.stats["raw_columns"] = list(df.columns)
                return df
            except UnicodeDecodeError:
                logger.warning(f"Encoding {enc} failed, trying next...")
        raise ValueError("Could not load dataset with any supported encoding.")

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_len = len(df)
        if "video_id" in df.columns:
            df = df.dropna(subset=["video_id"])
            df = df[df["video_id"].astype(str).str.strip() != ""]
        text_defaults = {"title": "Unknown Title", "channel_title": "Unknown Channel",
                         "description": "", "tags": "[none]", "thumbnail_link": ""}
        for col, default in text_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default).astype(str)
        for col in ["views", "likes", "dislikes", "comment_count"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)
        if "category_id" in df.columns:
            df["category_id"] = pd.to_numeric(df["category_id"], errors="coerce").fillna(0).astype(int)
        for col in ["comments_disabled", "ratings_disabled", "video_error_or_removed"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().isin(["true", "1", "yes"]).astype(int)
        dropped = initial_len - len(df)
        if dropped > 0:
            logger.info(f"Dropped {dropped} rows with missing video_id")
        return df

    def engineer_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "title" in df.columns:
            titles = df["title"].astype(str)
            df["title_length"] = titles.str.len()
            df["title_word_count"] = titles.str.split().str.len()
            df["uppercase_ratio"] = titles.apply(
                lambda t: sum(1 for c in t if c.isupper()) / max(len(t), 1))
            df["punctuation_count"] = titles.apply(
                lambda t: sum(1 for c in t if c in "!?,.:;-'\"()"))
            df["question_mark_count"] = titles.str.count(r"\?")
            df["exclamation_count"] = titles.str.count("!")
            df["title_length_bucket"] = df["title_length"].apply(self._title_length_bucket)
        if "description" in df.columns:
            df["description_length"] = df["description"].astype(str).str.len()
            df["description_word_count"] = df["description"].astype(str).str.split().str.len()
        if "tags" in df.columns:
            df["tag_count"] = df["tags"].astype(str).apply(
                lambda t: 0 if t.strip().lower() in ("[none]", "none", "")
                else len([x.strip() for x in t.split("|") if x.strip()]))
        return df

    def _title_length_bucket(self, length: int) -> str:
        for low, high, label in TITLE_LENGTH_BUCKETS:
            if low <= length <= high:
                return label
        return "100+"

    def engineer_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "publish_time" not in df.columns:
            logger.warning("publish_time not found - skipping time features")
            return df
        try:
            df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce", utc=True)
            df["publish_date"] = df["publish_time"].dt.date.astype(str)
            df["publish_year"] = df["publish_time"].dt.year.fillna(0).astype(int)
            df["publish_month"] = df["publish_time"].dt.month.fillna(0).astype(int)
            df["publish_day"] = df["publish_time"].dt.day.fillna(0).astype(int)
            df["publish_hour"] = df["publish_time"].dt.hour.fillna(0).astype(int)
            df["publish_weekday"] = df["publish_time"].dt.weekday.fillna(0).astype(int)
            df["publish_weekday_name"] = df["publish_time"].dt.day_name().fillna("Unknown")
            df["is_weekend"] = df["publish_weekday"].isin([5, 6]).astype(int)
            df["upload_time_bucket"] = df["publish_hour"].apply(self._hour_to_bucket)
            df["publish_time"] = df["publish_time"].astype(str)
        except Exception as e:
            logger.error(f"Time feature engineering failed: {e}")
        return df

    def _hour_to_bucket(self, hour: int) -> str:
        for start, end, label in UPLOAD_TIME_BUCKETS:
            if start <= hour < end:
                return label
        return "Night"

    def engineer_engagement_features(self, df: pd.DataFrame) -> pd.DataFrame:
        views = df.get("views", pd.Series(0, index=df.index)).fillna(0).clip(lower=1)
        likes = df.get("likes", pd.Series(0, index=df.index)).fillna(0).clip(lower=0)
        comments = df.get("comment_count", pd.Series(0, index=df.index)).fillna(0).clip(lower=0)
        dislikes = df.get("dislikes", pd.Series(0, index=df.index)).fillna(0).clip(lower=0)
        df["views"] = views
        df["likes"] = likes
        df["comment_count"] = comments
        df["like_rate"] = (likes / views).round(6)
        df["comment_rate"] = (comments / views).round(6)
        df["engagement_rate"] = ((likes + comments) / views).round(6)
        if "dislikes" in df.columns and dislikes.sum() > 0:
            df["dislikes"] = dislikes
            df["dislike_rate"] = (dislikes / views).round(6)
            df["engagement_score"] = ((likes + comments + dislikes) / views).round(6)
        else:
            df["engagement_score"] = df["engagement_rate"]
        return df

    def calculate_trending_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        if "trending_date" not in df.columns or "video_id" not in df.columns:
            logger.warning("Cannot calculate trending duration: missing columns")
            df["trending_duration_days"] = 1
            return df
        try:
            parsed = pd.to_datetime(df["trending_date"], errors="coerce", format="%y.%d.%m")
            mask = parsed.isna()
            if mask.sum() > 0:
                parsed[mask] = pd.to_datetime(df.loc[mask, "trending_date"], errors="coerce")
            df["_td_parsed"] = parsed
            grp = df.groupby("video_id")["_td_parsed"]
            df["first_trending_date"] = df["video_id"].map(grp.min()).astype(str)
            df["last_trending_date"] = df["video_id"].map(grp.max()).astype(str)
            df["trending_duration_days"] = df["video_id"].map(grp.nunique()).fillna(1).astype(int)
            df.drop(columns=["_td_parsed"], inplace=True, errors="ignore")
            logger.info(f"Trending duration: min={df['trending_duration_days'].min()}, "
                        f"max={df['trending_duration_days'].max()}, "
                        f"mean={df['trending_duration_days'].mean():.2f}")
        except Exception as e:
            logger.error(f"Trending duration error: {e}")
            df["trending_duration_days"] = 1
            df["first_trending_date"] = df.get("trending_date", "")
            df["last_trending_date"] = df.get("trending_date", "")
        return df

    def add_category_names(self, df: pd.DataFrame) -> pd.DataFrame:
        if "category_id" in df.columns and self.category_map:
            df["category_name"] = df["category_id"].map(
                lambda c: self.category_map.get(int(c), f"Category_{c}"))
        elif "category_id" in df.columns:
            df["category_name"] = "Category_" + df["category_id"].astype(str)
        return df

    def add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        df["processed_at"] = datetime.utcnow().isoformat()
        td_col = df.get("trending_date", pd.Series("", index=df.index))
        df["record_id"] = (df["video_id"].astype(str) + "_" + td_col.astype(str)).apply(
            lambda x: hashlib.md5(x.encode()).hexdigest()[:12])
        return df

    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        if "trending_date" in df.columns and "video_id" in df.columns:
            initial = len(df)
            df = df.sort_values("trending_date", ascending=False)
            agg_cols = ["trending_duration_days", "first_trending_date", "last_trending_date"]
            has_agg = all(c in df.columns for c in agg_cols)
            if has_agg:
                agg_data = df.groupby("video_id")[agg_cols].first().reset_index()
            df = df.drop_duplicates(subset="video_id", keep="first")
            if has_agg:
                df = df.drop(columns=[c for c in agg_cols if c in df.columns])
                df = df.merge(agg_data, on="video_id", how="left")
            logger.info(f"Deduplication: {initial} -> {len(df)} unique videos")
        return df

    def run(self, output_path: Optional[str] = None) -> pd.DataFrame:
        logger.info("=" * 60)
        logger.info("TrendPulse Preprocessing Pipeline START")
        logger.info("=" * 60)
        df = self.load_dataset()
        df = self.handle_missing_values(df)
        df = self.engineer_text_features(df)
        df = self.engineer_time_features(df)
        df = self.engineer_engagement_features(df)
        df = self.calculate_trending_duration(df)
        df = self.add_category_names(df)
        df = self.add_metadata(df)
        df = self.deduplicate(df)
        df = df.replace([np.inf, -np.inf], np.nan)
        self.stats["final_rows"] = len(df)
        self.stats["final_columns"] = list(df.columns)
        logger.info(f"Pipeline complete: {self.stats['raw_rows']} raw -> {len(df)} processed rows")
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"Saved to: {output_path}")
        return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TrendPulse Data Preprocessor")
    parser.add_argument("--input", default=os.getenv("DATASET_PATH", "data/raw/USvideos.csv"))
    parser.add_argument("--categories", default=os.getenv("CATEGORY_JSON_PATH", "data/raw/US_category_id.json"))
    parser.add_argument("--output", default="data/processed/cleaned_videos.csv")
    args = parser.parse_args()
    Path("logs").mkdir(exist_ok=True)
    preprocessor = YouTubePreprocessor(args.input, args.categories)
    df = preprocessor.run(output_path=args.output)
    print(f"\nPreprocessing complete. {len(df)} videos ready.")
    print(df[["video_id", "title", "views", "engagement_rate", "trending_duration_days"]].head())
