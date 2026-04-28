import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { Pill } from "../components/Pill";
import { Eyebrow } from "./Colors";

export const PillScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - 6,
    fps,
    config: { damping: 14, stiffness: 95, mass: 0.6 },
  });

  // Pretend audio level — undulates so the waveform is alive
  const level = 0.55 + Math.sin(frame * 0.15) * 0.25 + Math.sin(frame * 0.07) * 0.2;

  const captionOpacity = interpolate(frame, [22, 44], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="04 — THE PILL" />
      <div style={{ transform: `scale(${scale * 3.5})` }}>
        <Pill mode="recording" level={Math.max(0.1, Math.min(1, level))} />
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 20,
          color: COLORS.muted,
          marginTop: 64,
          letterSpacing: 0.1,
          opacity: captionOpacity,
        }}
      >
        214 × 44 px · 22 dots · 30 fps
      </div>
    </AbsoluteFill>
  );
};
