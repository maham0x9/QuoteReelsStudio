import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  VIDEO_HEIGHT,
  VIDEO_WIDTH,
  loopSin,
  mulberry32,
  range,
} from "./utils";

type Particle = {
  baseX: number;
  baseY: number;
  z: number; // 0..1, controls parallax + size
  size: number;
  driftX: number;
  driftY: number;
  phase: number;
  color: string;
  twinkleCycles: number;
};

const PARTICLE_COUNT = 220;

const COLORS = [
  PALETTE.cyanBright,
  PALETTE.cyan,
  PALETTE.teal,
  PALETTE.violetSoft,
  PALETTE.highlight,
];

function buildParticles(seed: number): Particle[] {
  const rand = mulberry32(seed);
  return range(PARTICLE_COUNT).map(() => {
    const z = rand();
    return {
      baseX: rand() * VIDEO_WIDTH,
      baseY: rand() * VIDEO_HEIGHT,
      z,
      size: 1 + z * 4 + rand() * 1.5,
      driftX: (rand() - 0.5) * (40 + z * 80),
      driftY: (rand() - 0.5) * (24 + z * 60),
      phase: rand() * TAU,
      color: COLORS[Math.floor(rand() * COLORS.length)] ?? PALETTE.cyan,
      twinkleCycles: 1 + Math.floor(rand() * 3),
    };
  });
}

const particles = buildParticles(0xa1b2c3);

export const ParticleField: React.FC<{ parallaxX: number; parallaxY: number }> = ({
  parallaxX,
  parallaxY,
}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {particles.map((p, i) => {
        const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;
        const x = p.baseX + Math.sin(TAU * t + p.phase) * p.driftX + parallaxX * (0.2 + p.z * 0.8);
        const y =
          p.baseY +
          Math.cos(TAU * t + p.phase * 0.7) * p.driftY +
          parallaxY * (0.2 + p.z * 0.8);
        const twinkle = 0.4 + 0.6 * (0.5 + 0.5 * loopSin(frame, p.twinkleCycles, p.phase));
        const opacity = (0.15 + p.z * 0.55) * twinkle;
        const glow = 6 + p.z * 18;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - p.size / 2,
              top: y - p.size / 2,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: p.color,
              opacity,
              boxShadow: `0 0 ${glow}px ${p.color}, 0 0 ${glow * 2.2}px ${p.color}`,
              willChange: "transform, opacity",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
