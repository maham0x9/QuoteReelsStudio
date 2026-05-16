import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  VIDEO_HEIGHT,
  VIDEO_WIDTH,
  bezier,
  bezierPath,
  loopSin,
  mulberry32,
  range,
} from "./utils";

type Pipe = {
  p0: [number, number];
  p1: [number, number];
  p2: [number, number];
  p3: [number, number];
  color: string;
  width: number;
  speed: number;
  pulseCount: number;
  phase: number;
  dashOffset: number;
};

const PIPE_COLORS = [PALETTE.cyan, PALETTE.teal, PALETTE.blue, PALETTE.violetSoft];

function buildPipes(seed: number, count: number): Pipe[] {
  const rand = mulberry32(seed);
  return range(count).map(() => {
    const startSide = rand() > 0.5 ? "left" : "right";
    const p0: [number, number] =
      startSide === "left"
        ? [-40, VIDEO_HEIGHT * (0.15 + rand() * 0.7)]
        : [VIDEO_WIDTH + 40, VIDEO_HEIGHT * (0.15 + rand() * 0.7)];
    const p3: [number, number] =
      startSide === "left"
        ? [VIDEO_WIDTH + 40, VIDEO_HEIGHT * (0.15 + rand() * 0.7)]
        : [-40, VIDEO_HEIGHT * (0.15 + rand() * 0.7)];

    // Two control points pulled toward the center with random vertical bias.
    const midY = (p0[1] + p3[1]) / 2;
    const p1: [number, number] = [
      VIDEO_WIDTH * 0.32,
      midY + (rand() - 0.5) * 360,
    ];
    const p2: [number, number] = [
      VIDEO_WIDTH * 0.68,
      midY + (rand() - 0.5) * 360,
    ];

    return {
      p0,
      p1,
      p2,
      p3,
      color: PIPE_COLORS[Math.floor(rand() * PIPE_COLORS.length)] ?? PALETTE.cyan,
      width: 0.8 + rand() * 1.4,
      speed: 0.6 + rand() * 1.4,
      pulseCount: 2 + Math.floor(rand() * 3),
      phase: rand(),
      dashOffset: rand() * 60,
    };
  });
}

const pipes = buildPipes(0x5a17ed, 8);

const PipeView: React.FC<{ pipe: Pipe; intensity: number }> = ({ pipe, intensity }) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;
  const d = bezierPath(pipe.p0, pipe.p1, pipe.p2, pipe.p3);
  const opacity = 0.18 + 0.22 * intensity;
  // Animated dash gives the impression of data flow.
  const dashAnim = (-t * pipe.speed * 220 + pipe.dashOffset) % 60;

  return (
    <g>
      {/* Halo */}
      <path
        d={d}
        fill="none"
        stroke={pipe.color}
        strokeOpacity={opacity * 0.45}
        strokeWidth={pipe.width * 5}
        style={{
          filter: `blur(6px)`,
        }}
      />
      {/* Core line */}
      <path
        d={d}
        fill="none"
        stroke={pipe.color}
        strokeOpacity={opacity + 0.25 * intensity}
        strokeWidth={pipe.width}
        strokeDasharray="10 6 2 6"
        strokeDashoffset={dashAnim}
      />
      {/* Traveling pulses */}
      {range(pipe.pulseCount).map((k) => {
        const u = (t * pipe.speed + pipe.phase + k / pipe.pulseCount) % 1;
        const [x, y] = bezier(u, pipe.p0, pipe.p1, pipe.p2, pipe.p3);
        return (
          <g key={k}>
            <circle
              cx={x}
              cy={y}
              r={3}
              fill="white"
              opacity={0.85}
              style={{
                filter: `drop-shadow(0 0 6px ${pipe.color}) drop-shadow(0 0 14px ${pipe.color})`,
              }}
            />
          </g>
        );
      })}
    </g>
  );
};

export const Workflows: React.FC<{
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ parallaxX, parallaxY, intensity }) => {
  const frame = useCurrentFrame();
  // Light vertical wobble to make pipes feel suspended.
  const wobble = loopSin(frame, 1) * 4;
  void TAU;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        transform: `translate3d(${parallaxX * 0.5}px, ${parallaxY * 0.5 + wobble}px, 0)`,
      }}
    >
      <svg
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
        viewBox={`0 0 ${VIDEO_WIDTH} ${VIDEO_HEIGHT}`}
      >
        {pipes.map((p, i) => (
          <PipeView key={i} pipe={p} intensity={intensity} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
