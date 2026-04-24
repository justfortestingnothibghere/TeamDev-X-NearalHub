"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @Main—File
  
  Read @licence File  Adm @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import os
import re
import io
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import config

BOT_TOKEN     = config.BOT_TOKEN
API_BASE      = config.API_BASE
API_SECRET    = config.API_SECRET
ADMIN_IDS     = config.ADMIN_IDS
DL_API_BASE   = config.DL_API_BASE
DL_API_KEY    = config.DL_API_KEY

from models.db import (
    sync_ensure_config, sync_get_config, sync_set_config, sync_get_all_config,
    sync_get_user, sync_update_user, sync_set_last_msg,
    sync_check_cooldown, sync_check_pm_limit, sync_check_group_limit,
    sync_check_img_limit, sync_check_dl_limit,
    sync_increment_count, sync_get_usage_stats,
    sync_set_user_plan, sync_get_all_users_stats,
    sync_ban_user, sync_unban_user, sync_restrict_user, sync_unrestrict_user,
    sync_is_banned, sync_is_restricted,
    sync_log_user_action, sync_get_user_history,
    sync_get_fsub_channels, sync_add_fsub_channel, sync_remove_fsub_channel,
    sync_fsub_enabled, sync_set_fsub_enabled,
    sync_get_welcome_video, sync_set_welcome_video,
    sync_get_chatbot_enabled, sync_set_chatbot_enabled,
    sync_get_ads, sync_set_ad, sync_delete_ad, sync_get_ads_enabled, sync_set_ads_enabled,
    _month_key, _day_key, VALID_PLANS,
)
from lang import t, tf, LANGUAGES, SUPPORTED

DL_DIRECT_PLATFORMS = ["instagram.com","tiktok.com","pinterest.com","pin.it"]
DL_LINK_ONLY_PLATFORMS = [
    "youtube.com","youtu.be","facebook.com","fb.com","fb.watch",
    "twitter.com","x.com","bandcamp.com","vimeo.com","dailymotion.com","reddit.com",
]
PHUB_DOMAINS  = ["pornhub.com","pornhub.net","pornhub.org"]
XHAM_DOMAINS  = [
    "xhamster.com","xhamster.desi","xhamster2.com","xhamster3.com",
    "xhamster4.com","xhamster5.com","xhamster10.com","xhamster15.com",
    "xhamster18.com","xhamster20.com","xhamster45.desi",
]
HCITY_DOMAINS = ["hentaicity.com"]
DL_ALL_PLATFORMS = DL_DIRECT_PLATFORMS + DL_LINK_ONLY_PLATFORMS + PHUB_DOMAINS + XHAM_DOMAINS + HCITY_DOMAINS
TERABOX_DOMAINS = [
    "terabox.com","1024terabox.com","teraboxapp.com",
    "4funbox.com","mirrobox.com","nephobox.com","freeterabox.com","tibibox.com",
]

MAX_DIRECT_MB   = 45
AUDIO_EXTS      = ("mp3","m4a","opus","ogg","flac","wav")
MIN_VIDEO_HEIGHT = 240

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

PLAN_BADGE = {
    "free":      " Free",
    "basic":     " Basic",
    "pro":       " Pro",
    "ultra":     " Ultra",
    "ultra_pro": " Ultra Pro",
}
PLAN_EMOJI = {
    "free": "", "basic": "", "pro": "", "ultra": "", "ultra_pro": ""
}

def _bar(used, limit, width=10) -> str:
    if limit == "∞" or limit == 0:
        return "" * width + " ∞"
    pct  = min(used / int(limit), 1.0)
    fill = round(pct * width)
    return "" * fill + "" * (width - fill)

def _h():
    return {"X-Bot-Secret": API_SECRET}

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def ulang(uid: int) -> str:
    return sync_get_user(uid).get("lang", "en")

def ul(uid: int, key: str, **kw) -> str:
    lang = ulang(uid)
    return tf(key, lang=lang, **kw) if kw else t(key, lang=lang)

def send_chunked(chat_id: int, text: str, reply_to: int = None, uid: int = None, parse_mode: str = None):
    chunk_size = 3800
    lang   = ulang(uid) if uid else "en"
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    total  = len(chunks)
    for n, chunk in enumerate(chunks, 1):
        body = chunk
        if total > 1:
            body = f"{chunk}\n\n{tf('ai.chunk_footer', lang=lang, n=n, total=total)}"
        try:
            if reply_to and n == 1:
                bot.send_message(chat_id, body, reply_to_message_id=reply_to, parse_mode=parse_mode)
            else:
                bot.send_message(chat_id, body, parse_mode=parse_mode)
        except Exception as e:
            print(f"[!] Chunk send error: {e}")
            try:
                if reply_to and n == 1:
                    bot.send_message(chat_id, body, reply_to_message_id=reply_to)
                else:
                    bot.send_message(chat_id, body)
            except Exception as e2:
                print(f"[!] Fallback send failed: {e2}")

def is_dl_url(text: str) -> bool:
    text = text.lower()
    return text.startswith("http") and any(p in text for p in DL_ALL_PLATFORMS)

def is_terabox_url(text: str) -> bool:
    text = text.lower()
    return text.startswith("http") and any(p in text for p in TERABOX_DOMAINS)

def is_direct_dl_platform(url: str) -> bool:
    return any(p in url.lower() for p in DL_DIRECT_PLATFORMS)

def is_phub_url(url: str)  -> bool: return any(p in url.lower() for p in PHUB_DOMAINS)
def is_xham_url(url: str)  -> bool: return any(p in url.lower() for p in XHAM_DOMAINS)
def is_hcity_url(url: str) -> bool: return any(p in url.lower() for p in HCITY_DOMAINS)

def extract_url(text: str):
    m = re.search(r"https?://\S+", text)
    return m.group(0) if m else None

def check_fsub(uid: int, chat_id: int) -> list:
    if not sync_fsub_enabled():
        return []
    channels = sync_get_fsub_channels()
    not_joined = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch, uid)
            if member.status in ("left", "kicked"):
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

