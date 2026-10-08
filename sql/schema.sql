-- ============================================================
-- TrendPulse - PostgreSQL Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------
-- Videos (processed, one row per unique video)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    id                    SERIAL PRIMARY KEY,
    video_id              VARCHAR(20) UNIQUE NOT NULL,
    title                 TEXT,
    channel_title         VARCHAR(255),
    category_id           INTEGER,
    category_name         VARCHAR(100),
    publish_time          TIMESTAMP WITH TIME ZONE,
    publish_hour          SMALLINT,
    publish_weekday       SMALLINT,
    publish_weekday_name  VARCHAR(20),
    is_weekend            BOOLEAN DEFAULT FALSE,
    upload_time_bucket    VARCHAR(30),
    tags                  TEXT,
    tag_count             INTEGER DEFAULT 0,
    views                 BIGINT DEFAULT 0,
    likes                 BIGINT DEFAULT 0,
    dislikes              BIGINT DEFAULT 0,
    comment_count         BIGINT DEFAULT 0,
    engagement_rate       NUMERIC(10,6) DEFAULT 0,
    engagement_score      NUMERIC(10,6) DEFAULT 0,
    like_rate             NUMERIC(10,6) DEFAULT 0,
    comment_rate          NUMERIC(10,6) DEFAULT 0,
    title_length          INTEGER DEFAULT 0,
    title_word_count      INTEGER DEFAULT 0,
    title_length_bucket   VARCHAR(20),
    description_length    INTEGER DEFAULT 0,
    uppercase_ratio       NUMERIC(6,4) DEFAULT 0,
    punctuation_count     INTEGER DEFAULT 0,
    exclamation_count     INTEGER DEFAULT 0,
    question_mark_count   INTEGER DEFAULT 0,
    trending_duration_days INTEGER DEFAULT 1,
    first_trending_date   DATE,
    last_trending_date    DATE,
    trending_duration_bucket VARCHAR(20),
    view_velocity         NUMERIC(15,2) DEFAULT 0,
    trendpulse_score      NUMERIC(5,2) DEFAULT 0,
    trendpulse_label      VARCHAR(20),
    comments_disabled     BOOLEAN DEFAULT FALSE,
    ratings_disabled      BOOLEAN DEFAULT FALSE,
    video_error_or_removed BOOLEAN DEFAULT FALSE,
    processed_at          TIMESTAMP DEFAULT NOW(),
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_category_id ON videos(category_id);
CREATE INDEX IF NOT EXISTS idx_videos_trending_duration ON videos(trending_duration_days DESC);
CREATE INDEX IF NOT EXISTS idx_videos_trendpulse_score ON videos(trendpulse_score DESC);
CREATE INDEX IF NOT EXISTS idx_videos_views ON videos(views DESC);
CREATE INDEX IF NOT EXISTS idx_videos_engagement_rate ON videos(engagement_rate DESC);
CREATE INDEX IF NOT EXISTS idx_videos_publish_hour ON videos(publish_hour);
CREATE INDEX IF NOT EXISTS idx_videos_upload_bucket ON videos(upload_time_bucket);

-- -----------------------------------------------------------
-- Category Analytics (MapReduce Job 1 output)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS category_analytics (
    id                        SERIAL PRIMARY KEY,
    category_id               INTEGER UNIQUE NOT NULL,
    category_name             VARCHAR(100),
    total_videos              INTEGER DEFAULT 0,
    avg_views                 NUMERIC(15,2) DEFAULT 0,
    avg_likes                 NUMERIC(12,2) DEFAULT 0,
    avg_comments              NUMERIC(12,2) DEFAULT 0,
    avg_engagement_rate       NUMERIC(10,6) DEFAULT 0,
    avg_trending_duration     NUMERIC(8,2) DEFAULT 0,
    max_trending_duration     INTEGER DEFAULT 0,
    min_trending_duration     INTEGER DEFAULT 1,
    std_trending_duration     NUMERIC(8,2) DEFAULT 0,
    top_channel               VARCHAR(255),
    computed_at               TIMESTAMP DEFAULT NOW()
);

-- -----------------------------------------------------------
-- Upload Time Analytics (MapReduce Job 2 output)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS upload_time_analytics (
    id                        SERIAL PRIMARY KEY,
    publish_hour              SMALLINT UNIQUE NOT NULL,
    upload_time_bucket        VARCHAR(30),
    total_videos              INTEGER DEFAULT 0,
    avg_trending_duration     NUMERIC(8,2) DEFAULT 0,
    avg_views                 NUMERIC(15,2) DEFAULT 0,
    avg_engagement_rate       NUMERIC(10,6) DEFAULT 0,
    max_trending_duration     INTEGER DEFAULT 0,
    computed_at               TIMESTAMP DEFAULT NOW()
);

