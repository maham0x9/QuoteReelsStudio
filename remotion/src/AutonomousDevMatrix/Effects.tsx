import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  loopSin,
} from "./utils";

// Subtle grain via SVG fractal noise. Re-seeded by frame for an organic
// shimmer; opacity is intentionally low (~6%).
export const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  // Cycle the seed so the noise looks animated but stays loopable.
  const seed = (frame % 8) + 1;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        opacity: 0.06,
        mixBlendMode: "overlay",
      }}
    >
      <svg width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <defs>
          <filter id={`grain-${seed}`}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.9"
              numOctaves="2"
              seed={seed}
              stitchTiles="stitch"
            />
            <feColorMatrix
              type="matrix"
              values="0 0 0 0 1
                      0 0 0 0 1
                      0 0 0 0 1
                      0 0 0 0.55 0"
            />
          </filter>
        </defs>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

// Cinematic vignette with a subtle warm-to-cool falloff.
export const Vignette: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background:
          "radial-gradient(ellipse at 50% 52%, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 85%, rgba(0,0,0,0.85) 100%)",
        mixBlendMode: "multiply",
      }}
    />
  );
};

// Faint scanlines for a high-tech monitor feel.
export const Scanlines: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        opacity: 0.08,
        background:
          "repeating-linear-gradient(180deg, rgba(255,255,255,0) 0 2px, rgba(255,255,255,0.05) 2px 3px)",
        mixBlendMode: "overlay",
      }}
    />
  );
};

// Chromatic aberration: re-render a slightly offset cyan/red tint over the
// frame. The actual color split is achieved by stacking two thin gradients;
// we keep it very subtle to avoid neon overload.
export const ChromaticAberration: React.FC<{ amount: number }> = ({ amount }) => {
  const offset = amount;
  return (
    <>
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          transform: `translate3d(${offset}px, 0, 0)`,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(255,40,40,0.04) 0%, rgba(255,40,40,0) 60%)",
          mixBlendMode: "screen",
          opacity: 0.6,
        }}
      />
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          transform: `translate3d(${-offset}px, 0, 0)`,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(40,200,255,0.05) 0%, rgba(40,200,255,0) 60%)",
          mixBlendMode: "screen",
          opacity: 0.6,
        }}
      />
    </>
  );
};

// Pulsing global bloom — a soft, broad veil that breathes with the scene.
export const Bloom: React.FC<{ intensity: number }> = ({ intensity }) => {
  const frame = useCurrentFrame();
  const breathe = 0.5 + 0.5 * loopSin(frame, 1);
  const opacity = 0.08 + 0.08 * intensity * breathe;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: `radial-gradient(ellipse at 50% 50%, ${PALETTE.cyan}22 0%, transparent 60%)`,
        opacity,
        mixBlendMode: "screen",
      }}
    />
  );
};

// 1-second fade-in and 1-second fade-out so the loop seam isn't a hard cut.
export const LoopSeamFade: React.FC = () => {
  const frame = useCurrentFrame();
  const fps = 30;
  const total = DURATION_FRAMES;
  const fadeFrames = fps; // 1 second
  let alpha = 0;
  if (frame < fadeFrames) {
    // fade in from black
    alpha = 1 - frame / fadeFrames;
  } else if (frame > total - fadeFrames) {
    // fade out to black (matches the start state for a clean wrap)
    alpha = (frame - (total - fadeFrames)) / fadeFrames;
  }
  if (alpha <= 0) return null;
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: "#000",
        opacity: alpha,
      }}
    />
  );
};