def fsub_markup(not_joined: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for ch in not_joined:
        try:
            chat = bot.get_chat(ch)
            link = getattr(chat, "invite_link", None) or f"https://t.me/c/{str(ch).replace('-100','')}"
            title = getattr(chat, "title", str(ch))
            kb.row(InlineKeyboardButton(f"Join {title}", url=link))
        except Exception:
            kb.row(InlineKeyboardButton(f"Join Channel {ch}", url=f"https://t.me/c/{str(ch).replace('-100','')}"))
    kb.row(InlineKeyboardButton("Verified", callback_data="fsub_verify"))
    return kb

def api_chat(prompt: str, uid: int, first_name: str = "", model: str = "fast") -> dict:
    try:
        if model == "fast":
            r = requests.get(
                f"{API_BASE}/",
                params={"g": prompt, "uid": uid, "first_name": first_name or "Jaan"},
                headers=_h(),
                timeout=30,
            )
        else:
            r = requests.get(
                f"{API_BASE}/",
                params={"c": prompt, "uid": uid, "first_name": first_name},
                headers=_h(),
                timeout=90,
            )
        return r.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def api_image(prompt: str, uid: int) -> dict:
    try:
        r = requests.get(f"{API_BASE}/", params={"i": prompt, "uid": uid},
                         headers=_h(), timeout=120)
        return r.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def api_stats() -> dict:
    try:
        r = requests.get(f"{API_BASE}/admin/stats", headers=_h(), timeout=10)
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def api_user_info(uid: int) -> dict:
    try:
        r = requests.get(f"{API_BASE}/admin/user", params={"uid": uid}, headers=_h(), timeout=10)
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _aio_params(extra: dict = None) -> dict:
    p = {}
    if DL_API_KEY:
        p["api"] = DL_API_KEY
    if extra:
        p.update(extra)
    return p

def dl_fetch(url: str)       -> dict: return _dl_get("/api/v1/dl",    {"url": url})
def dl_fetch_terabox(url)    -> dict: return _dl_get("/api/v1/tb",    {"url": url})
def dl_fetch_phub(url)       -> dict: return _dl_get("/api/v1/phub",  {"url": url})
def dl_fetch_xham(url)       -> dict: return _dl_get("/api/v1/xham",  {"url": url})
def dl_fetch_hcity(url)      -> dict: return _dl_get("/api/v1/hcity", {"url": url})

def _dl_get(path: str, extra: dict) -> dict:
    try:
        r = requests.get(f"{DL_API_BASE}{path}", params=_aio_params(extra), timeout=30)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def _quality_to_int(q) -> int:
    if not q: return 0
    try: return int(str(q).lower().replace("p","").strip())
    except Exception: return 0

def _filter_min_quality(medias: list) -> list:
    audios  = [m for m in medias if m.get("ext") in AUDIO_EXTS]
    videos  = [m for m in medias if m.get("ext") not in AUDIO_EXTS]
    filtered = [v for v in videos if _quality_to_int(v.get("quality")) >= MIN_VIDEO_HEIGHT]
    if not filtered and videos:
        filtered = [sorted(videos, key=lambda x: _quality_to_int(x.get("quality")))[0]]
    return filtered + audios

def get_best_media(medias: list) -> dict:
    filtered = _filter_min_quality(medias)
    audios = [m for m in filtered if m.get("ext") in AUDIO_EXTS]
    videos = [m for m in filtered if m.get("ext") not in AUDIO_EXTS]
    if videos:
        return sorted(videos, key=lambda x: _quality_to_int(x.get("quality")), reverse=True)[0]
    if audios:
        return sorted(audios, key=lambda x: _quality_to_int(x.get("quality")), reverse=True)[0]
    return medias[0] if medias else None

def get_file_size_mb(url: str):
    try:
        r = requests.head(url, timeout=8, allow_redirects=True)
        cl = r.headers.get("Content-Length")
        if cl:
            return int(cl) / (1024 * 1024)
    except Exception:
        pass
    return None

def _size_label(m: dict) -> str:
    s = m.get("size")
    if s:
        try:
            mb = int(s) / (1024 * 1024)
            return f" {mb:.0f}MB"
        except Exception:
            pass
    return ""

def _dl_quality_markup(medias: list) -> InlineKeyboardMarkup:
    filtered = _filter_min_quality(medias)
    if len(filtered) <= 1:
        return None
    kb  = InlineKeyboardMarkup()
    row = []
    for m in filtered[:8]:
        dl_url = m.get("url") or m.get("download_url","")
        if not dl_url: continue
        qual  = m.get("quality") or m.get("ext") or "?"
        icon  = "" if m.get("ext") in AUDIO_EXTS else ""
        label = f"{icon} {qual}{_size_label(m)}"
        row.append(InlineKeyboardButton(label, url=dl_url))
        if len(row) == 2:
            kb.row(*row); row = []
    if row: kb.row(*row)
    return kb

def send_ad_to_user(chat_id: int, uid: int):
    try:
        user = sync_get_user(uid)
        plan = user.get("plan", "free")
        if plan != "free":
            return
        if not sync_get_ads_enabled():
            return
        ads = sync_get_ads()
        if not ads:
            return
        import random
        ad = random.choice(ads)
        ad_type   = ad.get("type", "text")
        caption   = ad.get("caption", "")
        file_id   = ad.get("file_id", "")
        buttons   = ad.get("buttons", [])

        kb = None
        if buttons:
            kb = InlineKeyboardMarkup()
            row = []
            for btn in buttons:
                btn_text = btn.get("text","")
                btn_url  = btn.get("url","")
                if btn_text and btn_url:
                    row.append(InlineKeyboardButton(btn_text, url=btn_url))
                    if len(row) == 2:
                        kb.row(*row); row = []
            if row: kb.row(*row)

        parse_mode = "HTML" if caption else None

        if ad_type == "photo" and file_id:
            bot.send_photo(chat_id, file_id, caption=caption or None,
                           parse_mode=parse_mode, reply_markup=kb)
        elif ad_type == "video" and file_id:
            bot.send_video(chat_id, file_id, caption=caption or None,
                           parse_mode=parse_mode, reply_markup=kb)
        elif ad_type == "audio" and file_id:
            bot.send_audio(chat_id, file_id, caption=caption or None,
                           parse_mode=parse_mode, reply_markup=kb)
        elif ad_type == "text" and caption:
            bot.send_message(chat_id, caption, parse_mode=parse_mode, reply_markup=kb)
        elif caption:
            bot.send_message(chat_id, caption, parse_mode=parse_mode, reply_markup=kb)
    except Exception as e:
        print(f"[!] Ad send error: {e}")

def handle_download(msg, url: str):
    uid  = msg.from_user.id
    lang = ulang(uid)
    cd = sync_check_cooldown(uid)
    if cd > 0:
        bot.reply_to(msg, tf("error.cooldown", lang, seconds=cd)); return
    if not sync_check_dl_limit(uid):
        plan  = sync_get_user(uid).get("plan","free")
        limit = sync_get_config(f"{plan}_dl_day")
        bot.reply_to(msg, tf("error.dl_limit", lang, limit=limit)); return

    if is_terabox_url(url): _handle_terabox(msg, url, uid, lang); return
    if is_phub_url(url):    _handle_phub(msg, url, uid, lang);    return
    if is_xham_url(url):    _handle_xham(msg, url, uid, lang);    return
    if is_hcity_url(url):   _handle_hcity(msg, url, uid, lang);   return

    if not is_direct_dl_platform(url):
        thinking = bot.reply_to(msg, "Be Patient We Are Working...\n 10%", parse_mode="HTML")
        data = dl_fetch(url)
        _safe_delete(msg.chat.id, thinking.message_id)
        if not data.get("success"):
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton(" Open / Download", url=url))
            bot.reply_to(msg, "<b>Direct link ready</b>\n\n<i>Tap below to open or download</i>",
                         parse_mode="HTML", reply_markup=kb)
            send_ad_to_user(msg.chat.id, uid)
            return

        medias   = data.get("medias", [])
        title    = (data.get("title") or "Media")[:60]
        platform = (data.get("source") or "").capitalize()
        thumb    = data.get("thumbnail","")

        if not medias:
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton(" Open / Download", url=url))
            bot.reply_to(msg, f"<b>{title}</b>\n {platform}", parse_mode="HTML", reply_markup=kb)
            send_ad_to_user(msg.chat.id, uid)
            return

        sync_increment_count(uid, f"dl_{_day_key()}")
        filtered = _filter_min_quality(medias)
        kb  = InlineKeyboardMarkup()
        row = []
        seen = set()
        for m in filtered:
            dl_url = m.get("url") or m.get("download_url","")
            if not dl_url: continue
            ext    = (m.get("ext") or "").lower()
            height = m.get("height") or 0
            if ext not in AUDIO_EXTS:
                key = (height, ext)
                if height and ext == "webm" and (height, "mp4") in seen: continue
                seen.add(key)
            qual  = m.get("quality") or m.get("label") or ext.upper()
            icon  = "" if ext in AUDIO_EXTS else ""
            label = f"{icon} {qual}{_size_label(m)}"
            row.append(InlineKeyboardButton(label, url=dl_url))
            if len(row) == 2: kb.row(*row); row = []
        if row: kb.row(*row)
        caption = f" <b>{title}</b>\n {platform}"
        try:
            if thumb and thumb.startswith("http"):
                bot.send_photo(msg.chat.id, thumb, caption=caption,
                               parse_mode="HTML", reply_markup=kb,
                               reply_to_message_id=msg.message_id)
            else:
                bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
        send_ad_to_user(msg.chat.id, uid)
        return

    thinking = bot.reply_to(msg, "⏳ <b>Processing...</b>\n 20%", parse_mode="HTML")
    data = dl_fetch(url)
    _safe_delete(msg.chat.id, thinking.message_id)
    if not data.get("success"):
        err = data.get("error") or str(data.get("detail","unknown"))
        bot.reply_to(msg, tf("dl.error", lang, error=err)); return
    medias = data.get("medias",[])
    if not medias: bot.reply_to(msg, t("dl.no_media",lang)); return
    best = get_best_media(medias)
    if not best: bot.reply_to(msg, t("dl.no_media",lang)); return

    dl_url   = best.get("url") or best.get("download_url","")
    title    = (data.get("title") or "Media")[:60]
    platform = (data.get("source") or "").capitalize()
    ext      = best.get("ext","mp4")
    quality  = best.get("quality") or ext.upper()

    size_mb = None
    raw_size = best.get("size")
    if raw_size:
        try: size_mb = int(str(raw_size).strip()) / (1024 * 1024)
        except Exception: pass
    if size_mb is None:
        size_mb = get_file_size_mb(dl_url)

    vid_duration = best.get("duration") or 0
    vid_width    = best.get("width") or 0
    vid_height   = best.get("height") or 0
    try: vid_duration = int(vid_duration)
    except Exception: vid_duration = 0

    sync_increment_count(uid, f"dl_{_day_key()}")
    markup = _dl_quality_markup(medias)

    send_msg = None
    try:
        send_msg = bot.reply_to(msg, " <b>Downloading...</b>\n 50%", parse_mode="HTML")
        file_bytes = requests.get(dl_url, timeout=120).content
        actual_mb  = len(file_bytes) / (1024 * 1024)
        _safe_delete(msg.chat.id, send_msg.message_id); send_msg = None
        caption = (
            f"<b>{title}</b>\n"
            f" {platform}  ·   {quality}\n"
            f" {actual_mb:.1f} MB"
        )
        buf = io.BytesIO(file_bytes)
        buf.name = f"media.{ext}"
        if ext in AUDIO_EXTS:
            bot.send_audio(msg.chat.id, buf, caption=caption, title=title,
                           reply_to_message_id=msg.message_id, reply_markup=markup)
        else:
            bot.send_video(msg.chat.id, buf, caption=caption, duration=vid_duration or None,
                           width=vid_width or None, height=vid_height or None,
                           reply_to_message_id=msg.message_id,
                           supports_streaming=True, reply_markup=markup)
        send_ad_to_user(msg.chat.id, uid)
    except Exception as e:
        print(f"[!] Direct send failed: {e}")
        if send_msg:
            _safe_delete(msg.chat.id, send_msg.message_id)
        size_str = f"{size_mb:.1f} MB" if size_mb else "Unknown"
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton(" Download Now", url=dl_url))
        if markup:
            for row in markup.keyboard: kb.row(*row)
        bot.reply_to(msg, f" <b>{title}</b>\n {platform}  ·   {size_str}",
                     parse_mode="HTML", reply_markup=kb)
        send_ad_to_user(msg.chat.id, uid)


