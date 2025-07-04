# celery_worker.py — MakerWorks task runner

import os

from celery import Celery

# ─────────────────────────────────────────────────────────────
# Redis: default local Redis on db 0
# ─────────────────────────────────────────────────────────────

# Connection URL for Celery's broker and result backend.
# Defaults to the docker-compose Redis instance but can be overridden via the
# CELERY_REDIS_URL environment variable.
CELERY_REDIS_URL = os.environ.get("CELERY_REDIS_URL", "redis://redis:6379/0")

# ─────────────────────────────────────────────────────────────
# Celery App
# ─────────────────────────────────────────────────────────────

celery_app = Celery(
    "makerworks",
    broker=CELERY_REDIS_URL,
    backend=CELERY_REDIS_URL,
    include=["app.tasks.render"],  # Task modules auto-imported
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
