import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { Eyebrow } from "./Colors";

export const Icon: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Scale-in spring for the icon
  const scale = spring({
    frame: frame - 8,
    fps,
    config: { damping: 12, stiffness: 110, mass: 0.8 },
  });

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
      <Eyebrow frame={frame} text="03 — APP ICON" />
      <div style={{ marginTop: 16, transform: `scale(${scale})` }}>
        <AppIcon frame={frame} />
      </div>
      <Caption frame={frame} />
    </AbsoluteFill>
  );
};

const AppIcon: React.FC<{ frame: number }> = ({ frame }) => {
  const SIZE = 360;
  const phase = frame * 0.18;

  return (
    <div
      style={{
        width: SIZE,
        height: SIZE,
        background: "#0a0a0a",
        borderRadius: 80,
        boxShadow: "0 24px 60px rgba(0,0,0,0.7), 0 0 0 1px #1a1a1a",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg width={SIZE * 0.66} height={SIZE * 0.4} viewBox="0 0 220 140">
        {Array.from({ length: 15 }).map((_, i) => {
          const t = i / 14;
          const x = 10 + t * 200;
          const cy = 70;
          const w1 = Math.sin(t * Math.PI * 3 + phase) * 0.7;
          const w2 = Math.sin(t * Math.PI * 2 - phase * 0.6) * 0.4;
          const wave = w1 + w2;
          const y = cy + wave * 50;
          const v = 0.55 + Math.abs(wave) * 0.45;
          const r = 4 + Math.abs(wave) * 6;
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={r}
              fill={`rgba(${(v * 255) | 0}, ${(v * 255) | 0}, ${(v * 255) | 0}, 1)`}
            />
          );
        })}
      </svg>
    </div>
  );
};

const Caption: React.FC<{ frame: number }> = ({ frame }) => {
  const opacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        fontFamily: FONT_SANS,
        fontSize: 16,
        color: COLORS.muted,
        marginTop: 36,
        opacity,
        letterSpacing: 0.2,
      }}
    >
      The dots are the audio.
    </div>
  );
};
