#!/bin/bash
echo "=============================================================="
echo "TrendPulse - Data Engineering & Analytics Pipeline Runner"
echo "=============================================================="
cd "$(dirname "$0")/.."

echo "[1/4] Starting Docker services (Kafka, Hadoop, Postgres, Backend)..."
docker-compose up -d
echo "Waiting for services to initialize..."
sleep 30

echo "[2/4] Running Python Preprocessing and Analytics..."
python3 -m pip install -r requirements.txt
python3 data/sample/generate_sample.py
python3 preprocessing/preprocess.py --input data/sample/sample_youtube_trending.csv --categories data/sample/US_category_id.json --output data/processed/cleaned_videos.csv

echo "[3/4] Running Orchestration (Loads DB)..."
python3 run_demo.py

echo "[4/4] Starting Dashboard..."
cd dashboard
npm install
npm run dev &

echo "=============================================================="
echo "Pipeline is running!"
echo "Dashboard: http://localhost:5173"
echo "API Docs:  http://localhost:8000/docs"
echo "=============================================================="
