import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.processor.subtitle_polisher import SubtitlePolisher, STYLE_PRESETS
from app.schemas.processor_config import VideoProcessingConfig

class TestSubtitlePolisher(unittest.TestCase):
    def setUp(self):
        self.polisher = SubtitlePolisher()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_style_presets_integrity(self):
        """Kiểm tra sự đầy đủ của 4 preset phong cách kịch bản"""
        expected_keys = ["tiktok_viral", "reviewer", "storytelling", "formal"]
        for key in expected_keys:
            self.assertIn(key, STYLE_PRESETS)
            preset = STYLE_PRESETS[key]
            self.assertIn("name", preset)
            self.assertIn("system_role", preset)
            self.assertIn("guidelines", preset)

    def test_build_prompt_contains_critical_rules(self):
        """Kiểm tra prompt chứa đầy đủ các yêu cầu cốt lõi: hàn gắn câu cụt, TTS cadence, độ dài thị giác"""
        sample_srt = "1\n00:00:01,000 --> 00:00:02,000\nCái món này là\n\n"
        prompt = self.polisher.build_prompt(sample_srt, style="tiktok_viral")
        
        self.assertIn("TikTok Viral", prompt)
        self.assertIn("Hàn gắn câu cụt", prompt)
        self.assertIn("Tối ưu nhịp thở cho Giọng đọc AI", prompt)
        self.assertIn("5 đến 8 từ", prompt)
        self.assertIn(sample_srt.strip(), prompt)

    def test_normalize_timeline(self):
        """Kiểm tra thuật toán chuẩn hóa và bảo toàn tính liên tục của mốc thời gian"""
        import pysrt
        
        orig_content = (
            "1\n00:00:01,000 --> 00:00:02,000\nĐoạn 1\n\n"
            "2\n00:00:02,500 --> 00:00:04,000\nĐoạn 2\n\n"
        )
        polished_content = (
            "1\n00:00:00,500 --> 00:00:04,500\nĐoạn gộp đã làm đẹp hoàn chỉnh\n\n"
        )
        
        orig_subs = pysrt.from_string(orig_content)
        polished_subs = pysrt.from_string(polished_content)
        
        normalized = self.polisher._normalize_timeline(orig_subs, polished_subs)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].index, 1)
        # Bắt đầu không trước sub gốc (00:00:01,000)
        self.assertEqual(str(normalized[0].start), "00:00:01,000")
        # Kết thúc không vượt quá sub gốc (00:00:04,000)
        self.assertEqual(str(normalized[0].end), "00:00:04,000")

    @patch.object(SubtitlePolisher, '_call_llm')
    def test_polish_srt_success(self, mock_llm):
        """Kiểm tra quy trình làm đẹp SRT khi LLM phản hồi thành công"""
        input_srt_path = os.path.join(self.temp_dir, "input.srt")
        output_srt_path = os.path.join(self.temp_dir, "output.srt")
        
        # Whisper cắt vụn thành 3 mẩu cụt
        raw_srt = (
            "1\n00:00:01,000 --> 00:00:02,200\nCái món này thực sự là\n\n"
            "2\n00:00:02,250 --> 00:00:03,500\nkhiến cho mình cảm thấy\n\n"
            "3\n00:00:03,550 --> 00:00:04,800\nvô cùng bất ngờ luôn.\n\n"
        )
        with open(input_srt_path, "w", encoding="utf-8") as f:
            f.write(raw_srt)
            
        # LLM trả về câu đã được hàn gắn hoàn hảo, ngắt dấu phẩy chuẩn TTS
        llm_response = (
            "1\n00:00:01,000 --> 00:00:04,800\nMón này thực sự, làm mình bất ngờ luôn!\n\n"
        )
        mock_llm.return_value = llm_response
        
        result_path = self.polisher.polish_srt(input_srt_path, output_srt_path, style="tiktok_viral")
        self.assertEqual(result_path, output_srt_path)
        self.assertTrue(os.path.exists(output_srt_path))
        
        with open(output_srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Món này thực sự, làm mình bất ngờ luôn!", content)

    @patch.object(SubtitlePolisher, '_call_llm')
    def test_polish_srt_fallback_on_error(self, mock_llm):
        """Kiểm tra cơ chế fallback an toàn: Nếu AI lỗi, giữ nguyên file gốc không làm hỏng luồng video"""
        input_srt_path = os.path.join(self.temp_dir, "input.srt")
        output_srt_path = os.path.join(self.temp_dir, "output.srt")
        
        raw_srt = "1\n00:00:01,000 --> 00:00:02,000\nPhụ đề gốc ban đầu\n\n"
        with open(input_srt_path, "w", encoding="utf-8") as f:
            f.write(raw_srt)
            
        # Mô phỏng AI bị lỗi mạng hoặc hết quota
        mock_llm.side_effect = Exception("API Quota Exceeded / Network Timeout")
        
        result_path = self.polisher.polish_srt(input_srt_path, output_srt_path, style="tiktok_viral")
        self.assertEqual(result_path, output_srt_path)
        self.assertTrue(os.path.exists(output_srt_path))
        
        # File output phải có nội dung file gốc ban đầu
        with open(output_srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Phụ đề gốc ban đầu", content)

    def test_schema_defaults(self):
        """Kiểm tra VideoProcessingConfig có default giá trị đúng"""
        config = VideoProcessingConfig()
        self.assertTrue(config.enable_ai_subtitle_polish)
        self.assertEqual(config.subtitle_polish_style, "tiktok_viral")
        self.assertEqual(config.subtitle_bg_opacity, 100)

        custom_config = VideoProcessingConfig(subtitle_bg_opacity=75)
        self.assertEqual(custom_config.subtitle_bg_opacity, 75)

if __name__ == '__main__':
    unittest.main()
