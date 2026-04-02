"""Simple JSON-backed per-user settings for the Discord bot."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

try:
    from .config import REPLY_LANGUAGE, USER_SETTINGS_PATH, WATCHLIST_TICKERS
    from .ticker_map import canonicalize_ticker_symbol
except ImportError:  # pragma: no cover - script execution fallback
    from config import REPLY_LANGUAGE, USER_SETTINGS_PATH, WATCHLIST_TICKERS
    from ticker_map import canonicalize_ticker_symbol


SETTINGS_LOCK = RLock()
VALID_LANGUAGES = {"en", "zh", "bilingual"}


def _default_settings() -> dict[str, Any]:
    """Return default settings for a new Discord user."""
    return {
        "language": REPLY_LANGUAGE,
        "compact_mode": False,
        "default_watchlist": [],
    }


def _ensure_settings_file() -> None:
    """Create the settings file if it does not exist yet."""
    USER_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not USER_SETTINGS_PATH.exists():
        USER_SETTINGS_PATH.write_text("{}", encoding="utf-8")


def _load_all_settings() -> dict[str, Any]:
    """Load all saved user settings from disk."""
    _ensure_settings_file()
    try:
        raw = USER_SETTINGS_PATH.read_text(encoding="utf-8").strip() or "{}"
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_all_settings(settings_map: dict[str, Any]) -> None:
    """Persist all user settings to disk."""
    _ensure_settings_file()
    USER_SETTINGS_PATH.write_text(
        json.dumps(settings_map, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _normalize_watchlist(tickers: list[str]) -> list[str]:
    """Normalize a watchlist into unique uppercase tickers."""
    seen: set[str] = set()
    normalized: list[str] = []
    for ticker in tickers:
        clean = canonicalize_ticker_symbol(str(ticker))
        if not clean or clean in seen:
            continue
        seen.add(clean)
        normalized.append(clean)
    return normalized


def get_user_settings(user_id: int) -> dict[str, Any]:
    """Load one user's settings with defaults filled in."""
    with SETTINGS_LOCK:
        payload = _load_all_settings()
        stored = payload.get(str(user_id), {})

    defaults = _default_settings()
    settings = {
        "language": stored.get("language", defaults["language"]),
        "compact_mode": bool(stored.get("compact_mode", defaults["compact_mode"])),
        "default_watchlist": _normalize_watchlist(stored.get("default_watchlist", [])),
    }
    if settings["language"] not in VALID_LANGUAGES:
        settings["language"] = defaults["language"]
    return settings


def set_user_language(user_id: int, language: str) -> dict[str, Any]:
    """Update one user's reply language."""
    language = str(language).strip().lower()
    if language not in VALID_LANGUAGES:
        raise ValueError("Language must be one of: en, zh, bilingual.")

    with SETTINGS_LOCK:
        payload = _load_all_settings()
        settings = get_user_settings(user_id)
        settings["language"] = language
        payload[str(user_id)] = settings
        _save_all_settings(payload)
    return settings


def set_user_compact_mode(user_id: int, compact_mode: bool) -> dict[str, Any]:
    """Update one user's compact mode preference."""
    with SETTINGS_LOCK:
        payload = _load_all_settings()
        settings = get_user_settings(user_id)
        settings["compact_mode"] = bool(compact_mode)
        payload[str(user_id)] = settings
        _save_all_settings(payload)
    return settings


def set_user_watchlist(user_id: int, tickers: list[str]) -> dict[str, Any]:
    """Update one user's default watchlist."""
    normalized = _normalize_watchlist(tickers)
    if not normalized:
        raise ValueError("Watchlist cannot be empty.")

    with SETTINGS_LOCK:
        payload = _load_all_settings()
        settings = get_user_settings(user_id)
        settings["default_watchlist"] = normalized
        payload[str(user_id)] = settings
        _save_all_settings(payload)
    return settings


def add_user_ticker(user_id: int, ticker: str) -> dict[str, Any]:
    """Add one ticker to a user's default watchlist."""
    normalized = _normalize_watchlist([ticker])
    if not normalized:
        raise ValueError("Ticker cannot be empty.")

    with SETTINGS_LOCK:
        payload = _load_all_settings()
        settings = get_user_settings(user_id)
        current = settings["default_watchlist"] or list(WATCHLIST_TICKERS)
        settings["default_watchlist"] = _normalize_watchlist(current + normalized)
        payload[str(user_id)] = settings
        _save_all_settings(payload)
    return settings


def remove_user_ticker(user_id: int, ticker: str) -> dict[str, Any]:
    """Remove one ticker from a user's default watchlist."""
    target = canonicalize_ticker_symbol(str(ticker))
    if not target:
        raise ValueError("Ticker cannot be empty.")

    with SETTINGS_LOCK:
        payload = _load_all_settings()
        settings = get_user_settings(user_id)
        current = settings["default_watchlist"] or list(WATCHLIST_TICKERS)
        updated = [item for item in current if item != target]
        if not updated:
            raise ValueError("Watchlist cannot be empty. Add another ticker before removing the last one.")
        settings["default_watchlist"] = updated
        payload[str(user_id)] = settings
        _save_all_settings(payload)
    return settings


def reset_user_settings(user_id: int) -> dict[str, Any]:
    """Reset one user's settings to defaults."""
    defaults = _default_settings()
    with SETTINGS_LOCK:
        payload = _load_all_settings()
        payload.pop(str(user_id), None)
        _save_all_settings(payload)
    return defaults


def parse_watchlist_input(raw_value: str) -> list[str]:
    """Parse comma/semicolon/newline separated watchlist input from Discord."""
    normalized = raw_value.replace("\n", ",").replace(";", ",")
    return _normalize_watchlist(normalized.split(","))


def get_effective_watchlist(user_id: int) -> list[str]:
    """Return a user's saved watchlist or fall back to the system default."""
    settings = get_user_settings(user_id)
    return settings["default_watchlist"] or list(WATCHLIST_TICKERS)
