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

type Blob = {
  cx: number;
  cy: number;
  r: number;
  color: string;
  driftX: number;
  driftY: number;
  phase: number;
  opacity: number;
};

const BLOBS: Blob[] = (() => {
  const rand = mulberry32(0xb10b);
  const palette = [
    PALETTE.cyanDeep,
    PALETTE.blueDeep,
    PALETTE.violet,
    PALETTE.teal,
    PALETTE.cyan,
  ];
  return range(8).map(() => ({
    cx: rand() * VIDEO_WIDTH,
    cy: rand() * VIDEO_HEIGHT,
    r: 280 + rand() * 360,
    color: palette[Math.floor(rand() * palette.length)] ?? PALETTE.cyan,
    driftX: (rand() - 0.5) * 240,
    driftY: (rand() - 0.5) * 180,
    phase: rand() * TAU,
    opacity: 0.06 + rand() * 0.09,
  }));
})();

export const VolumetricHaze: React.FC<{ parallaxX: number; parallaxY: number }> = ({
  parallaxX,
  parallaxY,
}) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: `radial-gradient(ellipse at 50% 55%, ${PALETTE.navyLight} 0%, ${PALETTE.navy} 35%, ${PALETTE.navyDeep} 70%, ${PALETTE.black} 100%)`,
        overflow: "hidden",
      }}
    >
      {BLOBS.map((b, i) => {
        const x = b.cx + Math.sin(TAU * t + b.phase) * b.driftX + parallaxX * 0.6;
        const y = b.cy + Math.cos(TAU * t + b.phase * 0.7) * b.driftY + parallaxY * 0.6;
        const breathe = 0.7 + 0.3 * (0.5 + 0.5 * loopSin(frame, 1, b.phase));
        // Multi-stop radial gradient gives the soft volumetric falloff
        // directly — no CSS filter:blur() needed. A 40px blur at this size
        // costs ~10ms per blob per frame on Chrome's compositor; replacing
        // 8 blurs with cheap gradients buys us ~80ms / frame.
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - b.r * 1.4,
              top: y - b.r * 1.4,
              width: b.r * 2.8,
              height: b.r * 2.8,
              borderRadius: "50%",
              background:
                `radial-gradient(circle, ${b.color} 0%, ${b.color} 8%, ` +
                `rgba(0,0,0,0) 55%, rgba(0,0,0,0) 100%)`,
              opacity: b.opacity * breathe,
              mixBlendMode: "screen",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
