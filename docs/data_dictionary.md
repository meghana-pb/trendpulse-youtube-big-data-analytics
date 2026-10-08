# Data Dictionary

## Raw Input Schema (YouTube Trending Dataset)
- `video_id`: Unique identifier for the video.
- `trending_date`: Date the video trended.
- `title`: Video title.
- `channel_title`: Channel name.
- `category_id`: Numeric category identifier.
- `publish_time`: Timestamp of video publication.
- `views`, `likes`, `dislikes`, `comment_count`: Engagement metrics.
- `tags`: Pipe-separated string of video tags.

## Engineered Features
- `engagement_rate`: (likes + comment_count) / views.
- `like_rate`: likes / views.
- `comment_rate`: comment_count / views.
- `title_length`: Number of characters in the title.
- `title_word_count`: Number of words in the title.
- `tag_count`: Number of tags used.
- `publish_hour`: Hour of the day the video was published (0-23).
- `is_weekend`: Boolean flag (True if published on Saturday/Sunday).
- `upload_time_bucket`: Categorical bucket (e.g., 'Morning', 'Afternoon').
- `trending_duration_days`: Number of unique days the video appeared on the trending list.
- `view_velocity`: views / trending_duration_days.

## Analytics Metrics
- `trendpulse_score`: A proprietary 0-100 score estimating the overall strength of a video's trending performance.
- `anomaly_score`: A score denoting how statistically irregular a video's performance is compared to the dataset mean.
