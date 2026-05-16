import { AbsoluteFill, useCurrentFrame } from "remotion";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  loopSin,
  mulberry32,
  range,
} from "./utils";

// Abstract code-like glyph set. Intentionally non-IDE, non-text, and not
// resembling any real programming language or interface.
const GLYPHS = "▓▒░█│║─═┌┐└┘┤├┬┴┼◆◇○●◐◑◯▮▯╴╶╵╷╳⟶⟵⟷⌬⌖";

type Panel = {
  id: number;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  z: number; // 0..1 depth for parallax
  scrollSpeed: number;
  fadePhase: number;
  glyphSize: number;
  columns: number;
  rows: number;
  hue: "cyan" | "violet" | "teal";
};

const PANELS: Panel[] = [
  {
    id: 0,
    x: 110,
    y: 180,
    width: 380,
    height: 520,
    rotation: 0,
    z: 0.85,
    scrollSpeed: 0.9,
    fadePhase: 0,
    glyphSize: 16,
    columns: 18,
    rows: 26,
    hue: "cyan",
  },
  {
    id: 1,
    x: 1420,
    y: 130,
    width: 420,
    height: 460,
    rotation: 0,
    z: 0.95,
    scrollSpeed: 1.1,
    fadePhase: 0.7,
    glyphSize: 14,
    columns: 22,
    rows: 25,
    hue: "violet",
  },
  {
    id: 2,
    x: 1380,
    y: 660,
    width: 470,
    height: 330,
    rotation: 0,
    z: 0.55,
    scrollSpeed: 0.75,
    fadePhase: 1.4,
    glyphSize: 14,
    columns: 24,
    rows: 18,
    hue: "teal",
  },
  {
    id: 3,
    x: 70,
    y: 760,
    width: 360,
    height: 250,
    rotation: 0,
    z: 0.4,
    scrollSpeed: 0.6,
    fadePhase: 2.1,
    glyphSize: 13,
    columns: 18,
    rows: 14,
    hue: "cyan",
  },
];

const HUE_TO_COLOR: Record<Panel["hue"], string> = {
  cyan: PALETTE.cyanBright,
  violet: PALETTE.violetSoft,
  teal: PALETTE.teal,
};

const HUE_TO_BORDER: Record<Panel["hue"], string> = {
  cyan: "rgba(34,211,238,0.35)",
  violet: "rgba(167,139,250,0.30)",
  teal: "rgba(45,212,191,0.32)",
};

function pickGlyphs(rand: () => number, count: number): string[] {
  return range(count).map(() => GLYPHS[Math.floor(rand() * GLYPHS.length)] ?? "▓");
}

const CodeStreamPanel: React.FC<{
  panel: Panel;
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ panel, parallaxX, parallaxY, intensity }) => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;

  const seed = 0xc0de + panel.id * 17;
  const rand = mulberry32(seed);

  // Pre-generate stable glyph rows. Each column scrolls vertically with its
  // own offset; we render `rows` worth and use modulo to wrap.
  const columnSeeds = range(panel.columns).map(() => Math.floor(rand() * 1e9));

  const px = panel.x + parallaxX * (0.4 + panel.z * 0.6);
  const py = panel.y + parallaxY * (0.4 + panel.z * 0.6);

  // Panel-level breathing so each one feels alive.
  const breathe = 0.85 + 0.15 * (0.5 + 0.5 * loopSin(frame, 1, panel.fadePhase));
  const panelOpacity = (0.55 + 0.35 * intensity) * breathe;

  const color = HUE_TO_COLOR[panel.hue];
  const border = HUE_TO_BORDER[panel.hue];

  const rowHeight = panel.glyphSize * 1.25;
  const colWidth = panel.width / panel.columns;

  return (
    <div
      style={{
        position: "absolute",
        left: px,
        top: py,
        width: panel.width,
        height: panel.height,
        opacity: panelOpacity,
        background:
          "linear-gradient(160deg, rgba(8,12,28,0.78) 0%, rgba(4,7,18,0.55) 100%)",
        border: `1px solid ${border}`,
        borderRadius: 6,
        boxShadow: `0 0 40px rgba(8,16,40,0.6), inset 0 0 60px rgba(0,0,0,0.55)`,
        overflow: "hidden",
        fontFamily: "ui-monospace, 'JetBrains Mono', Menlo, Consolas, monospace",
        fontSize: panel.glyphSize,
        color,
        textShadow: `0 0 8px ${color}`,
        letterSpacing: "0.08em",
      }}
    >
      {/* Top status strip — three abstract dots, no labels (brand safe). */}
      <div
        style={{
          display: "flex",
          gap: 6,
          padding: "8px 10px",
          borderBottom: `1px solid ${border}`,
          background: "rgba(2,6,16,0.65)",
        }}
      >
        {[PALETTE.cyan, PALETTE.violetSoft, PALETTE.teal].map((c, i) => (
          <div
            key={i}
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: c,
              opacity: 0.6,
              boxShadow: `0 0 4px ${c}`,
            }}
          />
        ))}
      </div>

      {/* Column-based glyph rain. */}
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        {columnSeeds.map((cseed, c) => {
          const colRand = mulberry32(cseed);
          const speed = panel.scrollSpeed * (0.6 + colRand() * 0.9);
          const offset = (t * speed * panel.rows) % panel.rows;
          const glyphs = pickGlyphs(colRand, panel.rows + 4);
          return (
            <div
              key={c}
              style={{
                position: "absolute",
                left: c * colWidth,
                top: 0,
                width: colWidth,
                height: "100%",
                overflow: "hidden",
              }}
            >
              {glyphs.map((g, r) => {
                const y = (r - offset) * rowHeight;
                const fade = Math.max(0, 1 - Math.abs(r - panel.rows / 2) / panel.rows);
                // brightest near the leading edge of each column
                const lead = Math.max(0, 1 - Math.abs(r - (panel.rows - offset)) / 6);
                const opacity = Math.min(1, 0.18 + fade * 0.4 + lead * 0.9);
                const isLead = lead > 0.6;
                return (
                  <span
                    key={r}
                    style={{
                      position: "absolute",
                      left: 0,
                      top: y + 30,
                      width: colWidth,
                      textAlign: "center",
                      opacity,
                      color: isLead ? PALETTE.white : color,
                      textShadow: isLead
                        ? `0 0 10px ${color}, 0 0 18px ${color}`
                        : undefined,
                    }}
                  >
                    {g}
                  </span>
                );
              })}
            </div>
          );
        })}

        {/* Soft top/bottom fade so the rain doesn't pop at edges. */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            background:
              "linear-gradient(180deg, rgba(2,6,16,0.95) 0%, rgba(2,6,16,0) 18%, rgba(2,6,16,0) 82%, rgba(2,6,16,0.95) 100%)",
          }}
        />
      </div>
    </div>
  );
};

export const CodeStreams: React.FC<{
  parallaxX: number;
  parallaxY: number;
  intensity: number;
}> = ({ parallaxX, parallaxY, intensity }) => {
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {PANELS.map((panel) => (
        <CodeStreamPanel
          key={panel.id}
          panel={panel}
          parallaxX={parallaxX}
          parallaxY={parallaxY}
          intensity={intensity}
        />
      ))}
    </AbsoluteFill>
  );
};

// Silence unused imports (TAU only used indirectly via utils; kept for parity)
void TAU;
