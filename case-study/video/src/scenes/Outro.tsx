import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS, FONT_MONO } from "../tokens";
import { EASE_OUT } from "../timing";

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();

  const headOpacity = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const headY = interpolate(frame, [0, 30], [40, 0], { extrapolateRight: "clamp", easing: EASE_OUT });
  const linkOpacity = interpolate(frame, [16, 36], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [44, 60], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 96,
          fontWeight: 600,
          color: COLORS.text,
          letterSpacing: -2,
          opacity: headOpacity,
          transform: `translateY(${headY}px)`,
          lineHeight: 0.95,
        }}
      >
        VoiceScribe
      </div>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 18,
          color: COLORS.muted,
          marginTop: 24,
          letterSpacing: 0.4,
          opacity: linkOpacity,
        }}
      >
        github.com/kalaanakonda/VoiceScribe
      </div>
    </AbsoluteFill>
  );
};
