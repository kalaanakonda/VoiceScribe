import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { EASE_OUT } from "../timing";
import { Eyebrow } from "./Colors";

export const Buttons: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
      <Eyebrow frame={frame} text="06 — CONTROLS" />
      <div style={{ display: "flex", gap: 48, alignItems: "center", marginTop: 24 }}>
        <Stagger frame={frame} delay={10}>
          <PrimaryBtn label="Add word" />
        </Stagger>
        <Stagger frame={frame} delay={18}>
          <IconBtn label="Copy" />
        </Stagger>
        <Stagger frame={frame} delay={26}>
          <IconBtn label="Delete" danger />
        </Stagger>
        <Stagger frame={frame} delay={34}>
          <StopBtn />
        </Stagger>
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 16,
          color: COLORS.muted,
          marginTop: 56,
          letterSpacing: 0.1,
          opacity: interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        Primary · Icon · Danger · Stop
      </div>
    </AbsoluteFill>
  );
};

const Stagger: React.FC<{ frame: number; delay: number; children: React.ReactNode }> = ({
  frame,
  delay,
  children,
}) => {
  const opacity = interpolate(frame, [delay, delay + 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [delay, delay + 22], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const blur = interpolate(frame, [delay, delay + 22], [8, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{ opacity, transform: `translateY(${y}px) scale(2)`, filter: `blur(${blur}px)` }}>
      {children}
    </div>
  );
};

const PrimaryBtn: React.FC<{ label: string }> = ({ label }) => (
  <button
    style={{
      background: "#eeeeee",
      color: "#0d0d0d",
      border: "none",
      borderRadius: 8,
      padding: "8px 14px",
      font: `600 13px ${FONT_SANS}`,
    }}
  >
    {label}
  </button>
);

const IconBtn: React.FC<{ label: string; danger?: boolean }> = ({ label, danger }) => (
  <button
    style={{
      background: "transparent",
      color: danger ? "#ff8080" : COLORS.muted,
      border: "none",
      padding: "4px 8px",
      font: `400 12px ${FONT_SANS}`,
    }}
  >
    {label}
  </button>
);

const StopBtn: React.FC = () => (
  <div
    style={{
      width: 26,
      height: 26,
      borderRadius: 13,
      background: COLORS.pillRed,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div style={{ width: 9, height: 9, background: "#fff" }} />
  </div>
);
