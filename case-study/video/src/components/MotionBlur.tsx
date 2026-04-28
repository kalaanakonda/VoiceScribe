import React, { CSSProperties } from "react";

/**
 * Cheap motion-blur effect: stacks the same content twice with a CSS
 * `blur(...)` filter scaled by the current velocity (passed in by the
 * parent — typically computed from interpolation deltas).
 */
export const MotionBlur: React.FC<{
  velocity: number;
  children: React.ReactNode;
  axis?: "x" | "y" | "both";
  style?: CSSProperties;
}> = ({ velocity, children, axis = "x", style }) => {
  const amount = Math.min(Math.abs(velocity) * 0.35, 12);
  const filter =
    axis === "x"
      ? `blur(${amount}px) blur(0)`
      : axis === "y"
      ? `blur(${amount}px)`
      : `blur(${amount}px)`;
  return (
    <div style={{ filter, ...style }}>{children}</div>
  );
};
