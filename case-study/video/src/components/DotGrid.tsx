import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS } from "../tokens";

/**
 * Subtly-drifting dotted grid background.  Two layers of dots at different
 * scales drift in opposite directions, giving a quiet sense of depth without
 * pulling attention.
 */
export const DotGrid: React.FC<{ intensity?: number }> = ({ intensity = 1 }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // 1px-per-frame drift, looped
  const dx1 = (frame * 0.4) % 40;
  const dx2 = -(frame * 0.25) % 60;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: COLORS.bg,
        overflow: "hidden",
        // Establish a stacking context so the inner vignette only darkens
        // the dot pattern itself — never the scene content above it.
        zIndex: 0,
      }}
    >
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0, opacity: intensity }}
      >
        <defs>
          <pattern
            id="dots-fine"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${dx1}, ${dx1 * 0.5})`}
          >
            <circle cx="20" cy="20" r="1.0" fill="rgba(255,255,255,0.06)" />
          </pattern>
          <pattern
            id="dots-coarse"
            width="60"
            height="60"
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${dx2}, ${dx2 * -0.3})`}
          >
            <circle cx="30" cy="30" r="1.6" fill="rgba(255,255,255,0.04)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dots-fine)" />
        <rect width="100%" height="100%" fill="url(#dots-coarse)" />
      </svg>
      {/* Subtle radial darkening — drawn last so it only dims the dots
          (it lives inside the stacking context above) and never the foreground. */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at center, transparent 35%, rgba(0,0,0,0.7) 100%)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
