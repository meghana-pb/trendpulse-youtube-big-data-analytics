"""
TrendPulse - Database Loader
Loads processed analytics data into PostgreSQL tables.
"""
import logging
import math
from datetime import datetime
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger("trendpulse.loader")
CHUNK_SIZE = 500


def _safe_float(v) -> Optional[float]:
    if v is None: return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError): return None


def _safe_int(v) -> Optional[int]:
    f = _safe_float(v)
    return int(f) if f is not None else None


def load_videos(df: pd.DataFrame, engine) -> int:
    """Bulk upsert videos into the videos table."""
    logger.info(f"Loading {len(df)} videos into database...")
    cols = [
        "video_id","title","channel_title","category_id","category_name",
        "publish_hour","publish_weekday","publish_weekday_name","is_weekend",
        "upload_time_bucket","tags","tag_count","views","likes","dislikes",
        "comment_count","engagement_rate","engagement_score","like_rate",
        "comment_rate","title_length","title_word_count","title_length_bucket",
        "description_length","uppercase_ratio","punctuation_count",
        "exclamation_count","question_mark_count","trending_duration_days",
        "first_trending_date","last_trending_date","trending_duration_bucket",
        "view_velocity","trendpulse_score","trendpulse_label",
        "comments_disabled","ratings_disabled","video_error_or_removed","processed_at",
    ]
    available = [c for c in cols if c in df.columns]
    count = 0
    for i in range(0, len(df), CHUNK_SIZE):
        chunk = df.iloc[i:i+CHUNK_SIZE][available].copy()
        chunk = chunk.where(pd.notnull(chunk), None)
        records = chunk.to_dict("records")
        with engine.begin() as conn:
            for rec in records:
                rec["video_id"] = str(rec.get("video_id", ""))[:20]
                if not rec["video_id"]:
                    continue
                for bcol in ("is_weekend", "comments_disabled", "ratings_disabled", "video_error_or_removed"):
                    if bcol in rec and rec[bcol] is not None:
                        rec[bcol] = bool(rec[bcol])
                placeholders = ", ".join(f":{k}" for k in rec.keys())
                cols_str = ", ".join(rec.keys())
                update_str = ", ".join(f"{k}=EXCLUDED.{k}" for k in rec.keys() if k != "video_id")
                sql = text(f"""
                    INSERT INTO videos ({cols_str}) VALUES ({placeholders})
                    ON CONFLICT (video_id) DO UPDATE SET {update_str}
                """)
                conn.execute(sql, rec)
                count += 1
    logger.info(f"Loaded {count} videos.")
    return count


def load_category_analytics(df: pd.DataFrame, engine) -> None:
    logger.info("Computing and loading category analytics...")
    if "category_id" not in df.columns:
        return
    grp = df.groupby(["category_id","category_name"]).agg(
        total_videos=("video_id","count"),
        avg_views=("views","mean"), avg_likes=("likes","mean"),
        avg_comments=("comment_count","mean"),
        avg_engagement_rate=("engagement_rate","mean"),
        avg_trending_duration=("trending_duration_days","mean"),
        max_trending_duration=("trending_duration_days","max"),
        min_trending_duration=("trending_duration_days","min"),
    ).reset_index()
    with engine.begin() as conn:
        for _, row in grp.iterrows():
            conn.execute(text("""
                INSERT INTO category_analytics
                    (category_id,category_name,total_videos,avg_views,avg_likes,avg_comments,
                     avg_engagement_rate,avg_trending_duration,max_trending_duration,min_trending_duration,computed_at)
                VALUES (:cid,:cname,:tv,:av,:al,:ac,:ae,:atd,:max_td,:min_td,:ts)
                ON CONFLICT (category_id) DO UPDATE SET
                    category_name=EXCLUDED.category_name, total_videos=EXCLUDED.total_videos,
                    avg_views=EXCLUDED.avg_views, avg_engagement_rate=EXCLUDED.avg_engagement_rate,
                    avg_trending_duration=EXCLUDED.avg_trending_duration,
                    max_trending_duration=EXCLUDED.max_trending_duration,
                    min_trending_duration=EXCLUDED.min_trending_duration, computed_at=EXCLUDED.computed_at
            """), {"cid":int(row.category_id),"cname":str(row.category_name),
                   "tv":int(row.total_videos),"av":_safe_float(row.avg_views),
                   "al":_safe_float(row.avg_likes),"ac":_safe_float(row.avg_comments),
                   "ae":_safe_float(row.avg_engagement_rate),
                   "atd":_safe_float(row.avg_trending_duration),
                   "max_td":_safe_int(row.max_trending_duration),
                   "min_td":_safe_int(row.min_trending_duration),
                   "ts":datetime.utcnow()})
    logger.info("Category analytics loaded.")


