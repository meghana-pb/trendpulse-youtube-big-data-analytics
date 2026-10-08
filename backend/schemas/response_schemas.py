"""
TrendPulse - Pydantic v2 Response Schemas
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class VideoResponse(BaseModel):
    video_id: str
    title: Optional[str] = None
    channel_title: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comment_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    trending_duration_days: Optional[int] = None
    trending_duration_bucket: Optional[str] = None
    publish_hour: Optional[int] = None
    publish_weekday_name: Optional[str] = None
    upload_time_bucket: Optional[str] = None
    title_length: Optional[int] = None
    tag_count: Optional[int] = None
    trendpulse_score: Optional[float] = None
    trendpulse_label: Optional[str] = None
    publish_time: Optional[str] = None

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[VideoResponse]


class CategoryAnalyticsResponse(BaseModel):
    category_id: int
    category_name: Optional[str] = None
    total_videos: int
    avg_views: Optional[float] = None
    avg_likes: Optional[float] = None
    avg_comments: Optional[float] = None
    avg_engagement_rate: Optional[float] = None
    avg_trending_duration: Optional[float] = None
    max_trending_duration: Optional[int] = None
    min_trending_duration: Optional[int] = None

    model_config = {"from_attributes": True}


class UploadTimeResponse(BaseModel):
    publish_hour: int
    upload_time_bucket: Optional[str] = None
    total_videos: int
    avg_trending_duration: Optional[float] = None
    avg_views: Optional[float] = None
    avg_engagement_rate: Optional[float] = None

    model_config = {"from_attributes": True}


class TitleAnalysisResponse(BaseModel):
    bucket: str
    bucket_min: Optional[int] = None
    bucket_max: Optional[int] = None
    total_videos: int
    avg_views: Optional[float] = None
    avg_engagement_rate: Optional[float] = None
    avg_trending_duration: Optional[float] = None

    model_config = {"from_attributes": True}


class TrendingFactorResponse(BaseModel):
    rank_position: int
    factor: str
    factor_label: Optional[str] = None
    score: float
    association_type: Optional[str] = None
    pearson_r: Optional[float] = None
    spearman_r: Optional[float] = None
    anova_f: Optional[float] = None
    effect_size: Optional[float] = None
    mutual_info: Optional[float] = None
    p_value: Optional[float] = None
    interpretation: Optional[str] = None

    model_config = {"from_attributes": True}


class TopFactorsResponse(BaseModel):
    factors: List[TrendingFactorResponse]
    insights: List[str] = []
    computed_at: Optional[str] = None


class BreakoutVideoResponse(BaseModel):
    video_id: str
    title: Optional[str] = None
    category_name: Optional[str] = None
    views: Optional[int] = None
    engagement_rate: Optional[float] = None
    trending_duration_days: Optional[int] = None
    trendpulse_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    anomaly_reasons: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class ServiceStatus(BaseModel):
    name: str
    status: str  # ONLINE, PROCESSING, WARNING, ERROR
    details: Optional[str] = None
    last_checked: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    overall_status: str
    services: List[ServiceStatus]
    kafka_messages_produced: Optional[int] = None
    kafka_messages_consumed: Optional[int] = None
    kafka_messages_failed: Optional[int] = None
    hdfs_records_written: Optional[int] = None
    mapreduce_jobs_run: Optional[int] = None
    analytics_records: Optional[int] = None
    last_run: Optional[str] = None


class QualityCheckResponse(BaseModel):
    check: str
    passed: int
    failed: int
    pass_rate: float
    details: Optional[str] = None


class DataQualityResponse(BaseModel):
    quality_score: float
    total_records: int
    failed_records: int
    checks: List[QualityCheckResponse]
    recorded_at: Optional[str] = None


class OverviewKPIResponse(BaseModel):
    total_videos: int
    total_trending_observations: Optional[int] = None
    avg_trending_duration: float
    avg_engagement_rate: float
    max_trending_duration: int
    breakout_video_count: int
    categories_count: int
    data_quality_score: Optional[float] = None
    insights: List[str] = []


class TrendScoreResponse(BaseModel):
    video_id: str
    score: float
    label: str
    contributing_factors: Dict[str, float] = {}
    note: str = "Analytical score only. Not a prediction of future trending performance."