def _handle_phub(msg, url, uid, lang):
    thinking = bot.reply_to(msg, "⏳ <b>Fetching Pornhub...</b>", parse_mode="HTML")
    data = dl_fetch_phub(url)
    _safe_delete(msg.chat.id, thinking.message_id)
    if not data.get("success"):
        bot.reply_to(msg, "Pornhub: " + str(data.get("error","unknown"))); return
    title   = (data.get("title") or "Video")[:60]
    thumb   = data.get("thumbnail","")
    dur     = data.get("duration") or 0
    formats = data.get("formats") or []
    direct  = [f for f in formats if not str(f.get("format_id","")).startswith("hls")]
    if not direct: direct = formats
    if not direct: bot.reply_to(msg,"No formats found."); return
    kb = InlineKeyboardMarkup(); row = []
    for f in direct:
        furl = f.get("url","")
        if not furl: continue
        label = " " + str(f.get("format_id") or str(f.get("height","")) + "p")
        row.append(InlineKeyboardButton(label, url=furl))
        if len(row)==2: kb.row(*row); row=[]
    if row: kb.row(*row)
    sync_increment_count(uid, f"dl_{_day_key()}")
    dur_str = ""
    try:
        d = int(dur)
        dur_str = f"⏱ {d//3600}h {(d%3600)//60}m" if d>=3600 else (f"⏱ {d//60}m {d%60}s" if d>0 else "")
    except Exception: pass
    caption = f" <b>{title}</b>" + (f"\n{dur_str}" if dur_str else "") + "\n Pornhub"
    if thumb and thumb.startswith("http"):
        try:
            bot.send_photo(msg.chat.id, thumb, caption=caption, parse_mode="HTML",
                           reply_markup=kb, reply_to_message_id=msg.message_id)
            send_ad_to_user(msg.chat.id, uid)
            return
        except Exception: pass
    bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
    send_ad_to_user(msg.chat.id, uid)


def _handle_xham(msg, url, uid, lang):
    thinking = bot.reply_to(msg, "⏳ <b>Fetching XHamster...</b>", parse_mode="HTML")
    data = dl_fetch_xham(url)
    _safe_delete(msg.chat.id, thinking.message_id)
    if not data.get("success"):
        bot.reply_to(msg, "XHamster: " + str(data.get("error","unknown"))); return
    title   = (data.get("title") or "Video")[:60]
    thumb   = data.get("thumbnail","")
    streams = data.get("streams") or {}
    if not streams: bot.reply_to(msg,"No streams found."); return
    sync_increment_count(uid, f"dl_{_day_key()}")
    def _hh(k):
        try: return int(k.replace("p",""))
        except: return 0
    kb = InlineKeyboardMarkup(); row = []
    for q in sorted(streams.keys(), key=_hh):
        surl = streams[q]
        if not surl: continue
        row.append(InlineKeyboardButton(" " + q, url=surl))
        if len(row)==2: kb.row(*row); row=[]
    if row: kb.row(*row)
    caption = f" <b>{title}</b>\n XHamster"
    if thumb and thumb.startswith("http"):
        try:
            bot.send_photo(msg.chat.id, thumb, caption=caption, parse_mode="HTML",
                           reply_markup=kb, reply_to_message_id=msg.message_id)
            send_ad_to_user(msg.chat.id, uid)
            return
        except Exception: pass
    bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
    send_ad_to_user(msg.chat.id, uid)


def _handle_hcity(msg, url, uid, lang):
    thinking = bot.reply_to(msg, "⏳ <b>Fetching HentaiCity...</b>", parse_mode="HTML")
    data = dl_fetch_hcity(url)
    _safe_delete(msg.chat.id, thinking.message_id)
    if not data.get("success"):
        bot.reply_to(msg, f"Error: {data.get('error','unknown')}"); return
    title   = (data.get("title") or "Video")[:60]
    thumb   = data.get("thumbnail","")
    m3u8    = data.get("m3u8","")
    trailer = data.get("trailer","")
    sync_increment_count(uid, f"dl_{_day_key()}")
    kb = InlineKeyboardMarkup()
    if m3u8:    kb.row(InlineKeyboardButton(" Stream (M3U8)", url=m3u8))
    if trailer: kb.row(InlineKeyboardButton(" Trailer", url=trailer))
    caption = f" <b>{title}</b>\n HentaiCity"
    try:
        if thumb and thumb.startswith("http"):
            bot.send_photo(msg.chat.id, thumb, caption=caption, parse_mode="HTML",
                           reply_markup=kb, reply_to_message_id=msg.message_id)
        else:
            bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
    except Exception:
        bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
    send_ad_to_user(msg.chat.id, uid)


