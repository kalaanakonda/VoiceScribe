"""Persistent crash / error logging for VoiceScribe.

Writes to ~/Library/Application Support/VoiceScribe/crash.log so users
can easily find and share it when reporting issues.  The file is rotated
once it exceeds ~500 KB to avoid unbounded growth.
"""

import os
import sys
import time
import traceback
import platform
from pathlib import Path
from voicescribe import __version__

_DIR = Path.home() / "Library" / "Application Support" / "VoiceScribe"
_LOG = _DIR / "crash.log"
_MAX_SIZE = 500_000  # bytes


def _ensure_dir():
    _DIR.mkdir(parents=True, exist_ok=True)


def _rotate_if_needed():
    try:
        if _LOG.exists() and _LOG.stat().st_size > _MAX_SIZE:
            bak = _LOG.with_suffix(".log.old")
            if bak.exists():
                bak.unlink()
            _LOG.rename(bak)
    except Exception:
        pass


def log_info(msg: str):
    """Write an informational line to crash.log."""
    _ensure_dir()
    _rotate_if_needed()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(_LOG, "a") as f:
        f.write(f"[{ts}] INFO  {msg}\n")


def log_error(msg: str, exc: Exception = None):
    """Write an error (with optional traceback) to crash.log."""
    _ensure_dir()
    _rotate_if_needed()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(_LOG, "a") as f:
        f.write(f"[{ts}] ERROR {msg}\n")
        if exc:
            f.write(traceback.format_exc() + "\n")


def log_startup():
    """Write a startup banner with system info — helpful for debugging."""
    _ensure_dir()
    _rotate_if_needed()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    mac_ver = platform.mac_ver()[0]
    arch = platform.machine()
    py_ver = platform.python_version()
    with open(_LOG, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{ts}] VoiceScribe v{__version__} started\n")
        f.write(f"  macOS {mac_ver} ({arch}), Python {py_ver}\n")
        f.write(f"{'='*60}\n")


def install_global_handler():
    """Replace sys.excepthook so any uncaught exception is logged before
    the process terminates."""
    original = sys.excepthook

    def _handler(exc_type, exc_value, exc_tb):
        try:
            _ensure_dir()
            _rotate_if_needed()
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            with open(_LOG, "a") as f:
                f.write(f"\n[{ts}] CRASH (uncaught exception)\n{tb}\n")
        except Exception:
            pass
        # Still call the original hook so the process exits normally
        original(exc_type, exc_value, exc_tb)

    sys.excepthook = _handler


def get_log_path() -> str:
    """Return the path to the crash log for display in the menu."""
    return str(_LOG)
