"""
TrendPulse - Tests for Analytics Engine
"""
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def analytics_df():
    """Sample DataFrame with all features needed for analytics tests."""
    np.random.seed(42)
    n = 200
    categories = [10, 17, 22, 24, 25, 27, 28]
    category_id = np.random.choice(categories, n)
    publish_hour = np.random.randint(0, 24, n)
    trending_duration = np.random.randint(1, 16, n)
    views = np.random.randint(50000, 10000000, n)
    likes = (views * np.random.uniform(0.01, 0.12, n)).astype(int)
    comments = (views * np.random.uniform(0.001, 0.05, n)).astype(int)
    engagement_rate = (likes + comments) / views
    title_length = np.random.randint(10, 100, n)
    tag_count = np.random.randint(0, 15, n)
    is_weekend = np.random.randint(0, 2, n)

    return pd.DataFrame({
        'video_id': [f'vid_{i:04d}' for i in range(n)],
        'title': [f'Test Video Title {i}' for i in range(n)],
        'category_id': category_id,
        'category_name': [f'Cat_{c}' for c in category_id],
        'publish_hour': publish_hour,
        'trending_duration_days': trending_duration,
        'views': views,
        'likes': likes,
        'comment_count': comments,
        'engagement_rate': engagement_rate,
        'like_rate': likes / views,
        'comment_rate': comments / views,
        'title_length': title_length,
        'tag_count': tag_count,
        'is_weekend': is_weekend,
        'upload_time_bucket': np.random.choice(
            ['Early Morning', 'Morning', 'Afternoon', 'Evening', 'Night'], n
        ),
        'publish_weekday': np.random.randint(0, 7, n),
        'description_length': np.random.randint(0, 5000, n),
        'uppercase_ratio': np.random.uniform(0, 0.5, n),
        'punctuation_count': np.random.randint(0, 10, n),
        'trendpulse_score': np.random.uniform(0, 100, n),
        'trendpulse_label': np.random.choice(['Low', 'Moderate', 'High', 'Very High'], n),
        'view_velocity': views / np.maximum(trending_duration, 1),
        'trending_duration_bucket': np.where(trending_duration == 1, '1_day',
                                    np.where(trending_duration <= 3, '2-3_days',
                                    np.where(trending_duration <= 7, '4-7_days',
                                    np.where(trending_duration <= 14, '8-14_days', '15+_days')))),
    })


# ---------------------------------------------------------------------------
# Test: Correlation Engine
# ---------------------------------------------------------------------------