def load_upload_time_analytics(df: pd.DataFrame, engine) -> None:
    if "publish_hour" not in df.columns: return
    grp = df.groupby(["publish_hour","upload_time_bucket"]).agg(
        total_videos=("video_id","count"),
        avg_trending_duration=("trending_duration_days","mean"),
        avg_views=("views","mean"),
        avg_engagement_rate=("engagement_rate","mean"),
        max_trending_duration=("trending_duration_days","max"),
    ).reset_index()
    with engine.begin() as conn:
        for _, row in grp.iterrows():
            conn.execute(text("""
                INSERT INTO upload_time_analytics
                    (publish_hour,upload_time_bucket,total_videos,avg_trending_duration,avg_views,avg_engagement_rate,max_trending_duration,computed_at)
                VALUES (:ph,:utb,:tv,:atd,:av,:ae,:mtd,:ts)
                ON CONFLICT (publish_hour) DO UPDATE SET
                    upload_time_bucket=EXCLUDED.upload_time_bucket,
                    total_videos=EXCLUDED.total_videos,
                    avg_trending_duration=EXCLUDED.avg_trending_duration,
                    avg_views=EXCLUDED.avg_views, avg_engagement_rate=EXCLUDED.avg_engagement_rate,
                    computed_at=EXCLUDED.computed_at
            """), {"ph":int(row.publish_hour),"utb":str(row.get("upload_time_bucket","")),"tv":int(row.total_videos),
                   "atd":_safe_float(row.avg_trending_duration),"av":_safe_float(row.avg_views),
                   "ae":_safe_float(row.avg_engagement_rate),"mtd":_safe_int(row.max_trending_duration),
                   "ts":datetime.utcnow()})
    logger.info("Upload time analytics loaded.")


def load_title_analytics(df: pd.DataFrame, engine) -> None:
    if "title_length_bucket" not in df.columns: return
    grp = df.groupby("title_length_bucket").agg(
        total_videos=("video_id","count"),
        avg_views=("views","mean"),
        avg_engagement_rate=("engagement_rate","mean"),
        avg_trending_duration=("trending_duration_days","mean"),
    ).reset_index()
    with engine.begin() as conn:
        for _, row in grp.iterrows():
            conn.execute(text("""
                INSERT INTO title_length_analytics (bucket,total_videos,avg_views,avg_engagement_rate,avg_trending_duration,computed_at)
                VALUES (:b,:tv,:av,:ae,:atd,:ts)
                ON CONFLICT (bucket) DO UPDATE SET total_videos=EXCLUDED.total_videos,
                    avg_views=EXCLUDED.avg_views, avg_engagement_rate=EXCLUDED.avg_engagement_rate,
                    avg_trending_duration=EXCLUDED.avg_trending_duration, computed_at=EXCLUDED.computed_at
            """), {"b":str(row.title_length_bucket),"tv":int(row.total_videos),
                   "av":_safe_float(row.avg_views),"ae":_safe_float(row.avg_engagement_rate),
                   "atd":_safe_float(row.avg_trending_duration),"ts":datetime.utcnow()})
    logger.info("Title analytics loaded.")


def load_trending_factors(factors_df: pd.DataFrame, engine) -> None:
    if factors_df.empty: return
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM trending_factors"))
        for _, row in factors_df.iterrows():
            conn.execute(text("""
                INSERT INTO trending_factors
                    (rank_position,factor,score,pearson_r,spearman_r,anova_f,effect_size,mutual_info,p_value,association_type,interpretation,computed_at)
                VALUES (:rp,:f,:s,:pr,:sr,:af,:es,:mi,:pv,:at,:interp,:ts)
                ON CONFLICT (factor) DO UPDATE SET rank_position=EXCLUDED.rank_position, score=EXCLUDED.score,
                    interpretation=EXCLUDED.interpretation, computed_at=EXCLUDED.computed_at
            """), {
                "rp":int(row.rank_position),"f":str(row.factor),
                "s":_safe_float(row.get("score",0)),
                "pr":_safe_float(row.get("pearson_r")),"sr":_safe_float(row.get("spearman_r")),
                "af":_safe_float(row.get("anova_f")),"es":_safe_float(row.get("effect_size")),
                "mi":_safe_float(row.get("mutual_info")),"pv":_safe_float(row.get("p_value")),
                "at":str(row.get("association_type","")),"interp":str(row.get("interpretation","")),
                "ts":datetime.utcnow()})
    logger.info(f"Loaded {len(factors_df)} trending factors.")


