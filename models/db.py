"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @Database—File
  
  Read @licence File  And @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import os
from datetime import datetime, timezone

import config

MONGO_URI = config.MONGO_URI
DB_NAME   = config.MONGO_DB

_sync_client = None
_sync_db     = None

def get_sync_db():
    global _sync_client, _sync_db
    if _sync_db is None:
        from pymongo import MongoClient
        _sync_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        _sync_db     = _sync_client[DB_NAME]
    return _sync_db

_async_client = None
_async_db     = None

def get_async_db():
    global _async_client, _async_db
    if _async_db is None:
        from motor.motor_asyncio import AsyncIOMotorClient
        _async_client = AsyncIOMotorClient(MONGO_URI)
        _async_db     = _async_client[DB_NAME]
    return _async_db

ULTRA_PRO_LIMIT = 999999
VALID_PLANS = ["free", "basic", "pro", "ultra", "ultra_pro"]

DEFAULT_CONFIG = {
    "free_dl_day":            5,
    "free_cooldown_sec":      300,
    "free_pm_month":          150,
    "free_group_month":       1000,
    "free_img_day":           2,
    "basic_dl_day":           15,
    "basic_cooldown_sec":     120,
    "basic_pm_month":         300,
    "basic_group_month":      2000,
    "basic_img_day":          5,
    "pro_dl_day":             30,
    "pro_cooldown_sec":       60,
    "pro_pm_month":           1000,
    "pro_group_month":        5000,
    "pro_img_day":            20,
    "ultra_dl_day":           100,
    "ultra_cooldown_sec":     10,
    "ultra_pm_month":         5000,
    "ultra_group_month":      20000,
    "ultra_img_day":          50,
    "ultra_pro_dl_day":       ULTRA_PRO_LIMIT,
    "ultra_pro_cooldown_sec": 0,
    "ultra_pro_pm_month":     ULTRA_PRO_LIMIT,
    "ultra_pro_group_month":  ULTRA_PRO_LIMIT,
    "ultra_pro_img_day":      ULTRA_PRO_LIMIT,
    "api_secret":             config.API_SECRET,
    "chunk_size":             3800,
    "max_response_chars":     3800,
    "fsub_channels":          "",
    "fsub_enabled":           False,
    "welcome_video_file_id":  "",
    "welcome_caption":        "",
    "ads_enabled":            False,
}

def _month_key():
    n = datetime.now(timezone.utc)
    return f"{n.year}-{n.month:02d}"

def _day_key():
    n = datetime.now(timezone.utc)
    return f"{n.year}-{n.month:02d}-{n.day:02d}"

def _is_unlimited(plan: str) -> bool:
    return plan == "ultra_pro"

def sync_ensure_config():
    db = get_sync_db()
    existing_keys = {d["key"] for d in db.config.find({}, {"key": 1})}
    new_docs = [{"key": k, "value": v} for k, v in DEFAULT_CONFIG.items() if k not in existing_keys]
    if new_docs:
        db.config.insert_many(new_docs)

def sync_get_config(key: str):
    doc = get_sync_db().config.find_one({"key": key})
    return doc["value"] if doc else DEFAULT_CONFIG.get(key)

def sync_set_config(key: str, value):
    get_sync_db().config.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

def sync_get_all_config() -> dict:
    return {d["key"]: d["value"] for d in get_sync_db().config.find({})}

def sync_get_user(uid: int) -> dict:
    db   = get_sync_db()
    user = db.users.find_one({"uid": uid})
    if not user:
        doc = {
            "uid":        uid,
            "plan":       "free",
            "lang":       "en",
            "created":    datetime.now(timezone.utc),
            "last_msg":   None,
            "counts":     {},
            "banned":     False,
            "restricted": False,
        }
        db.users.insert_one(doc)
        user = db.users.find_one({"uid": uid})
    return user

def sync_update_user(uid: int, update: dict):
    get_sync_db().users.update_one({"uid": uid}, {"$set": update}, upsert=True)

def sync_increment_count(uid: int, key: str):
    get_sync_db().users.update_one({"uid": uid}, {"$inc": {f"counts.{key}": 1}}, upsert=True)

def sync_set_last_msg(uid: int):
    sync_update_user(uid, {"last_msg": datetime.now(timezone.utc)})

def sync_set_user_plan(uid: int, plan: str):
    sync_update_user(uid, {"plan": plan})

def sync_check_cooldown(uid: int) -> int:
    user = sync_get_user(uid)
    plan = user.get("plan", "free")
    if _is_unlimited(plan):
        return 0
    cd   = int(sync_get_config(f"{plan}_cooldown_sec") or 300)
    last = user.get("last_msg")
    if not last:
        return 0
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    remaining = cd - (datetime.now(timezone.utc) - last).total_seconds()
    return max(0, int(remaining))

