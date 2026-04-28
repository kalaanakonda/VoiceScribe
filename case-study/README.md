# VoiceScribe — Case Study

> A voice-to-text tool that disappears.
> Free, local, open-source — designed against a category dominated by $14/mo subscriptions and cloud APIs.

| | |
|---|---|
| **Role** | Design + engineering |
| **Timeline** | 2 weeks |
| **Stack** | Python · PyObjC · Whisper · C |
| **Output** | Open-source macOS app |

---

## The problem

Voice-to-text on macOS already exists. But every option costs something — your privacy, your money, or your attention.

| Product | Cost/yr | Local? | Open? |
|---|---|---|---|
| Wispr Flow | $168 | No | No |
| Superwhisper | $96 | Partial | No |
| macOS Dictation | Free | No (cloud) | No |
| **VoiceScribe** | **$0** | **Yes** | **Yes** |

Whisper has been open-source since 2022. The ML problem was solved. The remaining problem was *design* — wrapping a 1.5 GB model in something that feels like a feature, not a tool.

---

## The insight

I watched myself dictate. The flow was four steps:

```
[ tap hotkey ] → [ speak ] → [ tap again ] → [ text appears ]
```

Anything else is friction. Every design decision after this came from one question:
**Does this stay out of the way?**

---

## Design principles

1. **Invisible until needed.** No menu bar UI. No window. The app exists only between tap and paste.
2. **One gesture, two states.** Double-tap Fn to start. Double-tap Fn to stop. The whole app is two states.
3. **Trust through restraint.** Monochrome only. No animations that aren't audio-reactive. No copy that asks for engagement.
4. **Local by default.** No sign-in. No account. No API key.

---

## The solution

A floating pill at the bottom of the screen that breathes with your voice.

```
┌─────────────────────────────────────────────┐
│  · · ·  ·  ·  · · · · ·  ·  · · ·      [■] │
└─────────────────────────────────────────────┘
                  214 × 44 px
```

That's the entire UI.

---

## Four decisions

### 01 · Placement — Bottom of screen, not top
The pill sits 80 pixels above the dock. Most typing happens in the lower 60% of the screen. Putting feedback near the action shortens the loop between speech and visual confirmation.

> *Wispr Flow's top-anchored bar pulls your eyes toward the menu bar — away from where you're typing.*

### 02 · Focus — NSPanel with NSNonactivatingPanelMask
The first build used a normal NSWindow. Clicking the stop button stole focus from whatever text field the user was typing into — so the auto-pasted text went nowhere. NSPanel + `NSNonactivatingPanelMask` made the pill clickable but invisible to the focus system.

> *A non-obvious bug that surfaced through real use. Test the click in context, not in isolation.*

### 03 · Restraint — I removed the menu bar button
The first iteration had a dedicated record toggle in the menu bar. On a MacBook Pro, it pushed Bluetooth, Wi-Fi, and Battery indicators behind the camera notch. The single-feature win wasn't worth the system-level loss.

> *Removing features is a design decision.*

### 04 · Permissions — A native paste helper for TCC stability
macOS attributes Accessibility permission per-binary. The C launcher inside `VoiceScribe.app` spawns Python — so when Python tried to send Cmd+V, macOS asked "does *Python* have permission?" Answer: no, not after the next OS update.

The fix was a 50-line C binary inside the .app bundle. Python calls it as a subprocess. macOS now sees the keystroke source as `com.voicescribe.app` — a stable, signed bundle ID.

> *A design problem masquerading as a permissions bug.*

---

## How it works

```
┌──────────┐   ┌─────────────┐   ┌─────────┐   ┌──────────┐
│   Mic    │ → │ sounddevice │ → │ Whisper │ → │ Cleaner  │
└──────────┘   └─────────────┘   └─────────┘   └────┬─────┘
                                                    ▼
┌──────────┐   ┌──────────────┐   ┌─────────────────────┐
│ Focused  │ ← │ paste_helper │ ← │    NSPasteboard     │
│   app    │   │  (bundled)   │   │     (clipboard)     │
└──────────┘   └──────────────┘   └─────────────────────┘
                      │
                      └── TCC: com.voicescribe.app ✓
```

The bundled `paste_helper` is what makes the keystroke survive macOS updates.

---

## Outcomes

| | |
|---|---|
| **Subscription cost** | $0 |
| **Local audio** | 100% |
| **Install command** | 1 |
| **UI lines of code** | ~250 |

Shipped publicly as MIT-licensed. Installs via a single `curl` command or Homebrew tap. Audio capture → transcription → paste, all without leaving the machine.

---

## What I learned

**The OS is the canvas. Respect it.**
Three of the four key decisions came from *not* overriding system behavior — using NSPanel instead of fighting the focus system, using a hotkey instead of crowding the menu bar, signing the helper into the bundle instead of working around TCC.

**Permission systems are UX problems.**
The auto-paste failure looked like a bug. It was actually a design constraint I hadn't internalized — TCC tracks *who* is asking, not *what* they're doing. The fix wasn't more code; it was placing the right binary in the right folder.

**Removing features is a design decision.**
The menu bar button, the multi-color waveform, the always-visible toolbar — each one shipped, then got cut. The pill is what's left after the unnecessary parts were removed.

> The product is the part that stayed.

---

[github.com/kalaanakonda/VoiceScribe](https://github.com/kalaanakonda/VoiceScribe) · 2026