def load_breakout_videos(anomalies_df: pd.DataFrame, engine) -> None:
    if anomalies_df.empty: return
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM breakout_videos"))
        for _, row in anomalies_df.iterrows():
            reasons = row.get("anomaly_reasons", [])
            if isinstance(reasons, list):
                reasons_arr = "{" + ",".join(f'"{r}"' for r in reasons) + "}"
            else:
                reasons_arr = "{}"
            conn.execute(text("""
                INSERT INTO breakout_videos (video_id,title,category_name,views,engagement_rate,trending_duration_days,trendpulse_score,anomaly_score,anomaly_reasons,detected_at)
                VALUES (:vid,:t,:cn,:v,:er,:tdd,:ts,:as,:ar,:dt)
            """), {"vid":str(row.video_id),"t":str(row.get("title","")),"cn":str(row.get("category_name","")),
                   "v":_safe_int(row.get("views",0)),"er":_safe_float(row.get("engagement_rate")),
                   "tdd":_safe_int(row.get("trending_duration_days",1)),"ts":_safe_float(row.get("trendpulse_score")),
                   "as":_safe_float(row.get("anomaly_score")),"ar":reasons_arr,"dt":datetime.utcnow()})
    logger.info(f"Loaded {len(anomalies_df)} breakout videos.")


def load_pipeline_metrics(metrics: dict, engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_metrics
                (kafka_messages_produced,kafka_messages_consumed,kafka_messages_failed,
                 hdfs_records_written,mapreduce_jobs_run,analytics_records,pipeline_stage,status,notes,recorded_at)
            VALUES (:kp,:kc,:kf,:hr,:mr,:ar,:ps,:st,:n,:ts)
        """), {"kp":metrics.get("kafka_produced",0),"kc":metrics.get("kafka_consumed",0),
               "kf":metrics.get("kafka_failed",0),"hr":metrics.get("hdfs_written",0),
               "mr":metrics.get("mapreduce_jobs",0),"ar":metrics.get("analytics_records",0),
               "ps":metrics.get("stage","demo"),"st":metrics.get("status","done"),
               "n":metrics.get("notes",""),"ts":datetime.utcnow()})
    logger.info("Pipeline metrics recorded.")


def load_data_quality(quality_report, engine) -> None:
    data = quality_report.to_dict() if hasattr(quality_report, "to_dict") else quality_report
    with engine.begin() as conn:
        for check in data.get("checks", []):
            conn.execute(text("""
                INSERT INTO data_quality_metrics
                    (total_records,failed_records,quality_score,check_name,passed_count,failed_count,pass_rate,details,recorded_at)
                VALUES (:tr,:fr,:qs,:cn,:pc,:fc,:pr,:d,:ts)
            """), {"tr":_safe_int(data.get("total_records",0)),"fr":_safe_int(data.get("failed_records",0)),
                   "qs":_safe_float(data.get("quality_score",100)),"cn":str(check.get("check","")),
                   "pc":_safe_int(check.get("passed",0)),"fc":_safe_int(check.get("failed",0)),
                   "pr":_safe_float(check.get("pass_rate",100)),"d":str(check.get("details","")),
                   "ts":datetime.utcnow()})
    logger.info("Data quality metrics loaded.")


def load_trend_scores(df: pd.DataFrame, engine) -> None:
    if "trendpulse_score" not in df.columns: return
    with engine.begin() as conn:
        for i in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[i:i+CHUNK_SIZE]
            for _, row in chunk.iterrows():
                conn.execute(text("""
                    INSERT INTO trend_scores (video_id,score,label,computed_at)
                    VALUES (:vid,:s,:l,:ts)
                    ON CONFLICT (video_id) DO UPDATE SET score=EXCLUDED.score, label=EXCLUDED.label, computed_at=EXCLUDED.computed_at
                """), {"vid":str(row.video_id),"s":_safe_float(row.trendpulse_score) or 0,
                       "l":str(row.get("trendpulse_label","Low")),"ts":datetime.utcnow()})
    logger.info(f"Trend scores loaded for {len(df)} videos.")
