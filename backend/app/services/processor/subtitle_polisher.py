import os
import re
import json
import logging
from typing import List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/.env"))

STYLE_PRESETS = {
    "tiktok_viral": {
        "name": "TikTok Viral",
        "description": "Ngắn gọn, giật tít nhẹ, bắt trend, từ ngữ đời thường cuốn hút, lôi cuốn ngay 3 giây đầu",
        "system_role": "Bạn là biên tập viên kịch bản video ngắn TikTok/Reels triệu view hàng đầu.",
        "guidelines": (
            "- Sử dụng ngôn ngữ nói tự nhiên, hiện đại, bắt tai, giàu tính biểu cảm của giới trẻ.\n"
            "- Loại bỏ hoàn toàn lối dịch máy cứng nhắc (như: 'tiến hành', 'thực hiện việc', 'cái đó thì là').\n"
            "- Giữ câu từ súc tích, nhịp điệu nhanh, dứt khoát.\n"
            "- Đại từ xưng hô đồng nhất, gần gũi (ví dụ: mình - các bạn, tôi - anh em)."
        )
    },
    "reviewer": {
        "name": "Reviewer / Ẩm thực & Đời sống",
        "description": "Trực diện, chân thực, sống động, hào hứng, cảm nhận sắc sảo",
        "system_role": "Bạn là biên tập viên kịch bản chuyên nghiệp cho reviewer ẩm thực, công nghệ và đời sống.",
        "guidelines": (
            "- Giọng điệu hào hứng, chân thực, nêu bật cảm nhận trực tiếp giác quan (thơm lừng, giòn rụm, đỉnh chóp).\n"
            "- Câu văn mạch lạc, tạo cảm giác trải nghiệm thực tế cho người xem.\n"
            "- Xưng hô thân thiện, tự nhiên như đang chia sẻ bí quyết với bạn bè."
        )
    },
    "storytelling": {
        "name": "Kể chuyện / Tâm sự",
        "description": "Mượt mà, sâu lắng, trau chuốt, giàu hình ảnh và cảm xúc",
        "system_role": "Bạn là nhà biên kịch và kể chuyện truyền cảm xúc cho video ngắn.",
        "guidelines": (
            "- Câu văn trau chuốt, nhịp điệu êm ái, giàu chất thơ và hình ảnh gợi cảm.\n"
            "- Sử dụng các từ ngữ diễn tả chiều sâu tâm trạng, gợi mở sự tò mò và đồng cảm.\n"
            "- Dấu câu ngắt nghỉ có độ lắng để giọng đọc TTS tạo chiều sâu."
        )
    },
    "formal": {
        "name": "Tin tức / Kiến thức",
        "description": "Gãy gọn, chuẩn xác, trung tính, cấu trúc ngữ pháp chuẩn mực",
        "system_role": "Bạn là biên tập viên tin tức và kịch bản phổ biến kiến thức khoa học/đời sống.",
        "guidelines": (
            "- Câu từ trong sáng, chuẩn mực tiếng Việt phổ thông, không dùng từ lóng hay tiếng lóng mạng.\n"
            "- Diễn đạt khúc chiết, mạch lạc, dễ hiểu, thông tin rõ ràng và khách quan.\n"
            "- Cấu trúc ngữ pháp hoàn chỉnh đầy đủ chủ ngữ - vị ngữ."
        )
    }
}

