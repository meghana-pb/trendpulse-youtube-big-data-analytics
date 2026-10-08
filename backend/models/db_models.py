"""
TrendPulse - SQLAlchemy ORM Models
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (Column, Integer, BigInteger, String, Text, Float,
                        Boolean, DateTime, SmallInteger, ARRAY, Numeric, Date)
from backend.database.connection import Base


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True)
    video_id = Column(String(20), unique=True, nullable=False)
    title = Column(Text)
    channel_title = Column(String(255))
    category_id = Column(Integer)
    category_name = Column(String(100))
    publish_time = Column(DateTime(timezone=True))
    publish_hour = Column(SmallInteger)
    publish_weekday = Column(SmallInteger)
    publish_weekday_name = Column(String(20))
    is_weekend = Column(Boolean, default=False)
    upload_time_bucket = Column(String(30))
    tags = Column(Text)
    tag_count = Column(Integer, default=0)
    views = Column(BigInteger, default=0)
    likes = Column(BigInteger, default=0)
    dislikes = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    engagement_rate = Column(Numeric(10, 6), default=0)
    engagement_score = Column(Numeric(10, 6), default=0)
    like_rate = Column(Numeric(10, 6), default=0)
    comment_rate = Column(Numeric(10, 6), default=0)
    title_length = Column(Integer, default=0)
    title_word_count = Column(Integer, default=0)
    title_length_bucket = Column(String(20))
    description_length = Column(Integer, default=0)
    uppercase_ratio = Column(Numeric(6, 4), default=0)
    punctuation_count = Column(Integer, default=0)
    exclamation_count = Column(Integer, default=0)
    question_mark_count = Column(Integer, default=0)
    trending_duration_days = Column(Integer, default=1)
    first_trending_date = Column(String(50))
    last_trending_date = Column(String(50))
    trending_duration_bucket = Column(String(20))
    view_velocity = Column(Numeric(15, 2), default=0)
    trendpulse_score = Column(Numeric(5, 2), default=0)
    trendpulse_label = Column(String(20))
    comments_disabled = Column(Boolean, default=False)
    ratings_disabled = Column(Boolean, default=False)
    video_error_or_removed = Column(Boolean, default=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class CategoryAnalytics(Base):
    __tablename__ = "category_analytics"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, unique=True, nullable=False)
    category_name = Column(String(100))
    total_videos = Column(Integer, default=0)
    avg_views = Column(Numeric(15, 2), default=0)
    avg_likes = Column(Numeric(12, 2), default=0)
    avg_comments = Column(Numeric(12, 2), default=0)
    avg_engagement_rate = Column(Numeric(10, 6), default=0)
    avg_trending_duration = Column(Numeric(8, 2), default=0)
    max_trending_duration = Column(Integer, default=0)
    min_trending_duration = Column(Integer, default=1)
    computed_at = Column(DateTime, default=datetime.utcnow)


class UploadTimeAnalytics(Base):
    __tablename__ = "upload_time_analytics"
    id = Column(Integer, primary_key=True)
    publish_hour = Column(SmallInteger, unique=True, nullable=False)
    upload_time_bucket = Column(String(30))
    total_videos = Column(Integer, default=0)
    avg_trending_duration = Column(Numeric(8, 2), default=0)
    avg_views = Column(Numeric(15, 2), default=0)
    avg_engagement_rate = Column(Numeric(10, 6), default=0)
    max_trending_duration = Column(Integer, default=0)
    computed_at = Column(DateTime, default=datetime.utcnow)


class TitleLengthAnalytics(Base):
    __tablename__ = "title_length_analytics"
    id = Column(Integer, primary_key=True)
    bucket = Column(String(20), unique=True, nullable=False)
    bucket_min = Column(Integer)
    bucket_max = Column(Integer)
    total_videos = Column(Integer, default=0)
    avg_views = Column(Numeric(15, 2), default=0)
    avg_engagement_rate = Column(Numeric(10, 6), default=0)
    avg_trending_duration = Column(Numeric(8, 2), default=0)
    computed_at = Column(DateTime, default=datetime.utcnow)


class TrendingFactor(Base):
    __tablename__ = "trending_factors"
    id = Column(Integer, primary_key=True)
    rank_position = Column(SmallInteger, nullable=False)
    factor = Column(String(100), unique=True, nullable=False)
    score = Column(Numeric(6, 4), default=0)
    pearson_r = Column(Numeric(8, 6))
    spearman_r = Column(Numeric(8, 6))
    anova_f = Column(Numeric(10, 4))
    effect_size = Column(Numeric(8, 6))
    mutual_info = Column(Numeric(8, 6))
    p_value = Column(Numeric(12, 10))
    association_type = Column(String(30))
    interpretation = Column(Text)
    computed_at = Column(DateTime, default=datetime.utcnow)


class BreakoutVideo(Base):
    __tablename__ = "breakout_videos"
    id = Column(Integer, primary_key=True)
    video_id = Column(String(20))
    title = Column(Text)
    category_name = Column(String(100))
    views = Column(BigInteger)
    engagement_rate = Column(Numeric(10, 6))
    trending_duration_days = Column(Integer)
    trendpulse_score = Column(Numeric(5, 2))
    anomaly_score = Column(Numeric(6, 2))
    anomaly_reasons = Column(ARRAY(Text))
    detected_at = Column(DateTime, default=datetime.utcnow)


class PipelineMetrics(Base):
    __tablename__ = "pipeline_metrics"
    id = Column(Integer, primary_key=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    kafka_messages_produced = Column(BigInteger, default=0)
    kafka_messages_consumed = Column(BigInteger, default=0)
    kafka_messages_failed = Column(BigInteger, default=0)
    hdfs_records_written = Column(BigInteger, default=0)
    mapreduce_jobs_run = Column(Integer, default=0)
    mapreduce_jobs_failed = Column(Integer, default=0)
    analytics_records = Column(Integer, default=0)
    pipeline_stage = Column(String(50))
    status = Column(String(20), default="running")
    notes = Column(Text)


class DataQualityMetrics(Base):
    __tablename__ = "data_quality_metrics"
    id = Column(Integer, primary_key=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    total_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    quality_score = Column(Numeric(5, 2), default=100)
    check_name = Column(String(100))
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    pass_rate = Column(Numeric(5, 2), default=100)
    details = Column(Text)


class TrendScore(Base):
    __tablename__ = "trend_scores"
    id = Column(Integer, primary_key=True)
    video_id = Column(String(20), unique=True)
    score = Column(Numeric(5, 2), nullable=False)
    label = Column(String(20))
    engagement_contribution = Column(Numeric(6, 4))
    view_contribution = Column(Numeric(6, 4))
    timing_contribution = Column(Numeric(6, 4))
    content_contribution = Column(Numeric(6, 4))
    computed_at = Column(DateTime, default=datetime.utcnow)
