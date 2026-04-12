"""VoiceScribe — Wispr Flow-style voice-to-text. Background app with floating pill overlay."""

import os
import sys
import time
import threading
import fcntl
from AppKit import NSEvent, NSFlagsChangedMask, NSPasteboard, NSPasteboardTypeString
import rumps

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
from voicescribe import stats

MODEL_SIZES = ["tiny", "base", "small", "medium"]
DEFAULT_MODEL = "base"


class VoiceScribeApp(rumps.App):
    def __init__(self):
        super().__init__("VoiceScribe", title="\U0001f3a4", quit_button=None)

        self.recorder = Recorder()
        self.transcriber = Transcriber(DEFAULT_MODEL)
        self.recording = False
        self.overlay = WaveformOverlay()
        self.dashboard = DashboardWindow()
        self._record_started_at = 0.0

        self.record_btn = rumps.MenuItem("Start Recording  (double-tap Fn)", callback=self._toggle_recording)
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

        self.menu = [
            self.record_btn,
            self.status_item,
            None,
            self.dashboard_btn,
            None,
            self.model_menu,
            self.clean_toggle,
            None,
            rumps.MenuItem("Quit", callback=self._quit),
        ]

        self._loading = True
        threading.Thread(target=self._load_model, daemon=True).start()
        self._register_hotkey()

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
        self.title = "\u231B"
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
        self.record_btn.title = "Stop Recording  (double-tap Fn)"
        self.status_item.title = "Recording..."
        self._record_started_at = time.time()
        self.recorder.start()
        self.overlay.show(self.recorder)

    def _open_dashboard(self, _):
        self.dashboard.show()

    def _stop_recording(self):
        self.recording = False
        self.title = "\u231B"
        self.record_btn.title = "Start Recording  (double-tap Fn)"
        self.status_item.title = "Transcribing..."
        self.overlay.hide()
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            duration = max(0.0, time.time() - self._record_started_at)
            audio = self.recorder.stop()
            if len(audio) == 0:
                self.title = "\U0001f3a4"
                self.status_item.title = "Ready"
                return

            # Bias transcription toward user's custom vocabulary
            prompt = stats.dictionary_prompt()
            text = self.transcriber.transcribe(audio, initial_prompt=prompt)
            if self.clean_toggle.state:
                text = clean(text)
            # Snippet expansion (e.g. "intro email" → template)
            text = stats.apply_snippets(text)

            if text:
                self._auto_paste(text)

            self.title = "\U0001f3a4"
            word_count = len(text.split()) if text else 0
            self.status_item.title = f"Last: {word_count} words"

            # Persist session stats + refresh dashboard if open
            if word_count > 0 and duration > 0:
                stats.record_session(word_count, duration, text)
                try:
                    from PyObjCTools import AppHelper
                    AppHelper.callAfter(self.dashboard.push_stats)
                except Exception:
                    pass
        except Exception as e:
            print(f"Error: {e}", flush=True)
            self.title = "\U0001f3a4"
            self.status_item.title = f"Error: {str(e)[:40]}"

    def _auto_paste(self, text):
        """Copy to clipboard and simulate Cmd+V — synthesis MUST run on main thread
        because macOS 26's TSM asserts main-thread for keyboard input source lookup."""
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSPasteboardTypeString)

        from PyObjCTools import AppHelper
        from Quartz import (
            CGEventCreateKeyboardEvent, CGEventPost, CGEventSetFlags,
            kCGHIDEventTap, kCGEventFlagMaskCommand,
        )
        KVK_V = 9  # ANSI "V"

        def _do_paste():
            try:
                down = CGEventCreateKeyboardEvent(None, KVK_V, True)
                CGEventSetFlags(down, kCGEventFlagMaskCommand)
                CGEventPost(kCGHIDEventTap, down)
                up = CGEventCreateKeyboardEvent(None, KVK_V, False)
                CGEventSetFlags(up, kCGEventFlagMaskCommand)
                CGEventPost(kCGHIDEventTap, up)
            except Exception as e:
                print(f"[paste] error: {e}", flush=True)

        # Hop to main thread. callAfter uses the main runloop, so this runs
        # after the short delay for the pasteboard to settle.
        AppHelper.callAfter(_do_paste)

    def _quit(self, _):
        self.overlay.hide()
        rumps.quit_application()


def main():
    VoiceScribeApp().run()


if __name__ == "__main__":
    main()
