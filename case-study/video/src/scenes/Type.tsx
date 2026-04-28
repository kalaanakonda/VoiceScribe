import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS, FONT_SERIF, FONT_MONO } from "../tokens";
import { EASE_OUT } from "../timing";
import { Eyebrow } from "./Colors";

const SAMPLES: Array<{ size: number; weight: number; family: string; text: string; mono?: boolean }> = [
  { size: 96, weight: 600, family: FONT_SANS, text: "Display" },
  { size: 56, weight: 600, family: FONT_SANS, text: "Section title" },
  { size: 32, weight: 500, family: FONT_SANS, text: "Body 13 → 32" },
  { size: 44, weight: 400, family: FONT_SERIF, text: "Speaks your code's language." },
  { size: 22, weight: 400, family: FONT_MONO, text: "useState · app.py · git push" },
];

export const Type: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="02 — TYPE" />
      <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "flex-start" }}>
        {SAMPLES.map((s, i) => {
          const start = 14 + i * 8;
          const opacity = interpolate(frame, [start, start + 22], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const x = interpolate(frame, [start, start + 22], [-60, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: EASE_OUT,
          });
          const blur = interpolate(frame, [start, start + 22], [10, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                fontFamily: s.family,
                fontSize: s.size,
                fontWeight: s.weight,
                color: COLORS.text,
                letterSpacing: s.size > 60 ? -2 : -0.4,
                lineHeight: 1.05,
                opacity,
                transform: `translateX(${x}px)`,
                filter: `blur(${blur}px)`,
              }}
            >
              {s.text}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
