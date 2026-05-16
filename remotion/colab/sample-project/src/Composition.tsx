import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// A minimal, brand-safe sample scene. Animated gradient + drifting circle so
// you can immediately confirm a Colab render is producing motion.
export const SampleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / durationInFrames;

  const hue = interpolate(t, [0, 1], [200, 260]);
  const x = interpolate(Math.sin((frame / fps) * 1.2), [-1, 1], [-260, 260]);
  const y = interpolate(Math.cos((frame / fps) * 0.9), [-1, 1], [-160, 160]);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 55%, hsl(${hue} 60% 14%) 0%, #04060d 75%)`,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          width: 520,
          height: 520,
          borderRadius: "50%",
          transform: `translate3d(${x}px, ${y}px, 0)`,
          background: `radial-gradient(circle, hsl(${hue + 20} 80% 60%) 0%, transparent 70%)`,
          filter: "blur(2px)",
          opacity: 0.85,
        }}
      />
    </AbsoluteFill>
  );
};
