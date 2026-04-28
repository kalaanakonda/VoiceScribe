import React from "react";
import { useCurrentFrame } from "remotion";
import { COLORS, FONT_SANS } from "../tokens";

const WIDTH = 214;
const HEIGHT = 44;
const DOT_COUNT = 22;
const STOP_BTN_W = 34;

interface PillProps {
  /** "recording" plays the live waveform; otherwise text mode. */
  mode: "recording" | "transcribing" | "polishing" | "no-words" | "idle";
  /** 0..1 — pretend "audio level" used to drive amplitude when recording. */
  level?: number;
  scale?: number;
}

export const Pill: React.FC<PillProps> = ({ mode, level = 0.7, scale = 1 }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: WIDTH * scale,
        height: HEIGHT * scale,
        background: "rgba(20,20,20,0.94)",
        border: "1px solid #333",
        borderRadius: HEIGHT / 2 * scale,
        boxShadow: "0 -3px 14px rgba(0,0,0,0.55), 0 8px 24px rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        position: "relative",
        overflow: "hidden",
        transform: `scale(${scale})`,
        transformOrigin: "center",
      }}
    >
      {mode === "recording" ? (
        <Waveform frame={frame} level={level} />
      ) : (
        <StatusText frame={frame} mode={mode} />
      )}

      {mode === "recording" && <StopButton />}
    </div>
  );
};

const Waveform: React.FC<{ frame: number; level: number }> = ({ frame, level }) => {
  const phase = frame * 0.18;
  const margin = 14;
  const dotsRight = WIDTH - STOP_BTN_W;
  const totalW = dotsRight - margin;
  const cy = HEIGHT / 2;
  const maxAmp = HEIGHT / 2 - 6;

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      style={{ position: "absolute", inset: 0 }}
    >
      {Array.from({ length: DOT_COUNT }).map((_, i) => {
        const t = i / (DOT_COUNT - 1);
        const x = margin + t * totalW;
        const w1 = Math.sin(t * Math.PI * 3.0 + phase) * level;
        const w2 = Math.sin(t * Math.PI * 2.0 - phase * 0.6) * level * 0.6;
        const w3 = Math.sin(t * Math.PI * 4.5 + phase * 1.3) * level * 0.25;
        const wave = w1 + w2 + w3;
        const y = cy + wave * maxAmp;
        const v = Math.max(0, Math.min(1, 0.55 + Math.abs(wave) * 0.45));
        const r = 1.6 + Math.abs(wave) * 1.8;
        const fill = `rgb(${v * 255 | 0}, ${v * 255 | 0}, ${v * 255 | 0})`;
        return <circle key={i} cx={x} cy={y} r={r} fill={fill} />;
      })}
    </svg>
  );
};

const StopButton: React.FC = () => (
  <div
    style={{
      position: "absolute",
      right: 4,
      top: HEIGHT / 2 - 11,
      width: 22,
      height: 22,
      borderRadius: 11,
      background: COLORS.pillRed,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div style={{ width: 7, height: 7, background: "#fff" }} />
  </div>
);

const StatusText: React.FC<{ frame: number; mode: string }> = ({ frame, mode }) => {
  // Animate trailing dots: ".", "..", "..." cycling every ~12 frames
  const animated = mode === "transcribing" || mode === "polishing";
  const dotCount = animated ? Math.floor(frame / 6) % 4 : 0;
  const labelMap: Record<string, string> = {
    transcribing: "Transcribing",
    polishing: "Polishing",
    "no-words": "No words detected",
    idle: "Ready",
  };
  const label = labelMap[mode] ?? "";
  const display = animated ? label + ".".repeat(dotCount) : label;
  return (
    <div
      style={{
        flex: 1,
        textAlign: "center",
        color: "rgba(240,240,240,0.92)",
        fontSize: 14,
        fontFamily: FONT_SANS,
        letterSpacing: 0.1,
      }}
    >
      {display}
    </div>
  );
};
