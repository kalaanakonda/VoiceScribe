// Scene timing — each entry is [fromFrame, durationFrames]
// 30 fps, total ~28 seconds (840 frames)
export const SCENES = {
  title:    { from: 0,    duration: 90  },  // 0–3s   intro
  colors:   { from: 90,   duration: 90  },  // 3–6s
  type:     { from: 180,  duration: 90  },  // 6–9s
  icon:     { from: 270,  duration: 75  },  // 9–11.5s
  pill:     { from: 345,  duration: 90  },  // 11.5–14.5s
  states:   { from: 435,  duration: 135 },  // 14.5–19s
  buttons:  { from: 570,  duration: 75  },  // 19–21.5s
  toggle:   { from: 645,  duration: 60  },  // 21.5–23.5s
  cards:    { from: 705,  duration: 75  },  // 23.5–26s
  outro:    { from: 780,  duration: 60  },  // 26–28s
} as const;

export const TOTAL_FRAMES = 840; // 28 seconds at 30 fps
export const FPS = 30;

// Cubic bezier easing curves — apply via interpolate( ..., { easing: ... })
import { Easing } from "remotion";

export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);   // smooth-out
export const EASE_IN = Easing.bezier(0.7, 0, 0.84, 0);     // smooth-in
export const EASE_IN_OUT = Easing.bezier(0.65, 0, 0.35, 1);
export const SPRING = Easing.bezier(0.34, 1.56, 0.64, 1); // overshoot
