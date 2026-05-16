import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  loopSin,
  mulberry32,
  range,
} from "./utils";

type Stack = {
  x: number;
  y: number;
  width: number;
  height: number;
  bars: number;
  z: number;
  phase: number;
  color: string;
  speed: number;
};

const STACKS: Stack[] = [
  {
    x: 540,
    y: 880,
    width: 380,
    height: 110,
    bars: 24,
    z: 0.45,
    phase: 0,
    color: PALETTE.cyan,
    speed: 1.0,
  },
  {
    x: 960,
    y: 60,
    width: 320,
    height: 90,
    bars: 20,
    z: 0.7,
    phase: 1.6,
    color: PALETTE.violetSoft,
    speed: 0.8,
  },
  {
    x: 1020,
    y: 920,
    width: 300,
    height: 100,
    bars: 22,
    z: 0.5,
    phase: 2.4,
    color: PALETTE.teal,
    speed: 1.2,
  },
];

const StackView: React.FC<{
  stack: Stack;
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ stack, parallaxX, parallaxY, intensity }) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;
  const rand = mulberry32(0xdeb01 + Math.floor(stack.x));
  // Stable per-bar phase offsets.
  const phases = range(stack.bars).map(() => rand() * TAU);

  const px = stack.x + parallaxX * (0.4 + stack.z * 0.5);
  const py = stack.y + parallaxY * (0.4 + stack.z * 0.5);
  const barGap = 2;
  const barWidth = (stack.width - barGap * (stack.bars - 1)) / stack.bars;
  const groupOpacity = 0.55 + 0.35 * intensity;
  const breathe = 0.5 + 0.5 * loopSin(frame, 1, stack.phase);

  return (
    <div
      style={{
        position: "absolute",
        left: px,
        top: py,
        width: stack.width,
        height: stack.height,
        display: "flex",
        alignItems: "flex-end",
        gap: barGap,
        opacity: groupOpacity,
      }}
    >
      {range(stack.bars).map((i) => {
        const wave =
          0.4 + 0.6 * (0.5 + 0.5 * Math.sin(TAU * (t * stack.speed) + phases[i]! + i * 0.35));
        const h = stack.height * (0.18 + wave * 0.82);
        const isHot = wave > 0.78;
        return (
          <div
            key={i}
            style={{
              flex: `0 0 ${barWidth}px`,
              height: h,
              borderRadius: 1,
              background: isHot ? PALETTE.white : stack.color,
              opacity: 0.55 + wave * 0.4,
              boxShadow: `0 0 ${4 + wave * 10}px ${stack.color}, 0 0 ${
                isHot ? 18 : 8
              }px ${stack.color}`,
            }}
          />
        );
      })}
      {/* Underline */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: -6,
          height: 1,
          background: `linear-gradient(90deg, transparent, ${stack.color}, transparent)`,
          opacity: 0.4 * (0.6 + 0.4 * breathe),
        }}
      />
    </div>
  );
};

export const DeploymentGraphs: React.FC<{
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ parallaxX, parallaxY, intensity }) => {
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {STACKS.map((s, i) => (
        <StackView
          key={i}
          stack={s}
          parallaxX={parallaxX}
          parallaxY={parallaxY}
          intensity={intensity}
        />
      ))}
    </AbsoluteFill>
  );
};
