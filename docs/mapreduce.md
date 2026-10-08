# MapReduce Implementation Guide

TrendPulse uses Apache Hadoop MapReduce for distributed processing of the dataset across 5 specific analytical dimensions.

## Job 1: Category Analysis
- **Mapper**: Extracts `category_id` as the key. Outputs views, likes, comments, engagement rate, and trending duration.
- **Reducer**: Aggregates totals and computes averages per category. Identifies max/min trending duration.

## Job 2: Upload Time Analysis
- **Mapper**: Extracts `publish_hour` (0-23) as the key. Outputs metrics.
- **Reducer**: Computes average views and trending duration per hour of the day to identify optimal upload windows.

## Job 3: Title Length Analysis
- **Mapper**: Extracts `title_length_bucket` (e.g., "41-60") as the key.
- **Reducer**: Calculates average engagement and trending duration per title length bucket.

## Job 4: Engagement Analysis
- **Mapper**: Buckets videos into Low/Medium/High/Very_High engagement based on the `engagement_rate`. Uses this bucket as the key.
- **Reducer**: Analyzes how engagement buckets correlate with trending duration.

## Job 5: Trending Duration Analysis
- **Mapper**: Uses the `trending_duration_bucket` (e.g., "1_day", "4-7_days") as the key.
- **Reducer**: Aggregates average views, engagement, and title lengths for videos that trend for specific durations.

## Build and Execute
Navigate to the `hadoop/` directory.
```bash
mvn clean install
hadoop jar category/target/category-analysis-1.0.0.jar com.trendpulse.CategoryDriver /input/path /output/path
```
