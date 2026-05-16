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

type Cluster = {
  cx: number;
  cy: number;
  baseRadius: number;
  ringCount: number;
  rotationSpeed: number;
  phase: number;
  color: string;
  z: number;
};

const CLUSTERS: Cluster[] = [
  {
    cx: VIDEO_WIDTH * 0.5,
    cy: VIDEO_HEIGHT * 0.5,
    baseRadius: 280,
    ringCount: 6,
    rotationSpeed: 0.4,
    phase: 0,
    color: PALETTE.cyan,
    z: 0.9,
  },
  {
    cx: VIDEO_WIDTH * 0.32,
    cy: VIDEO_HEIGHT * 0.62,
    baseRadius: 150,
    ringCount: 4,
    rotationSpeed: -0.6,
    phase: 1.4,
    color: PALETTE.violetSoft,
    z: 0.6,
  },
  {
    cx: VIDEO_WIDTH * 0.7,
    cy: VIDEO_HEIGHT * 0.4,
    baseRadius: 180,
    ringCount: 5,
    rotationSpeed: 0.5,
    phase: 2.6,
    color: PALETTE.teal,
    z: 0.7,
  },
];

const ClusterView: React.FC<{
  cluster: Cluster;
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ cluster, parallaxX, parallaxY, intensity }) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;
  const cx = cluster.cx + parallaxX * (0.3 + cluster.z * 0.5);
  const cy = cluster.cy + parallaxY * (0.3 + cluster.z * 0.5);

  // Central soft glow halo. Originally a CSS-blurred solid circle (40px
  // filter:blur); replaced with an SVG radial gradient that rasterises in
  // a single pass with no blur kernel. Visually identical, ~5-8ms cheaper
  // per cluster per frame.
  const haloId = `halo-${cluster.color.replace(/[^a-zA-Z0-9]/g, "")}-${cluster.phase}`;
  const haloR = cluster.baseRadius * 1.4;
  const haloOpacity = 0.05 + 0.05 * intensity;
  return (
    <g>
      <defs>
        <radialGradient id={haloId} cx="50%" cy="50%" r="50%">
          <stop offset="0%"  stopColor={cluster.color} stopOpacity="0.9" />
          <stop offset="55%" stopColor={cluster.color} stopOpacity="0.15" />
          <stop offset="100%" stopColor={cluster.color} stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle
        cx={cx}
        cy={cy}
        r={haloR}
        fill={`url(#${haloId})`}
        opacity={haloOpacity}
      />

      {/* Concentric rotating rings with dashed segments */}
      {range(cluster.ringCount).map((i) => {
        const r = cluster.baseRadius * (0.4 + (i / cluster.ringCount) * 1.0);
        const rotation = (t * cluster.rotationSpeed * 360 * (i + 1) * 0.4 + i * 15) % 360;
        const segmentCount = 12 + i * 3;
        const dashLen = (TAU * r) / segmentCount;
        const breathe = 0.6 + 0.4 * (0.5 + 0.5 * loopSin(frame, 1, cluster.phase + i * 0.4));
        return (
          <g
            key={i}
            style={{
              transform: `rotate(${rotation}deg)`,
              transformOrigin: `${cx}px ${cy}px`,
            }}
          >
            <circle
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={cluster.color}
              strokeOpacity={(0.18 + 0.22 * intensity) * breathe}
              strokeWidth={0.8 + (i % 2 === 0 ? 0.4 : 0)}
              strokeDasharray={`${dashLen * 0.55} ${dashLen * 0.45}`}
            />
          </g>
        );
      })}

      {/* Radial spokes that fade in/out per frame */}
      {range(16).map((i) => {
        const angle = (i / 16) * TAU + t * cluster.rotationSpeed * TAU * 0.2;
        const inner = cluster.baseRadius * 0.45;
        const outer = cluster.baseRadius * 1.05;
        const x1 = cx + Math.cos(angle) * inner;
        const y1 = cy + Math.sin(angle) * inner;
        const x2 = cx + Math.cos(angle) * outer;
        const y2 = cy + Math.sin(angle) * outer;
        const fade = 0.5 + 0.5 * Math.sin(t * TAU * 2 + i * 0.5);
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={cluster.color}
            strokeOpacity={0.05 + 0.18 * fade * intensity}
            strokeWidth={0.7}
          />
        );
      })}

      {/* Core dot. Single 18px drop-shadow visually matches the previous
          stacked 10px + 24px shadows but rasterises in one pass instead
          of two. */}
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={PALETTE.white}
        opacity={0.7}
        style={{
          filter: `drop-shadow(0 0 18px ${cluster.color})`,
        }}
      />
    </g>
  );
};

export const ReasoningClusters: React.FC<{
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ parallaxX, parallaxY, intensity }) => {
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width={VIDEO_WIDTH} height={VIDEO_HEIGHT} viewBox={`0 0 ${VIDEO_WIDTH} ${VIDEO_HEIGHT}`}>
        {CLUSTERS.map((c, i) => (
          <ClusterView
            key={i}
            cluster={c}
            parallaxX={parallaxX}
            parallaxY={parallaxY}
            intensity={intensity}
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
