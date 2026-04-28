"""Pill-shaped waveform overlay — pure PyObjC, drawn in the main process."""

import math
import time

import objc
from AppKit import (
    NSPanel, NSView, NSColor, NSScreen,
    NSTimer, NSGraphicsContext,
    NSBorderlessWindowMask, NSBackingStoreBuffered,
    NSNonactivatingPanelMask,
    NSAttributedString, NSFont,
    NSForegroundColorAttributeName, NSFontAttributeName,
)
from Foundation import NSMakeRect, NSMakePoint
import Quartz


WINDOW_W = 214.0
WINDOW_H = 44.0
DOT_COUNT = 22
STOP_BTN_W = 34.0  # width of the stop-button hit area on the right


# ─── PillView (NSView subclass) ───────────────────────────────────────────────
class PillView(NSView):
    def initWithFrame_recorder_onStop_(self, frame, recorder, on_stop):
        self = objc.super(PillView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._recorder = recorder
        self._on_stop = on_stop
        self._phase = 0.0
        self._start = time.time()
        self._timer = None
        self._stop_hover = False
        # Status mode: when set to a string, the pill renders a status label
        # ("Transcribing", "Polishing", "No words detected") instead of the
        # live waveform. None = recording mode (default).
        self._status_text = None
        self._status_animate = False
        self._status_started = 0.0
        return self

    @objc.python_method
    def setStatus(self, text, animate=False):
        """Switch to status-label mode. Pass None to return to waveform mode."""
        self._status_text = text
        self._status_animate = bool(animate)
        self._status_started = time.time()
        self.setNeedsDisplay_(True)

    @objc.python_method
    def startTimer(self):
        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / 30.0, self, b'tick:', None, True
        )

    @objc.python_method
    def stopTimer(self):
        if self._timer:
            self._timer.invalidate()
            self._timer = None

    def tick_(self, _timer):
        self.setNeedsDisplay_(True)

    def acceptsFirstMouse_(self, event):
        return True

    def mouseDown_(self, event):
        # Status mode (transcribing/polishing/etc.) — ignore clicks
        if self._status_text is not None:
            return
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        bounds = self.bounds()
        stop_x = bounds.size.width - STOP_BTN_W
        if loc.x >= stop_x:
            if self._on_stop:
                self._on_stop()

    def mouseEntered_(self, event):
        self._stop_hover = True
        self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        self._stop_hover = False
        self.setNeedsDisplay_(True)

    def isFlipped(self):
        return False

    def drawRect_(self, dirty):
        try:
            self._draw()
        except Exception as e:
            import traceback, sys
            print(f"[pill] drawRect_ error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    @objc.python_method
    def _draw(self):
        ctx = NSGraphicsContext.currentContext().CGContext()
        bounds = self.bounds()
        w = bounds.size.width
        h = bounds.size.height
        cs = Quartz.CGColorSpaceCreateDeviceRGB()

        # Clear (transparent window)
        Quartz.CGContextClearRect(ctx, bounds)

        # ── Rounded rect pill background ──
        inset = 1.0
        rect = Quartz.CGRectMake(inset, inset, w - 2 * inset, h - 2 * inset)
        radius = (h - 2 * inset) / 2.0
        path = _rounded_rect_path(rect, radius)

        Quartz.CGContextSaveGState(ctx)
        Quartz.CGContextSetShadowWithColor(
            ctx, Quartz.CGSizeMake(0, -3), 10.0,
            Quartz.CGColorCreate(cs, [0.0, 0.0, 0.0, 0.5])
        )
        Quartz.CGContextSetFillColorWithColor(
            ctx, Quartz.CGColorCreate(cs, [0.08, 0.08, 0.08, 0.94])
        )
        Quartz.CGContextAddPath(ctx, path)
        Quartz.CGContextFillPath(ctx)
        Quartz.CGContextRestoreGState(ctx)

        # Hairline border
        Quartz.CGContextSaveGState(ctx)
        Quartz.CGContextSetStrokeColorWithColor(
            ctx, Quartz.CGColorCreate(cs, [0.20, 0.20, 0.20, 1.0])
        )
        Quartz.CGContextSetLineWidth(ctx, 1.0)
        Quartz.CGContextAddPath(ctx, path)
        Quartz.CGContextStrokePath(ctx)
        Quartz.CGContextRestoreGState(ctx)

        # Branch on mode: status label vs live waveform
        if self._status_text is not None:
            self._draw_status(ctx, w, h, cs)
        else:
            self._phase += 0.15
            self._draw_waveform(ctx, w, h, cs)
            self._draw_stop_button(ctx, w, h, cs)

    @objc.python_method
    def _draw_waveform(self, ctx, w, h, cs):
        level = float(getattr(self._recorder, "level", 0.0))
        cy = h / 2.0
        margin = 14.0
        dots_right = w - STOP_BTN_W
        total_w = dots_right - margin
        max_amp = (h / 2.0) - 6.0

        for i in range(DOT_COUNT):
            t = i / (DOT_COUNT - 1)
            x = margin + t * total_w

            wave1 = math.sin(t * math.pi * 3.0 + self._phase) * level
            wave2 = math.sin(t * math.pi * 2.0 - self._phase * 0.6) * level * 0.6
            wave3 = math.sin(t * math.pi * 4.5 + self._phase * 1.3) * level * 0.25
            wave = wave1 + wave2 + wave3
            y = cy + wave * max_amp

            v = 0.55 + abs(wave) * 0.45
            v = max(0.0, min(1.0, v))
            dot_r = 1.6 + abs(wave) * 1.8

            Quartz.CGContextSaveGState(ctx)
            Quartz.CGContextSetFillColorWithColor(
                ctx, Quartz.CGColorCreate(cs, [v, v, v, 1.0])
            )
            Quartz.CGContextFillEllipseInRect(
                ctx, Quartz.CGRectMake(x - dot_r, y - dot_r, dot_r * 2, dot_r * 2)
            )
            Quartz.CGContextRestoreGState(ctx)

    @objc.python_method
    def _draw_stop_button(self, ctx, w, h, cs):
        btn_cx = w - STOP_BTN_W / 2.0 - 4.0
        btn_cy = h / 2.0
        circle_r = 11.0

        Quartz.CGContextSaveGState(ctx)
        red_alpha = 1.0 if self._stop_hover else 0.92
        Quartz.CGContextSetFillColorWithColor(
            ctx, Quartz.CGColorCreate(cs, [0.92, 0.26, 0.21, red_alpha])
        )
        Quartz.CGContextFillEllipseInRect(
            ctx, Quartz.CGRectMake(btn_cx - circle_r, btn_cy - circle_r, circle_r * 2, circle_r * 2)
        )
        Quartz.CGContextRestoreGState(ctx)

        sq = 7.0
        Quartz.CGContextSaveGState(ctx)
        Quartz.CGContextSetFillColorWithColor(
            ctx, Quartz.CGColorCreate(cs, [1.0, 1.0, 1.0, 1.0])
        )
        Quartz.CGContextFillRect(
            ctx, Quartz.CGRectMake(btn_cx - sq / 2.0, btn_cy - sq / 2.0, sq, sq)
        )
        Quartz.CGContextRestoreGState(ctx)

    @objc.python_method
    def _draw_status(self, ctx, w, h, cs):
        """Draw a centered status label (e.g. 'Transcribing...', 'Polishing...',
        'No words detected'). When `_status_animate` is set, three loading
        dots cycle next to the label."""
        text = self._status_text or ""

        # Build label + animated trailing dots if requested
        if self._status_animate:
            n_dots = int((time.time() - self._status_started) * 2.5) % 4
            text = text + "." * n_dots

        # Render text via NSAttributedString — drawing into the focused
        # NSGraphicsContext (which is current during drawRect_).
        white = NSColor.colorWithCalibratedWhite_alpha_(0.92, 1.0)
        font = NSFont.systemFontOfSize_(13.0)
        attrs = {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: white,
        }
        astr = NSAttributedString.alloc().initWithString_attributes_(text, attrs)
        size = astr.size()
        x = (w - size.width) / 2.0
        y = (h - size.height) / 2.0 - 1.0  # tiny optical adjust
        astr.drawAtPoint_(NSMakePoint(x, y))


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _rounded_rect_path(rect, radius):
    path = Quartz.CGPathCreateMutable()
    x = rect.origin.x
    y = rect.origin.y
    w = rect.size.width
    h = rect.size.height
    Quartz.CGPathMoveToPoint(path, None, x + radius, y)
    Quartz.CGPathAddLineToPoint(path, None, x + w - radius, y)
    Quartz.CGPathAddArcToPoint(path, None, x + w, y, x + w, y + radius, radius)
    Quartz.CGPathAddLineToPoint(path, None, x + w, y + h - radius)
    Quartz.CGPathAddArcToPoint(path, None, x + w, y + h, x + w - radius, y + h, radius)
    Quartz.CGPathAddLineToPoint(path, None, x + radius, y + h)
    Quartz.CGPathAddArcToPoint(path, None, x, y + h, x, y + h - radius, radius)
    Quartz.CGPathAddLineToPoint(path, None, x, y + radius)
    Quartz.CGPathAddArcToPoint(path, None, x, y, x + radius, y, radius)
    Quartz.CGPathCloseSubpath(path)
    return path


# ─── Public overlay controller ────────────────────────────────────────────────
class WaveformOverlay:
    def __init__(self):
        self._window = None
        self._view = None

    def show(self, recorder, on_stop=None):
        if self._window is not None:
            return
        print("[pill] show() called", flush=True)

        screen = NSScreen.mainScreen()
        sf = screen.frame()
        x = sf.origin.x + (sf.size.width - WINDOW_W) / 2.0
        # Place near bottom of screen (above the Dock)
        y = sf.origin.y + 80.0
        win_rect = NSMakeRect(x, y, WINDOW_W, WINDOW_H)

        # NSPanel with NSNonactivatingPanelMask: accepts clicks without ever
        # becoming key window, so the previously-focused text field keeps its
        # focus when the user clicks the stop button.
        win = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            win_rect,
            NSBorderlessWindowMask | NSNonactivatingPanelMask,
            NSBackingStoreBuffered,
            False,
        )
        win.setLevel_(
            Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey) - 1
        )
        win.setOpaque_(False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setHasShadow_(False)
        # Accept clicks on the pill — but the nonactivating panel mask
        # ensures clicking does NOT steal key-window focus from the app behind.
        win.setIgnoresMouseEvents_(False)
        win.setBecomesKeyOnlyIfNeeded_(True)
        win.setHidesOnDeactivate_(False)
        win.setFloatingPanel_(True)
        win.setCollectionBehavior_(
            Quartz.NSWindowCollectionBehaviorCanJoinAllSpaces |
            Quartz.NSWindowCollectionBehaviorStationary |
            Quartz.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        view = PillView.alloc().initWithFrame_recorder_onStop_(
            NSMakeRect(0, 0, WINDOW_W, WINDOW_H), recorder, on_stop
        )
        win.setContentView_(view)
        # orderFrontRegardless shows the window without activating our app,
        # preserving whichever app/text-field was focused before.
        win.orderFrontRegardless()
        view.startTimer()

        self._window = win
        self._view = view

    def hide(self):
        if self._window is None:
            return
        if self._view:
            self._view.stopTimer()
        self._window.orderOut_(None)
        self._window = None
        self._view = None

    def set_status(self, text, animate=True):
        """Switch the visible pill into status-label mode. No-op if hidden.
        Pass None to switch back to live waveform mode."""
        if self._view is None:
            return
        self._view.setStatus(text, animate)

    @property
    def visible(self):
        return self._window is not None
