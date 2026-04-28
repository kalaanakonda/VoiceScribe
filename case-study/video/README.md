# VoiceScribe — Design System Explainer

A Remotion-rendered explainer video showing every primitive, component, and state in the VoiceScribe design system.

**Length:** 28 s · **Resolution:** 1920 × 1080 · **FPS:** 30

## What's in it

| # | Scene | Duration |
|---|-------|----------|
| 01 | Title — "VoiceScribe · Design system" | 3 s |
| 02 | Color palette (7 swatches, staggered) | 3 s |
| 03 | Type scale (display → mono) | 3 s |
| 04 | App icon (spring scale-in, live waveform) | 2.5 s |
| 05 | The pill — recording state | 3 s |
| 06 | Pill state transitions (Recording → Transcribing → Polishing → No words) | 4.5 s |
| 07 | Buttons & controls (primary, icon, danger, stop) | 2.5 s |
| 08 | Toggle switch (off → on) | 2 s |
| 09 | Stat cards (numbers count up) | 2.5 s |
| 10 | Outro | 2 s |

Every scene lives over a persistent **dotted-grid background** that drifts subtly throughout. Transitions use cubic-bezier easing (`0.16, 1, 0.3, 1` for ease-out), and large headline elements get a CSS-blur-as-motion-blur treatment tied to their interpolation.

## Run it

```bash
cd case-study/video
npm install
npm run dev          # opens Remotion Studio at localhost:3000
```

## Render to MP4

```bash
npm run build        # writes out/voicescribe.mp4
```

## Render a still poster

```bash
npm run still        # writes out/poster.png at frame 60
```

## File map

```
src/
├── index.ts             ← registerRoot
├── Root.tsx             ← <Composition> registration
├── Video.tsx            ← top-level scene timeline
├── timing.ts            ← scene timestamps + easing curves
├── tokens.ts            ← color / font tokens (mirrors the actual app)
├── components/
│   ├── DotGrid.tsx      ← drifting dotted background
│   ├── Pill.tsx         ← reusable pill (recording + status modes)
│   └── MotionBlur.tsx   ← cheap velocity-based blur
└── scenes/
    ├── Title.tsx
    ├── Colors.tsx       (also exports the shared <Eyebrow>)
    ├── Type.tsx
    ├── Icon.tsx
    ├── PillScene.tsx
    ├── States.tsx       ← 4-state crossfade
    ├── Buttons.tsx
    ├── Toggle.tsx
    ├── Cards.tsx
    └── Outro.tsx
```
