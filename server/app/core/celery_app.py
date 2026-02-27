"""
Celery application configuration for async task processing
"""

import os
import platform

# Fix macOS fork() crash with Objective-C runtime
if platform.system() == "Darwin":
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "code_rag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.indexing"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Use solo pool on macOS to avoid fork() crashes with ChromaDB
    worker_pool="solo" if platform.system() == "Darwin" else "prefork",
)
