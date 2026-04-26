"""Auto-update checker — queries GitHub for newer versions on launch."""

import json
import threading
import urllib.request
import urllib.error
from voicescribe import __version__

GITHUB_REPO = "kalaanakonda/VoiceScribe"
CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_version(v: str):
    """Turn '1.2.3' into (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_update(callback):
    """Check GitHub for a newer release in a background thread.

    `callback(latest_version: str, download_url: str)` is called on the
    main thread (via AppHelper) only when a newer version exists.
    If the check fails or the app is already up-to-date, nothing happens.
    """
    def _check():
        try:
            req = urllib.request.Request(
                CHECK_URL,
                headers={"Accept": "application/vnd.github.v3+json",
                         "User-Agent": "VoiceScribe-UpdateCheck"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            latest_tag = data.get("tag_name", "")
            latest = _parse_version(latest_tag)
            current = _parse_version(__version__)

            if latest > current:
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                # Schedule callback on main thread
                from PyObjCTools import AppHelper
                AppHelper.callAfter(callback, latest_tag.lstrip("v"), html_url)

        except Exception:
            # Silently ignore — update check is best-effort
            pass

    threading.Thread(target=_check, daemon=True).start()