def _handle_terabox(msg, url, uid, lang):
    thinking = bot.reply_to(msg, "⏳ <b>Fetching Terabox...</b>", parse_mode="HTML")
    data = dl_fetch_terabox(url)
    _safe_delete(msg.chat.id, thinking.message_id)
    if not data.get("success"):
        bot.reply_to(msg, f"Terabox: {data.get('error','unknown')}"); return
    files = data.get("list",[])
    if not files: bot.reply_to(msg,"No files found."); return
    sync_increment_count(uid, f"dl_{_day_key()}")
    for f in files[:5]:
        name    = f.get("name","File")
        dl_url  = f.get("normal_dlink") or f.get("download_url") or f.get("url","")
        zip_url = f.get("zip_dlink","")
        thumb   = f.get("thumbnail","")
        ftype   = f.get("type","")
        size_str = ""
        sf = f.get("size_formatted")
        if sf: size_str = f" · {sf}"
        else:
            raw = f.get("size")
            if raw:
                try: size_str = f" · {int(raw)/(1024*1024):.1f} MB"
                except Exception: size_str = f" · {raw}"
        icon = "" if ftype=="video" else ("" if ftype=="audio" else "")
        caption = f"{icon} <b>{name}</b>{size_str}\n Terabox"
        kb = InlineKeyboardMarkup()
        if dl_url:  kb.row(InlineKeyboardButton(" Download", url=dl_url))
        if zip_url: kb.row(InlineKeyboardButton(" Download ZIP", url=zip_url))
        try:
            if thumb and thumb.startswith("http"):
                bot.send_photo(msg.chat.id, thumb, caption=caption, parse_mode="HTML",
                               reply_markup=kb, reply_to_message_id=msg.message_id)
            else:
                bot.reply_to(msg, caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            bot.reply_to(msg, caption, reply_markup=kb)
    send_ad_to_user(msg.chat.id, uid)


def _safe_delete(chat_id, msg_id):
    try: bot.delete_message(chat_id, msg_id)
    except Exception: pass

def _get_overall_stats() -> str:
    st = sync_get_all_users_stats()
    from datetime import date
    import calendar
    today = date.today()
    return (
        "\n"
        "      ʙᴏᴛ ᴛᴀᴛɪᴛɪᴄ\n"
        "\n\n"
        f" Total Users  ›  <b>{st['total']}</b>\n"
        f"  Free         ›  <b>{st.get('free',0)}</b>\n"
        f"  Basic        ›  <b>{st.get('basic',0)}</b>\n"
        f"  Pro          ›  <b>{st.get('pro',0)}</b>\n"
        f"  Ultra        ›  <b>{st.get('ultra',0)}</b>\n"
        f"  Ultra Pro    ›  <b>{st.get('ultra_pro',0)}</b>\n\n"
        f" Banned       ›  <b>{st.get('banned',0)}</b>\n"
        f" Restricted   ›  <b>{st.get('restricted',0)}</b>\n\n"
        f"  {today.strftime('%d %b %Y')}"
    )

def _get_dl_stats() -> str:
    from models.db import get_sync_db
    day = _day_key()
    pipeline = [
        {"$project": {"dl_today": f"$counts.dl_{day}"}},
        {"$group": {"_id": None, "total": {"$sum": "$dl_today"}}},
    ]
    res         = list(get_sync_db().users.aggregate(pipeline))
    total_today = res[0]["total"] if res else 0
    return (
        "<b>Download Stats — Today</b>\n\n"
        f"  Downloads    ›  <b>{total_today}</b>"
    )

def _do_broadcast(origin_msg, text: str):
    from models.db import get_sync_db
    users = list(get_sync_db().users.find({}, {"uid": 1}))
    sent = failed = 0
    status_msg = bot.reply_to(origin_msg, f"Broadcasting to <b>{len(users)}</b> users...", parse_mode="HTML")
    for u in users:
        try:
            bot.send_message(u["uid"], text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
    bar_s = "" * min(10, round(sent/max(len(users),1)*10))
    bar_f = "" * (10 - len(bar_s))
    try:
        bot.edit_message_text(
            f"<b>Broadcast Complete!</b>\n\n"
            f"{bar_s}{bar_f}\n\n"
            f" Sent    ›  <b>{sent}</b>\n"
            f" Failed  ›  <b>{failed}</b>",
            origin_msg.chat.id, status_msg.message_id,
            parse_mode="HTML", reply_markup=back_markup("menu_admin")
        )
    except Exception:
        pass

def main_menu_markup(uid: int) -> InlineKeyboardMarkup:
    lang = ulang(uid)
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(t("btn.status", lang),    callback_data="menu_status"),
        InlineKeyboardButton(t("btn.subscribe", lang), callback_data="menu_sub"),
    )
    kb.row(
        InlineKeyboardButton(t("btn.help", lang),      callback_data="menu_help"),
        InlineKeyboardButton("Downloader",             callback_data="menu_dl"),
    )
    kb.row(
        InlineKeyboardButton(t("btn.language", lang),  callback_data="menu_lang"),
    )
    if is_admin(uid):
        kb.row(InlineKeyboardButton(t("btn.admin", lang), callback_data="menu_admin"))
    return kb

def back_markup(dest="menu_back", lang="en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(t("btn.back", lang), callback_data=dest))
    return kb

def admin_panel_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Stats",         callback_data="adm_stats"),
        InlineKeyboardButton("DL Stats",      callback_data="adm_dl_stats"),
    )
    kb.row(
        InlineKeyboardButton("All Users",     callback_data="adm_all_users"),
        InlineKeyboardButton("Broadcast",     callback_data="adm_bcast_prompt"),
    )
    kb.row(
        InlineKeyboardButton("User Info",     callback_data="adm_user_prompt"),
        InlineKeyboardButton("History",       callback_data="adm_hist_prompt"),
    )
    kb.row(
        InlineKeyboardButton("Set Plan",      callback_data="adm_plan_prompt"),
        InlineKeyboardButton("ChatBot",       callback_data="adm_chatbot"),
    )
    kb.row(
        InlineKeyboardButton("Ban",           callback_data="adm_ban_prompt"),
        InlineKeyboardButton("Unban",          callback_data="adm_unban_prompt"),
    )
    kb.row(
        InlineKeyboardButton("Restrict",      callback_data="adm_restrict_prompt"),
        InlineKeyboardButton("Unrestrict",    callback_data="adm_unrestrict_prompt"),
    )
    kb.row(
        InlineKeyboardButton("FSub Settings", callback_data="adm_fsub"),
        InlineKeyboardButton("Config",        callback_data="adm_config"),
    )
    kb.row(
        InlineKeyboardButton(" Ads Manager",   callback_data="adm_ads"),
        InlineKeyboardButton(" Clear Cache",   callback_data="adm_clear_cache"),
    )
    kb.row(InlineKeyboardButton("Back", callback_data="menu_back"))
    return kb

def plan_select_markup(uid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(" Free",      callback_data=f"adm_setplan_{uid}_free"),
        InlineKeyboardButton(" Basic",     callback_data=f"adm_setplan_{uid}_basic"),
    )
    kb.row(
        InlineKeyboardButton(" Pro",        callback_data=f"adm_setplan_{uid}_pro"),
        InlineKeyboardButton(" Ultra",      callback_data=f"adm_setplan_{uid}_ultra"),
    )
    kb.row(
        InlineKeyboardButton(" Ultra Pro",  callback_data=f"adm_setplan_{uid}_ultra_pro"),
    )
    kb.row(InlineKeyboardButton("Back", callback_data="menu_admin"))
    return kb

def user_action_markup(target_uid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Set Plan",   callback_data=f"adm_planmenu_{target_uid}"),
        InlineKeyboardButton("History",    callback_data=f"adm_histview_{target_uid}"),
    )
    kb.row(
        InlineKeyboardButton("Ban",        callback_data=f"adm_ban_{target_uid}"),
        InlineKeyboardButton("Unban",       callback_data=f"adm_unban_{target_uid}"),
    )
    kb.row(
        InlineKeyboardButton("Restrict",   callback_data=f"adm_restrict_{target_uid}"),
        InlineKeyboardButton("Unrestrict", callback_data=f"adm_unrestrict_{target_uid}"),
    )
    kb.row(InlineKeyboardButton("‹ Back to Admin", callback_data="menu_admin"))
    return kb

def fsub_panel_markup() -> InlineKeyboardMarkup:
    enabled = sync_fsub_enabled()
    channels = sync_get_fsub_channels()
    kb = InlineKeyboardMarkup()
    if enabled:
        kb.row(InlineKeyboardButton(" Disable FSub", callback_data="fsub_off"))
    else:
        kb.row(InlineKeyboardButton(" Enable FSub",  callback_data="fsub_on"))
    kb.row(InlineKeyboardButton(" Add Channel",    callback_data="fsub_add_prompt"))
    for ch in channels:
        try:
            chat  = bot.get_chat(ch)
            title = getattr(chat,"title",str(ch))[:20]
        except Exception:
            title = str(ch)
        kb.row(InlineKeyboardButton(f" Remove: {title}", callback_data=f"fsub_rm_{ch}"))
    kb.row(InlineKeyboardButton("Back", callback_data="menu_admin"))
    return kb

def chatbot_toggle_markup(group_id=None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    suffix = f"_{group_id}" if group_id else "_global"
    kb.row(
        InlineKeyboardButton("Enable",  callback_data=f"cb_enable{suffix}"),
        InlineKeyboardButton("Disable", callback_data=f"cb_disable{suffix}"),
    )
    kb.row(InlineKeyboardButton("Back", callback_data="menu_admin"))
    return kb

def ads_panel_markup() -> InlineKeyboardMarkup:
    ads_on = sync_get_ads_enabled()
    kb = InlineKeyboardMarkup()
    if ads_on:
        kb.row(InlineKeyboardButton(" Disable Ads", callback_data="ads_off"))
    else:
        kb.row(InlineKeyboardButton(" Enable Ads",  callback_data="ads_on"))
    kb.row(InlineKeyboardButton(" Add New Ad", callback_data="ads_add_prompt"))
    ads = sync_get_ads()
    for ad in ads:
        ad_id   = str(ad.get("_id",""))
        ad_type = ad.get("type","text")
        preview = (ad.get("caption","") or "")[:20] or f"[{ad_type}]"
        icon    = {"photo":"","video":"","audio":"","text":""}.get(ad_type,"")
        kb.row(InlineKeyboardButton(f"{icon} {preview}…", callback_data=f"ads_view_{ad_id}"),
               InlineKeyboardButton(" Delete",          callback_data=f"ads_del_{ad_id}"))
    kb.row(InlineKeyboardButton("Back", callback_data="menu_admin"))
    return kb

_pending = {}

def _expect(uid: int, action: str, **kw):
    _pending[uid] = {"action": action, **kw}

def _get_pending(uid: int) -> dict:
    return _pending.pop(uid, None)

def _peek_pending(uid: int) -> dict:
    return _pending.get(uid, None)

@bot.message_handler(commands=["start","help"])
def cmd_start(msg):
    uid  = msg.from_user.id
    sync_get_user(uid)
    lang = ulang(uid)
    name = msg.from_user.first_name or "there"

    not_joined = check_fsub(uid, msg.chat.id)
    if not_joined:
        bot.reply_to(
            msg,
            "\n"
            "   ᴊᴏɪɴ ʀᴇQᴜɪʀᴇᴅ\n"
            "\n\n"
            " Please join the required channels/groups to use this bot.",
            reply_markup=fsub_markup(not_joined),
            parse_mode="HTML",
        )
        return

    wv = sync_get_welcome_video()
    if wv.get("file_id"):
        caption = wv.get("caption") or _build_welcome(uid, name, lang)
        kb = main_menu_markup(uid)
        try:
            bot.send_video(msg.chat.id, wv["file_id"], caption=caption,
                           parse_mode="HTML", reply_markup=kb)
            return
        except Exception as e:
            print(f"[!] Welcome video send failed: {e}")

    text = _build_welcome(uid, name, lang)
    bot.reply_to(msg, text, reply_markup=main_menu_markup(uid), parse_mode="HTML")

def _build_welcome(uid: int, name: str, lang: str) -> str:
    plan = sync_get_user(uid).get("plan","free")
    badge = PLAN_BADGE.get(plan, plan)
    return (
        "\n"
        "  ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ\n"
        "\n\n"
        f" Welcome, <b>{name}</b>!\n"
        f"Plan  ›  <b>{badge}</b>\n\n"
        "  Send any message  →  AI replies\n"
        "  /img &lt;prompt&gt;  →  Generate image\n"
        "  /dl &lt;url&gt;  →  Download media\n"
        "  /tb &lt;url&gt;  →  Terabox download\n\n"
        "  <i>Powered by @TEAM_X_OG</i>"
    )

@bot.message_handler(commands=["swv"])
def cmd_swv(msg):
    uid = msg.from_user.id
    if not is_admin(uid):
        bot.reply_to(msg, " <b>Admins only.</b>", parse_mode="HTML"); return

    reply = msg.reply_to_message
    if not reply or not reply.video:
        bot.reply_to(
            msg,
            " <b>Usage:</b>  Reply to a video with <code>/swv</code>\n\n"
            "The video (with its caption) will be saved as the welcome message.\n"
            "Inline buttons from /start menu will be added automatically.",
            parse_mode="HTML"
        ); return

    file_id = reply.video.file_id
    caption = reply.caption or ""
    sync_set_welcome_video(file_id, caption)
    bot.send_message(
        msg.chat.id,
        "<b>Welcome video saved!</b>\n\n"
        "New users will see this video on /start.\n"
        f" Caption: <code>{caption[:100] or '(none)'}</code>\n\n"
        "Use /swv on a new video to update, or clear via admin panel.",
        parse_mode="HTML",
        reply_markup=admin_panel_markup()
    )

def lang_select_markup() -> InlineKeyboardMarkup:
    kb   = InlineKeyboardMarkup()
    row  = []
    for code, name, _ in LANGUAGES:
        row.append(InlineKeyboardButton(name, callback_data=f"cb_lang_{code}"))
        if len(row) == 3:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    return kb

@bot.message_handler(commands=["lang"])
def cmd_lang(msg):
    uid  = msg.from_user.id
    lang = ulang(uid)
    bot.reply_to(
        msg,
        f"<b>{t('lang.header', lang)}</b>",
        parse_mode="HTML",
        reply_markup=lang_select_markup()
    )

MODEL_LABELS = {
    "fast": " Fast Response  (Llama 3.3 70B)",
}

def umodel(uid: int) -> str:
    return sync_get_user(uid).get("ai_model", "fast")

def model_select_markup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    return kb

def _model_text(current: str) -> str:
    return (
        "\n"
        "     ᴀɪ ᴍᴏᴅᴇʟ ᴇʟᴇᴄᴛᴏʀ\n"
        "\n\n"
        " <b>Fast Response (Llama 3.3 70B)</b> — Active\n\n"
        "<i>GPT-4 model is currently under maintenance.\n"
        "Only Groq (Fast) is available right now.</i>"
    )

@bot.message_handler(commands=["model"])
def cmd_model(msg):
    uid = msg.from_user.id
    bot.reply_to(msg, _model_text("fast"), parse_mode="HTML")

@bot.message_handler(commands=["sub"])
def cmd_sub(msg):
    uid  = msg.from_user.id
    lang = ulang(uid)
    plan = sync_get_user(uid).get("plan","free")
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton(" Upgrade Now", url="https://t.me/Team_X_Og"))
    kb.row(InlineKeyboardButton("Back", callback_data="menu_back"))
    bot.reply_to(msg, _build_plans_text(plan), reply_markup=kb, parse_mode="HTML")

def _build_plans_text(current_plan: str) -> str:
    def _check(plan): return "  You" if plan == current_plan else ""
    return (
        "\n"
        "        ᴜʙᴄʀɪᴘᴛɪᴏɴ ᴘʟᴀɴ\n"
        "\n\n"

        f" <b>Free</b>{_check('free')}\n"
        "    Downloads   5/day\n"
        "   ⏱ Cooldown   5 min\n"
        "    PM/month   150\n"
        "    Images/day  2\n\n"

        f" <b>Basic</b>{_check('basic')}\n"
        "    Downloads   15/day\n"
        "   ⏱ Cooldown   2 min\n"
        "    PM/month   300\n"
        "    Images/day  5\n\n"

        f" <b>Pro</b>{_check('pro')}\n"
        "    Downloads   30/day\n"
        "   ⏱ Cooldown   1 min\n"
        "    PM/month   1000\n"
        "    Images/day  20\n\n"

        f" <b>Ultra</b>{_check('ultra')}\n"
        "    Downloads   100/day\n"
        "   ⏱ Cooldown   10 sec\n"
        "    PM/month   5000\n"
        "    Images/day  50\n\n"

        f" <b>Ultra Pro</b>{_check('ultra_pro')}\n"
        "    Downloads   ∞ Unlimited\n"
        "   ⏱ Cooldown   None\n"
        "    PM/month   ∞ Unlimited\n"
        "    Images/day  ∞ Unlimited\n\n"

        "\n"
        "Contact @TEAM_X_OG to upgrade."
    )

@bot.message_handler(commands=["status"])
def cmd_status(msg):
    uid  = msg.from_user.id
    lang = ulang(uid)
    s    = sync_get_usage_stats(uid)
    from datetime import date
    import calendar
    today    = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    reset    = f"{today.year}-{today.month:02d}-{last_day}"
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(" Upgrade", callback_data="menu_sub"),
        InlineKeyboardButton("Back",     callback_data="menu_back"),
    )
    bot.reply_to(msg, _build_status_text(s, reset), reply_markup=kb, parse_mode="HTML")

