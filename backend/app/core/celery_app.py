import os
import sys
from celery import Celery
from celery.signals import worker_process_init

# Ensure UTF-8 output on Windows consoles to prevent UnicodeEncodeError on Chinese/emojis
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core.config import REDIS_URL

celery_app = Celery(
    "autoreup_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.crawler_tasks", "app.tasks.processor_tasks", "app.tasks.uploader_tasks", "app.tasks.health_tasks", "app.tasks.faceless_tasks", "app.tasks.ai_studio_tasks"]
)

# Tối ưu hóa cấu hình Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # Giới hạn 1 task tối đa 1 tiếng (dành cho video nặng)
    worker_max_tasks_per_child=50, # Restart worker sau 50 tasks để giải phóng RAM/VRAM
)

# Cấu hình định kỳ cho Celery Beat
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    "check-scheduled-uploads-every-minute": {
        "task": "check_scheduled_uploads",
        "schedule": crontab(minute="*/10"), # Chạy mỗi 10 phút
    },
    "check-account-health-every-hour": {
        "task": "check_all_accounts_health_task",
        "schedule": crontab(minute="0"), # Chạy mỗi đầu giờ
    }
}

@worker_process_init.connect
def _fix_cudnn_on_worker_start(**kwargs):
    """Disable cuDNN/Flash SDP at worker boot to prevent Error 127.
    
    onnxruntime-gpu 1.17 bundles cuDNN DLLs that conflict with
    PyTorch 2.4+cu124 on Windows. Disabling these backends forces
    PyTorch to use the math-only SDP path which is stable.
    """
    try:
        import torch
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
    except Exception:
        pass
