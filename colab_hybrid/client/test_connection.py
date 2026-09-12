#!/usr/bin/env python3
# ==============================================================================
# Script Kiểm Tra Kết Nối & Benchmark Tốc Độ GPU T4 Từ Máy Local
# ==============================================================================

import sys
import time
from colab_client import ColabGPUClient


def main():
    print("=" * 60)
    print("🔍 KIỂM TRA KẾT NỐI TỚI GOOGLE COLAB GPU WORKER")
    print("=" * 60)

    colab_url = ""
    if len(sys.argv) > 1:
        colab_url = sys.argv[1]
    else:
        colab_url = input("\n👉 Nhập địa chỉ Cloudflare Tunnel từ Colab (VD: https://xxx.trycloudflare.com): ").strip()

    if not colab_url:
        print("❌ Lỗi: Bạn chưa nhập URL!")
        return

    if not colab_url.startswith("http"):
        colab_url = f"https://{colab_url}"

    print(f"\n[*] Đang kết nối tới: {colab_url}...")
    client = ColabGPUClient(base_url=colab_url)

    start_time = time.time()
    try:
        health = client.check_health()
        latency_ms = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        print(f"\n❌ Kết nối thất bại: {e}")
        print("👉 Gợi ý: Hãy kiểm tra xem cell Colab vẫn đang chạy và link Tunnel có chính xác không.")
        return

    gpu_info = health.get("gpu", {})
    print("\n" + "=" * 60)
    print("🎉 KẾT NỐI THÀNH CÔNG!")
    print("=" * 60)
    print(f"⏱️ Độ trễ mạng (Ping):      {latency_ms} ms")
    print(f"🖥️ Tên Card Đồ Họa:         {gpu_info.get('device_name', 'N/A')}")
    print(f"🚀 CUDA Available:          {gpu_info.get('cuda_available')}")
    print(f"📦 Tổng VRAM GPU:           {gpu_info.get('vram_total_mb', 0)} MB (~16 GB)")
    print(f"📊 VRAM Trống:              {gpu_info.get('vram_free_mb', 0)} MB")
    print(f"🎬 Hỗ trợ Render NVENC:     {'CÓ (Siêu Tốc)' if gpu_info.get('nvenc_supported') else 'KHÔNG'}")
    print(f"🐍 Phiên bản PyTorch:       {gpu_info.get('pytorch_version', 'N/A')}")
    print(f"⚡ Phiên bản CUDA:          {gpu_info.get('cuda_version', 'N/A')}")
    print("=" * 60)
    print("✅ Hệ thống đã sẵn sàng xử lý các tác vụ AI nặng (Whisper, Vieneu, NVENC)!")


if __name__ == "__main__":
    main()