def sync_check_pm_limit(uid: int) -> bool:
    user = sync_get_user(uid)
    plan = user.get("plan", "free")
    if _is_unlimited(plan):
        return True
    limit = int(sync_get_config(f"{plan}_pm_month") or 150)
    used  = user.get("counts", {}).get(f"pm_{_month_key()}", 0)
    return used < limit

def sync_check_group_limit(uid: int) -> bool:
    user = sync_get_user(uid)
    plan = user.get("plan", "free")
    if _is_unlimited(plan):
        return True
    limit = int(sync_get_config(f"{plan}_group_month") or 1000)
    used  = user.get("counts", {}).get(f"grp_{_month_key()}", 0)
    return used < limit

def sync_check_img_limit(uid: int) -> bool:
    user = sync_get_user(uid)
    plan = user.get("plan", "free")
    if _is_unlimited(plan):
        return True
    limit = int(sync_get_config(f"{plan}_img_day") or 2)
    used  = user.get("counts", {}).get(f"img_{_day_key()}", 0)
    return used < limit

def sync_check_dl_limit(uid: int) -> bool:
    user = sync_get_user(uid)
    plan = user.get("plan", "free")
    if _is_unlimited(plan):
        return True
    limit = int(sync_get_config(f"{plan}_dl_day") or 5)
    used  = user.get("counts", {}).get(f"dl_{_day_key()}", 0)
    return used < limit

def sync_get_usage_stats(uid: int) -> dict:
    user    = sync_get_user(uid)
    plan    = user.get("plan", "free")
    mk, dk  = _month_key(), _day_key()
    counts  = user.get("counts", {})
    cfg     = sync_get_all_config()
    unlim   = _is_unlimited(plan)
    return {
        "plan":      plan,
        "pm_used":   counts.get(f"pm_{mk}", 0),
        "pm_limit":  "∞" if unlim else int(cfg.get(f"{plan}_pm_month", 150)),
        "grp_used":  counts.get(f"grp_{mk}", 0),
        "grp_limit": "∞" if unlim else int(cfg.get(f"{plan}_group_month", 1000)),
        "img_used":  counts.get(f"img_{dk}", 0),
        "img_limit": "∞" if unlim else int(cfg.get(f"{plan}_img_day", 2)),
        "dl_used":   counts.get(f"dl_{dk}", 0),
        "dl_limit":  "∞" if unlim else int(cfg.get(f"{plan}_dl_day", 5)),
        "cooldown":  0 if unlim else int(cfg.get(f"{plan}_cooldown_sec", 300)),
        "unlimited": unlim,
        "banned":    user.get("banned", False),
        "restricted": user.get("restricted", False),
    }

def sync_get_all_users_stats() -> dict:
    db    = get_sync_db()
    total = db.users.count_documents({})
    stats = {"total": total}
    for plan in VALID_PLANS:
        stats[plan] = db.users.count_documents({"plan": plan})
    stats["banned"]     = db.users.count_documents({"banned": True})
    stats["restricted"] = db.users.count_documents({"restricted": True})
    return stats

def sync_ban_user(uid: int):
    sync_update_user(uid, {"banned": True})
    sync_log_user_action(uid, "banned")

def sync_unban_user(uid: int):
    sync_update_user(uid, {"banned": False})
    sync_log_user_action(uid, "unbanned")

def sync_restrict_user(uid: int):
    sync_update_user(uid, {"restricted": True})
    sync_log_user_action(uid, "restricted")

def sync_unrestrict_user(uid: int):
    sync_update_user(uid, {"restricted": False})
    sync_log_user_action(uid, "unrestricted")

def sync_is_banned(uid: int) -> bool:
    u = get_sync_db().users.find_one({"uid": uid})
    return bool(u and u.get("banned", False))

def sync_is_restricted(uid: int) -> bool:
    u = get_sync_db().users.find_one({"uid": uid})
    return bool(u and u.get("restricted", False))

def sync_log_user_action(uid: int, action: str, detail: str = ""):
    get_sync_db().user_logs.insert_one({
        "uid":    uid,
        "action": action,
        "detail": detail,
        "ts":     datetime.now(timezone.utc),
    })

def sync_get_user_history(uid: int, limit: int = 15) -> list:
    return list(get_sync_db().user_logs.find(
        {"uid": uid}, sort=[("ts", -1)], limit=limit
    ))

