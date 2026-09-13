import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from app.db.session import SessionLocal
from app.models.upload_schedule import UploadSchedule

db = SessionLocal()
schedules = db.query(UploadSchedule).filter(UploadSchedule.video_history_id == 119).all()

for sch in schedules:
    print(f"Sch ID: {sch.id}, Account ID: {sch.account_id}, Status: {sch.status}")
print("Done")
