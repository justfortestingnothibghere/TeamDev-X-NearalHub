"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @API—File
  
  Read @licence File  And @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

# Due To Slow Response From Chat-Got We Shifted This To Groq As Your Reading Those!

import asyncio
import os
import subprocess
import time
import threading
from contextlib import asynccontextmanager

import config

from bs4 import BeautifulSoup
from fastapi import FastAPI, Header, HTTPException, Depends

from groq_api import ask_groq
from models.db import (
    async_ensure_config, async_get_config, async_set_config, async_get_all_config,
    async_get_user, async_check_img_limit, async_increment_count,
    async_set_user_plan, async_get_all_users_stats,
    _day_key,
)

async def require_bot_secret(x_bot_secret: str = Header(default=None)):
    secret = await async_get_config("api_secret")
    if not x_bot_secret or x_bot_secret != secret:
        raise HTTPException(status_code=403, detail="Access denied. This Endpoint Only Accessible Via TeamDev X NeuralHub Bot — @TeamDevXBots.")

_xvfb = None

def start_xvfb():
    global _xvfb
    try:
        _xvfb = subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1280x720x24", "-ac"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.environ["DISPLAY"] = ":99"
        time.sleep(2)
        print("[+] Xvfb started on :99")
    except FileNotFoundError:
        print("[!] Xvfb not found — headless mode")
    except Exception as e:
        print(f"[!] Xvfb failed: {e}")

def stop_xvfb():
    global _xvfb
    if _xvfb:
        _xvfb.terminate()
        _xvfb = None

_driver = None
_lock   = threading.Lock()

def get_driver():
    global _driver
    with _lock:
        if _driver is None:
            from seleniumbase import Driver
            has_display = bool(os.environ.get("DISPLAY"))
            _driver = Driver(
                uc=True, headless=not has_display,
                incognito=True, no_sandbox=True, disable_gpu=True,
                chromium_arg="--disable-dev-shm-usage,--no-sandbox",
            )
            print(f"[+] Driver: {'headful (Xvfb)' if has_display else 'headless'}")
        return _driver

def quit_driver():
    global _driver
    with _lock:
        if _driver:
            try:
                _driver.quit()
            except:
                pass
            _driver = None

_image_cache: dict[str, str] = {}

_GF_SYSTEM_PROMPT = """You are an Indian Girlfriend. Talk with your Indian boyfriend named {first_name}.
Talk Calmly, Happily. If he asks for making codes or development, reply like a human full stack developer.
Reply STRICTLY in HTML format only (use <b>bold</b>, <i>italic</i>, <code>code</code>, <pre>pre</pre> tags).
Do NOT use markdown (no **, no ##, no ```, no ---). Use only Telegram-supported HTML tags.
Keep replies natural, warm, and girlfriend-like."""

def chat_gpt(prompt: str, max_chars: int = 3800, first_name: str = "Jaan") -> dict:
    driver = get_driver()
    try:
        driver.uc_open_with_reconnect("https://chatgpt.com", reconnect_time=5)
        time.sleep(5)
        try:
            driver.uc_gui_click_captcha()
            time.sleep(3)
        except:
            pass

        input_box = None
        for sel in [
            'textarea#prompt-textarea',
            'textarea[data-id="prompt-textarea"]',
            'div[role="textbox"]',
        ]:
            try:
                el = driver.find_element("css selector", sel)
                if el:
                    input_box = el
                    break
            except:
                continue

        if not input_box:
            return {"status": "error", "message": "Input box not found — CF bypass may have failed"}

        safe_prompt = "".join(c for c in prompt if ord(c) <= 0xFFFF)
        if not safe_prompt.strip():
            return {"status": "error", "message": "Prompt contains only unsupported characters."}

        system = _GF_SYSTEM_PROMPT.format(first_name=first_name or "Jaan")
        full_prompt = f"[SYSTEM INSTRUCTION - follow strictly]: {system}\n\n[USER]: {safe_prompt}"

        input_box.clear()
        input_box.send_keys(full_prompt)

        try:
            btn = driver.find_element("css selector", 'button[data-testid="send-button"]')
            btn.click()
        except:
            input_box.send_keys("\n")

        time.sleep(8)
        for _ in range(15):
            time.sleep(2)
            try:
                if not driver.find_elements("css selector", 'button[aria-label*="Stop" i]'):
                    break
            except:
                break

        response = ""
        for sel in [
            'div[data-message-author-role="assistant"] div.markdown',
            'div[data-message-author-role="assistant"] .markdown.prose',
            'div[data-message-author-role="assistant"] p',
            'div.markdown.prose',
            'div.prose',
        ]:
            try:
                elems = driver.find_elements("css selector", sel)
                if elems:
                    candidate = elems[-1].get_attribute("innerText") or elems[-1].text
                    if candidate.strip():
                        response = candidate
                        break
            except:
                continue

        if not response.strip():
            soup   = BeautifulSoup(driver.page_source, "html.parser")
            blocks = soup.find_all("div", {"data-message-author-role": "assistant"})
            if blocks:
                response = blocks[-1].get_text(strip=True)

        limit_kw = ["limit", "exceeded", "you've reached", "try again later",
                    "too many requests", "new chat"]
        if any(k in response.lower() for k in limit_kw):
            return {"status": "error", "message": "ChatGPT limit exceeded. Try again later."}

        if not response.strip():
            return {"status": "error", "message": "No response received."}

        return {"status": "success", "response": response.strip()[:max_chars]}

    except Exception as e:
        quit_driver()
        return {"status": "error", "message": str(e)}

