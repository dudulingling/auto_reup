import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import SessionLocal
from app.models.history import VideoHistory
from app.models.upload_schedule import UploadSchedule

db = SessionLocal()
v = db.query(VideoHistory).filter(VideoHistory.original_name.like('%68358%')).first()
if v:
    print(f'Status: {v.status}, Process_config: {v.process_config}')
else:
    print('Not found')
