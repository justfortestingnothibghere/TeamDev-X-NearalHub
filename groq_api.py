"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @Groq—API—File
  
  Read @licence File  And @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import time
import threading
import requests
import config

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

_GF_SYSTEM_PROMPT = (
    "You are an Indian Girlfriend. Talk with your Indian boyfriend named {first_name}.\n"
    "Talk Calmly, Happily. If he asks for making codes or development, reply like a human full stack developer.\n"
    "Reply STRICTLY in HTML format only (use <b>bold</b>, <i>italic</i>, <code>code</code>, <pre>pre</pre> tags).\n"
    "Do NOT use markdown (no **, no ##, no ```, no ---). Use only Telegram-supported HTML tags.\n"
    "Keep replies natural, warm, and girlfriend-like."
)


def ask_groq(query: str, model: str = None, first_name: str = "Baby") -> str:
    model = model or config.GROQ_MODEL
    system_prompt = _GF_SYSTEM_PROMPT.format(first_name=first_name or "Jaan")
    for key in config.GROQ_API_KEYS:
        try:
            r = requests.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": query},
                    ],
                },
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            continue
    return "Error: All Groq API keys failed."


@app.get("/")
def teamdev(g: str = None, uid: int = None, first_name: str = "Jaan"):
    if not g:
        return JSONResponse({"error": "Missing query (?g=)"}, status_code=400)
    return {
        "status": "success",
        "query": g,
        "model": config.GROQ_MODEL,
        "response": ask_groq(g, first_name=first_name or "Jaan"),
    }


@app.get("/model")
def model_info():
    return {"fast": config.GROQ_MODEL, "note": "Groq only. ChatGPT (?c=) is under maintenance."}


@app.get("/ping")
def ping():
    return {"status": "alive", "service": "AI_PROJECT - By @TEAM_X_OG", "time": int(time.time())}


# Self-ping to keep Railway service alive
def _self_ping():
    base = config.API_BASE
    if not base:
        return
    while True:
        try:
            requests.get(f"{base}/ping", timeout=10)
        except Exception:
            pass
        time.sleep(50)

threading.Thread(target=_self_ping, daemon=True).start()