def _build_status_text(s: dict, reset: str) -> str:
    plan    = s["plan"]
    badge   = PLAN_BADGE.get(plan, plan)
    unlim   = s.get("unlimited", False)
    pm_bar  = _bar(s["pm_used"],  s["pm_limit"])
    grp_bar = _bar(s["grp_used"], s["grp_limit"])
    img_bar = _bar(s["img_used"], s["img_limit"])
    dl_bar  = _bar(s["dl_used"],  s["dl_limit"])
    cd_sec  = s.get("cooldown", 0)
    cd_str  = "None " if cd_sec == 0 else (f"{cd_sec//60}m {cd_sec%60}s" if cd_sec>=60 else f"{cd_sec}s")
    return (
        "\n"
        "         ᴜᴀɢᴇ ᴛᴀᴛᴜ\n"
        "\n\n"
        f" Plan         ›  <b>{badge}</b>\n\n"
        f"  PM (month)\n"
        f"    {pm_bar}  {s['pm_used']}/{s['pm_limit']}\n\n"
        f" Group (month)\n"
        f"    {grp_bar}  {s['grp_used']}/{s['grp_limit']}\n\n"
        f"  Images (day)\n"
        f"    {img_bar}  {s['img_used']}/{s['img_limit']}\n\n"
        f"  Downloads (day)\n"
        f"    {dl_bar}  {s['dl_used']}/{s['dl_limit']}\n\n"
        f"⏱  Cooldown    ›  <b>{cd_str}</b>\n"
        f"  Resets on   ›  <b>{reset}</b>"
    )

@bot.message_handler(commands=["img"])
def cmd_img(msg):
    uid    = msg.from_user.id
    lang   = ulang(uid)
    prompt = msg.text.partition(" ")[2].strip()
    if not prompt:
        bot.reply_to(msg, " Usage: <code>/img your prompt here</code>", parse_mode="HTML"); return
    if not sync_check_img_limit(uid):
        plan  = sync_get_user(uid).get("plan","free")
        limit = sync_get_config(f"{plan}_img_day")
        bot.reply_to(msg, tf("error.img_limit", lang, limit=limit)); return
    thinking = bot.reply_to(msg, " <b>Generating...</b>\n 40%", parse_mode="HTML")
    result   = api_image(prompt, uid)
    _safe_delete(msg.chat.id, thinking.message_id)
    if result.get("status") == "limit":
        bot.reply_to(msg, tf("error.img_limit", lang, limit=result.get("limit","?"))); return
    if result.get("status") == "success":
        url = result.get("image_url","")
        sync_set_last_msg(uid)
        if url.startswith("http"):
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton(" Open Full Image", url=url))
            try:
                bot.send_photo(msg.chat.id, url, reply_to_message_id=msg.message_id, reply_markup=kb)
            except Exception:
                bot.reply_to(msg, f" <b>Image ready:</b>\n{url}", parse_mode="HTML", reply_markup=kb)
        else:
            bot.reply_to(msg, t("ai.no_response",lang))
    else:
        err = result.get("message","unknown")
        bot.reply_to(msg, t("error.timeout",lang) if err=="timeout" else tf("error.api_error",lang,message=err))

@bot.message_handler(commands=["dl","download"])
def cmd_dl(msg):
    uid  = msg.from_user.id
    lang = ulang(uid)
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton("Back", callback_data="menu_back"))
        bot.reply_to(msg,
            " <b>Downloader</b>\n\n"
            " <b>Direct send:</b>  Instagram · TikTok · Pinterest\n"
            " <b>Link only:</b>  YouTube · Facebook · Twitter/X · Reddit\n"
            " <b>Terabox:</b>  /tb &lt;url&gt;\n\n"
            "Just send a link or: <code>/dl &lt;url&gt;</code>",
            parse_mode="HTML", reply_markup=kb); return
    handle_download(msg, args[1].strip())

@bot.message_handler(commands=["tb","terabox"])
def cmd_terabox(msg):
    uid  = msg.from_user.id
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(msg, "Usage: <code>/tb &lt;terabox_url&gt;</code>", parse_mode="HTML"); return
    handle_download(msg, args[1].strip())

@bot.message_handler(commands=["chatbot"])
def cmd_chatbot(msg):
    uid     = msg.from_user.id
    chat_id = msg.chat.id
    is_grp  = msg.chat.type in ("group","supergroup")
    if is_grp:
        try:
            member = bot.get_chat_member(chat_id, uid)
            if member.status not in ("administrator","creator"):
                bot.reply_to(msg, " Only group admins can toggle chatbot."); return
        except Exception:
            bot.reply_to(msg, " Cannot verify admin status."); return
    else:
        if not is_admin(uid):
            bot.reply_to(msg, " Only bot admins can change global chatbot setting."); return
    args = msg.text.split()
    if len(args) < 2:
        current = sync_get_chatbot_enabled(chat_id if is_grp else None)
        status  = "Enabled" if current else "Disabled"
        scope   = f"Group: {msg.chat.title}" if is_grp else "Global (PM)"
        bot.reply_to(msg, f"<b>ChatBot</b>\n {scope}\nStatus: {status}\n\nUse /chatbot on|off",
                     parse_mode="HTML",
                     reply_markup=chatbot_toggle_markup(chat_id if is_grp else None)); return
    arg = args[1].lower()
    if arg in ("on","true","enable","1","yes"):   enable = True
    elif arg in ("off","false","disable","0","no"): enable = False
    else: bot.reply_to(msg," Usage: /chatbot on | off"); return
    sync_set_chatbot_enabled(chat_id if is_grp else None, enable)
    state = "Enabled" if enable else "Disabled"
    scope = "in this group" if is_grp else "globally"
    bot.reply_to(msg, f"ChatBot {state} {scope}.", parse_mode="HTML")

