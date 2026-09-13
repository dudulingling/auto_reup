import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.api.upload_schedule import UploadScheduleCreate, create_schedule
from app.tasks.uploader_tasks import execute_upload, warmup_account_task
from app.services.uploader.base_engine import TaskAbortedByUser
from app.services.uploader.adb_engine import ADBUploader
from app.services.uploader.warmup_engine import AdbWarmupEngine

class TestCancellationAndDuplicate(unittest.TestCase):

    def test_upload_schedule_schema(self):
        data = {
            "video_history_id": 1,
            "account_id": 2,
            "caption": "Test caption",
            "hashtags": "#test",
            "allow_duplicate": True
        }
        obj = UploadScheduleCreate(**data)
        self.assertTrue(obj.allow_duplicate)
        self.assertEqual(obj.video_history_id, 1)

        data_default = {
            "video_history_id": 1,
            "account_id": 2,
        }
        obj_default = UploadScheduleCreate(**data_default)
        self.assertFalse(obj_default.allow_duplicate)

    def test_create_schedule_duplicate_blocked(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(id=1),  # video
            MagicMock(id=2),  # account
            MagicMock(id=99), # existing schedule
        ]
        
        req = UploadScheduleCreate(video_history_id=1, account_id=2, allow_duplicate=False)
        with self.assertRaises(HTTPException) as cm:
            create_schedule(req, db=mock_db)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("đã được lên lịch cho tài khoản này", cm.exception.detail)

    def test_create_schedule_duplicate_allowed(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(id=1),  # video
            MagicMock(id=2),  # account
        ]
        
        req = UploadScheduleCreate(video_history_id=1, account_id=2, allow_duplicate=True)
        with patch("app.tasks.uploader_tasks.execute_upload.delay") as mock_task:
            created = create_schedule(req, db=mock_db)
            self.assertTrue(mock_db.add.called)
            self.assertTrue(mock_db.commit.called)

    def test_execute_upload_skips_when_schedule_paused(self):
        with patch("app.tasks.uploader_tasks.get_db_session") as mock_get_db, \
             patch("app.core.redis_pool.get_sync_redis") as mock_get_redis, \
             patch("app.services.uploader.adb_engine.ADBUploader") as mock_adb:
            
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_schedule = MagicMock(status="paused")
            mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
            mock_get_redis.return_value.get.return_value = None

            execute_upload(123)
            self.assertFalse(mock_adb.called)

    def test_execute_upload_skips_when_redis_stop_flag(self):
        with patch("app.tasks.uploader_tasks.get_db_session") as mock_get_db, \
             patch("app.core.redis_pool.get_sync_redis") as mock_get_redis, \
             patch("app.services.uploader.adb_engine.ADBUploader") as mock_adb:
            
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_schedule = MagicMock(status="pending")
            mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
            mock_get_redis.return_value.get.return_value = "stop"

            execute_upload(123)
            self.assertFalse(mock_adb.called)

    def test_warmup_task_skips_when_stop_flag(self):
        with patch("app.tasks.uploader_tasks.get_db_session") as mock_get_db, \
             patch("app.core.redis_pool.get_sync_redis") as mock_get_redis, \
             patch("app.services.uploader.warmup_engine.WarmupEngineFactory.get_engine") as mock_factory:
            
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_redis.return_value.get.return_value = "1"

            warmup_account_task({"id": 456, "username": "test_user"})
            self.assertFalse(mock_factory.called)

    def test_adb_uploader_check_abort_raises(self):
        uploader = ADBUploader({"auth_data": "127.0.0.1:5555"}, schedule_id=999)
        with patch("app.core.redis_pool.get_sync_redis") as mock_get_redis, \
             patch("subprocess.run") as mock_subproc:
            mock_get_redis.return_value.get.return_value = "stop"
            with self.assertRaises(TaskAbortedByUser):
                uploader._check_abort()
            # Should have pressed HOME key to reset device UI
            self.assertTrue(mock_subproc.called)

    def test_warmup_engine_aborts_immediately(self):
        engine = AdbWarmupEngine({"id": 789, "device_id": "127.0.0.1:5555", "platform": "tiktok"})
        with patch("app.core.redis_pool.get_sync_redis") as mock_get_redis, \
             patch("subprocess.run") as mock_subproc:
            mock_subproc.return_value = MagicMock(
                returncode=0,
                stdout="127.0.0.1:5555\tdevice\nPhysical size: 720x1280\n",
                stderr=""
            )
            mock_get_redis.return_value.get.return_value = "1"
            engine.warmup()
            # Must have sent keyevent 3 on abort / completion
            self.assertTrue(mock_subproc.called)

if __name__ == "__main__":
    unittest.main()
