import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";
import { Pill } from "../components/Pill";
import { Eyebrow } from "./Colors";
import { EASE_IN_OUT } from "../timing";

// Show 4 pill states cycling.  Each holds for ~30f, with crossfades.
const SEGMENTS = [
  { mode: "recording" as const, label: "Recording" },
  { mode: "transcribing" as const, label: "Transcribing" },
  { mode: "polishing" as const, label: "Polishing" },
  { mode: "no-words" as const, label: "No words detected" },
];

const SEGMENT_FRAMES = 32;
const CROSSFADE = 6;

export const States: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Eyebrow frame={frame} text="05 — FOUR STATES" />
      <div
        style={{
          position: "relative",
          width: 750,
          height: 160,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {SEGMENTS.map((seg, i) => {
          const segStart = i * SEGMENT_FRAMES;
          const segEnd = segStart + SEGMENT_FRAMES;
          const opacity = interpolate(
            frame,
            [
              segStart - CROSSFADE,
              segStart + CROSSFADE,
              segEnd - CROSSFADE,
              segEnd + CROSSFADE,
            ],
            [0, 1, 1, 0],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_IN_OUT,
            }
          );
          const x = interpolate(
            frame,
            [segStart - CROSSFADE, segStart + CROSSFADE],
            [40, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_IN_OUT }
          );
          const blur = interpolate(
            frame,
            [segStart - CROSSFADE, segStart + CROSSFADE],
            [12, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          return (
            <div
              key={seg.label}
              style={{
                position: "absolute",
                opacity,
                transform: `translateX(${x}px) scale(3.2)`,
                filter: `blur(${blur}px)`,
              }}
            >
              <Pill mode={seg.mode} level={0.7} />
            </div>
          );
        })}
      </div>
      <Labels frame={frame} />
    </AbsoluteFill>
  );
};

const Labels: React.FC<{ frame: number }> = ({ frame }) => {
  return (
    <div
      style={{
        marginTop: 80,
        position: "relative",
        width: 600,
        height: 40,
      }}
    >
      {SEGMENTS.map((seg, i) => {
        const segStart = i * SEGMENT_FRAMES;
        const segEnd = segStart + SEGMENT_FRAMES;
        const opacity = interpolate(
          frame,
          [segStart - CROSSFADE, segStart + CROSSFADE, segEnd - CROSSFADE, segEnd + CROSSFADE],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        return (
          <div
            key={seg.label}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 0,
              textAlign: "center",
              fontFamily: FONT_SANS,
              fontSize: 22,
              color: COLORS.text,
              fontWeight: 500,
              letterSpacing: 0.2,
              opacity,
            }}
          >
            {seg.label}
          </div>
        );
      })}
    </div>
  );
};
