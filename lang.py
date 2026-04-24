"""
╔══════════════════════════╗
                ᴛᴇᴀᴍᴅᴇᴠ × ɴᴇᴜʀᴀʟʜᴜʙ
╚══════════════════════════╝

     @Lang—File
  
  Read @licence File  And @README.md
  
  Dev: https://t.me/MR_ARMAN_08
  Updates: https://t.me/TeamDevXBots
  Support: https://t.me/Team_X_Og
  Donate: https://pay.teamdev.sbs
"""

import os
import yaml

LANG_DIR     = os.path.join(os.path.dirname(__file__), "assets", "lang")
DEFAULT_LANG = "en"

LANGUAGES = [
    ("en",       "English",    "EN"),
    ("hi",       "Hindi",      "HI"),
    ("hinglish", "Hinglish",   "HG"),
    ("te",       "Telugu",     "TE"),
    ("ta",       "Tamil",      "TA"),
    ("ml",       "Malayalam",  "ML"),
    ("mni",      "Manipuri",   "MN"),
    ("bn",       "Bengali",    "BN"),
    ("my",       "Burmese",    "MY"),
    ("ur",       "Urdu",       "UR"),
    ("ar",       "Arabic",     "AR"),
    ("ru",       "Russian",    "RU"),
    ("tr",       "Turkish",    "TR"),
    ("es",       "Espanol",    "ES"),
    ("fr",       "Francais",   "FR"),
    ("de",       "Deutsch",    "DE"),
    ("pt",       "Portugues",  "PT"),
    ("id",       "Indonesia",  "ID"),
    ("ja",       "Japanese",   "JA"),
    ("ko",       "Korean",     "KO"),
    ("zh",       "Chinese",    "ZH"),
]

SUPPORTED = {code for code, _, _ in LANGUAGES}

_cache: dict[str, dict] = {}


def _load(lang: str) -> dict:
    if lang not in _cache:
        path = os.path.join(LANG_DIR, f"{lang}.yml")
        if not os.path.exists(path):
            path = os.path.join(LANG_DIR, f"{DEFAULT_LANG}.yml")
        with open(path, "r", encoding="utf-8") as f:
            _cache[lang] = yaml.safe_load(f)
    return _cache[lang]


def _resolve(data: dict, key: str):
    parts = key.split(".")
    node  = data
    for p in parts:
        if isinstance(node, dict) and p in node:
            node = node[p]
        else:
            return None
    return node


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    data   = _load(lang)
    result = _resolve(data, key)
    if result is None and lang != DEFAULT_LANG:
        data   = _load(DEFAULT_LANG)
        result = _resolve(data, key)
    return str(result).strip() if result is not None else f"[{key}]"


def tf(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    raw = t(key, lang)
    try:
        return raw.format(**kwargs)
    except KeyError:
        return raw
