// Helpers for the AutonomousDevMatrix composition.
// All motion is expressed as functions of (frame / DURATION_FRAMES) so the
// 20-second clip loops seamlessly back to frame 0.

export const TAU = Math.PI * 2;

export const DURATION_SECONDS = 20;
export const VIDEO_FPS = 30;
export const DURATION_FRAMES = DURATION_SECONDS * VIDEO_FPS; // 600
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;

// Brand-safe color palette.
export const PALETTE = {
  black: "#000000",
  navyDeep: "#050912",
  navy: "#0a1024",
  navyLight: "#0f1a35",
  cyan: "#22d3ee",
  cyanBright: "#67e8f9",
  cyanDeep: "#0891b2",
  teal: "#2dd4bf",
  blue: "#3b82f6",
  blueDeep: "#1d4ed8",
  violet: "#8b5cf6",
  violetSoft: "#a78bfa",
  white: "#f8fafc",
  highlight: "#e0f2fe",
};

// Phase in [0, TAU) for a given frame within the loop.
export const loopPhase = (frame: number, duration = DURATION_FRAMES): number =>
  ((frame % duration) / duration) * TAU;

// Loop-safe sine wave, amplitude 1.
export const loopSin = (
  frame: number,
  cycles = 1,
  phase = 0,
  duration = DURATION_FRAMES,
): number => Math.sin(loopPhase(frame, duration) * cycles + phase);

export const loopCos = (
  frame: number,
  cycles = 1,
  phase = 0,
  duration = DURATION_FRAMES,
): number => Math.cos(loopPhase(frame, duration) * cycles + phase);

// Smooth 0→1→0 envelope across the loop with a wide plateau, useful for fades
// that breathe but always end where they started.
export const loopEnvelope = (
  frame: number,
  cycles = 1,
  phase = 0,
  duration = DURATION_FRAMES,
): number => 0.5 + 0.5 * Math.cos(loopPhase(frame, duration) * cycles + phase);

// Deterministic PRNG so element placements are stable between renders.
export function mulberry32(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Range helper.
export const range = (n: number): number[] => Array.from({ length: n }, (_, i) => i);

// Linear interpolation that clamps to [a, b].
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export const clamp = (v: number, lo: number, hi: number): number =>
  v < lo ? lo : v > hi ? hi : v;

// Cubic-bezier point sample.
export function bezier(
  t: number,
  p0: [number, number],
  p1: [number, number],
  p2: [number, number],
  p3: [number, number],
): [number, number] {
  const u = 1 - t;
  const tt = t * t;
  const uu = u * u;
  const uuu = uu * u;
  const ttt = tt * t;
  const x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0];
  const y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1];
  return [x, y];
}

// Build an SVG cubic-bezier "d" string.
export function bezierPath(
  p0: [number, number],
  p1: [number, number],
  p2: [number, number],
  p3: [number, number],
): string {
  return `M ${p0[0]} ${p0[1]} C ${p1[0]} ${p1[1]}, ${p2[0]} ${p2[1]}, ${p3[0]} ${p3[1]}`;
}
