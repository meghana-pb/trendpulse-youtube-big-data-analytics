# TrendPulse - System Architecture

## Overview
TrendPulse is a complete Big Data Engineering and Analytics platform designed to analyze the lifecycle and attributes of trending YouTube videos. The architecture spans data ingestion, distributed storage, streaming, analytics, and a modern frontend dashboard.

## Components

### 1. Data Ingestion & Streaming (Apache Kafka)
- **Producer**: Reads raw or preprocessed datasets and streams them as JSON events into the `youtube-trending-events` topic.
- **Consumer**: Subscribes to the topic in real-time, batches events, and writes them to distributed storage.

### 2. Distributed Storage & Processing (Hadoop HDFS & MapReduce)
- **HDFS**: Stores batched JSON events in a partitioned structure (`year=YYYY/month=MM/day=DD`).
- **MapReduce Jobs**: 5 Java-based MapReduce jobs process the massive datasets for specific analytical dimensions:
  - Category Analysis
  - Upload Time Analysis
  - Title Length Analysis
  - Engagement Analysis
  - Trending Duration Analysis

### 3. Analytics & Machine Learning Pipeline (Python)
- **Preprocessing**: Handles missing values, unifies schemas, and extracts temporal/textual features.
- **Feature Engineering**: Calculates velocity, normalizes metrics, and logs distributions.
- **Correlation Engine**: Computes statistical significance (Pearson, Spearman, ANOVA) and Mutual Information.
- **Anomaly Detection**: Identifies "breakout" videos using IQR and z-scores.
- **Trend Score**: Generates a composite score (0-100) based on reach and engagement.

### 4. Serving Layer (PostgreSQL & FastAPI)
- **Database**: PostgreSQL 16 stores the aggregated analytical results and specific video metrics.
- **Backend API**: FastAPI provides a high-performance RESTful API using SQLAlchemy ORM and Pydantic validation.

### 5. Frontend Dashboard (React & Vite)
- **Framework**: React 18 with Vite.
- **UI/Charts**: Tremor (React components for building dashboards) and Tailwind CSS.
- **Pages**: Overview, Trending Factors, Content Strategy, Video Explorer, Breakout Videos, and Pipeline Monitor.
