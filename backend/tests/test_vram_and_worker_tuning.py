import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import app.services.processor.audio_extractor as audio_extractor
from app.services.processor.tts_generator import TTSGenerator

class TestVramAndWorkerTuning(unittest.TestCase):
    def setUp(self):
        self.tts = TTSGenerator()

    def test_release_audio_separator_empty(self):
        """Kiểm tra release_audio_separator khi chưa nạp separator không gây lỗi"""
        audio_extractor._separator_instance = None
        result = audio_extractor.release_audio_separator()
        self.assertFalse(result)
        self.assertIsNone(audio_extractor._separator_instance)

    def test_release_audio_separator_active(self):
        """Kiểm tra release_audio_separator khi đang có separator trong bộ nhớ"""
        mock_sep = MagicMock()
        audio_extractor._separator_instance = mock_sep
        
        log_messages = []
        result = audio_extractor.release_audio_separator(log_callback=lambda msg: log_messages.append(msg))
        
        self.assertTrue(result)
        self.assertIsNone(audio_extractor._separator_instance)
        self.assertTrue(any("VRAM" in m for m in log_messages))

    def test_get_optimal_workers_cloud_tts(self):
        """Kiểm tra Cloud TTS (Edge, FPT, OpenAI...) giữ nguyên 3 worker"""
        # Edge TTS
        workers_edge = self.tts._get_optimal_workers("edge_namminh")
        self.assertEqual(workers_edge, 3)
        
        # FPT AI
        workers_fpt = self.tts._get_optimal_workers("fpt_banmai")
        self.assertEqual(workers_fpt, 3)

        # OpenAI
        workers_openai = self.tts._get_optimal_workers("openai_onyx")
        self.assertEqual(workers_openai, 3)

    @patch("torch.cuda.is_available")
    @patch("torch.cuda.get_device_properties")
    def test_get_optimal_workers_vieneu_4gb_gpu(self, mock_props, mock_cuda_avail):
        """Kiểm tra VieNeu trên card 4GB VRAM bắt buộc ép về 1 worker tuần tự"""
        mock_cuda_avail.return_value = True
        
        # Giả lập GPU 4GB VRAM (GTX 1050 / GTX 1650)
        device_prop = MagicMock()
        device_prop.total_memory = 4 * 1024 * 1024 * 1024 # 4GB
        mock_props.return_value = device_prop
        
        workers = self.tts._get_optimal_workers("vieneu_Trúc Ly")
        self.assertEqual(workers, 1, "Card 4GB VRAM phải trả về đúng 1 worker để chống tràn VRAM OOM!")

    @patch("torch.cuda.is_available")
    @patch("torch.cuda.get_device_properties")
    def test_get_optimal_workers_vieneu_8gb_gpu(self, mock_props, mock_cuda_avail):
        """Kiểm tra VieNeu trên card 8GB VRAM được cấp 2 worker"""
        mock_cuda_avail.return_value = True
        
        device_prop = MagicMock()
        device_prop.total_memory = 8 * 1024 * 1024 * 1024 # 8GB
        mock_props.return_value = device_prop
        
        workers = self.tts._get_optimal_workers("vieneu_Trúc Ly")
        self.assertEqual(workers, 2)

    @patch("torch.cuda.is_available")
    @patch("torch.cuda.get_device_properties")
    def test_get_optimal_workers_vieneu_16gb_gpu(self, mock_props, mock_cuda_avail):
        """Kiểm tra VieNeu trên card 16GB VRAM được cấp 3 worker tối đa"""
        mock_cuda_avail.return_value = True
        
        device_prop = MagicMock()
        device_prop.total_memory = 16 * 1024 * 1024 * 1024 # 16GB
        mock_props.return_value = device_prop
        
        workers = self.tts._get_optimal_workers("vieneu_Trúc Ly")
        self.assertEqual(workers, 3)

    @patch("torch.cuda.is_available")
    def test_get_optimal_workers_vieneu_cpu(self, mock_cuda_avail):
        """Kiểm tra VieNeu khi chạy CPU trả về 1 worker"""
        mock_cuda_avail.return_value = False
        
        workers = self.tts._get_optimal_workers("vieneu_Trúc Ly")
        self.assertEqual(workers, 1)

if __name__ == '__main__':
    unittest.main()
