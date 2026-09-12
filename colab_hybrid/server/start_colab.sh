#!/bin/bash
# ==============================================================================
# Script Khởi Động GPU Worker Trên Google Colab & Mở Cloudflare Tunnel
# ==============================================================================

set -e

echo "========================================================"
echo "🚀 Khởi Động Auto Reup GPU Worker (Tesla T4 Free)"
echo "========================================================"

# 1. Kiểm tra card đồ họa NVIDIA
echo "[*] Đang kiểm tra trạng thái GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ Lỗi: Không tìm thấy GPU NVIDIA! Hãy vào menu: Runtime -> Change runtime type -> Chọn T4 GPU."
    exit 1
fi
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# 2. Cài đặt Cloudflared nếu chưa có
if ! command -v cloudflared &> /dev/null; then
    echo "[*] Đang tải và cài đặt Cloudflared..."
    wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i cloudflared-linux-amd64.deb > /dev/null 2>&1 || apt-get install -f -y > /dev/null 2>&1
fi

# 3. Dừng tiến trình cũ nếu đang chạy
echo "[*] Dọn dẹp các tiến trình cũ..."
pkill -f "uvicorn colab_server:app" || true
pkill -f "cloudflared tunnel" || true
sleep 1

# 4. Khởi động Uvicorn FastAPI Server
echo "[*] Khởi chạy FastAPI GPU Server trên cổng 8000..."
nohup python3 -m uvicorn colab_server:app --host 0.0.0.0 --port 8000 > /content/gpu_server.log 2>&1 &

# Chờ server sẵn sàng
echo "[*] Đang chờ server khởi động..."
for i in {1..15}; do
    if curl -s http://127.0.0.1:8000/api/gpu/health > /dev/null; then
        echo "✅ FastAPI GPU Server đã sẵn sàng!"
        break
    fi
    sleep 1
done

# 5. Khởi động Cloudflare Tunnel
echo "[*] Đang thiết lập đường hầm bảo mật Cloudflare Tunnel..."
rm -f /content/tunnel.log
nohup cloudflared tunnel --url http://127.0.0.1:8000 > /content/tunnel.log 2>&1 &

# Đợi link trycloudflare xuất hiện trong log
echo "[*] Đang lấy đường dẫn Public HTTPS..."
TUNNEL_URL=""
for i in {1..20}; do
    TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*trycloudflare.com' /content/tunnel.log | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 1
done

echo ""
echo "========================================================"
if [ -n "$TUNNEL_URL" ]; then
    echo "🎉 CHÚC MỪNG! GPU WORKER ĐÃ CHẠY THÀNH CÔNG!"
    echo ""
    echo "👉 ĐỊA CHỈ GPU CLOUD CỦA BẠN:"
    echo "   $TUNNEL_URL"
    echo ""
    echo "👉 API Docs (Swagger UI):"
    echo "   $TUNNEL_URL/docs"
    echo ""
    echo "Hãy copy địa chỉ URL trên và dán vào máy Local (trong file .env hoặc colab_client.py)!"
else
    echo "⚠️ Chưa bắt được link Cloudflare. Xem log chi tiết tại: /content/tunnel.log"
fi
echo "========================================================"
