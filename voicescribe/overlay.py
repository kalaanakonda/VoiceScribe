"""Pill-shaped waveform overlay — pure PyObjC, drawn in the main process."""

import math
import time

import objc
from AppKit import (
    NSWindow, NSView, NSColor, NSScreen,
    NSTimer, NSGraphicsContext,
    NSBorderlessWindowMask, NSBackingStoreBuffered,
)
from Foundation import NSMakeRect, NSMakePoint
import Quartz


WINDOW_W = 180.0
WINDOW_H = 44.0
DOT_COUNT = 22


# ─── PillView (NSView subclass) ───────────────────────────────────────────────
class PillView(NSView):
    def initWithFrame_recorder_(self, frame, recorder):
        self = objc.super(PillView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._recorder = recorder
        self._phase = 0.0
        self._start = time.time()
        self._timer = None
        return self

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

        level = float(getattr(self._recorder, "level", 0.0))
        self._phase += 0.15

        cs = Quartz.CGColorSpaceCreateDeviceRGB()

        # Clear (transparent window)
        Quartz.CGContextClearRect(ctx, bounds)

        # ── Rounded rect pill background (grayscale, pill-shaped) ──
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

        # ── Waveform dots (grayscale, centred, tight) ──
        cy = h / 2.0
        margin = 14.0
        total_w = w - margin * 2.0
        max_amp = (h / 2.0) - 6.0  # keep dots inside the pill

        for i in range(DOT_COUNT):
            t = i / (DOT_COUNT - 1)
            x = margin + t * total_w

            wave1 = math.sin(t * math.pi * 3.0 + self._phase) * level
            wave2 = math.sin(t * math.pi * 2.0 - self._phase * 0.6) * level * 0.6
            wave3 = math.sin(t * math.pi * 4.5 + self._phase * 1.3) * level * 0.25
            wave = wave1 + wave2 + wave3

            y = cy + wave * max_amp

            # Pure grayscale, brightness driven by amplitude
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

    def show(self, recorder):
        if self._window is not None:
            return
        print("[pill] show() called", flush=True)

        screen = NSScreen.mainScreen()
        sf = screen.frame()
        x = sf.origin.x + (sf.size.width - WINDOW_W) / 2.0
        # Place near top of screen (below menu bar)
        y = sf.origin.y + sf.size.height - WINDOW_H - 80.0
        win_rect = NSMakeRect(x, y, WINDOW_W, WINDOW_H)

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            win_rect,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False,
        )
        win.setLevel_(
            Quartz.CGWindowLevelForKey(Quartz.kCGMaximumWindowLevelKey) - 1
        )
        win.setOpaque_(False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setHasShadow_(False)
        win.setIgnoresMouseEvents_(True)
        win.setCollectionBehavior_(
            Quartz.NSWindowCollectionBehaviorCanJoinAllSpaces |
            Quartz.NSWindowCollectionBehaviorStationary |
            Quartz.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        view = PillView.alloc().initWithFrame_recorder_(
            NSMakeRect(0, 0, WINDOW_W, WINDOW_H), recorder
        )
        win.setContentView_(view)
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

    @property
    def visible(self):
        return self._window is not None
