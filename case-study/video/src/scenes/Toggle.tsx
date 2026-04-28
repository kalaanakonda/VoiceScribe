import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { EASE_IN_OUT } from "../timing";
import { Eyebrow } from "./Colors";

export const Toggle: React.FC = () => {
  const frame = useCurrentFrame();

  // Toggle animates: 0..15 off-state hold, 15..28 transition, 28..50 on-state hold
  const t = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_IN_OUT,
  });

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="07 — STATE" />
      <BigToggle progress={t} />
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 24,
          color: COLORS.text,
          marginTop: 64,
          fontWeight: 500,
        }}
      >
        AI Polish · {t > 0.5 ? "On" : "Off"}
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 16,
          color: COLORS.muted,
          marginTop: 12,
          opacity: interpolate(frame, [32, 50], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        Same green as the live status dot.
      </div>
    </AbsoluteFill>
  );
};

const BigToggle: React.FC<{ progress: number }> = ({ progress }) => {
  // Scale up 5x for hero presentation
  const SCALE = 5;
  const trackW = 36 * SCALE;
  const trackH = 20 * SCALE;
  const thumb = 14 * SCALE;
  const inset = 3 * SCALE;
  const trackBg = `rgb(${51 + (74 - 51) * progress}, ${51 + (222 - 51) * progress}, ${51 + (128 - 51) * progress})`;
  const thumbX = inset + progress * (trackW - thumb - inset * 2);

  return (
    <div
      style={{
        position: "relative",
        width: trackW,
        height: trackH,
        borderRadius: trackH / 2,
        background: trackBg,
        boxShadow: progress > 0.5 ? `0 0 ${24}px rgba(74,222,128,0.4)` : "none",
        transition: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: thumbX,
          top: inset,
          width: thumb,
          height: thumb,
          borderRadius: thumb / 2,
          background: "#f0f0f0",
          boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
        }}
      />
    </div>
  );
};
