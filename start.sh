#!/usr/bin/env bash
# ───── TeamDev X NeuralHub ─────
set -e

echo ""
echo "╔═══════════════════╗"
echo "         ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ"
echo "╚═══════════════════╝"
echo ""

python3 groq_api.py &
GROQ_PID=$!

python3 -m uvicorn c-gpt:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "[~] Waiting for API..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/home > /dev/null 2>&1; then
        echo "[+] API ready."
        break
    fi
    sleep 2
done

echo "[+] Starting bot..."
python3 bot.py

kill $API_PID $GROQ_PID 2>/dev/null
