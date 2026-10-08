@echo off
echo ==============================================================
echo TrendPulse - Data Engineering & Analytics Pipeline Runner
echo ==============================================================
cd %~dp0\..

echo [1/4] Starting Docker services (Kafka, Hadoop, Postgres, Backend)...
docker-compose up -d
echo Waiting for services to initialize...
timeout /t 30 /nobreak >nul

echo [2/4] Running Python Preprocessing and Analytics...
call python -m pip install -r requirements.txt >nul
call python data\sample\generate_sample.py
call python preprocessing\preprocess.py --input data\sample\sample_youtube_trending.csv --categories data\sample\US_category_id.json --output data\processed\cleaned_videos.csv

echo [3/4] Running MapReduce Jobs in Hadoop...
echo Note: Requires Maven and Hadoop to be accessible locally, or run inside Docker.
echo (Skipping local MapReduce build in this bat script - refer to docs/mapreduce.md)

echo [4/4] Starting Dashboard...
cd dashboard
call cmd /c "npm install"
start cmd /c "npm run dev"

echo ==============================================================
echo Pipeline is running!
echo Dashboard: http://localhost:5173
echo API Docs:  http://localhost:8000/docs
echo ==============================================================
pause
