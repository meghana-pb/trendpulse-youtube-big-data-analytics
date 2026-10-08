# Project Methodology & Analytical Approach

## Objective
The goal of this project is not to build a simple CRUD app, but to demonstrate a robust Big Data Engineering pipeline capable of ingesting, processing, and analyzing large datasets to extract meaningful, data-driven insights about YouTube trending videos.

## 1. Data Processing Strategy
Instead of loading everything into memory (which fails for Big Data), the architecture relies on streaming (Kafka) and distributed processing (Hadoop MapReduce). For immediate analytics serving, data is aggregated and stored in a relational database (PostgreSQL).

## 2. Statistical Correlation
The `Correlation Engine` computes multiple metrics to evaluate factor importance:
- **Pearson's r**: Linear correlation for continuous variables.
- **Spearman's rank**: Monotonic relationship evaluation.
- **ANOVA F-statistic & Eta-squared**: Used for categorical variables (like `category_id` or `publish_weekday`) to measure group variance against the continuous target (`trending_duration`).
- **Mutual Information**: Captures non-linear dependencies.

## 3. Factor Ranking
Features are ranked based on a composite score derived from normalized correlation strength, effect size, and statistical significance (p-value).

## 4. Anomaly Detection
Breakout videos are identified using Interquartile Range (IQR) and Z-score methods across multiple dimensions (views, engagement rate, duration).
