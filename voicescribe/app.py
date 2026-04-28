"""VoiceScribe — Wispr Flow-style voice-to-text. Background app with floating pill overlay."""

import os
import sys
import time
import threading
import fcntl
import subprocess
from AppKit import NSEvent, NSFlagsChangedMask, NSPasteboard, NSPasteboardTypeString
import rumps

from voicescribe import __version__
from voicescribe.crash_log import (
    log_info, log_error, log_startup, install_global_handler, get_log_path,
)

# Install global crash handler immediately
install_global_handler()

# ── File-based logging (stdout is swallowed by the .app launcher) ────────────
_LOG = "/tmp/voicescribe_debug.log"
def _log(msg):
    with open(_LOG, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    # Also write to persistent crash log
    log_info(msg)


# ── Permission checks ───────────────────────────────────────────────────────
def _check_accessibility():
    """Check if Accessibility permission is granted.  If not, trigger the
    macOS system prompt and show a rumps notification."""
    import ctypes
    import ctypes.util
    # Load ApplicationServices framework
    lib = ctypes.cdll.LoadLibrary(
        ctypes.util.find_library("ApplicationServices")
    )
    # AXIsProcessTrustedWithOptions(options) → bool
    # Passing kAXTrustedCheckOptionPrompt=True makes macOS show the
    # "allow Accessibility" dialog automatically.
    from Foundation import NSDictionary
    import objc
    CoreFoundation = ctypes.cdll.LoadLibrary(
        ctypes.util.find_library("CoreFoundation")
    )
    try:
        # Use PyObjC to call AXIsProcessTrustedWithOptions
        from ApplicationServices import AXIsProcessTrustedWithOptions
        opts = NSDictionary.dictionaryWithObject_forKey_(True, "AXTrustedCheckOptionPrompt")
        trusted = AXIsProcessTrustedWithOptions(opts)
    except ImportError:
        # Fallback: call via ctypes
        lib.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
        lib.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
        trusted = lib.AXIsProcessTrustedWithOptions(None)
    return trusted


def _check_microphone():
    """Check microphone permission by attempting a quick recording."""
    import AVFoundation
    status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
        AVFoundation.AVMediaTypeAudio
    )
    # 0=NotDetermined, 1=Restricted, 2=Denied, 3=Authorized
    if status == 0:
        # Not yet asked — requesting will trigger the system prompt
        # (handled by Info.plist NSMicrophoneUsageDescription)
        return None  # will be asked on first use
    return status == 3


