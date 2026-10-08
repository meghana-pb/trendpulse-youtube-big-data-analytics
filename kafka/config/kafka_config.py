"""
TrendPulse - Kafka Configuration
"""
import os
from dotenv import load_dotenv
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "youtube-trending-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "trendpulse-consumer-group")
KAFKA_AUTO_OFFSET_RESET = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")

def get_producer_config() -> dict:
    return {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS.split(","),
        "value_serializer": None,
        "acks": "all",
        "retries": 3,
        "max_block_ms": 10000,
        "request_timeout_ms": 15000,
    }

def get_consumer_config() -> dict:
    return {
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS.split(","),
        "group_id": KAFKA_GROUP_ID,
        "auto_offset_reset": KAFKA_AUTO_OFFSET_RESET,
        "enable_auto_commit": True,
        "auto_commit_interval_ms": 1000,
        "max_poll_records": 100,
        "session_timeout_ms": 30000,
    }