@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    uid = msg.from_user.id
    if not is_admin(uid):
        bot.reply_to(msg, " <b>Admins only.</b>", parse_mode="HTML"); return
        
    bot.send_message(
        msg.chat.id,
        "\n"
        "         ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ\n"
        "\n\n"
        "Select an action below:",
        parse_mode="HTML",
        reply_markup=admin_panel_markup()
    )

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid  = call.from_user.id
    lang = ulang(uid)
    d    = call.data

    def answer(txt=None): 
        try:
            bot.answer_callback_query(call.id, txt)
        except Exception:
            pass

    def edit(text, markup=None, parse_mode="HTML"):
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=markup, parse_mode=parse_mode)
        except Exception as e:
            if "stale" in str(e).lower() or "message" in str(e).lower():
                try:
                    bot.send_message(call.message.chat.id, text,
                                     reply_markup=markup, parse_mode=parse_mode)
                except Exception:
                    pass

    if d == "fsub_verify":
        not_joined = check_fsub(uid, call.message.chat.id)
        if not_joined:
            answer("Not joined all channels yet.")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                              reply_markup=fsub_markup(not_joined))
            except Exception: pass
        else:
            answer("Verified!")
            name = call.from_user.first_name or "there"
            wv = sync_get_welcome_video()
            if wv.get("file_id"):
                caption = wv.get("caption") or _build_welcome(uid, name, lang)
                try:
                    bot.send_video(call.message.chat.id, wv["file_id"], caption=caption,
                                   parse_mode="HTML", reply_markup=main_menu_markup(uid)); return
                except Exception: pass
            edit(_build_welcome(uid, name, lang), main_menu_markup(uid))
        return

    if d.startswith("cb_lang_"):
        chosen = d[len("cb_lang_"):]
        if chosen in SUPPORTED:
            sync_update_user(uid, {"lang": chosen})
            lang = chosen
            answer()
            name = call.from_user.first_name or "there"
            edit(
                f"<b>{tf('lang.set', lang, lang=chosen)}</b>\n\n"
                + _build_welcome(uid, name, lang),
                main_menu_markup(uid)
            )
        else:
            answer("Unknown language")
        return

    if d == "menu_lang":
        answer()
        edit(
            f"<b>{t('lang.header', lang)}</b>",
            lang_select_markup()
        )
        return

    if d in ("model_fast", "model_slow"):
        answer("Only Groq (Fast) is available right now.")
        return

    if d == "menu_back":
        answer()
        name = call.from_user.first_name or "there"
        edit(_build_welcome(uid, name, lang), main_menu_markup(uid))

    elif d == "menu_status":
        answer()
        s = sync_get_usage_stats(uid)
        from datetime import date; import calendar
        today    = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        reset    = f"{today.year}-{today.month:02d}-{last_day}"
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton(t("btn.upgrade", lang), callback_data="menu_sub"),
               InlineKeyboardButton(t("btn.back",    lang), callback_data="menu_back"))
        edit(_build_status_text(s, reset), kb)

    elif d == "menu_sub":
        answer()
        plan = sync_get_user(uid).get("plan","free")
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton(t("btn.upgrade", lang), url="https://t.me/Team_X_Og"))
        kb.row(InlineKeyboardButton(t("btn.back",    lang), callback_data="menu_back"))
        edit(_build_plans_text(plan), kb)

    elif d == "menu_help":
        answer()
        edit(
            "\n"
            "           HELP\n"
            "\n\n"
            "/start   — Main menu\n"
            "/img &lt;prompt&gt;  — Generate image\n"
            "/dl &lt;url&gt;  — Download media\n"
            "/tb &lt;url&gt;  — Terabox download\n"
            "/sub  — View plans\n"
            "/status  — Your usage stats\n"
            "/lang  — Change language\n"
            "/chatbot on|off  — Toggle AI chat\n"
            "/swv  (reply to video)  — Set welcome video",
            back_markup(lang=lang)
        )

    elif d == "menu_dl":
        answer()
        edit(
            "<b>Downloader</b>\n\n"
            "<b>Direct send:</b>  Instagram · TikTok · Pinterest\n"
            "<b>Link only:</b>  YouTube · FB · Twitter · Reddit · Vimeo\n"
            "<b>Terabox:</b>  /tb &lt;url&gt;\n\n"
            "Just send a link or /dl &lt;url&gt;",
            back_markup(lang=lang)
        )

    elif d == "menu_admin":
        answer()
        if not is_admin(uid):
            answer("Not admin"); return
        edit(
            "\n"
            "        ADMIN PANEL\n"
            "\n\n"
            "Select an action below:",
            admin_panel_markup()
        )

    elif d == "adm_stats" and is_admin(uid):
        answer()
        edit(_get_overall_stats(), back_markup("menu_admin"))

    elif d == "adm_dl_stats" and is_admin(uid):
        answer()
        edit(_get_dl_stats(), back_markup("menu_admin"))

    elif d == "adm_config" and is_admin(uid):
        answer()
        cfg   = sync_get_all_config()
        lines = ["<b>Bot Config</b>\n"]
        for k, v in sorted(cfg.items()):
            lines.append(f"  <code>{k}</code>  =  <b>{v}</b>")
        edit("\n".join(lines), back_markup("menu_admin"))

    elif d == "adm_all_users" and is_admin(uid):
        answer()
        from models.db import get_sync_db
        users = list(get_sync_db().users.find(
            {}, {"uid":1,"plan":1,"banned":1,"restricted":1}
        ).sort("created",-1).limit(20))
        lines = ["<b>Recent Users</b> (last 20)\n"]
        for u in users:
            icons = PLAN_EMOJI.get(u.get("plan","free"),"?")
            ban   = "" if u.get("banned") else ("" if u.get("restricted") else "")
            lines.append(f"{ban} {icons} <code>{u['uid']}</code>")
        edit("\n".join(lines), back_markup("menu_admin"))

    elif d == "adm_bcast_prompt" and is_admin(uid):
        answer()
        _expect(uid, "broadcast")
        edit(
            "<b>Broadcast</b>\n\nSend your message (HTML supported).\nType /cancel to abort.",
            back_markup("menu_admin")
        )

    elif d == "adm_user_prompt" and is_admin(uid):
        answer()
        _expect(uid, "user_info")
        edit("<b>User Info</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d == "adm_hist_prompt" and is_admin(uid):
        answer()
        _expect(uid, "history")
        edit("<b>User History</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d == "adm_plan_prompt" and is_admin(uid):
        answer()
        _expect(uid, "plan_uid")
        edit("<b>Set Plan</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d.startswith("adm_planmenu_") and is_admin(uid):
        target = int(d.split("_")[-1])
        answer()
        u = sync_get_user(target)
        current = u.get("plan","free")
        edit(
            f"<b>Set Plan</b>\n\n"
            f"User: <code>{target}</code>\n"
            f"Current: <b>{PLAN_BADGE.get(current,current)}</b>\n\n"
            f"Select new plan:",
            plan_select_markup(target)
        )

    elif d.startswith("adm_setplan_") and is_admin(uid):
        parts  = d.split("_")
        target = int(parts[2])
        plan   = "_".join(parts[3:])
        if plan not in VALID_PLANS:
            answer("Invalid plan"); return
        sync_set_user_plan(target, plan)
        sync_log_user_action(target, "plan_set", plan)
        answer(f"Plan set to {plan}")
        edit(
            f"<b>Plan Updated</b>\n\n"
            f"User: <code>{target}</code>\n"
            f"New plan: <b>{PLAN_BADGE.get(plan,plan)}</b>",
            user_action_markup(target)
        )

    elif d == "adm_ban_prompt" and is_admin(uid):
        answer(); _expect(uid,"ban")
        edit("<b>Ban User</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d == "adm_unban_prompt" and is_admin(uid):
        answer(); _expect(uid,"unban")
        edit("<b>Unban User</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d.startswith("adm_ban_") and not d.startswith("adm_ban_prompt") and is_admin(uid):
        target = int(d.replace("adm_ban_",""))
        sync_ban_user(target)
        answer(f"Banned {target}")
        edit(f"User <code>{target}</code> has been <b>banned</b>.",
             user_action_markup(target))

    elif d.startswith("adm_unban_") and not d.startswith("adm_unban_prompt") and is_admin(uid):
        target = int(d.replace("adm_unban_",""))
        sync_unban_user(target)
        answer(f"Unbanned {target}")
        edit(f"User <code>{target}</code> has been <b>unbanned</b>.",
             user_action_markup(target))

    elif d == "adm_restrict_prompt" and is_admin(uid):
        answer(); _expect(uid,"restrict")
        edit("<b>Restrict User</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d == "adm_unrestrict_prompt" and is_admin(uid):
        answer(); _expect(uid,"unrestrict")
        edit("<b>Unrestrict User</b>\n\nSend the user ID:", back_markup("menu_admin"))

    elif d.startswith("adm_restrict_") and not d.startswith("adm_restrict_prompt") and is_admin(uid):
        target = int(d.replace("adm_restrict_",""))
        sync_restrict_user(target)
        answer(f"Restricted {target}")
        edit(f"User <code>{target}</code> is now <b>restricted</b>.", user_action_markup(target))

    elif d.startswith("adm_unrestrict_") and not d.startswith("adm_unrestrict_prompt") and is_admin(uid):
        target = int(d.replace("adm_unrestrict_",""))
        sync_unrestrict_user(target)
        answer(f"Unrestricted {target}")
        edit(f"User <code>{target}</code> has been <b>unrestricted</b>.", user_action_markup(target))

    elif d.startswith("adm_histview_") and is_admin(uid):
        target = int(d.replace("adm_histview_",""))
        answer()
        logs = sync_get_user_history(target, 15)
        if not logs:
            edit(f" No history for <code>{target}</code>.", user_action_markup(target)); return
        lines = [f"<b>History — {target}</b>\n"]
        for log in logs:
            ts  = log["ts"].strftime("%d/%m %H:%M") if log.get("ts") else "?"
            act = log.get("action","?")
            det = f"  ({log['detail']})" if log.get("detail") else ""
            lines.append(f"  <code>{ts}</code>  {act}{det}")
        edit("\n".join(lines), user_action_markup(target))

    elif d == "adm_fsub" and is_admin(uid):
        answer()
        enabled  = sync_fsub_enabled()
        channels = sync_get_fsub_channels()
        status   = " <b>Enabled</b>" if enabled else " <b>Disabled</b>"
        ch_list  = "\n".join(f"  • <code>{c}</code>" for c in channels) if channels else "  (none)"
        edit(
            f"<b>Force Subscribe</b>\n\nStatus: {status}\n\nChannels:\n{ch_list}\n\n"
            "Bot must be admin in the channel/group.\nUser must be admin/owner to add it.",
            fsub_panel_markup()
        )

    elif d == "fsub_on" and is_admin(uid):
        sync_set_fsub_enabled(True)
        answer(" FSub enabled")
        channels = sync_get_fsub_channels()
        ch_list  = "\n".join(f"  • <code>{c}</code>" for c in channels) if channels else "  (none)"
        edit(f"<b>Force Subscribe</b>\n\nStatus:  <b>Enabled</b>\n\nChannels:\n{ch_list}", fsub_panel_markup())

    elif d == "fsub_off" and is_admin(uid):
        sync_set_fsub_enabled(False)
        answer(" FSub disabled")
        channels = sync_get_fsub_channels()
        ch_list  = "\n".join(f"  • <code>{c}</code>" for c in channels) if channels else "  (none)"
        edit(f"<b>Force Subscribe</b>\n\nStatus:  <b>Disabled</b>\n\nChannels:\n{ch_list}", fsub_panel_markup())

    elif d == "fsub_add_prompt" and is_admin(uid):
        answer(); _expect(uid,"fsub_add")
        edit(
            " <b>Add FSub Channel</b>\n\n"
            "Send the channel/group <b>ID</b> (e.g. <code>-100123456789</code>)\n\n"
            " Bot must be admin in that channel/group.\n"
            " You must be admin/owner of that channel/group.",
            back_markup("adm_fsub")
        )

    elif d.startswith("fsub_rm_") and is_admin(uid):
        ch = int(d.replace("fsub_rm_",""))
        sync_remove_fsub_channel(ch)
        answer(f"Removed {ch}")
        channels = sync_get_fsub_channels()
        enabled  = sync_fsub_enabled()
        status   = " <b>Enabled</b>" if enabled else " <b>Disabled</b>"
        ch_list  = "\n".join(f"  • <code>{c}</code>" for c in channels) if channels else "  (none)"
        edit(f"<b>Force Subscribe</b>\n\nStatus: {status}\n\nChannels:\n{ch_list}", fsub_panel_markup())

    elif d == "adm_chatbot" and is_admin(uid):
        answer()
        edit("<b>Toggle ChatBot</b>\n\nChoose scope:", chatbot_toggle_markup())

    elif d.startswith("cb_enable"):
        suffix = d.replace("cb_enable","")
        gid = None if suffix in ("_global","") else int(suffix.lstrip("_"))
        if gid:
            try:
                member = bot.get_chat_member(gid, uid)
                if member.status not in ("administrator","creator"):
                    answer(" Only group admins."); return
            except Exception:
                answer(" Cannot verify."); return
        else:
            if not is_admin(uid): answer(" Only bot admins."); return
        sync_set_chatbot_enabled(gid, True)
        scope = f"Group {gid}" if gid else "Global (PM)"
        answer("Enabled")
        edit(f"ChatBot enabled ({scope})", back_markup("menu_admin"))

    elif d.startswith("cb_disable"):
        suffix = d.replace("cb_disable","")
        gid = None if suffix in ("_global","") else int(suffix.lstrip("_"))
        if gid:
            try:
                member = bot.get_chat_member(gid, uid)
                if member.status not in ("administrator","creator"):
                    answer(" Only group admins."); return
            except Exception:
                answer(" Cannot verify."); return
        else:
            if not is_admin(uid): answer(" Only bot admins."); return
        sync_set_chatbot_enabled(gid, False)
        scope = f"Group {gid}" if gid else "Global (PM)"
        answer("Disabled")
        edit(f"ChatBot disabled ({scope})", back_markup("menu_admin"))

    elif d == "adm_clear_cache" and is_admin(uid):
        answer(" Clearing...")
        try: requests.delete(f"{API_BASE}/cache", headers=_h(), timeout=5)
        except Exception: pass
        edit("<b>Cache cleared.</b>", back_markup("menu_admin"))

    elif d == "adm_ads" and is_admin(uid):
        answer()
        ads_on  = sync_get_ads_enabled()
        ads     = sync_get_ads()
        status  = " <b>Enabled</b>" if ads_on else " <b>Disabled</b>"
        count   = len(ads)
        edit(
            f" <b>Ads Manager</b>\n\n"
            f"Status: {status}\n"
            f"Total Ads: <b>{count}</b>\n\n"
            "Ads are shown to <b>Free plan users only</b> after every successful download.\n\n"
            "<b>Ad Types:</b> Photo · Video · Audio · Text\n"
            "<b>Features:</b> Caption · HTML · Inline Buttons",
            ads_panel_markup()
        )

    elif d == "ads_on" and is_admin(uid):
        sync_set_ads_enabled(True)
        answer(" Ads enabled")
        edit(" <b>Ads Manager</b>\n\nStatus:  <b>Enabled</b>", ads_panel_markup())

    elif d == "ads_off" and is_admin(uid):
        sync_set_ads_enabled(False)
        answer(" Ads disabled")
        edit(" <b>Ads Manager</b>\n\nStatus:  <b>Disabled</b>", ads_panel_markup())

    elif d == "ads_add_prompt" and is_admin(uid):
        answer()
        _expect(uid, "ads_add_step1")
        edit(
            " <b>Add New Ad</b> — Step 1/3\n\n"
            "Select ad type by sending one of:\n\n"
            "<code>photo</code>  — Image with optional caption\n"
            "<code>video</code>  — Video with optional caption\n"
            "<code>audio</code>  — Audio with optional caption\n"
            "<code>text</code>   — Text message only\n\n"
            "Type /cancel to abort.",
            back_markup("adm_ads")
        )

    elif d.startswith("ads_del_") and is_admin(uid):
        ad_id = d.replace("ads_del_","")
        sync_delete_ad(ad_id)
        answer(" Ad deleted")
        edit(" <b>Ads Manager</b>\n\nAd deleted successfully.", ads_panel_markup())

    elif d.startswith("ads_view_") and is_admin(uid):
        from models.db import get_sync_db
        from bson import ObjectId
        ad_id = d.replace("ads_view_","")
        try:
            ad = get_sync_db().ads.find_one({"_id": ObjectId(ad_id)})
        except Exception:
            ad = None
        if not ad:
            answer("Ad not found"); return
        answer()
        ad_type  = ad.get("type","text")
        caption  = ad.get("caption","") or "(none)"
        file_id  = ad.get("file_id","") or "(none)"
        buttons  = ad.get("buttons",[])
        btn_str  = "\n".join(f"  • {b['text']} → {b['url']}" for b in buttons) if buttons else "  (none)"
        edit(
            f" <b>Ad Details</b>\n\n"
            f"Type: <b>{ad_type}</b>\n"
            f"File ID: <code>{file_id[:40]}</code>\n"
            f"Caption: {caption[:100]}\n\n"
            f"Inline Buttons:\n{btn_str}",
            back_markup("adm_ads")
        )

    else:
        answer()


@bot.message_handler(func=lambda m: True, content_types=["text","photo","video","audio"])
def handle_text(msg):
    uid    = msg.from_user.id
    lang   = ulang(uid)
    is_pm  = msg.chat.type == "private"
    content_type = msg.content_type
    prompt = (msg.text or msg.caption or "").strip()

    if sync_is_banned(uid):
        bot.reply_to(msg,
            "<b>Access Denied</b>\n\n"
            "You have been banned from using this bot.\n"
            "Contact @TEAM_X_OG if you think this is a mistake.",
            parse_mode="HTML"); return

    restricted = sync_is_restricted(uid)

    if is_pm:
        not_joined = check_fsub(uid, msg.chat.id)
        if not_joined:
            bot.reply_to(msg,
                "<b>Join Required</b>\n\n"
                "You must join our channels to use this bot.",
                reply_markup=fsub_markup(not_joined), parse_mode="HTML"); return

    pending = _peek_pending(uid)
    if pending and is_admin(uid):
        action = pending["action"]

        if action == "ads_add_step1":
            if content_type != "text":
                bot.reply_to(msg, " Please send the ad type as text: photo/video/audio/text"); return
            ad_type = prompt.lower()
            if ad_type not in ("photo","video","audio","text"):
                bot.reply_to(msg, " Invalid type. Send: photo / video / audio / text"); return
            _pending.pop(uid, None)
            _expect(uid, "ads_add_step2", ad_type=ad_type)
            if ad_type == "text":
                bot.reply_to(msg,
                    " <b>Add New Ad</b> — Step 2/3\n\n"
                    "Send the <b>ad text</b> (HTML supported).\nType /cancel to abort.")
            else:
                bot.reply_to(msg,
                    f" <b>Add New Ad</b> — Step 2/3\n\n"
                    f"Send the <b>{ad_type} file</b> (with or without caption).\n"
                    "Type /cancel to abort.", parse_mode="HTML")
            return

        elif action == "ads_add_step2":
            ad_type = pending.get("ad_type","text")
            file_id = ""
            caption = ""

            if ad_type == "text":
                if content_type != "text":
                    bot.reply_to(msg, " Please send text for a text ad."); return
                caption = prompt
            elif ad_type == "photo":
                if content_type != "photo":
                    bot.reply_to(msg, " Please send a photo."); return
                file_id = msg.photo[-1].file_id
                caption = msg.caption or ""
            elif ad_type == "video":
                if content_type != "video":
                    bot.reply_to(msg, " Please send a video."); return
                file_id = msg.video.file_id
                caption = msg.caption or ""
            elif ad_type == "audio":
                if content_type != "audio":
                    bot.reply_to(msg, " Please send an audio file."); return
                file_id = msg.audio.file_id
                caption = msg.caption or ""

            _pending.pop(uid, None)
            _expect(uid, "ads_add_step3", ad_type=ad_type, file_id=file_id, caption=caption)
            bot.reply_to(msg,
                " <b>Add New Ad</b> — Step 3/3\n\n"
                "Add inline buttons? Send in format:\n\n"
                "<code>Button Text | https://url.com</code>\n"
                "<code>Button 2 | https://url2.com</code>\n\n"
                "One button per line. Or send <code>none</code> to skip.\n"
                "Type /cancel to abort.", parse_mode="HTML")
            return

        elif action == "ads_add_step3":
            ad_type = pending.get("ad_type","text")
            file_id = pending.get("file_id","")
            caption = pending.get("caption","")
            buttons = []

            if content_type == "text" and prompt.lower() != "none":
                for line in prompt.split("\n"):
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|", 1)
                        btn_text = parts[0].strip()
                        btn_url  = parts[1].strip()
                        if btn_text and btn_url:
                            buttons.append({"text": btn_text, "url": btn_url})

            _pending.pop(uid, None)
            sync_set_ad(ad_type, file_id, caption, buttons)
            btn_count = len(buttons)
            bot.reply_to(msg,
                f"<b>Ad saved!</b>\n\n"
                f"Type: <b>{ad_type}</b>\n"
                f"Caption: {caption[:60] or '(none)'}\n"
                f"Inline Buttons: <b>{btn_count}</b>",
                parse_mode="HTML", reply_markup=back_markup("adm_ads"))
            return

        _pending.pop(uid, None)

        if action == "broadcast":
            if content_type != "text":
                bot.reply_to(msg, " Broadcast supports text only."); return
            _do_broadcast(msg, prompt)
            return

        elif action in ("user_info","ban","unban","restrict","unrestrict","history","plan_uid","fsub_add"):
            if content_type != "text":
                bot.reply_to(msg, " Please send a user ID."); return
            try:
                target = int(prompt)
            except ValueError:
                bot.reply_to(msg, "Invalid user ID. Must be a number."); return

            if action == "user_info":
                u  = sync_get_user(target)
                s  = sync_get_usage_stats(target)
                from datetime import date
                joined = u.get("created")
                joined_str = joined.strftime("%d %b %Y") if joined else "Unknown"
                text = (
                    "\n"
                    "       ᴜᴇʀ ɪɴᴏ\n"
                    "\n\n"
                    f" UID        ›  <code>{target}</code>\n"
                    f" Plan       ›  <b>{PLAN_BADGE.get(u.get('plan','free'),'?')}</b>\n"
                    f" Banned     ›  <b>{'Yes' if u.get('banned') else 'No'}</b>\n"
                    f" Restricted ›  <b>{'Yes' if u.get('restricted') else 'No'}</b>\n"
                    f"  PM (month) ›  <b>{s['pm_used']}/{s['pm_limit']}</b>\n"
                    f"  DL (today) ›  <b>{s['dl_used']}/{s['dl_limit']}</b>\n"
                    f"  Joined     ›  <b>{joined_str}</b>"
                )
                bot.reply_to(msg, text, parse_mode="HTML", reply_markup=user_action_markup(target))
                return

            elif action == "ban":
                sync_ban_user(target)
                bot.reply_to(msg, f"User <code>{target}</code> banned.", parse_mode="HTML",
                             reply_markup=user_action_markup(target)); return

            elif action == "unban":
                sync_unban_user(target)
                bot.reply_to(msg, f"User <code>{target}</code> unbanned.", parse_mode="HTML",
                             reply_markup=user_action_markup(target)); return

            elif action == "restrict":
                sync_restrict_user(target)
                bot.reply_to(msg, f"User <code>{target}</code> restricted.", parse_mode="HTML",
                             reply_markup=user_action_markup(target)); return

            elif action == "unrestrict":
                sync_unrestrict_user(target)
                bot.reply_to(msg, f"User <code>{target}</code> unrestricted.", parse_mode="HTML",
                             reply_markup=user_action_markup(target)); return

            elif action == "history":
                logs = sync_get_user_history(target, 15)
                if not logs:
                    bot.reply_to(msg, f" No history for <code>{target}</code>.", parse_mode="HTML",
                                 reply_markup=back_markup("menu_admin")); return
                lines = [f"<b>History — {target}</b>\n"]
                for log in logs:
                    ts  = log["ts"].strftime("%d/%m %H:%M") if log.get("ts") else "?"
                    act = log.get("action","?")
                    det = f"  ({log['detail']})" if log.get("detail") else ""
                    lines.append(f"  <code>{ts}</code>  {act}{det}")
                bot.reply_to(msg, "\n".join(lines), parse_mode="HTML",
                             reply_markup=user_action_markup(target)); return

            elif action == "plan_uid":
                u = sync_get_user(target)
                current = u.get("plan","free")
                bot.reply_to(msg,
                    f"<b>Set Plan</b>\n\n"
                    f"User: <code>{target}</code>\n"
                    f"Current: <b>{PLAN_BADGE.get(current,current)}</b>\n\n"
                    "Select new plan:",
                    parse_mode="HTML", reply_markup=plan_select_markup(target)); return

            elif action == "fsub_add":
                try:
                    chat = bot.get_chat(target)
                except Exception:
                    bot.reply_to(msg, f"Cannot access chat <code>{target}</code>. Is the bot in it?",
                                 parse_mode="HTML"); return
                try:
                    member = bot.get_chat_member(target, uid)
                    if member.status not in ("administrator","creator"):
                        bot.reply_to(msg, " You must be admin/owner of that channel/group.", parse_mode="HTML"); return
                except Exception:
                    bot.reply_to(msg, " Cannot verify your status in that channel/group.", parse_mode="HTML"); return
                try:
                    bot_member = bot.get_chat_member(target, bot.get_me().id)
                    if bot_member.status not in ("administrator","creator"):
                        bot.reply_to(msg, " Bot must be admin in that channel/group.", parse_mode="HTML"); return
                except Exception:
                    bot.reply_to(msg, " Bot is not in that channel/group.", parse_mode="HTML"); return

                sync_add_fsub_channel(target)
                title = getattr(chat,"title",str(target))
                bot.reply_to(msg, f"Added <b>{title}</b> (<code>{target}</code>) to FSub list.",
                             parse_mode="HTML", reply_markup=back_markup("adm_fsub")); return

    if content_type not in ("text",):
        return

    if not prompt: return

    if is_dl_url(prompt) or is_terabox_url(prompt):
        url = extract_url(prompt)
        if url:
            handle_download(msg, url)
            return

    if restricted:
        bot.reply_to(msg,
            "<b>Restricted</b>\n\n"
            "Your AI access is restricted. Contact @TEAM_X_OG.",
            parse_mode="HTML"); return

    ai_model = "fast"

    if not is_pm:
        if not sync_get_chatbot_enabled(msg.chat.id):
            return

    if is_pm:
        if not sync_check_pm_limit(uid):
            plan  = sync_get_user(uid).get("plan","free")
            limit = sync_get_config(f"{plan}_pm_month")
            kb = InlineKeyboardMarkup()
            kb.row(InlineKeyboardButton(" Upgrade Plan", callback_data="menu_sub"))
            bot.reply_to(msg, tf("error.pm_limit", lang, limit=limit), reply_markup=kb); return
    else:
        if not sync_check_group_limit(uid):
            plan  = sync_get_user(uid).get("plan","free")
            limit = sync_get_config(f"{plan}_group_month")
            bot.reply_to(msg, tf("error.group_limit", lang, limit=limit)); return

    try:
        bot.send_chat_action(msg.chat.id, "typing")
    except Exception:
        pass

    first_name = msg.from_user.first_name or "Jaan"
    result     = api_chat(prompt, uid, first_name=first_name, model=ai_model)

    if ai_model == "fast" and "response" in result and "status" not in result:
        result = {"status": "success", "response": result["response"]}

    if result.get("status") == "success":
        response = result.get("response","")
        if not response:
            bot.reply_to(msg, t("ai.no_response",lang)); return
        sync_set_last_msg(uid)
        mk = _month_key()
        sync_increment_count(uid, f"pm_{mk}" if is_pm else f"grp_{mk}")
        send_chunked(msg.chat.id, response, reply_to=msg.message_id, uid=uid, parse_mode="HTML")
    else:
        err = result.get("message","unknown")
        bot.reply_to(msg, t("error.timeout",lang) if err=="timeout"
                     else tf("error.api_error",lang,message=err))


if __name__ == "__main__":
    sync_ensure_config()
    print("")
    print("        ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ")
    print("")
    print("[+] Bot running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
