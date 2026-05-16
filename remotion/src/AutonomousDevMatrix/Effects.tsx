import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  loopSin,
} from "./utils";

// Subtle grain via SVG fractal noise. Earlier versions re-seeded the
// turbulence every frame to make the grain shimmer, but feTurbulence is
// the single most expensive operation in this composition — re-seeding
// forces Chrome to re-rasterise a 1920x1080 noise field on every frame.
// Instead we now keep the filter completely static (Chrome caches the
// rasterised result across frames) and animate two cheap properties on
// the host layer:
//   1. a sub-pixel translate that pans the cached noise pattern, giving
//      the scene the impression of moving grain without paying the cost
//      of recomputing it;
//   2. a tiny opacity oscillation so the texture feels alive.
// Visually indistinguishable from the previous shimmer at 6% opacity over
// a dark moving scene.
export const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;
  // Loop-safe sub-pixel pan. Amplitude is intentionally tiny — the pattern
  // is a fractal noise so any drift produces a perceptible shimmer.
  const dx = Math.sin(TAU * t * 1.7) * 2;
  const dy = Math.cos(TAU * t * 1.3) * 2;
  // Loop-safe opacity oscillation around 6%, ±0.5pp.
  const op = 0.06 + 0.005 * (0.5 + 0.5 * loopSin(frame, 2, 0.4));
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        opacity: op,
        mixBlendMode: "overlay",
        transform: `translate3d(${dx}px, ${dy}px, 0)`,
      }}
    >
      <svg width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <defs>
          <filter id="grain-static">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.9"
              numOctaves="2"
              seed="1"
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
        <rect width="100%" height="100%" filter="url(#grain-static)" />
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
