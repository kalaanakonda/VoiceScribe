import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { EASE_OUT } from "../timing";

export const Title: React.FC = () => {
  const frame = useCurrentFrame();

  // Heading slides up from below with motion blur
  const headY = interpolate(frame, [0, 30], [60, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const headOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateRight: "clamp",
  });
  const headBlur = interpolate(frame, [0, 22], [12, 0], {
    extrapolateRight: "clamp",
  });

  // Subtitle, then tag pills, each staggered
  const subY = interpolate(frame, [12, 36], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const subOpacity = interpolate(frame, [12, 32], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 132,
          fontWeight: 700,
          color: COLORS.text,
          letterSpacing: -3,
          opacity: headOpacity,
          transform: `translateY(${headY}px)`,
          filter: `blur(${headBlur}px)`,
          lineHeight: 0.95,
        }}
      >
        VoiceScribe
      </div>
      <div
        style={{
          fontFamily: FONT_SANS,
          fontSize: 28,
          color: COLORS.muted,
          marginTop: 16,
          letterSpacing: 0.2,
          opacity: subOpacity,
          transform: `translateY(${subY}px)`,
        }}
      >
        Design system
      </div>
      <Tags frame={frame} />
    </AbsoluteFill>
  );
};

const Tags: React.FC<{ frame: number }> = ({ frame }) => {
  const tags = ["COMPONENTS", "SCREENS", "MOTION"];
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        marginTop: 40,
      }}
    >
      {tags.map((t, i) => {
        const start = 30 + i * 6;
        const opacity = interpolate(frame, [start, start + 18], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const y = interpolate(frame, [start, start + 18], [16, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: EASE_OUT,
        });
        return (
          <div
            key={t}
            style={{
              fontFamily: FONT_SANS,
              fontSize: 12,
              color: COLORS.muted,
              border: `1px solid ${COLORS.border}`,
              padding: "5px 12px",
              borderRadius: 100,
              letterSpacing: 2,
              opacity,
              transform: `translateY(${y}px)`,
            }}
          >
            {t}
          </div>
        );
      })}
    </div>
  );
};