-- -----------------------------------------------------------
-- Title Length Analytics (MapReduce Job 3 output)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS title_length_analytics (
    id                        SERIAL PRIMARY KEY,
    bucket                    VARCHAR(20) UNIQUE NOT NULL,
    bucket_min                INTEGER,
    bucket_max                INTEGER,
    total_videos              INTEGER DEFAULT 0,
    avg_views                 NUMERIC(15,2) DEFAULT 0,
    avg_engagement_rate       NUMERIC(10,6) DEFAULT 0,
    avg_trending_duration     NUMERIC(8,2) DEFAULT 0,
    computed_at               TIMESTAMP DEFAULT NOW()
);

-- -----------------------------------------------------------
-- Trending Factors (Correlation Analysis output)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS trending_factors (
    id                  SERIAL PRIMARY KEY,
    rank_position       SMALLINT NOT NULL,
    factor              VARCHAR(100) UNIQUE NOT NULL,
    score               NUMERIC(6,4) DEFAULT 0,
    pearson_r           NUMERIC(8,6),
    spearman_r          NUMERIC(8,6),
    anova_f             NUMERIC(10,4),
    effect_size         NUMERIC(8,6),
    mutual_info         NUMERIC(8,6),
    p_value             NUMERIC(12,10),
    association_type    VARCHAR(30),
    interpretation      TEXT,
    computed_at         TIMESTAMP DEFAULT NOW()
);

-- -----------------------------------------------------------
-- Breakout Videos (Anomaly Detection output)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS breakout_videos (
    id                      SERIAL PRIMARY KEY,
    video_id                VARCHAR(20) REFERENCES videos(video_id) ON DELETE CASCADE,
    title                   TEXT,
    category_name           VARCHAR(100),
    views                   BIGINT,
    engagement_rate         NUMERIC(10,6),
    trending_duration_days  INTEGER,
    trendpulse_score        NUMERIC(5,2),
    anomaly_score           NUMERIC(6,2),
    anomaly_reasons         TEXT[],
    detected_at             TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_breakout_anomaly_score ON breakout_videos(anomaly_score DESC);

-- -----------------------------------------------------------
-- Pipeline Metrics (for monitoring dashboard)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id                      SERIAL PRIMARY KEY,
    recorded_at             TIMESTAMP DEFAULT NOW(),
    kafka_messages_produced BIGINT DEFAULT 0,
    kafka_messages_consumed BIGINT DEFAULT 0,
    kafka_messages_failed   BIGINT DEFAULT 0,
    hdfs_records_written    BIGINT DEFAULT 0,
    mapreduce_jobs_run      INTEGER DEFAULT 0,
    mapreduce_jobs_failed   INTEGER DEFAULT 0,
    analytics_records       INTEGER DEFAULT 0,
    pipeline_stage          VARCHAR(50),
    status                  VARCHAR(20) DEFAULT 'running',
    notes                   TEXT
);

-- -----------------------------------------------------------
-- Data Quality Metrics
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id                  SERIAL PRIMARY KEY,
    recorded_at         TIMESTAMP DEFAULT NOW(),
    total_records       INTEGER DEFAULT 0,
    failed_records      INTEGER DEFAULT 0,
    quality_score       NUMERIC(5,2) DEFAULT 100,
    check_name          VARCHAR(100),
    passed_count        INTEGER DEFAULT 0,
    failed_count        INTEGER DEFAULT 0,
    pass_rate           NUMERIC(5,2) DEFAULT 100,
    details             TEXT
);

-- -----------------------------------------------------------
-- Trend Scores (individual video scores)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS trend_scores (
    id                      SERIAL PRIMARY KEY,
    video_id                VARCHAR(20) REFERENCES videos(video_id) ON DELETE CASCADE,
    score                   NUMERIC(5,2) NOT NULL,
    label                   VARCHAR(20),
    engagement_contribution NUMERIC(6,4),
    view_contribution       NUMERIC(6,4),
    timing_contribution     NUMERIC(6,4),
    content_contribution    NUMERIC(6,4),
    category_contribution   NUMERIC(6,4),
    computed_at             TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id)
);

-- -----------------------------------------------------------
-- Helper view: Video summary with all analytics
-- -----------------------------------------------------------
CREATE OR REPLACE VIEW video_summary AS
SELECT
    v.*,
    ca.avg_trending_duration AS category_avg_trending,
    ts.score AS ts_score,
    ts.label AS ts_label
FROM videos v
LEFT JOIN category_analytics ca ON v.category_id = ca.category_id
LEFT JOIN trend_scores ts ON v.video_id = ts.video_id;
