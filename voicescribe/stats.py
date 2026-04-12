"""Persistent data for VoiceScribe — sessions, dictionary, snippets, settings.

All of it lives in one JSON file at
~/Library/Application Support/VoiceScribe/data.json
"""

import json
import os
import time
from pathlib import Path

_DIR = Path.home() / "Library" / "Application Support" / "VoiceScribe"
_FILE = _DIR / "data.json"


def _default():
    return {
        "typing_wpm": 40,
        "sessions": [],        # list of {id, ts, words, duration, text}
        "dictionary": [],      # list of strings (custom vocab)
        "snippets": [],        # list of {trigger, expansion}
    }


def _load():
    try:
        with open(_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Try legacy stats.json from earlier build
        legacy = _DIR / "stats.json"
        try:
            with open(legacy, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    # Fill in any missing keys
    base = _default()
    for k, v in base.items():
        if k not in data:
            data[k] = v
    return data


def _save(data):
    _DIR.mkdir(parents=True, exist_ok=True)
    tmp = _FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, _FILE)


# ── Sessions ──────────────────────────────────────────────────────────────────
def record_session(words: int, duration: float, text: str = ""):
    if words <= 0 or duration <= 0:
        return
    data = _load()
    data["sessions"].append({
        "id": int(time.time() * 1000),
        "ts": time.time(),
        "words": int(words),
        "duration": float(duration),
        "text": text or "",
    })
    _save(data)


def delete_session(session_id: int):
    data = _load()
    data["sessions"] = [s for s in data["sessions"] if s.get("id") != session_id]
    _save(data)


# ── Settings ──────────────────────────────────────────────────────────────────
def set_typing_wpm(wpm: int):
    data = _load()
    data["typing_wpm"] = max(1, int(wpm))
    _save(data)


# ── Dictionary ────────────────────────────────────────────────────────────────
def get_dictionary():
    return list(_load().get("dictionary", []))


def add_dictionary_word(word: str):
    word = (word or "").strip()
    if not word:
        return
    data = _load()
    if word not in data["dictionary"]:
        data["dictionary"].append(word)
        _save(data)


def remove_dictionary_word(word: str):
    data = _load()
    data["dictionary"] = [w for w in data["dictionary"] if w != word]
    _save(data)


def dictionary_prompt() -> str:
    """Joined string suitable for Whisper's `initial_prompt`."""
    words = get_dictionary()
    if not words:
        return ""
    return ", ".join(words) + "."


# ── Snippets ──────────────────────────────────────────────────────────────────
def get_snippets():
    return list(_load().get("snippets", []))


def add_snippet(trigger: str, expansion: str):
    trigger = (trigger or "").strip()
    expansion = (expansion or "").strip()
    if not trigger or not expansion:
        return
    data = _load()
    # Replace existing trigger if present
    found = False
    for s in data["snippets"]:
        if s["trigger"].lower() == trigger.lower():
            s["expansion"] = expansion
            found = True
            break
    if not found:
        data["snippets"].append({"trigger": trigger, "expansion": expansion})
    _save(data)


def remove_snippet(trigger: str):
    data = _load()
    data["snippets"] = [s for s in data["snippets"] if s["trigger"] != trigger]
    _save(data)


def apply_snippets(text: str) -> str:
    """Replace trigger phrases with their expansions (case-insensitive, whole-phrase)."""
    if not text:
        return text
    import re
    snippets = get_snippets()
    # Longest trigger first so "intro email" beats "intro"
    for s in sorted(snippets, key=lambda x: -len(x["trigger"])):
        trigger = s["trigger"]
        expansion = s["expansion"]
        pattern = re.compile(
            r"(?i)(?<![A-Za-z0-9])" + re.escape(trigger) + r"(?![A-Za-z0-9])"
        )
        text = pattern.sub(expansion, text)
    return text


# ── Summary (dashboard) ───────────────────────────────────────────────────────
def get_summary():
    data = _load()
    sessions = data["sessions"]
    typing_wpm = data["typing_wpm"]

    now = time.time()
    week_ago = now - 7 * 24 * 3600

    total_words = sum(s["words"] for s in sessions)
    total_secs = sum(s["duration"] for s in sessions)
    total_sessions = len(sessions)

    week_words = sum(s["words"] for s in sessions if s["ts"] >= week_ago)
    week_secs = sum(s["duration"] for s in sessions if s["ts"] >= week_ago)

    avg_speak_wpm = (total_words / (total_secs / 60.0)) if total_secs > 0 else 0.0

    def _saved(words, secs):
        typed_secs = (words / typing_wpm) * 60.0
        return max(0.0, typed_secs - secs)

    # Sessions list, newest first
    history = sorted(sessions, key=lambda s: s["ts"], reverse=True)

    return {
        "typing_wpm": typing_wpm,
        "total_words": total_words,
        "total_secs": total_secs,
        "total_sessions": total_sessions,
        "avg_speak_wpm": round(avg_speak_wpm, 1),
        "saved_all_secs": _saved(total_words, total_secs),
        "saved_week_secs": _saved(week_words, week_secs),
        "week_words": week_words,
        "history": history,
        "dictionary": data["dictionary"],
        "snippets": data["snippets"],
    }
