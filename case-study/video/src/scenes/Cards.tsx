import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { EASE_OUT } from "../timing";
import { Eyebrow } from "./Colors";

export const Cards: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="08 — CARDS" />
      <div style={{ display: "flex", gap: 18, marginTop: 24, transform: "scale(2.0)" }}>
        <Stat frame={frame} delay={6} num={countUp(frame, 6, 10212)} label="Words" />
        <Stat frame={frame} delay={12} num={countUp(frame, 12, 315).toString()} label="Sessions" />
        <Stat frame={frame} delay={18} num={`${countUp(frame, 18, 95)}m`} label="Recorded" />
        <Stat frame={frame} delay={24} num={(countUp(frame, 24, 1071) / 10).toFixed(1)} label="Avg WPM" />
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 16,
          color: COLORS.muted,
          marginTop: 100,
          opacity: interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        Stat · History · Dictionary · Snippet — same chassis, different content.
      </div>
    </AbsoluteFill>
  );
};

const Stat: React.FC<{
  frame: number;
  delay: number;
  num: string | number;
  label: string;
}> = ({ frame, delay, num, label }) => {
  const opacity = interpolate(frame, [delay, delay + 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [delay, delay + 22], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  return (
    <div
      style={{
        background: COLORS.card,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 10,
        padding: "14px 16px",
        minWidth: 120,
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 26,
          fontWeight: 600,
          color: COLORS.text,
          letterSpacing: -1,
          lineHeight: 1.05,
        }}
      >
        {typeof num === "number" ? num.toLocaleString() : num}
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 10,
          color: COLORS.muted,
          letterSpacing: 1,
          textTransform: "uppercase",
          marginTop: 4,
        }}
      >
        {label}
      </div>
    </div>
  );
};

function countUp(frame: number, delay: number, target: number): number {
  const t = interpolate(frame, [delay, delay + 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // ease-out
  const eased = 1 - Math.pow(1 - t, 3);
  return Math.round(target * eased);
}
