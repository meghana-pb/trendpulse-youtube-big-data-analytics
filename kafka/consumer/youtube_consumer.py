"""
TrendPulse - Kafka Consumer
Subscribes to youtube-trending-events and writes to HDFS (or local fallback).
"""
import os, sys, json, logging, time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "consumer.log", "a")]
)
logger = logging.getLogger("trendpulse.consumer")

TOPIC = os.getenv("KAFKA_TOPIC", "youtube-trending-events")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "trendpulse-consumer-group")
HDFS_HOST = os.getenv("HDFS_NAMENODE_HOST", "localhost")
HDFS_PORT = int(os.getenv("HDFS_NAMENODE_PORT", "9000"))
HDFS_BASE = os.getenv("HDFS_BASE_PATH", "/youtube-trending")
FALLBACK_DIR = Path("data/hdfs_fallback")


def get_hdfs_path(layer: str = "raw") -> str:
    now = datetime.utcnow()
    return f"{HDFS_BASE}/{layer}/year={now.year}/month={now.month:02d}/day={now.day:02d}"


def get_local_path(layer: str = "raw") -> Path:
    now = datetime.utcnow()
    p = FALLBACK_DIR / layer / f"year={now.year}" / f"month={now.month:02d}" / f"day={now.day:02d}"
    p.mkdir(parents=True, exist_ok=True)
    return p


class HDFSWriter:
    def __init__(self):
        self.client = None
        self._init_hdfs()

    def _init_hdfs(self):
        try:
            from hdfs import InsecureClient
            url = f"http://{HDFS_HOST}:9870"
            self.client = InsecureClient(url, user="root")
            self.client.status("/")
            logger.info(f"HDFS connected: {url}")
        except Exception as e:
            logger.warning(f"HDFS unavailable ({e}). Using local fallback.")
            self.client = None

    def write_batch(self, records: list, layer: str = "raw"):
        ts = datetime.utcnow().strftime("%H%M%S_%f")[:12]
        content = "\n".join(json.dumps(r) for r in records) + "\n"
        if self.client:
            try:
                hdfs_path = get_hdfs_path(layer)
                filename = f"{hdfs_path}/part_{ts}.jsonl"
                with self.client.write(filename, encoding="utf-8", overwrite=True, append=False) as writer:
                    writer.write(content)
                logger.debug(f"Written {len(records)} records to HDFS: {filename}")
                return filename
            except Exception as e:
                logger.error(f"HDFS write failed: {e}. Falling back to local.")
        # Local fallback
        local_path = get_local_path(layer)
        filename = local_path / f"part_{ts}.jsonl"
        filename.write_text(content, encoding="utf-8")
        logger.debug(f"Written {len(records)} records locally: {filename}")
        return str(filename)


class YouTubeConsumer:
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.hdfs_writer = HDFSWriter()
        self.stats = {"received": 0, "failed": 0, "batches_written": 0, "start_time": None}
        self.consumer = None
        self._init_consumer()

    def _init_consumer(self):
        try:
            from kafka import KafkaConsumer
            self.consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVERS.split(","),
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: m.decode("utf-8"),
                consumer_timeout_ms=30000,
                max_poll_records=100,
            )
            logger.info(f"Kafka consumer connected. Subscribed to: {TOPIC}")
        except Exception as e:
            logger.error(f"Kafka unavailable: {e}")
            self.consumer = None

    def _parse_message(self, raw_msg, partition: int, offset: int) -> dict:
        event = json.loads(raw_msg)
        event["consumer_received_at"] = datetime.utcnow().isoformat() + "Z"
        event["kafka_partition"] = partition
        event["kafka_offset"] = offset
        return event

    def consume(self, max_messages: int = 0):
        if not self.consumer:
            logger.error("No Kafka consumer. Cannot consume messages.")
            return self.stats
        self.stats["start_time"] = time.time()
        batch = []
        logger.info(f"Starting consumer... (max_messages={max_messages or 'unlimited'})")
        print(f"\n{'='*60}")
        print(f" TrendPulse Kafka Consumer")
        print(f" Topic: {TOPIC}  |  Group: {GROUP_ID}")
        print(f"{'='*60}\n")
        try:
            for message in self.consumer:
                try:
                    event = self._parse_message(message.value, message.partition, message.offset)
                    batch.append(event)
                    self.stats["received"] += 1
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"Malformed message at offset {message.offset}: {e}")
                    self.stats["failed"] += 1
                if len(batch) >= self.batch_size:
                    self.hdfs_writer.write_batch(batch, layer="raw")
                    self.stats["batches_written"] += 1
                    batch = []
                if self.stats["received"] % 100 == 0 and self.stats["received"] > 0:
                    elapsed = time.time() - self.stats["start_time"]
                    rate = self.stats["received"] / elapsed if elapsed > 0 else 0
                    print(f"  Received: {self.stats['received']}  "
                          f"Rate: {rate:.1f} msg/s  Batches written: {self.stats['batches_written']}")
                if max_messages > 0 and self.stats["received"] >= max_messages:
                    break
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user.")
        finally:
            if batch:
                self.hdfs_writer.write_batch(batch, layer="raw")
                self.stats["batches_written"] += 1
            self.consumer.close()
        print(f"\n Consumer done. Received={self.stats['received']}  Failed={self.stats['failed']}")
        return self.stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TrendPulse Kafka Consumer")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--max-messages", type=int, default=0)
    args = parser.parse_args()
    consumer = YouTubeConsumer(batch_size=args.batch_size)
    consumer.consume(max_messages=args.max_messages)
