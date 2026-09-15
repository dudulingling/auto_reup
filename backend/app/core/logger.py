import logging
import logging.handlers
import os
import sys

# Đảm bảo console Windows hỗ trợ UTF-8 tránh lỗi charmap với tiếng Việt
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import glob
from datetime import datetime


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Tên file log theo phiên làm việc (Timestamp lúc khởi động)
_STARTUP_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_LOG_FILE = os.path.join(LOG_DIR, f"session_{_STARTUP_TIME}.log")
LATEST_LOG_FILE = os.path.join(LOG_DIR, "latest.log")


def _cleanup_old_logs(log_dir: str, max_sessions: int = 15):
    """Giữ lại tối đa max_sessions phiên gần nhất, tự động xóa các file log phiên cũ hơn hoặc bị rỗng (0 bytes)."""
    try:
        session_files = sorted(glob.glob(os.path.join(log_dir, "session_*.log")), key=os.path.getmtime)
        # Xóa các file rỗng 0-byte cũ (tránh làm đầy thư mục logs bởi các phiên import)
        for f in session_files:
            try:
                if os.path.exists(f) and os.path.getsize(f) == 0 and f != SESSION_LOG_FILE:
                    os.remove(f)
            except Exception:
                pass

        # Cập nhật lại danh sách sau khi xóa file rỗng
        session_files = sorted(glob.glob(os.path.join(log_dir, "session_*.log")), key=os.path.getmtime)
        if len(session_files) > max_sessions:
            for old_file in session_files[:-max_sessions]:
                try:
                    os.remove(old_file)
                except Exception:
                    pass
    except Exception:
        pass


# Tự động dọn dẹp các phiên log cũ
_cleanup_old_logs(LOG_DIR, max_sessions=15)

# Standard formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 1. Handler ghi vào file của phiên hiện tại (delay=True để không sinh file 0-byte khi chưa có log)
session_handler = logging.FileHandler(SESSION_LOG_FILE, encoding="utf-8", mode="a", delay=True)
session_handler.setFormatter(formatter)

# 2. Handler ghi vào latest.log để tiện tra cứu trực tiếp phiên mới nhất
latest_handler = logging.FileHandler(LATEST_LOG_FILE, encoding="utf-8", mode="a", delay=True)
latest_handler.setFormatter(formatter)

# 3. Console output (hiển thị trên terminal Uvicorn / Celery)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Tránh gắn handler trùng lặp khi hàm được gọi nhiều lần
    if not logger.handlers:
        logger.addHandler(session_handler)
        logger.addHandler(latest_handler)
        logger.addHandler(stream_handler)
        # Ngăn chặn propagation tránh duplicate logs với root logger của uvicorn
        logger.propagate = False

    return logger

