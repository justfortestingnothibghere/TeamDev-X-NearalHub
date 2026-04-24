"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     Config File
  
  Read @licence File  Adm @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import requests

BATBIN_API_URL = "https://batbin.me/api/paste/{paste_id}"



BOT_TOKEN  = "875xxxx52:AxxxxcxVit-ceyxN2WvIAZDsvcO0"
API_SECRET = "TeamDev@2026"
ADMIN_IDS  = [8163739723]

MONGO_URI = "mongodb+srv://txxxxxdb_user:xxxx8@cluster0.6xywr7u.mongodb.net/?appName=Cluster0"
MONGO_DB  = "teamdev_neuralhub"

# ───────────────── Internal service URLs ─────────────────
API_BASE      = "http://localhost:8000"

# ───────────────── Downloader API  ─────────────────
DL_API_BASE = "https://aio-production-df67.up.railway.app"
DL_API_KEY  = ""

GROQ_MODEL = "llama-3.3-70b-versatile"

# ───────────────── GROQ API-KEY LOADER  ─────────────────
BATBIN_URL = "https://batbin.me/deboned"

def _load_groq_keys() -> list[str]:
    url = BATBIN_URL.strip()
    paste_id = url.rstrip("/").split("/")[-1]
    print(f"[config] Loading Groq keys from batbin paste: {paste_id}", flush=True)

    content = None

    try:
        r = requests.get(BATBIN_API_URL.format(paste_id=paste_id), timeout=15)
        r.raise_for_status()
        data = r.json()
        content = (
            data.get("content")
            or (data.get("paste") or {}).get("content")
            or (data.get("data") or {}).get("content")
        )
    except Exception:
        pass

    if not content:
        try:
            r2 = requests.get(f"https://batbin.me/raw/{paste_id}", timeout=15)
            r2.raise_for_status()
            content = r2.text
        except Exception as e:
            raise RuntimeError(f"[config] Could not fetch batbin paste: {e}")

    keys = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not keys:
        raise RuntimeError("[config] No Groq API keys found in paste. Add one key per line.")

    print(f"[config] {len(keys)} Groq key(s) loaded.", flush=True)
    return keys


GROQ_API_KEYS = _load_groq_keys()
