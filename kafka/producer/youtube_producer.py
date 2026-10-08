"""
TrendPulse - Kafka Producer
Reads cleaned YouTube trending data and streams events to Kafka.
"""
import os, sys, json, time, uuid, logging, math
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "producer.log", "a")]
)
logger = logging.getLogger("trendpulse.producer")

TOPIC = os.getenv("KAFKA_TOPIC", "youtube-trending-events")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DELAY = float(os.getenv("PRODUCER_DELAY_SECONDS", "0.05"))
DATASET_PATH = os.getenv("DATASET_PATH", "data/processed/cleaned_videos.csv")

NUMERIC_COLS = [
    "views","likes","dislikes","comment_count","engagement_rate","engagement_score",
    "like_rate","comment_rate","title_length","title_word_count","description_length",
    "tag_count","uppercase_ratio","punctuation_count","question_mark_count",
    "exclamation_count","publish_hour","publish_weekday","is_weekend",
    "trending_duration_days","trendpulse_score","view_velocity",
]


def clean_value(v):
    """Make a value JSON-safe."""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def row_to_event(row: dict, idx: int) -> dict:
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "ingestion_timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "kaggle_youtube_trending",
        "sequence": idx,
    }
    for col in ["video_id","title","channel_title","category_id","category_name",
                "publish_time","publish_date","trending_date","tags",
                "upload_time_bucket","publish_weekday_name","title_length_bucket",
                "trending_duration_bucket","trendpulse_label","first_trending_date",
                "last_trending_date","record_id","processed_at"]:
        if col in row:
            event[col] = str(row[col]) if row[col] is not None else None
    for col in NUMERIC_COLS:
        if col in row:
            event[col] = clean_value(row.get(col))
    for col in ["comments_disabled","ratings_disabled","video_error_or_removed"]:
        if col in row:
            event[col] = bool(row.get(col, 0))
    return event


class YouTubeProducer:
    def __init__(self, dataset_path: str = DATASET_PATH, replay: bool = False):
        self.dataset_path = Path(dataset_path)
        self.replay = replay
        self.producer = None
        self.stats = {"sent": 0, "failed": 0, "start_time": None}
        self._init_kafka()

    def _init_kafka(self):
        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all", retries=3,
                max_block_ms=10000,
                request_timeout_ms=15000,
            )
            logger.info(f"Kafka producer connected to {BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Kafka unavailable: {e}")
            logger.warning("Running in FILE-ONLY mode (no Kafka).")
            self.producer = None

    def load_data(self) -> pd.DataFrame:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        df = pd.read_csv(self.dataset_path, low_memory=False)
        logger.info(f"Loaded {len(df)} records from {self.dataset_path}")
        return df

    def _send_event(self, event: dict):
        if self.producer:
            future = self.producer.send(TOPIC, value=event)
            future.get(timeout=10)

    def produce(self, delay: float = DELAY):
        df = self.load_data()
        self.stats["start_time"] = time.time()
        total = len(df)
        logger.info(f"Starting producer: {total} records, delay={delay}s, topic={TOPIC}")
        print(f"\n{'='*60}")
        print(f" TrendPulse Kafka Producer")
        print(f" Topic: {TOPIC}  |  Records: {total}  |  Delay: {delay}s")
        print(f"{'='*60}\n")
        for idx, row in df.iterrows():
            try:
                event = row_to_event(row.to_dict(), idx)
                self._send_event(event)
                self.stats["sent"] += 1
            except Exception as e:
                logger.warning(f"Failed to send event {idx}: {e}")
                self.stats["failed"] += 1
            if self.stats["sent"] % 100 == 0 and self.stats["sent"] > 0:
                elapsed = time.time() - self.stats["start_time"]
                rate = self.stats["sent"] / elapsed if elapsed > 0 else 0
                pct = self.stats["sent"] / total * 100
                print(f"  Progress: {self.stats['sent']}/{total} ({pct:.1f}%)  "
                      f"Rate: {rate:.1f} msg/s  Failed: {self.stats['failed']}")
            if delay > 0:
                time.sleep(delay)
        if self.producer:
            self.producer.flush()
        elapsed = time.time() - self.stats["start_time"]
        print(f"\n{'='*60}")
        print(f" Producer Done! Sent: {self.stats['sent']}  Failed: {self.stats['failed']}")
        print(f" Total time: {elapsed:.1f}s  Avg rate: {self.stats['sent']/max(elapsed,1):.1f} msg/s")
        print(f"{'='*60}")
        return self.stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TrendPulse Kafka Producer")
    parser.add_argument("--input", default=DATASET_PATH)
    parser.add_argument("--delay", type=float, default=DELAY)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    producer = YouTubeProducer(dataset_path=args.input, replay=args.replay)
    producer.produce(delay=args.delay)
