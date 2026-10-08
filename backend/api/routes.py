"""
TrendPulse - FastAPI Route Handlers
All endpoints serve data from PostgreSQL analytics database.
"""
import os
import math
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, asc

from backend.database.connection import get_db
from backend.models.db_models import (
    Video, CategoryAnalytics, UploadTimeAnalytics, TitleLengthAnalytics,
    TrendingFactor, BreakoutVideo, PipelineMetrics, DataQualityMetrics, TrendScore
)
from backend.schemas.response_schemas import (
    VideoResponse, VideoListResponse, CategoryAnalyticsResponse,
    UploadTimeResponse, TitleAnalysisResponse, TrendingFactorResponse,
    TopFactorsResponse, BreakoutVideoResponse, PipelineStatusResponse,
    DataQualityResponse, OverviewKPIResponse, TrendScoreResponse,
    ServiceStatus, QualityCheckResponse
)

logger = logging.getLogger("trendpulse.api")
router = APIRouter(prefix="/api", tags=["TrendPulse Analytics"])


# ---------------------------------------------------------------------------
# Overview / KPIs
# ---------------------------------------------------------------------------
@router.get("/overview", response_model=OverviewKPIResponse)
def get_overview(db: Session = Depends(get_db)):
    try:
        total = db.query(func.count(Video.id)).scalar() or 0
        avg_dur = db.query(func.avg(Video.trending_duration_days)).scalar() or 0
        avg_eng = db.query(func.avg(Video.engagement_rate)).scalar() or 0
        max_dur = db.query(func.max(Video.trending_duration_days)).scalar() or 0
        breakout_count = db.query(func.count(BreakoutVideo.id)).scalar() or 0
        cat_count = db.query(func.count(func.distinct(Video.category_id))).scalar() or 0
        dq = db.query(DataQualityMetrics).order_by(desc(DataQualityMetrics.recorded_at)).first()
        dq_score = float(dq.quality_score) if dq else None

        # Insights from DB
        factors = db.query(TrendingFactor).order_by(TrendingFactor.rank_position).limit(3).all()
        insights = [f.interpretation for f in factors if f.interpretation]

        return OverviewKPIResponse(
            total_videos=total,
            avg_trending_duration=round(float(avg_dur), 2),
            avg_engagement_rate=round(float(avg_eng), 6),
            max_trending_duration=int(max_dur),
            breakout_video_count=int(breakout_count),
            categories_count=int(cat_count),
            data_quality_score=dq_score,
            insights=insights[:3],
        )
    except Exception as e:
        logger.error(f"/overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@router.get("/categories", response_model=List[CategoryAnalyticsResponse])
def get_categories(
    sort_by: str = Query("avg_trending_duration", description="Sort field"),
    db: Session = Depends(get_db)
):
    try:
        sort_col = getattr(CategoryAnalytics, sort_by, CategoryAnalytics.avg_trending_duration)
        cats = db.query(CategoryAnalytics).order_by(desc(sort_col)).all()
        if not cats:
            # Compute on-the-fly from videos table
            rows = db.execute(text("""
                SELECT category_id, category_name,
                       COUNT(*) as total_videos,
                       AVG(views) as avg_views, AVG(likes) as avg_likes,
                       AVG(comment_count) as avg_comments,
                       AVG(engagement_rate) as avg_engagement_rate,
                       AVG(trending_duration_days) as avg_trending_duration,
                       MAX(trending_duration_days) as max_trending_duration,
                       MIN(trending_duration_days) as min_trending_duration
                FROM videos GROUP BY category_id, category_name
                ORDER BY avg_trending_duration DESC
            """)).fetchall()
            return [CategoryAnalyticsResponse(
                category_id=r.category_id or 0,
                category_name=r.category_name,
                total_videos=r.total_videos,
                avg_views=round(float(r.avg_views or 0), 2),
                avg_likes=round(float(r.avg_likes or 0), 2),
                avg_comments=round(float(r.avg_comments or 0), 2),
                avg_engagement_rate=round(float(r.avg_engagement_rate or 0), 6),
                avg_trending_duration=round(float(r.avg_trending_duration or 0), 2),
                max_trending_duration=r.max_trending_duration,
                min_trending_duration=r.min_trending_duration,
            ) for r in rows]
        return cats
    except Exception as e:
        logger.error(f"/categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Upload Times
# ---------------------------------------------------------------------------
@router.get("/upload-times", response_model=List[UploadTimeResponse])
def get_upload_times(db: Session = Depends(get_db)):
    try:
        rows_db = db.query(UploadTimeAnalytics).order_by(UploadTimeAnalytics.publish_hour).all()
        if not rows_db:
            rows = db.execute(text("""
                SELECT publish_hour, upload_time_bucket,
                       COUNT(*) as total_videos,
                       AVG(trending_duration_days) as avg_trending_duration,
                       AVG(views) as avg_views,
                       AVG(engagement_rate) as avg_engagement_rate,
                       MAX(trending_duration_days) as max_trending_duration
                FROM videos WHERE publish_hour IS NOT NULL
                GROUP BY publish_hour, upload_time_bucket
                ORDER BY publish_hour
            """)).fetchall()
            return [UploadTimeResponse(
                publish_hour=r.publish_hour,
                upload_time_bucket=r.upload_time_bucket,
                total_videos=r.total_videos,
                avg_trending_duration=round(float(r.avg_trending_duration or 0), 2),
                avg_views=round(float(r.avg_views or 0), 2),
                avg_engagement_rate=round(float(r.avg_engagement_rate or 0), 6),
            ) for r in rows]
        return rows_db
    except Exception as e:
        logger.error(f"/upload-times error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Title Analysis
# ---------------------------------------------------------------------------
@router.get("/title-analysis", response_model=List[TitleAnalysisResponse])
def get_title_analysis(db: Session = Depends(get_db)):
    try:
        rows_db = db.query(TitleLengthAnalytics).all()
        if not rows_db:
            rows = db.execute(text("""
                SELECT title_length_bucket as bucket,
                       COUNT(*) as total_videos,
                       AVG(views) as avg_views,
                       AVG(engagement_rate) as avg_engagement_rate,
                       AVG(trending_duration_days) as avg_trending_duration
                FROM videos WHERE title_length_bucket IS NOT NULL
                GROUP BY title_length_bucket
                ORDER BY avg_trending_duration DESC
            """)).fetchall()
            return [TitleAnalysisResponse(
                bucket=r.bucket,
                total_videos=r.total_videos,
                avg_views=round(float(r.avg_views or 0), 2),
                avg_engagement_rate=round(float(r.avg_engagement_rate or 0), 6),
                avg_trending_duration=round(float(r.avg_trending_duration or 0), 2),
            ) for r in rows]
        return rows_db
    except Exception as e:
        logger.error(f"/title-analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Trending Factors
# ---------------------------------------------------------------------------
@router.get("/trending-factors", response_model=TopFactorsResponse)
def get_trending_factors(db: Session = Depends(get_db)):
    try:
        factors = db.query(TrendingFactor).order_by(TrendingFactor.rank_position).limit(10).all()
        factor_responses = [TrendingFactorResponse(
            rank_position=f.rank_position,
            factor=f.factor,
            score=float(f.score or 0),
            association_type=f.association_type,
            pearson_r=float(f.pearson_r) if f.pearson_r else None,
            spearman_r=float(f.spearman_r) if f.spearman_r else None,
            anova_f=float(f.anova_f) if f.anova_f else None,
            effect_size=float(f.effect_size) if f.effect_size else None,
            mutual_info=float(f.mutual_info) if f.mutual_info else None,
            p_value=float(f.p_value) if f.p_value else None,
            interpretation=f.interpretation,
        ) for f in factors]
        return TopFactorsResponse(
            factors=factor_responses,
            computed_at=factors[0].computed_at.isoformat() if factors else None,
        )
    except Exception as e:
        logger.error(f"/trending-factors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Video Explorer
# ---------------------------------------------------------------------------
@router.get("/videos", response_model=VideoListResponse)
def get_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    sort_by: str = Query("trendpulse_score"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db)
):
    try:
        q = db.query(Video)
        if search:
            q = q.filter(Video.title.ilike(f"%{search}%"))
        if category_id:
            q = q.filter(Video.category_id == category_id)
        sort_col = getattr(Video, sort_by, Video.trendpulse_score)
        q = q.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))
        total = q.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        videos = q.offset((page - 1) * page_size).limit(page_size).all()
        return VideoListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            data=[VideoResponse.model_validate(v) for v in videos],
        )
    except Exception as e:
        logger.error(f"/videos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Breakout Videos
# ---------------------------------------------------------------------------
@router.get("/breakout-videos", response_model=List[BreakoutVideoResponse])
def get_breakout_videos(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        videos = db.query(BreakoutVideo).order_by(
            desc(BreakoutVideo.anomaly_score)).limit(limit).all()
        return [BreakoutVideoResponse(
            video_id=v.video_id,
            title=v.title,
            category_name=v.category_name,
            views=v.views,
            engagement_rate=float(v.engagement_rate) if v.engagement_rate else None,
            trending_duration_days=v.trending_duration_days,
            trendpulse_score=float(v.trendpulse_score) if v.trendpulse_score else None,
            anomaly_score=float(v.anomaly_score) if v.anomaly_score else None,
            anomaly_reasons=v.anomaly_reasons or [],
        ) for v in videos]
    except Exception as e:
        logger.error(f"/breakout-videos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Pipeline Status
# ---------------------------------------------------------------------------
@router.get("/pipeline-status", response_model=PipelineStatusResponse)
def get_pipeline_status(db: Session = Depends(get_db)):
    from backend.database.connection import check_connection
    try:
        metrics = db.query(PipelineMetrics).order_by(
            desc(PipelineMetrics.recorded_at)).first()
        services = [
            ServiceStatus(name="PostgreSQL", status="ONLINE" if check_connection() else "ERROR",
                         details="Analytics database", last_checked=datetime.utcnow().isoformat()),
            ServiceStatus(name="Apache Kafka", status="WARNING",
                         details="Check Docker service", last_checked=datetime.utcnow().isoformat()),
            ServiceStatus(name="Hadoop HDFS", status="WARNING",
                         details="Check Docker service", last_checked=datetime.utcnow().isoformat()),
            ServiceStatus(name="MapReduce", status="PROCESSING" if metrics else "WARNING",
                         details=f"{metrics.mapreduce_jobs_run} jobs run" if metrics else "No jobs run yet",
                         last_checked=datetime.utcnow().isoformat()),
        ]
        return PipelineStatusResponse(
            overall_status="ONLINE",
            services=services,
            kafka_messages_produced=metrics.kafka_messages_produced if metrics else 0,
            kafka_messages_consumed=metrics.kafka_messages_consumed if metrics else 0,
            kafka_messages_failed=metrics.kafka_messages_failed if metrics else 0,
            hdfs_records_written=metrics.hdfs_records_written if metrics else 0,
            mapreduce_jobs_run=metrics.mapreduce_jobs_run if metrics else 0,
            analytics_records=metrics.analytics_records if metrics else 0,
            last_run=metrics.recorded_at.isoformat() if metrics else None,
        )
    except Exception as e:
        logger.error(f"/pipeline-status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Data Quality
# ---------------------------------------------------------------------------
@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality(db: Session = Depends(get_db)):
    try:
        checks = db.query(DataQualityMetrics).order_by(
            desc(DataQualityMetrics.recorded_at)).limit(20).all()
        if not checks:
            return DataQualityResponse(quality_score=0, total_records=0, failed_records=0, checks=[])
        latest = checks[0]
        quality_score = float(latest.quality_score or 0)
        check_responses = [QualityCheckResponse(
            check=c.check_name or "unknown",
            passed=c.passed_count or 0,
            failed=c.failed_count or 0,
            pass_rate=float(c.pass_rate or 0),
            details=c.details,
        ) for c in checks]
        return DataQualityResponse(
            quality_score=quality_score,
            total_records=latest.total_records or 0,
            failed_records=latest.failed_records or 0,
            checks=check_responses,
            recorded_at=latest.recorded_at.isoformat() if latest.recorded_at else None,
        )
    except Exception as e:
        logger.error(f"/data-quality error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Trend Score per Video
# ---------------------------------------------------------------------------
@router.get("/trend-score/{video_id}", response_model=TrendScoreResponse)
def get_trend_score(video_id: str, db: Session = Depends(get_db)):
    try:
        ts = db.query(TrendScore).filter(TrendScore.video_id == video_id).first()
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        score = float(ts.score) if ts else float(video.trendpulse_score or 0)
        label = ts.label if ts else str(video.trendpulse_label or "Low")
        contribs = {}
        if ts:
            contribs = {
                "engagement": float(ts.engagement_contribution or 0),
                "views": float(ts.view_contribution or 0),
                "timing": float(ts.timing_contribution or 0),
                "content": float(ts.content_contribution or 0),
            }
        return TrendScoreResponse(
            video_id=video_id, score=score, label=label,
            contributing_factors=contribs,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/trend-score error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
