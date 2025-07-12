# celery_worker.py — MakerWorks task runner

from celery import Celery

# ─────────────────────────────────────────────────────────────
# Redis: default local Redis on db 0
# ─────────────────────────────────────────────────────────────

CELERY_REDIS_URL = "redis://localhost:6379/0"

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
