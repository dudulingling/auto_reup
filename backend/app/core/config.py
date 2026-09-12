import os

# Đường dẫn thư mục gốc của toàn bộ dự án
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Thư mục lưu trữ dữ liệu tập trung (DB, files, video...)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Cấu hình Redis (Single Source of Truth)
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Cấu hình Google Colab T4 GPU Worker
COLAB_GPU_URL = os.environ.get("COLAB_GPU_URL", "").rstrip("/")
USE_COLAB_GPU = os.environ.get("USE_COLAB_GPU", "False").lower() == "true"

# Đảm bảo thư mục tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

