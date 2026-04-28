import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS, FONT_MONO } from "../tokens";
import { EASE_OUT } from "../timing";

const SWATCHES: Array<{ name: string; hex: string }> = [
  { name: "Background", hex: "#0A0A0A" },
  { name: "Card", hex: "#161616" },
  { name: "Border", hex: "#262626" },
  { name: "Text", hex: "#F0F0F0" },
  { name: "Muted", hex: "#7A7A7A" },
  { name: "Stop", hex: "#EB4338" },
  { name: "Live", hex: "#4ADE80" },
];

export const Colors: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="01 — COLOR" />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${SWATCHES.length}, 168px)`,
          gap: 18,
          marginTop: 24,
        }}
      >
        {SWATCHES.map((s, i) => {
          const start = 14 + i * 4;
          const opacity = interpolate(frame, [start, start + 18], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const y = interpolate(frame, [start, start + 22], [40, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: EASE_OUT,
          });
          const blur = interpolate(frame, [start, start + 18], [8, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={s.hex}
              style={{
                background: COLORS.card,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 14,
                padding: 14,
                opacity,
                transform: `translateY(${y}px)`,
                filter: `blur(${blur}px)`,
              }}
            >
              <div
                style={{
                  width: "100%",
                  height: 100,
                  background: s.hex,
                  borderRadius: 8,
                  border: "1px solid rgba(255,255,255,0.04)",
                }}
              />
              <div
                style={{
                  fontFamily: FONT_SANS,
                  color: COLORS.text,
                  fontSize: 14,
                  marginTop: 12,
                  fontWeight: 500,
                }}
              >
                {s.name}
              </div>
              <div
                style={{
                  fontFamily: FONT_MONO,
                  color: COLORS.muted,
                  fontSize: 12,
                  marginTop: 2,
                }}
              >
                {s.hex}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Eyebrow: React.FC<{ frame: number; text: string; topMargin?: number }> = ({
  frame,
  text,
  topMargin = 0,
}) => {
  const opacity = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const y = interpolate(frame, [0, 22], [16, 0], {
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  return (
    <div
      style={{
        fontFamily: FONT_SANS,
        fontSize: 13,
        color: COLORS.muted,
        letterSpacing: 4,
        textTransform: "uppercase",
        marginBottom: 12,
        marginTop: topMargin,
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      {text}
    </div>
  );
};