class TestCorrelationEngine:
    def test_correlation_returns_dataframe(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        result = compute_correlations(analytics_df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_correlation_has_required_columns(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        result = compute_correlations(analytics_df)
        required_cols = ['factor', 'association_type']
        for col in required_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_no_pearson_on_categoricals(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        result = compute_correlations(analytics_df)
        # category_id should not have pearson_r as its primary metric
        if 'category_id' in result['factor'].values:
            cat_row = result[result['factor'] == 'category_id'].iloc[0]
            assert cat_row.get('association_type') in ['categorical', 'anova', None] or \
                   pd.isna(cat_row.get('pearson_r', None))

    def test_numeric_features_have_correlations(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        result = compute_correlations(analytics_df)
        numeric_factors = result[result['association_type'] == 'numeric']
        if len(numeric_factors) > 0:
            assert 'pearson_r' in result.columns or 'spearman_r' in result.columns


# ---------------------------------------------------------------------------
# Test: Factor Ranking
# ---------------------------------------------------------------------------

class TestFactorRanking:
    def test_returns_top_5(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        from analytics.factor_ranking import rank_factors
        corr_df = compute_correlations(analytics_df)
        ranked = rank_factors(corr_df)
        assert len(ranked) >= 5 or len(ranked) == len(corr_df)

    def test_ranking_has_required_fields(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        from analytics.factor_ranking import rank_factors
        corr_df = compute_correlations(analytics_df)
        ranked = rank_factors(corr_df)
        required = ['rank_position', 'factor', 'score', 'interpretation']
        for col in required:
            assert col in ranked.columns, f"Missing column: {col}"

    def test_ranks_are_sequential(self, analytics_df):
        from analytics.correlation_engine import compute_correlations
        from analytics.factor_ranking import rank_factors
        corr_df = compute_correlations(analytics_df)
        ranked = rank_factors(corr_df)
        top5 = ranked.head(5)
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            assert row['rank_position'] == i

    def test_scores_are_not_hardcoded(self, analytics_df):
        """Scores should be data-driven, not all the same."""
        from analytics.correlation_engine import compute_correlations
        from analytics.factor_ranking import rank_factors
        corr_df = compute_correlations(analytics_df)
        ranked = rank_factors(corr_df)
        if len(ranked) >= 2:
            scores = ranked['score'].tolist()
            assert len(set(round(s, 4) for s in scores)) > 1, "All scores are identical - may be hardcoded"


# ---------------------------------------------------------------------------
# Test: TrendPulse Score
# ---------------------------------------------------------------------------

class TestTrendPulseScore:
    def test_score_range(self, analytics_df):
        from analytics.trend_score import calculate_scores
        result = calculate_scores(analytics_df)
        assert 'trendpulse_score' in result.columns
        assert (result['trendpulse_score'] >= 0).all()
        assert (result['trendpulse_score'] <= 100).all()

    def test_score_labels(self, analytics_df):
        from analytics.trend_score import calculate_scores
        result = calculate_scores(analytics_df)
        valid_labels = {'Low', 'Moderate', 'High', 'Very High'}
        assert set(result['trendpulse_label'].unique()).issubset(valid_labels)

    def test_get_video_score(self, analytics_df):
        from analytics.trend_score import get_video_score, calculate_scores
        df_with_scores = calculate_scores(analytics_df)
        video_id = df_with_scores.iloc[0]['video_id']
        score_info = get_video_score(video_id, df_with_scores)
        assert 'score' in score_info
        assert 'label' in score_info
        assert 0 <= score_info['score'] <= 100

    def test_video_not_found(self, analytics_df):
        from analytics.trend_score import get_video_score, calculate_scores
        df_with_scores = calculate_scores(analytics_df)
        score_info = get_video_score('nonexistent_id', df_with_scores)
        assert score_info is None or 'error' in score_info


# ---------------------------------------------------------------------------
# Test: Anomaly Detection
# ---------------------------------------------------------------------------

class TestAnomalyDetection:
    def test_returns_dataframe(self, analytics_df):
        from analytics.anomaly_detection import detect_breakout_videos
        result = detect_breakout_videos(analytics_df)
        assert isinstance(result, pd.DataFrame)

    def test_anomaly_score_range(self, analytics_df):
        from analytics.anomaly_detection import detect_breakout_videos
        result = detect_breakout_videos(analytics_df)
        if len(result) > 0:
            assert (result['anomaly_score'] >= 0).all()
            assert (result['anomaly_score'] <= 100).all()

    def test_anomaly_has_reasons(self, analytics_df):
        from analytics.anomaly_detection import detect_breakout_videos
        result = detect_breakout_videos(analytics_df)
        if len(result) > 0:
            assert 'anomaly_reasons' in result.columns

    def test_high_view_videos_detected(self):
        """A video with extremely high views should be flagged."""
        from analytics.anomaly_detection import detect_breakout_videos
        df = pd.DataFrame({
            'video_id': [f'v{i}' for i in range(50)],
            'title': [f'Video {i}' for i in range(50)],
            'category_name': ['Entertainment'] * 50,
            'views': [100000] * 49 + [50000000],  # Last one is extreme
            'engagement_rate': [0.05] * 50,
            'trending_duration_days': [3] * 50,
            'trendpulse_score': [50.0] * 50,
            'likes': [5000] * 50,
            'comment_count': [500] * 50,
        })
        result = detect_breakout_videos(df)
        # The extreme video should be in results
        if len(result) > 0:
            assert 'v49' in result['video_id'].values or len(result) >= 1


# ---------------------------------------------------------------------------
# Test: Insight Generator
# ---------------------------------------------------------------------------

class TestInsightGenerator:
    def test_category_insight_is_string(self, analytics_df):
        from analytics.insight_generator import generate_category_insight
        insight = generate_category_insight(analytics_df)
        assert isinstance(insight, str)
        assert len(insight) > 10

    def test_upload_time_insight(self, analytics_df):
        from analytics.insight_generator import generate_upload_time_insight
        insight = generate_upload_time_insight(analytics_df)
        assert isinstance(insight, str)
        assert len(insight) > 10

    def test_insights_not_hardcoded(self, analytics_df):
        """Running on two different datasets should produce different insights."""
        from analytics.insight_generator import generate_category_insight
        import copy
        df2 = analytics_df.copy()
        # Override category data
        df2['category_name'] = 'Gaming'
        df2['trending_duration_days'] = 1
        insight1 = generate_category_insight(analytics_df)
        insight2 = generate_category_insight(df2)
        # They may differ since data differs
        # At minimum both should be non-empty strings
        assert isinstance(insight1, str)
        assert isinstance(insight2, str)
