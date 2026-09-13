import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
from app.db.session import SessionLocal
from app.models.social_account import SocialAccount
from app.models.upload_schedule import UploadSchedule
from app.models.history import VideoHistory

db = SessionLocal()
videos = db.query(VideoHistory).filter(VideoHistory.original_name.like('%16235.mp4')).all()

for video in videos:
    print("Video ID:", video.id)
    print("Upload History JSON:", video.upload_history)
    print("Schedules:")
    for sch in video.schedules:
        print(f" - Sch ID: {sch.id}, Account ID: {sch.account_id}, Status: {sch.status}")
    print("---")