def _request_permissions():
    """Check and request all needed permissions on startup."""
    # Accessibility — triggers system prompt if not granted
    ax_ok = _check_accessibility()
    _log(f"[permissions] Accessibility: {'granted' if ax_ok else 'NOT granted'}")
    if not ax_ok:
        rumps.notification(
            "VoiceScribe — Permission Needed",
            "Accessibility access required",
            "Open System Settings → Privacy & Security → Accessibility and add VoiceScribe. "
            "Without this, auto-paste won't work.",
            sound=True,
        )
        # Open the settings pane
        subprocess.Popen([
            "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        ])

    # Microphone — Info.plist triggers the prompt automatically on first use,
    # but let's check and log the status
    mic_ok = _check_microphone()
    _log(f"[permissions] Microphone: {'granted' if mic_ok else 'not yet granted' if mic_ok is None else 'DENIED'}")
    if mic_ok is False:
        rumps.notification(
            "VoiceScribe — Permission Needed",
            "Microphone access required",
            "Open System Settings → Privacy & Security → Microphone and enable VoiceScribe.",
            sound=True,
        )
        subprocess.Popen([
            "open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
        ])

# ── Single-instance lock ──────────────────────────────────────────────────────
_LOCK_FILE = "/tmp/voicescribe.lock"
_lock_fd = open(_LOCK_FILE, "w")
try:
    fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    _lock_fd.write(str(os.getpid()))
    _lock_fd.flush()
except BlockingIOError:
    print("VoiceScribe is already running. Exiting duplicate instance.")
    sys.exit(0)
# ─────────────────────────────────────────────────────────────────────────────

from voicescribe.recorder import Recorder
from voicescribe.transcriber import Transcriber
from voicescribe.cleaner import clean
from voicescribe.overlay import WaveformOverlay
from voicescribe.dashboard import DashboardWindow
from voicescribe.updater import check_for_update
from voicescribe import stats

MODEL_SIZES = ["tiny", "base", "small", "medium"]
DEFAULT_MODEL = "base"


class VoiceScribeApp(rumps.App):
    def __init__(self):
        super().__init__("VoiceScribe", title="\U0001f3a4", quit_button=None)

        # Log startup with system info
        log_startup()
        _log(f"VoiceScribe v{__version__} launching")

        self.recorder = Recorder()
        self.transcriber = Transcriber(DEFAULT_MODEL)
        self.recording = False
        self.overlay = WaveformOverlay()
        self.dashboard = DashboardWindow()
        self._record_started_at = 0.0

        self.record_btn = rumps.MenuItem("Start Recording", callback=self._toggle_recording)
        self.dashboard_btn = rumps.MenuItem("Open Dashboard", callback=self._open_dashboard)
        self.status_item = rumps.MenuItem("Ready")
        self.status_item.set_callback(None)

        self.model_menu = rumps.MenuItem("Model")
        for size in MODEL_SIZES:
            item = rumps.MenuItem(size, callback=self._change_model)
            if size == DEFAULT_MODEL:
                item.state = True
            self.model_menu.add(item)

        self.clean_toggle = rumps.MenuItem("Remove filler words", callback=self._toggle_clean)
        self.clean_toggle.state = True

        self.version_item = rumps.MenuItem(f"v{__version__}")
        self.version_item.set_callback(None)

        self.update_item = None  # shown only when update available

        self.menu = [
            self.record_btn,
            self.status_item,
            None,
            self.dashboard_btn,
            None,
            self.model_menu,
            self.clean_toggle,
            None,
            rumps.MenuItem("View Error Log", callback=self._open_log),
            self.version_item,
            None,
            rumps.MenuItem("Quit", callback=self._quit),
        ]

        self._loading = True
        threading.Thread(target=self._load_model, daemon=True).start()
        self._register_hotkey()

        # Check permissions after a short delay (event loop must be running)
        def _deferred_perms():
            from PyObjCTools import AppHelper
            AppHelper.callAfter(_request_permissions)
        threading.Timer(1.0, _deferred_perms).start()

        # Check for updates (non-blocking, fires callback only if newer version exists)
        check_for_update(self._on_update_available)

    def _register_hotkey(self):
        FN_FLAG = 0x800000
        self._fn_last_tap = 0.0
        self._fn_was_down = False

        def handler(event):
            flags = event.modifierFlags()
            fn_down = bool(flags & FN_FLAG)
            if self._fn_was_down and not fn_down:
                now = time.time()
                if now - self._fn_last_tap < 0.4:
                    self._fn_last_tap = 0.0
                    self._toggle_recording(None)
                else:
                    self._fn_last_tap = now
            self._fn_was_down = fn_down

        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSFlagsChangedMask, handler)

    def _load_model(self):
        self.status_item.title = "Loading model..."
        self.title = "⌛"
        self.transcriber.load()
        self.status_item.title = "Ready"
        self.title = "\U0001f3a4"
        self._loading = False

    def _change_model(self, sender):
        for item in self.model_menu.values():
            if isinstance(item, rumps.MenuItem):
                item.state = False
        sender.state = True
        self.transcriber = Transcriber(sender.title)
        self._loading = True
        threading.Thread(target=self._load_model, daemon=True).start()

    def _toggle_clean(self, sender):
        sender.state = not sender.state

    def _toggle_recording(self, _):
        if self._loading:
            return
        if not self.recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self.recording = True
        self.title = "\U0001f534"
        self.record_btn.title = "Stop Recording"
        self.status_item.title = "Recording..."
        self._record_started_at = time.time()
        self.recorder.start()
        self.overlay.show(self.recorder, on_stop=self._stop_from_pill)

    def _stop_from_pill(self):
        """Callback fired when the user clicks the stop button on the pill."""
        if self.recording:
            from PyObjCTools import AppHelper
            AppHelper.callAfter(self._stop_recording)

    def _open_dashboard(self, _):
        self.dashboard.show()

    def _stop_recording(self):
        self.recording = False
        self.title = "⌛"
        self.record_btn.title = "Start Recording"
        self.status_item.title = "Transcribing..."
        # Keep the pill visible — switch to status-label mode so the user sees
        # progress (Transcribing → Polishing → result) without it disappearing.
        self.overlay.set_status("Transcribing", animate=True)
        threading.Thread(target=self._process, daemon=True).start()

    def _flash_pill(self, message, hide_after=1.4):
        """Show a final status message on the pill, then auto-hide.

        Used for terminal states like 'No words detected' — the pill lingers
        long enough for the user to read it, then closes itself.
        """
        from PyObjCTools import AppHelper
        AppHelper.callAfter(self.overlay.set_status, message, False)
        threading.Timer(
            hide_after,
            lambda: AppHelper.callAfter(self.overlay.hide),
        ).start()

    def _process(self):
        try:
            from PyObjCTools import AppHelper

            duration = max(0.0, time.time() - self._record_started_at)
            audio = self.recorder.stop()
            if len(audio) == 0:
                self.title = "\U0001f3a4"
                self.status_item.title = "Ready"
                self._flash_pill("No words detected")
                return

            # Bias transcription toward user's custom vocabulary
            prompt = stats.dictionary_prompt()
            text = self.transcriber.transcribe(audio, initial_prompt=prompt)
            _log(f"[transcribe] raw: '{text}'")

            # AI polish via Ollama — replaces rule-based filler removal when enabled
            polish_settings = stats.get_polish()
            polished = False
            if polish_settings["enabled"] and polish_settings["model"] and text.strip():
                self.status_item.title = "Polishing..."
                AppHelper.callAfter(self.overlay.set_status, "Polishing", True)
                from voicescribe import polisher
                cleaned = polisher.polish(text, polish_settings["model"])
                if cleaned:
                    text = cleaned
                    polished = True
                    _log(f"[polish] applied via {polish_settings['model']}: '{text}'")
                else:
                    _log("[polish] failed, falling back to rule-based clean")

            # Rule-based filler removal (only if polish didn't happen)
            if not polished and self.clean_toggle.state:
                text = clean(text)

            # Snippet expansion (e.g. "intro email" → template)
            text = stats.apply_snippets(text)

            _log(f"[transcribe] final: '{text}'")

            self.title = "\U0001f3a4"
            word_count = len(text.split()) if text else 0

            if not text or word_count == 0:
                # Whisper returned nothing (silence / unintelligible audio)
                self.status_item.title = "No words detected"
                self._flash_pill("No words detected")
                return

            # Got text — paste and close the pill
            self._auto_paste(text)
            AppHelper.callAfter(self.overlay.hide)
            self.status_item.title = f"Last: {word_count} words"

            # Persist session stats + refresh dashboard if open
            if duration > 0:
                stats.record_session(word_count, duration, text)
                try:
                    AppHelper.callAfter(self.dashboard.push_stats)
                except Exception:
                    pass
        except Exception as e:
            log_error(f"Transcription failed: {e}", e)
            _log(f"[process] error: {e}")
            self.title = "\U0001f3a4"
            self.status_item.title = f"Error: {str(e)[:40]}"
            self._flash_pill("Error")

    def _auto_paste(self, text):
        """Copy to clipboard and simulate Cmd+V.

        Strategy order (best → worst):
          1. paste_helper — native binary inside VoiceScribe.app/Contents/MacOS,
             so TCC attributes the keystroke to com.voicescribe.app (NOT to
             Python). This is the only strategy that works reliably after a
             macOS update or TCC reset.
          2. NSAppleScript / CGEvent / osascript — fallbacks if the helper
             isn't installed (e.g. running from source via `python run.py`).
        """
        _log("[paste] copying to clipboard...")
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        ok = pb.setString_forType_(text, NSPasteboardTypeString)
        _log(f"[paste] clipboard set: {ok}")

        from PyObjCTools import AppHelper

        def _do_paste():
            try:
                # Strategy 1 — bundled paste_helper (the reliable path)
                helper = "/Applications/VoiceScribe.app/Contents/MacOS/paste_helper"
                if os.path.exists(helper):
                    _log("[paste] launching paste_helper...")
                    try:
                        subprocess.Popen([helper])
                        _log("[paste] paste_helper launched")
                        return
                    except Exception as e:
                        _log(f"[paste] paste_helper failed: {e}")

                # Small delay to let clipboard settle and focus return
                time.sleep(0.15)

                # Strategy 2: In-process NSAppleScript (uses parent bundle identity)
                _log("[paste] trying NSAppleScript...")
                from Foundation import NSAppleScript
                script = NSAppleScript.alloc().initWithSource_(
                    'tell application "System Events" to keystroke "v" using command down'
                )
                result, error = script.executeAndReturnError_(None)
                if error:
                    err_msg = error.get("NSAppleScriptErrorMessage", "unknown")
                    _log(f"[paste] NSAppleScript error: {err_msg}")

                    # Strategy 3: CGEvent fallback
                    _log("[paste] trying CGEvent Cmd+V...")
                    from Quartz import (
                        CGEventCreateKeyboardEvent, CGEventPost, CGEventSetFlags,
                        kCGHIDEventTap, kCGEventFlagMaskCommand,
                    )
                    KVK_V = 9
                    down = CGEventCreateKeyboardEvent(None, KVK_V, True)
                    if down is not None:
                        CGEventSetFlags(down, kCGEventFlagMaskCommand)
                        CGEventPost(kCGHIDEventTap, down)
                        up = CGEventCreateKeyboardEvent(None, KVK_V, False)
                        CGEventSetFlags(up, kCGEventFlagMaskCommand)
                        CGEventPost(kCGHIDEventTap, up)
                        _log("[paste] CGEvent Cmd+V sent")

                    # Strategy 4: osascript subprocess
                    time.sleep(0.1)
                    _log("[paste] trying osascript subprocess...")
                    subprocess.Popen([
                        "osascript", "-e",
                        'tell application "System Events" to keystroke "v" using command down'
                    ])
                    _log("[paste] osascript sent")
                else:
                    _log("[paste] NSAppleScript Cmd+V sent ok")

            except Exception as e:
                _log(f"[paste] error: {e}")
                log_error("Paste failed", e)
                import traceback
                _log(traceback.format_exc())

        AppHelper.callAfter(_do_paste)

    def _on_update_available(self, latest_version, download_url):
        """Called on the main thread when a newer release is found on GitHub."""
        _log(f"[update] new version available: {latest_version}")
        self._update_url = download_url
        # Add a highlighted menu item
        update_btn = rumps.MenuItem(
            f"⬆ Update Available: v{latest_version}",
            callback=self._open_update_page,
        )
        self.menu.insert_after(self.version_item.title, update_btn)
        # Show a notification
        rumps.notification(
            "VoiceScribe Update Available",
            f"v{latest_version} is out",
            "Click 'Update Available' in the menu bar to get it.",
            sound=False,
        )

    def _open_update_page(self, _):
        url = getattr(self, "_update_url", f"https://github.com/kalaanakonda/VoiceScribe/releases")
        subprocess.Popen(["open", url])

    def _open_log(self, _):
        """Open the crash log in Console.app / default text editor."""
        log_path = get_log_path()
        subprocess.Popen(["open", log_path])

    def _quit(self, _):
        _log("VoiceScribe quitting")
        self.overlay.hide()
        rumps.quit_application()


def main():
    VoiceScribeApp().run()


if __name__ == "__main__":
    main()