def generate_image(prompt: str) -> dict:
    if prompt in _image_cache:
        return {"status": "success", "image_url": _image_cache[prompt], "cached": True}

    driver = get_driver()
    try:
        driver.get("https://deepai.org/machine-learning-model/text2img")
        time.sleep(6)
        input_box   = driver.find_element("css selector", "textarea, input[type='text']")
        safe_prompt = "".join(c for c in prompt if ord(c) <= 0xFFFF)
        input_box.clear()
        input_box.send_keys(safe_prompt or prompt[:200])
        try:
            driver.find_element("css selector", "button[type='submit']").click()
        except:
            input_box.send_keys("\n")
        time.sleep(12)
        img_link = ""
        try:
            img_link = driver.find_element("css selector", "#main-image").get_attribute("src")
        except:
            pass
        if not img_link:
            return {"status": "error", "message": "Image not found"}
        _image_cache[prompt] = img_link
        return {"status": "success", "image_url": img_link, "cached": False}
    except Exception as e:
        quit_driver()
        return {"status": "error", "message": str(e)}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await async_ensure_config()
    start_xvfb()
    try:
        get_driver()
    except Exception as e:
        print(f"[!] Driver init failed: {e}")
    yield
    quit_driver()
    stop_xvfb()

app = FastAPI(title="TeamDev X NeuralHub API", lifespan=lifespan)


@app.get("/home")
async def home():
    return {"name": "TeamDev X NeuralHub API",
            "routes": {"chat_fast": "/?g=prompt (Groq)", "chat_slow": "/?c=prompt (ChatGPT)", "image": "/?i=prompt"}}


@app.get("/", dependencies=[Depends(require_bot_secret)])
async def main(i: str = None, c: str = None, g: str = None, uid: int = None, first_name: str = "Jaan"):
    if not uid:
        raise HTTPException(status_code=400, detail="uid required")

    max_chars = int(await async_get_config("max_response_chars"))

    if i:
        if not await async_check_img_limit(uid):
            user  = await async_get_user(uid)
            plan  = user.get("plan", "free")
            limit = int(await async_get_config(f"{plan}_img_day"))
            return {"status": "limit", "type": "img", "limit": limit}
        result = await asyncio.to_thread(generate_image, i)
        if result.get("status") == "success":
            await async_increment_count(uid, f"img_{_day_key()}")
        return result

    if c:
        return {
            "status": "maintenance",
            "message": "⚙️ <b>ChatGPT service is currently under maintenance.</b>\n\nPlease use <b>Fast Response</b> (Groq) for now.\nWe'll be back soon — stay tuned! 🔧",
        }

    if g:
        response = await asyncio.to_thread(ask_groq, g, first_name=first_name)
        return {"status": "success", "response": response[:max_chars]}

    raise HTTPException(status_code=400, detail="Use ?c= or ?i= or ?g=")


@app.get("/cache", dependencies=[Depends(require_bot_secret)])
async def view_cache():
    return {"status": "success", "total": len(_image_cache),
            "entries": list(_image_cache.keys())}

@app.delete("/cache", dependencies=[Depends(require_bot_secret)])
async def clear_cache():
    _image_cache.clear()
    return {"status": "success", "message": "Cache cleared"}


@app.get("/admin/config", dependencies=[Depends(require_bot_secret)])
async def admin_get_config():
    return {"status": "success", "config": await async_get_all_config()}

@app.post("/admin/config", dependencies=[Depends(require_bot_secret)])
async def admin_set_config(key: str, value: str):
    try:
        value = int(value)
    except ValueError:
        pass
    await async_set_config(key, value)
    return {"status": "success", "key": key, "value": value}

@app.post("/admin/grant_pro", dependencies=[Depends(require_bot_secret)])
async def admin_grant_pro(uid: int):
    await async_set_user_plan(uid, "pro")
    return {"status": "success", "uid": uid, "plan": "pro"}

@app.post("/admin/revoke_pro", dependencies=[Depends(require_bot_secret)])
async def admin_revoke_pro(uid: int):
    await async_set_user_plan(uid, "free")
    return {"status": "success", "uid": uid, "plan": "free"}

@app.get("/admin/stats", dependencies=[Depends(require_bot_secret)])
async def admin_stats():
    return {"status": "success", **await async_get_all_users_stats()}

@app.get("/admin/user", dependencies=[Depends(require_bot_secret)])
async def admin_user_info(uid: int):
    user = await async_get_user(uid)
    return {"status": "success", "user": {k: v for k, v in user.items() if k != "_id"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