def sync_get_fsub_channels() -> list:
    raw = sync_get_config("fsub_channels") or ""
    result = []
    for x in str(raw).split(","):
        x = x.strip()
        if x:
            try:
                result.append(int(x))
            except ValueError:
                pass
    return result

def sync_add_fsub_channel(channel_id: int):
    channels = sync_get_fsub_channels()
    if channel_id not in channels:
        channels.append(channel_id)
    sync_set_config("fsub_channels", ",".join(str(c) for c in channels))

def sync_remove_fsub_channel(channel_id: int):
    channels = [c for c in sync_get_fsub_channels() if c != channel_id]
    sync_set_config("fsub_channels", ",".join(str(c) for c in channels))

def sync_fsub_enabled() -> bool:
    return bool(sync_get_config("fsub_enabled"))

def sync_set_fsub_enabled(enabled: bool):
    sync_set_config("fsub_enabled", enabled)

def sync_get_welcome_video() -> dict:
    return {
        "file_id": sync_get_config("welcome_video_file_id") or "",
        "caption": sync_get_config("welcome_caption") or "",
    }

def sync_set_welcome_video(file_id: str, caption: str = ""):
    sync_set_config("welcome_video_file_id", file_id)
    sync_set_config("welcome_caption", caption)

def sync_get_chatbot_enabled(group_id=None) -> bool:
    db  = get_sync_db()
    key = f"chatbot_group_{group_id}" if group_id else "chatbot_global"
    doc = db.chatbot_settings.find_one({"key": key})
    if doc is None:
        return True
    return bool(doc.get("enabled", True))

def sync_set_chatbot_enabled(group_id, enabled: bool):
    db  = get_sync_db()
    key = f"chatbot_group_{group_id}" if group_id else "chatbot_global"
    db.chatbot_settings.update_one(
        {"key": key},
        {"$set": {"key": key, "enabled": enabled}},
        upsert=True,
    )

async def async_ensure_config():
    db = get_async_db()
    if await db.config.count_documents({}) == 0:
        await db.config.insert_many([{"key": k, "value": v} for k, v in DEFAULT_CONFIG.items()])

async def async_get_config(key: str):
    doc = await get_async_db().config.find_one({"key": key})
    return doc["value"] if doc else DEFAULT_CONFIG.get(key)

async def async_set_config(key: str, value):
    await get_async_db().config.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

async def async_get_all_config() -> dict:
    docs = await get_async_db().config.find({}).to_list(length=None)
    return {d["key"]: d["value"] for d in docs}

async def async_get_user(uid: int) -> dict:
    db   = get_async_db()
    user = await db.users.find_one({"uid": uid})
    if not user:
        doc = {
            "uid":        uid,
            "plan":       "free",
            "lang":       "en",
            "created":    datetime.now(timezone.utc),
            "last_msg":   None,
            "counts":     {},
            "banned":     False,
            "restricted": False,
        }
        await db.users.insert_one(doc)
        user = await db.users.find_one({"uid": uid})
    return user

async def async_check_img_limit(uid: int) -> bool:
    user  = await async_get_user(uid)
    plan  = user.get("plan", "free")
    if _is_unlimited(plan):
        return True
    limit = int(await async_get_config(f"{plan}_img_day"))
    used  = user.get("counts", {}).get(f"img_{_day_key()}", 0)
    return used < limit

async def async_increment_count(uid: int, key: str):
    await get_async_db().users.update_one(
        {"uid": uid}, {"$inc": {f"counts.{key}": 1}}, upsert=True)

async def async_set_user_plan(uid: int, plan: str):
    await get_async_db().users.update_one({"uid": uid}, {"$set": {"plan": plan}}, upsert=True)

async def async_get_all_users_stats() -> dict:
    db    = get_async_db()
    total = await db.users.count_documents({})
    pro   = await db.users.count_documents({"plan": "pro"})
    return {"total": total, "pro": pro, "free": total - pro}

def sync_get_ads_enabled() -> bool:
    return bool(sync_get_config("ads_enabled"))

def sync_set_ads_enabled(enabled: bool):
    sync_set_config("ads_enabled", enabled)

def sync_get_ads() -> list:
    db = get_sync_db()
    return list(db.ads.find({}))

def sync_set_ad(ad_type: str, file_id: str, caption: str, buttons: list):
    db = get_sync_db()
    db.ads.insert_one({
        "type":    ad_type,
        "file_id": file_id,
        "caption": caption,
        "buttons": buttons,
        "created": datetime.now(timezone.utc),
    })

def sync_delete_ad(ad_id: str):
    from bson import ObjectId
    try:
        get_sync_db().ads.delete_one({"_id": ObjectId(ad_id)})
    except Exception as e:
        print(f"[!] Ad delete error: {e}")
