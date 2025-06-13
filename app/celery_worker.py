import os
from celery import Celery

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "makerworks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
    include=["app.tasks.render"],  # where your Blender task will live
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
)