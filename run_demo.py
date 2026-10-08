"""
TrendPulse - Full End-to-End Orchestration Demo Script
Runs the entire pipeline sequentially (without Docker dependencies) for demonstration.
"""
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("trendpulse.demo")


def run_step(name, func, *args, **kwargs):
    logger.info(f"--- STARTING: {name} ---")
    start = time.time()
    try:
        res = func(*args, **kwargs)
        logger.info(f"--- COMPLETED: {name} in {time.time() - start:.2f}s ---\n")
        return res
    except Exception as e:
        logger.error(f"--- FAILED: {name} - {e} ---")
        raise


def run_pipeline():
    logger.info("Initializing TrendPulse End-to-End Demo Pipeline...")

    # 1. Generate Sample Data
    from data.sample.generate_sample import generate_sample_dataset
    sample_path = "data/sample/sample_youtube_trending.csv"
    cat_path = "data/sample/US_category_id.json"
    if not os.path.exists(sample_path):
        run_step("Data Generation", generate_sample_dataset, num_videos=1000, output_path=sample_path)
    else:
        logger.info("Sample data already exists. Skipping generation.")

    # 2. Preprocessing
    from preprocessing.preprocess import YouTubePreprocessor
    from preprocessing.feature_engineering import run_feature_engineering
    from preprocessing.validators import validate_dataframe

    def preprocess_step():
        preprocessor = YouTubePreprocessor(dataset_path=sample_path, category_json_path=cat_path)
        df_clean = preprocessor.run()
        df_feat = run_feature_engineering(df_clean)
        report = validate_dataframe(df_feat)
        out_path = Path("data/processed/cleaned_videos.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_feat.to_csv(out_path, index=False)
        logger.info(f"Saved {len(df_feat)} rows to {out_path}")
        return df_feat, report

    df_clean, dq_report = run_step("Data Preprocessing & Feature Engineering", preprocess_step)

    # 3. Analytics
    from analytics.correlation_engine import compute_correlations
    from analytics.factor_ranking import rank_factors
    from analytics.trend_score import calculate_scores
    from analytics.anomaly_detection import detect_breakout_videos

    df_scored = run_step("Trend Score Calculation", calculate_scores, df_clean)
    corr_df = run_step("Correlation Analysis", compute_correlations, df_scored)
    factors_df = run_step("Factor Ranking", rank_factors, corr_df)
    anomalies_df = run_step("Anomaly Detection", detect_breakout_videos, df_scored)

    # 4. Database Loading
    from backend.database.connection import engine, check_connection
    from backend.models import db_models
    from backend.database import loader

    def load_db_step():
        if not check_connection():
            logger.warning("PostgreSQL not available. Skipping database load.")
            return False
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db_models.Base.metadata.create_all(bind=engine)
        
        loader.load_videos(df_scored, engine)
        loader.load_category_analytics(df_scored, engine)
        loader.load_upload_time_analytics(df_scored, engine)
        loader.load_title_analytics(df_scored, engine)
        loader.load_trending_factors(factors_df, engine)
        loader.load_breakout_videos(anomalies_df, engine)
        loader.load_trend_scores(df_scored, engine)
        loader.load_data_quality(dq_report, engine)
        loader.load_pipeline_metrics({
            "analytics_records": len(df_scored),
            "stage": "demo_pipeline", "status": "done"
        }, engine)
        return True

    run_step("Database Loading", load_db_step)
    logger.info("TrendPulse End-to-End Demo Completed Successfully!")


if __name__ == "__main__":
    run_pipeline()
