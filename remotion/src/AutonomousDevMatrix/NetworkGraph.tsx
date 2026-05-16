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

type Node = {
  x: number;
  y: number;
  z: number;
  radius: number;
  color: string;
  activatePhase: number; // 0..1 fraction of the loop where it lights up
  cluster: number;
};

type Edge = {
  a: number;
  b: number;
  phase: number;
  cycles: number;
};

const NODE_COUNT = 26;
const NODE_COLORS = [
  PALETTE.cyanBright,
  PALETTE.cyan,
  PALETTE.teal,
  PALETTE.violetSoft,
];

function buildGraph(seed: number): { nodes: Node[]; edges: Edge[] } {
  const rand = mulberry32(seed);

  // Place nodes in 4 loose clusters across the frame so the graph feels
  // composed rather than random.
  const clusterCenters: [number, number][] = [
    [VIDEO_WIDTH * 0.22, VIDEO_HEIGHT * 0.32],
    [VIDEO_WIDTH * 0.78, VIDEO_HEIGHT * 0.28],
    [VIDEO_WIDTH * 0.18, VIDEO_HEIGHT * 0.72],
    [VIDEO_WIDTH * 0.82, VIDEO_HEIGHT * 0.74],
  ];

  const nodes: Node[] = range(NODE_COUNT).map((i) => {
    const cluster = i % clusterCenters.length;
    const center = clusterCenters[cluster]!;
    const angle = rand() * TAU;
    const radius = 60 + rand() * 260;
    const z = rand();
    return {
      x: center[0] + Math.cos(angle) * radius,
      y: center[1] + Math.sin(angle) * radius * 0.72,
      z,
      radius: 4 + z * 12 + rand() * 4,
      color: NODE_COLORS[Math.floor(rand() * NODE_COLORS.length)] ?? PALETTE.cyan,
      activatePhase: rand(),
      cluster,
    };
  });

  // Wire each node to 2-3 nearest neighbors so it looks like a real mesh
  // but is not chaotic.
  const edges: Edge[] = [];
  const seen = new Set<string>();
  nodes.forEach((node, i) => {
    const distances = nodes
      .map((other, j) => ({
        j,
        d: Math.hypot(other.x - node.x, other.y - node.y),
      }))
      .filter((e) => e.j !== i)
      .sort((p, q) => p.d - q.d)
      .slice(0, 3);
    distances.forEach(({ j }) => {
      const key = i < j ? `${i}-${j}` : `${j}-${i}`;
      if (!seen.has(key)) {
        seen.add(key);
        edges.push({
          a: Math.min(i, j),
          b: Math.max(i, j),
          phase: rand() * TAU,
          cycles: 1 + Math.floor(rand() * 2),
        });
      }
    });
  });

  // A few cross-cluster long edges for visual interest.
  for (let k = 0; k < 5; k++) {
    const a = Math.floor(rand() * nodes.length);
    const b = Math.floor(rand() * nodes.length);
    if (a === b) continue;
    const key = a < b ? `${a}-${b}` : `${b}-${a}`;
    if (seen.has(key)) continue;
    seen.add(key);
    edges.push({
      a: Math.min(a, b),
      b: Math.max(a, b),
      phase: rand() * TAU,
      cycles: 1,
    });
  }

  return { nodes, edges };
}

const { nodes, edges } = buildGraph(0x2f8c19);

export const NetworkGraph: React.FC<{
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ parallaxX, parallaxY, intensity }) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;

  const positioned = nodes.map((n) => {
    const px = n.x + parallaxX * (0.4 + n.z * 0.6);
    const py = n.y + parallaxY * (0.4 + n.z * 0.6);
    // breathing wobble
    const wobble = 3 + n.z * 6;
    return {
      ...n,
      px: px + Math.sin(TAU * t * 1 + n.activatePhase * TAU) * wobble,
      py: py + Math.cos(TAU * t * 1 + n.activatePhase * TAU) * wobble,
    };
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
        viewBox={`0 0 ${VIDEO_WIDTH} ${VIDEO_HEIGHT}`}
        style={{ position: "absolute", inset: 0 }}
      >
        <defs>
          <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="white" stopOpacity="0.95" />
            <stop offset="40%" stopColor={PALETTE.cyanBright} stopOpacity="0.7" />
            <stop offset="100%" stopColor={PALETTE.cyanDeep} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Edges */}
        {edges.map((e, i) => {
          const a = positioned[e.a]!;
          const b = positioned[e.b]!;
          const pulse = 0.35 + 0.65 * (0.5 + 0.5 * loopSin(frame, e.cycles, e.phase));
          const baseOpacity = 0.12 + 0.18 * intensity;
          return (
            <line
              key={`e${i}`}
              x1={a.px}
              y1={a.py}
              x2={b.px}
              y2={b.py}
              stroke={PALETTE.cyan}
              strokeOpacity={baseOpacity + 0.25 * pulse * intensity}
              strokeWidth={0.8 + pulse * 0.8}
            />
          );
        })}

        {/* Pulses traveling along edges */}
        {edges.map((e, i) => {
          const a = positioned[e.a]!;
          const b = positioned[e.b]!;
          // Two pulses per edge, offset.
          return [0, 0.5].map((offset, k) => {
            const u = (t * (e.cycles + 1) + e.phase / TAU + offset) % 1;
            const x = a.px + (b.px - a.px) * u;
            const y = a.py + (b.py - a.py) * u;
            return (
              <circle
                key={`p${i}-${k}`}
                cx={x}
                cy={y}
                r={2.2}
                fill={k === 0 ? PALETTE.cyanBright : PALETTE.violetSoft}
                opacity={0.45 + 0.35 * intensity}
                style={{
                  filter: `drop-shadow(0 0 6px ${k === 0 ? PALETTE.cyan : PALETTE.violet}) drop-shadow(0 0 12px ${k === 0 ? PALETTE.cyan : PALETTE.violet})`,
                }}
              />
            );
          });
        })}

        {/* Nodes */}
        {positioned.map((n, i) => {
          const activate = 0.5 + 0.5 * loopSin(frame, 1, n.activatePhase * TAU);
          const opacity = 0.5 + 0.5 * activate * intensity;
          const r = n.radius * (0.9 + 0.25 * activate);
          return (
            <g key={`n${i}`} opacity={opacity}>
              <circle
                cx={n.px}
                cy={n.py}
                r={r * 3.5}
                fill="url(#nodeGlow)"
                opacity={0.55}
              />
              <circle
                cx={n.px}
                cy={n.py}
                r={r}
                fill={n.color}
                style={{
                  filter: `drop-shadow(0 0 ${4 + n.z * 8}px ${n.color}) drop-shadow(0 0 ${10 + n.z * 20}px ${n.color})`,
                }}
              />
              <circle
                cx={n.px}
                cy={n.py}
                r={r * 1.7}
                fill="none"
                stroke={n.color}
                strokeOpacity={0.35}
                strokeWidth={0.6}
              />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
