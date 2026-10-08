"""
TrendPulse - Tests for Preprocessing Pipeline
"""
import sys
import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.preprocess import YouTubePreprocessor, UPLOAD_TIME_BUCKETS, TITLE_LENGTH_BUCKETS
from preprocessing.feature_engineering import (
    add_trend_buckets, add_view_velocity, compute_trendpulse_score,
    run_feature_engineering
)
from preprocessing.validators import DataQualityReport, validate_dataframe, validate_event


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Minimal valid DataFrame for testing."""
    return pd.DataFrame({
        'video_id': ['abc123', 'def456', 'ghi789'],
        'title': ['Test Video One', 'A' * 50, 'Short'],
        'channel_title': ['Channel A', 'Channel B', 'Channel C'],
        'category_id': [24, 10, 17],
        'publish_time': ['2023-01-15T18:30:00.000Z', '2023-06-20T09:00:00.000Z', '2023-03-10T00:00:00.000Z'],
        'tags': ['music|fun|entertainment', '[none]', 'sports|live'],
        'views': [1000000, 500000, 2000000],
        'likes': [80000, 20000, 150000],
        'dislikes': [1000, 500, 2000],
        'comment_count': [5000, 1000, 8000],
        'trending_date': ['23.15.01', '23.20.06', '23.10.03'],
        'description': ['Great video!', '', 'Sports highlights.'],
        'comments_disabled': ['False', 'False', 'True'],
        'ratings_disabled': ['False', 'False', 'False'],
        'video_error_or_removed': ['False', 'False', 'False'],
    })


@pytest.fixture
def preprocessor(tmp_path, sample_df):
    """Create preprocessor with temp CSV file."""
    csv_path = tmp_path / 'test_videos.csv'
    sample_df.to_csv(csv_path, index=False)
    return YouTubePreprocessor(str(csv_path))


# ---------------------------------------------------------------------------
# Test: Title length calculation
# ---------------------------------------------------------------------------

class TestTitleLength:
    def test_title_length_basic(self):
        df = pd.DataFrame({'title': ['Hello World', 'A' * 45, '']})
        from preprocessing.preprocess import YouTubePreprocessor
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        result = p.engineer_text_features(df)
        assert result.loc[0, 'title_length'] == 11
        assert result.loc[1, 'title_length'] == 45
        assert result.loc[2, 'title_length'] == 0

    def test_title_word_count(self):
        df = pd.DataFrame({'title': ['One Two Three', 'Single', '']})
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        result = p.engineer_text_features(df)
        assert result.loc[0, 'title_word_count'] == 3
        assert result.loc[1, 'title_word_count'] == 1

    def test_title_length_bucket(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        assert p._title_length_bucket(15) == '0-20'
        assert p._title_length_bucket(30) == '21-40'
        assert p._title_length_bucket(55) == '41-60'
        assert p._title_length_bucket(105) == '100+'

    def test_uppercase_ratio(self):
        df = pd.DataFrame({'title': ['ALL CAPS TITLE', 'no caps', 'MiXeD']})
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        result = p.engineer_text_features(df)
        assert result.loc[0, 'uppercase_ratio'] > 0.8
        assert result.loc[1, 'uppercase_ratio'] == 0.0

    def test_exclamation_count(self):
        df = pd.DataFrame({'title': ['WOW!!! Amazing!!', 'Normal Title', '']})
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        result = p.engineer_text_features(df)
        assert result.loc[0, 'exclamation_count'] == 5
        assert result.loc[1, 'exclamation_count'] == 0


# ---------------------------------------------------------------------------
# Test: Engagement calculation
# ---------------------------------------------------------------------------

class TestEngagementCalculation:
    def setup_method(self):
        self.p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        self.p.dataset_path = Path('dummy')
        self.p.category_json_path = None
        self.p.category_map = {}
        self.p.stats = {}

    def test_engagement_rate_basic(self):
        df = pd.DataFrame({
            'views': [1000000],
            'likes': [80000],
            'comment_count': [5000],
        })
        result = self.p.engineer_engagement_features(df)
        expected = (80000 + 5000) / 1000000
        assert abs(result.loc[0, 'engagement_rate'] - expected) < 1e-6

    def test_engagement_rate_zero_views(self):
        """Should not divide by zero."""
        df = pd.DataFrame({
            'views': [0],
            'likes': [100],
            'comment_count': [10],
        })
        result = self.p.engineer_engagement_features(df)
        assert not np.isnan(result.loc[0, 'engagement_rate'])
        assert not np.isinf(result.loc[0, 'engagement_rate'])

    def test_like_rate(self):
        df = pd.DataFrame({'views': [1000], 'likes': [100], 'comment_count': [10]})
        result = self.p.engineer_engagement_features(df)
        assert abs(result.loc[0, 'like_rate'] - 0.1) < 1e-6

    def test_comment_rate(self):
        df = pd.DataFrame({'views': [1000], 'likes': [100], 'comment_count': [50]})
        result = self.p.engineer_engagement_features(df)
        assert abs(result.loc[0, 'comment_rate'] - 0.05) < 1e-6

    def test_engagement_with_dislikes(self):
        df = pd.DataFrame({
            'views': [1000], 'likes': [100], 'comment_count': [10], 'dislikes': [5]
        })
        result = self.p.engineer_engagement_features(df)
        expected_score = (100 + 10 + 5) / 1000
        assert abs(result.loc[0, 'engagement_score'] - expected_score) < 1e-6


# ---------------------------------------------------------------------------
# Test: Trending Duration
# ---------------------------------------------------------------------------

class TestTrendingDuration:
    def test_single_trending_day(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        df = pd.DataFrame({
            'video_id': ['vid1'],
            'trending_date': ['23.01.01'],
        })
        result = p.calculate_trending_duration(df)
        assert result.loc[0, 'trending_duration_days'] == 1

    def test_multiple_trending_days(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        df = pd.DataFrame({
            'video_id': ['vid1', 'vid1', 'vid1'],
            'trending_date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        })
        result = p.calculate_trending_duration(df)
        assert result['trending_duration_days'].max() == 3

    def test_trending_duration_min_is_1(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        df = pd.DataFrame({
            'video_id': ['vid1'],
            'trending_date': ['2023-05-10'],
        })
        result = p.calculate_trending_duration(df)
        assert result.loc[0, 'trending_duration_days'] >= 1


# ---------------------------------------------------------------------------
# Test: Time Features
# ---------------------------------------------------------------------------

class TestTimeFeatures:
    def setup_method(self):
        self.p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        self.p.dataset_path = Path('dummy')
        self.p.category_json_path = None
        self.p.category_map = {}
        self.p.stats = {}

    def test_hour_extraction(self):
        df = pd.DataFrame({'publish_time': ['2023-06-15T18:30:00.000Z']})
        result = self.p.engineer_time_features(df)
        assert result.loc[0, 'publish_hour'] == 18

    def test_is_weekend(self):
        # 2023-01-07 is Saturday (weekday=5)
        df = pd.DataFrame({'publish_time': ['2023-01-07T12:00:00.000Z', '2023-01-09T12:00:00.000Z']})
        result = self.p.engineer_time_features(df)
        assert result.loc[0, 'is_weekend'] == 1
        assert result.loc[1, 'is_weekend'] == 0

    def test_upload_time_bucket(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        assert p._hour_to_bucket(2) == 'Early Morning'
        assert p._hour_to_bucket(7) == 'Morning'
        assert p._hour_to_bucket(14) == 'Afternoon'
        assert p._hour_to_bucket(19) == 'Evening'
        assert p._hour_to_bucket(22) == 'Night'

    def test_weekday_extraction(self):
        df = pd.DataFrame({'publish_time': ['2023-01-02T12:00:00.000Z']})  # Monday
        result = self.p.engineer_time_features(df)
        assert result.loc[0, 'publish_weekday'] == 0  # 0=Monday


# ---------------------------------------------------------------------------
# Test: Tag Count
# ---------------------------------------------------------------------------

class TestTagCount:
    def test_tag_count_pipe_separated(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        df = pd.DataFrame({'tags': ['music|fun|entertainment|live']})
        result = p.engineer_text_features(df)
        assert result.loc[0, 'tag_count'] == 4

    def test_tag_count_none(self):
        p = YouTubePreprocessor.__new__(YouTubePreprocessor)
        p.dataset_path = Path('dummy')
        p.category_json_path = None
        p.category_map = {}
        p.stats = {}
        df = pd.DataFrame({'tags': ['[none]']})
        result = p.engineer_text_features(df)
        assert result.loc[0, 'tag_count'] == 0


# ---------------------------------------------------------------------------
# Test: Feature Engineering
# ---------------------------------------------------------------------------

class TestFeatureEngineering:
    def test_trend_buckets(self):
        df = pd.DataFrame({'trending_duration_days': [1, 2, 5, 10, 20]})
        result = add_trend_buckets(df)
        assert result.loc[0, 'trending_duration_bucket'] == '1_day'
        assert result.loc[1, 'trending_duration_bucket'] == '2-3_days'
        assert result.loc[2, 'trending_duration_bucket'] == '4-7_days'
        assert result.loc[3, 'trending_duration_bucket'] == '8-14_days'
        assert result.loc[4, 'trending_duration_bucket'] == '15+_days'

    def test_view_velocity(self):
        df = pd.DataFrame({'views': [1000000], 'trending_duration_days': [5]})
        result = add_view_velocity(df)
        assert result.loc[0, 'view_velocity'] == 200000.0

    def test_trendpulse_score_range(self):
        df = pd.DataFrame({
            'views': [1000000, 500000, 100000],
            'likes': [80000, 10000, 1000],
            'comment_count': [5000, 1000, 100],
            'engagement_rate': [0.085, 0.022, 0.011],
            'like_rate': [0.08, 0.02, 0.01],
            'comment_rate': [0.005, 0.002, 0.001],
            'tag_count': [8, 4, 2],
            'title_length': [45, 30, 10],
            'trending_duration_days': [10, 5, 1],
        })
        result = compute_trendpulse_score(df)
        assert 'trendpulse_score' in result.columns
        assert (result['trendpulse_score'] >= 0).all()
        assert (result['trendpulse_score'] <= 100).all()

    def test_trendpulse_labels(self):
        df = pd.DataFrame({
            'trendpulse_score': [10, 45, 70, 95]
        })
        # Manually apply label logic
        labels = pd.cut(df['trendpulse_score'], bins=[-0.1, 30, 60, 80, 100],
                        labels=['Low', 'Moderate', 'High', 'Very High'])
        assert labels.iloc[0] == 'Low'
        assert labels.iloc[1] == 'Moderate'
        assert labels.iloc[2] == 'High'
        assert labels.iloc[3] == 'Very High'


# ---------------------------------------------------------------------------
# Test: Data Validators
# ---------------------------------------------------------------------------

class TestDataValidators:
    def test_quality_report_score(self):
        report = DataQualityReport()
        report.add_check('test_check', passed=90, failed=10)
        assert report.quality_score == 90.0

    def test_validate_event_valid(self):
        event = {'video_id': 'abc123', 'title': 'Test Video', 'views': 1000000}
        is_valid, errors = validate_event(event)
        assert is_valid
        assert len(errors) == 0

    def test_validate_event_missing_field(self):
        event = {'title': 'Test Video', 'views': 1000}
        is_valid, errors = validate_event(event)
        assert not is_valid
        assert any('video_id' in e for e in errors)

    def test_validate_event_negative_views(self):
        event = {'video_id': 'abc', 'title': 'Test', 'views': -100}
        is_valid, errors = validate_event(event)
        assert not is_valid

    def test_validate_dataframe(self):
        df = pd.DataFrame({
            'video_id': ['abc', 'def', 'ghi'],
            'views': [1000, 2000, 3000],
            'likes': [100, 200, 300],
            'category_id': [24, 10, 17],
            'engagement_rate': [0.1, 0.2, 0.15],
            'trending_duration_days': [1, 3, 5],
        })
        report = validate_dataframe(df)
        assert report.quality_score > 80

    def test_validate_dataframe_with_negatives(self):
        df = pd.DataFrame({
            'video_id': ['abc'],
            'views': [-100],
            'likes': [-50],
            'category_id': [24],
            'engagement_rate': [0.1],
            'trending_duration_days': [1],
        })
        report = validate_dataframe(df)
        # Should detect negative views
        neg_check = next((c for c in report.checks if c['check'] == 'non_negative_views'), None)
        assert neg_check is not None
        assert neg_check['failed'] > 0


# ---------------------------------------------------------------------------
# Test: Kafka Event Serialization
# ---------------------------------------------------------------------------

class TestKafkaEventSerialization:
    def test_event_json_serializable(self):
        import json
        event = {
            'video_id': 'abc123',
            'title': 'Test Video',
            'category_id': 24,
            'views': 1000000,
            'likes': 80000,
            'engagement_rate': 0.085,
            'trending_duration_days': 5,
            'event_id': 'evt_001',
            'ingestion_timestamp': '2026-10-06T19:00:00',
            'source': 'kaggle_youtube_trending'
        }
        serialized = json.dumps(event)
        deserialized = json.loads(serialized)
        assert deserialized['video_id'] == 'abc123'
        assert deserialized['views'] == 1000000

    def test_event_with_nan_handled(self):
        import json
        import math
        # NaN values should be handled before serialization
        row = {'video_id': 'abc', 'views': 1000, 'likes': None, 'engagement_rate': float('nan')}
        # Clean NaN
        cleaned = {k: (None if (v is None or (isinstance(v, float) and math.isnan(v))) else v) 
                   for k, v in row.items()}
        serialized = json.dumps(cleaned)
        result = json.loads(serialized)
        assert result['likes'] is None
        assert result['engagement_rate'] is None
