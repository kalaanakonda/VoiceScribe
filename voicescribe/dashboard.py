"""Dashboard window — WKWebView loading dashboard.html, with a JS↔Python bridge."""

import json
import os

import objc
from AppKit import (
    NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskFullSizeContentView,
    NSBackingStoreBuffered, NSColor, NSApp,
    NSWindowTitleHidden,
)
from Foundation import NSObject, NSURL, NSMakeRect
from WebKit import (
    WKWebView, WKWebViewConfiguration, WKUserContentController,
    WKWebsiteDataStore,
)

from voicescribe import stats, polisher


WIN_W = 380.0
WIN_H = 480.0


class _Bridge(NSObject):
    """Receives messages from JS (window.webkit.messageHandlers.vsbridge.postMessage)
    and doubles as the WKNavigationDelegate so we push stats on load finish."""

    def initWithController_(self, controller):
        self = objc.super(_Bridge, self).init()
        if self is None:
            return None
        self._controller = controller
        return self

    # ── WKScriptMessageHandler ──
    def userContentController_didReceiveScriptMessage_(self, ucc, message):
        try:
            body = message.body()
            if not isinstance(body, dict):
                return
            mtype = body.get("type")
            if mtype == "refresh":
                pass
            elif mtype == "setTypingWpm":
                stats.set_typing_wpm(int(body.get("value", 40)))
            elif mtype == "deleteSession":
                stats.delete_session(int(body.get("id", 0)))
            elif mtype == "addWord":
                stats.add_dictionary_word(body.get("word", ""))
            elif mtype == "removeWord":
                stats.remove_dictionary_word(body.get("word", ""))
            elif mtype == "addSnippet":
                stats.add_snippet(body.get("trigger", ""), body.get("expansion", ""))
            elif mtype == "removeSnippet":
                stats.remove_snippet(body.get("trigger", ""))
            elif mtype == "setPolish":
                en = body.get("enabled")
                md = body.get("model")
                # Log what we received so we can diagnose the toggle bug
                try:
                    with open("/tmp/voicescribe_debug.log", "a") as f:
                        import time as _t
                        f.write(f"{_t.strftime('%H:%M:%S')} [dashboard] setPolish received enabled={en!r} model={md!r}\n")
                except Exception:
                    pass
                stats.set_polish(enabled=en, model=md)
                # Log what's saved after
                try:
                    saved = stats.get_polish()
                    with open("/tmp/voicescribe_debug.log", "a") as f:
                        import time as _t
                        f.write(f"{_t.strftime('%H:%M:%S')} [dashboard] setPolish saved -> {saved}\n")
                except Exception:
                    pass
            self._controller.push_stats()
        except Exception as e:
            print(f"[dashboard] bridge error: {e}", flush=True)

    # ── WKNavigationDelegate ──
    def webView_didFinishNavigation_(self, webview, nav):
        # Page + JS are fully parsed; now it's safe to push data.
        self._controller.push_stats()


class DashboardWindow:
    def __init__(self):
        self._window = None
        self._webview = None
        self._bridge = None

    def show(self):
        if self._window is not None:
            self._window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            self.push_stats()
            return

        style = (NSWindowStyleMaskTitled
                 | NSWindowStyleMaskClosable
                 | NSWindowStyleMaskFullSizeContentView)
        rect = NSMakeRect(0, 0, WIN_W, WIN_H)
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        win.setTitle_("VoiceScribe")
        win.setTitlebarAppearsTransparent_(True)
        win.setTitleVisibility_(NSWindowTitleHidden)
        win.setBackgroundColor_(
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.051, 0.051, 0.051, 1.0
            )
        )
        win.setMovableByWindowBackground_(True)
        win.center()

        # Webview config with a message handler named "vsbridge".
        ucc = WKUserContentController.alloc().init()
        bridge = _Bridge.alloc().initWithController_(self)
        ucc.addScriptMessageHandler_name_(bridge, "vsbridge")

        cfg = WKWebViewConfiguration.alloc().init()
        cfg.setUserContentController_(ucc)
        # Non-persistent data store → no caching across launches
        cfg.setWebsiteDataStore_(WKWebsiteDataStore.nonPersistentDataStore())

        wv = WKWebView.alloc().initWithFrame_configuration_(
            NSMakeRect(0, 0, WIN_W, WIN_H), cfg
        )
        wv.setNavigationDelegate_(bridge)
        # Transparent webview background so the window's dark bg shows through.
        try:
            wv.setValue_forKey_(False, "drawsBackground")
        except Exception:
            pass

        # Read the HTML fresh every time → immune to any caching.
        html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        with open(html_path, "r") as f:
            html = f.read()
        base_url = NSURL.fileURLWithPath_(os.path.dirname(html_path) + "/")
        wv.loadHTMLString_baseURL_(html, base_url)

        win.setContentView_(wv)
        win.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

        self._window = win
        self._webview = wv
        self._bridge = bridge

    def push_stats(self):
        if self._webview is None:
            return
        summary = stats.get_summary()

        # Augment with AI-polish state — runs Ollama HTTP probe (~2s timeout).
        polish_settings = stats.get_polish()
        ollama_models = polisher.list_models()
        ollama_up = bool(ollama_models) or polisher.is_available()

        # Auto-pick a default model the first time we detect Ollama
        chosen_model = polish_settings["model"]
        if ollama_models and chosen_model not in ollama_models:
            chosen_model = polisher.suggest_default_model(ollama_models)
            if chosen_model:
                stats.set_polish(model=chosen_model)

        summary["polish"] = {
            "enabled": polish_settings["enabled"],
            "model": chosen_model,
            "ollama_up": ollama_up,
            "models": ollama_models,
        }

        payload = json.dumps(summary)
        js = f"window.vsUpdate && window.vsUpdate({json.dumps(payload)});"
        self._webview.evaluateJavaScript_completionHandler_(js, None)

    def hide(self):
        if self._window is not None:
            self._window.orderOut_(None)
