"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @Groq—API—Loader
  
  Read @licence File  And @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import sys
import requests

BATBIN_API_URL = "https://batbin.me/api/paste/{paste_id}"


def fetch(url: str) -> list[str]:
    paste_id = url.strip().rstrip("/").split("/")[-1]
    print(f"[batbin] Fetching paste: {paste_id}")

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
        r2 = requests.get(f"https://batbin.me/raw/{paste_id}", timeout=15)
        r2.raise_for_status()
        content = r2.text

    keys = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
    print(f"[Info] {len(keys)} line(s) found")
    return keys


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    try:
        keys = fetch(sys.argv[1])
        print("\n───────────── Keys ──────────────")
        for k in keys:
            print(f"  {k[:8]}{'*' * max(0, len(k)-8)}")
        print("──────────────────────────")
    except Exception as e:
        print(f"[Info] {e}")
        sys.exit(1)