class SubtitlePolisher:
    """
    Module AI Subtitle Polisher & Script Doctor:
    - Nhận diện ngữ cảnh toàn kịch bản (Global Context).
    - Hàn gắn các mẩu câu bị Whisper bẻ cụt.
    - Điều phối dấu câu chuẩn xác cho nhịp thở TTS (TTS Cadence Sync).
    - Cân đối độ dài thị giác (Visual Subtitle Formatting: 5-8 từ/dòng).
    - Bảo toàn timeline âm thanh khớp video gốc.
    """
    def __init__(self):
        load_dotenv(ENV_PATH, override=True)

    def _get_active_ai_client(self):
        """Khởi tạo client AI theo Active Provider được cấu hình trong hệ thống."""
        from app.core.security import decrypt_data

        active_provider = os.getenv("ACTIVE_AI_PROVIDER", "gemini")
        gemini_key = decrypt_data(os.getenv("GEMINI_API_KEY", ""))
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        openai_key = decrypt_data(os.getenv("OPENAI_API_KEY", ""))
        anthropic_key = decrypt_data(os.getenv("ANTHROPIC_API_KEY", ""))
        xai_key = decrypt_data(os.getenv("XAI_API_KEY", ""))

        custom_ai_endpoint = os.getenv("CUSTOM_AI_ENDPOINT", "http://localhost:20128/v1")
        custom_ai_key = decrypt_data(os.getenv("CUSTOM_AI_KEY", ""))
        custom_ai_model = os.getenv("CUSTOM_AI_MODEL", "kr/claude-sonnet-4.5")

        if custom_ai_endpoint and custom_ai_key:
            active_provider = "custom"

        return {
            "provider": active_provider,
            "gemini_key": gemini_key,
            "gemini_model": gemini_model,
            "openai_key": openai_key,
            "anthropic_key": anthropic_key,
            "xai_key": xai_key,
            "custom_endpoint": custom_ai_endpoint,
            "custom_key": custom_ai_key,
            "custom_model": custom_ai_model
        }

    def _call_llm(self, prompt: str) -> str:
        """Thực thi prompt gọi LLM với cấu hình hiện tại."""
        cfg = self._get_active_ai_client()
        provider = cfg["provider"]
        output = ""

        if provider == "custom":
            if not cfg["custom_key"]:
                raise Exception("Chưa cấu hình Custom AI API Key")
            from openai import OpenAI
            client = OpenAI(api_key=cfg["custom_key"], base_url=cfg["custom_endpoint"])
            response = client.chat.completions.create(
                model=cfg["custom_model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            output = response.choices[0].message.content

        elif provider == "gemini":
            if not cfg["gemini_key"]:
                raise Exception("Chưa cấu hình Gemini API Key")
            from google import genai
            client = genai.Client(api_key=cfg["gemini_key"])
            response = client.models.generate_content(
                model=cfg["gemini_model"],
                contents=prompt
            )
            output = response.text

        elif provider == "openai":
            if not cfg["openai_key"]:
                raise Exception("Chưa cấu hình OpenAI API Key")
            from openai import OpenAI
            client = OpenAI(api_key=cfg["openai_key"])
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            output = response.choices[0].message.content

        elif provider == "anthropic":
            if not cfg["anthropic_key"]:
                raise Exception("Chưa cấu hình Anthropic API Key")
            from anthropic import Anthropic
            client = Anthropic(api_key=cfg["anthropic_key"])
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.3
            )
            output = response.content[0].text

        elif provider == "xai":
            if not cfg["xai_key"]:
                raise Exception("Chưa cấu hình xAI API Key")
            from openai import OpenAI
            client = OpenAI(api_key=cfg["xai_key"], base_url="https://api.x.ai/v1")
            response = client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            output = response.choices[0].message.content

        else:
            raise Exception(f"AI Provider '{provider}' không được hỗ trợ.")

        if output:
            output = re.sub(r'<thinking>.*?</thinking>', '', output, flags=re.DOTALL).strip()
            # Strip markdown code fences if any
            fence_match = re.search(r'```(?:srt|json)?\s*\n(.*?)\n\s*```', output, re.DOTALL)
            if fence_match:
                output = fence_match.group(1).strip()

        return output

    def build_prompt(self, raw_srt_content: str, style: str = "tiktok_viral") -> str:
        """Xây dựng prompt tối ưu hóa phụ đề với hướng dẫn chi tiết."""
        style_info = STYLE_PRESETS.get(style, STYLE_PRESETS["tiktok_viral"])
        
        prompt = f"""{style_info['system_role']}
Phong cách kịch bản bạn cần tuân theo: **{style_info['name']}** ({style_info['description']}).

HƯỚNG DẪN BIÊN TẬP & HIỆU CHỈNH:
{style_info['guidelines']}

NHIỆM VỤ ĐẶC BIỆT CỦA BẠN:
Dưới đây là một file phụ đề tiếng Việt định dạng SRT. Phụ đề này được dịch máy từ âm thanh bóc băng Whisper nên đang gặp các vấn đề nghiêm trọng:
1. **Hàn gắn câu cụt (Clause Healing)**: Các câu bị ngắt vụn theo hơi thở, nhiều dòng bị cụt nghĩa hoặc thiếu vị ngữ/chủ ngữ. Hãy đọc toàn bộ mạch kịch bản để hiểu trọn vẹn ngữ cảnh, sau đó viết lại thành những câu hoàn chỉnh, mạch lạc, dễ hiểu.
2. **Cân đối độ dài thị giác**: Mỗi dòng phụ đề tối ưu nhất từ **5 đến 8 từ** (tối đa 35-40 ký tự). TUYỆT ĐỐI không để dòng chỉ có 1-2 từ cụt lủn và không để dòng quá dài làm tràn màn hình video dọc 9:16.
3. **Tối ưu nhịp thở cho Giọng đọc AI (TTS Cadence Sync)**:
   - Thêm dấu phẩy `,` tại các điểm ngắt nghỉ ngữ điệu tự nhiên trong câu.
   - Thêm dấu chấm `.` khi hết một ý hoàn chỉnh.
   - Dùng dấu `!` hoặc `...` đúng chỗ để tạo cảm xúc nhấn nhá.
   - Điều này giúp mô hình Text-To-Speech (TTS) đọc trôi chảy, có hồn, không bị ngắt ngứ.
4. **Bảo toàn Nhãn Giọng đọc (nếu có)**:
   - Nếu dòng phụ đề có tiền tố phân vai như `[M]` (Nam) hoặc `[F]` (Nữ), hãy bảo lưu tiền tố đó ở đầu câu viết lại.
5. **Định dạng Đầu ra (BẮT BUỘC)**:
   - Trả về ĐÚNG định dạng chuẩn SRT (số thứ tự, timestamp `00:00:00,000 --> 00:00:00,000`, và dòng văn bản đã làm đẹp).
   - Hãy cố gắng giữ thời gian bắt đầu và kết thúc của các phân đoạn tương thích với timeline gốc (hoặc gộp khoảng thời gian khi bạn ghép 2-3 dòng cụt lại với nhau).
   - TUYỆT ĐỐI KHÔNG thêm bất kỳ lời bình luận, ghi chú hay markdown ngoài nội dung SRT.

FILE PHỤ ĐỀ GỐC CẦN HIỆU CHỈNH:
{raw_srt_content}
"""
        return prompt

    def polish_srt(self, input_srt: str, output_srt: str, style: str = "tiktok_viral") -> str:
        """
        Hiệu chỉnh và làm đẹp file SRT tiếng Việt bằng AI.
        Có cơ chế fallback an toàn: nếu lỗi, copy nguyên bản input_srt sang output_srt.
        """
        if not os.path.exists(input_srt) or os.path.getsize(input_srt) == 0:
            logger.warning(f"[SubtitlePolisher] File SRT đầu vào không tồn tại hoặc rỗng: {input_srt}")
            return input_srt

        try:
            import pysrt
            original_subs = pysrt.open(input_srt, encoding='utf-8')
            if len(original_subs) == 0:
                logger.warning(f"[SubtitlePolisher] Không tìm thấy segment nào trong {input_srt}")
                return input_srt

            with open(input_srt, "r", encoding="utf-8") as f:
                raw_srt_content = f.read()

            logger.info(f"[SubtitlePolisher] Bắt đầu làm đẹp {len(original_subs)} dòng phụ đề với phong cách '{style}'...")

            prompt = self.build_prompt(raw_srt_content, style=style)
            ai_output = self._call_llm(prompt)

            if not ai_output or not ai_output.strip():
                raise Exception("Phản hồi từ AI rỗng hoặc không hợp lệ")

            # Parse kết quả SRT từ AI
            polished_subs = pysrt.from_string(ai_output)
            if not polished_subs or len(polished_subs) == 0:
                # Cố gắng tìm khối SRT từ dòng đầu tiên có timestamp
                first_ts = re.search(r'(\d+)\s*\n\d{2}:\d{2}:\d{2}', ai_output, re.MULTILINE)
                if first_ts:
                    polished_subs = pysrt.from_string(ai_output[first_ts.start():])

            if not polished_subs or len(polished_subs) == 0:
                raise Exception("Không thể parse được cấu trúc SRT từ phản hồi của AI")

            # Chuẩn hóa lại index và kiểm tra timeline
            normalized_subs = self._normalize_timeline(original_subs, polished_subs)

            # Lưu ra file output_srt
            normalized_subs.save(output_srt, encoding='utf-8')
            logger.info(f"[SubtitlePolisher] Đã hiệu chỉnh phụ đề thành công ({len(normalized_subs)} dòng) -> {output_srt}")
            return output_srt

        except Exception as e:
            logger.warning(f"[SubtitlePolisher] Lỗi khi làm đẹp phụ đề bằng AI: {e}. Sử dụng file phụ đề gốc làm fallback an toàn.")
            if input_srt != output_srt:
                import shutil
                shutil.copy2(input_srt, output_srt)
            return output_srt

    def _normalize_timeline(self, original_subs, polished_subs):
        """
        Thuật toán chuẩn hóa và bảo vệ tính liên tục của mốc thời gian:
        - Đảm bảo thời gian bắt đầu của câu đầu tiên không trước sub gốc.
        - Đảm bảo thời gian kết thúc không vượt quá giới hạn sub gốc.
        - Đảm bảo start < end và không bị chồng lấn ngược dòng.
        """
        import pysrt

        if not original_subs or not polished_subs:
            return polished_subs

        min_start = original_subs[0].start
        max_end = original_subs[-1].end

        cleaned_items = []
        for i, sub in enumerate(polished_subs):
            text = sub.text.strip()
            if not text:
                continue

            # Đảm bảo start < end
            if sub.start >= sub.end:
                # Tối thiểu cho 1 phân đoạn là 500ms
                sub.end = pysrt.SubRipTime(milliseconds=sub.start.ordinal + 800)

            # Đảm bảo không âm
            if sub.start.ordinal < 0:
                sub.start = pysrt.SubRipTime(milliseconds=0)

            sub.index = len(cleaned_items) + 1
            cleaned_items.append(sub)

        # Căn chỉnh bao bọc biên độ nếu timeline bị trôi
        if cleaned_items:
            if cleaned_items[0].start < min_start:
                cleaned_items[0].start = min_start
            if cleaned_items[-1].end > max_end:
                cleaned_items[-1].end = max_end

        return pysrt.SubRipFile(items=cleaned_items)
