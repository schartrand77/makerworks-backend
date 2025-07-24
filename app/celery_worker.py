# celery_worker.py — MakerWorks task runner

import os
import logging
from celery import Celery
from dotenv import load_dotenv
from kombu.serialization import register
from kombu import Exchange, Queue

# ─────────────────────────────────────────────────────────────
# Load environment variables from .env if present
# ─────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────
# Redis: Broker + Result Backend
# ─────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

CELERY_REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ─────────────────────────────────────────────────────────────
# Celery App Config
# ─────────────────────────────────────────────────────────────
celery_app = Celery(
    "makerworks",
    broker=CELERY_REDIS_URL,
    backend=CELERY_REDIS_URL,
    include=[
        "app.tasks.render",
        "app.tasks.email",
        "app.tasks.analytics",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
    ),
    worker_send_task_events=True,
    task_send_sent_event=True,
    enable_utc=True,
    timezone='UTC',
    worker_enable_remote_control=True,
)

# ─────────────────────────────────────────────────────────────
# Prometheus Metrics Setup via Celery Prometheus Exporter
# ─────────────────────────────────────────────────────────────
try:
    import prometheus_client
    from prometheus_client import start_http_server

    PROMETHEUS_METRICS_PORT = int(os.getenv("PROMETHEUS_METRICS_PORT", 9808))
    start_http_server(PROMETHEUS_METRICS_PORT)
    logging.info(f"📈 Prometheus metrics exposed at :{PROMETHEUS_METRICS_PORT}")
except ImportError:
    logging.warning("Prometheus client not installed — metrics disabled")

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    logger.info("🚀 Starting Celery worker with broker: %s", CELERY_REDIS_URL)
    celery_app.start()
