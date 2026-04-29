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

# Dont Change
BATBIN_API_URL = "https://batbin.me/api/paste/{paste_id}"


# Change Only Bot-Token, (Optinal  API_SECRET) ADMIN_IDS.
BOT_TOKEN  = "875xxxx52:AxxxxcxVit-ceyxN2WvIAZDsvcO0"
API_SECRET = "TeamDev"
ADMIN_IDS  = [8163739723]

# change It
MONGO_URI = "mongodb+srv://txxxxxdb_user:xxxx8@cluster0.6xywr7u.mongodb.net/?appName=Cluster0"
MONGO_DB  = "teamdev_neuralhub"

# ───────────────── Internal service URLs Dont Change ─────────────────
API_BASE      = "http://localhost:8000"

# ───────────────── Downloader API ( Only Change When Your Deployed Your Own Api Fron Our AIO Repo  ─────────────────
DL_API_BASE = "https://aio-production-df67.up.railway.app"
DL_API_KEY  = "" # Dont Need For Now (Add If Your Api Need Key

GROQ_MODEL = "llama-3.3-70b-versatile"

# Dont Change From Gere Anything
# ───────────────── GROQ API-KEY LOADER  ─────────────────
BATBIN_URL = "https://batbin.me/desegregated"

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
