import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";

export const quoteSceneSchema = z.object({
  quote: z.string(),
  author: z.string(),
});

export type QuoteSceneProps = z.infer<typeof quoteSceneSchema>;

export const QuoteScene: React.FC<QuoteSceneProps> = ({ quote, author }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const intro = spring({
    frame,
    fps,
    config: { damping: 200 },
    durationInFrames: fps,
  });

  const outroStart = durationInFrames - fps;
  const outro = interpolate(frame, [outroStart, durationInFrames - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = intro * outro;
  const translateY = interpolate(intro, [0, 1], [40, 0]);

  return (
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 8%",
        fontFamily:
          "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          textAlign: "center",
          color: "white",
          maxWidth: "80%",
        }}
      >
        <p
          style={{
            fontSize: 160,
            fontWeight: 700,
            lineHeight: 1.15,
            margin: 0,
            textShadow: "0 8px 40px rgba(0,0,0,0.45)",
          }}
        >
          &ldquo;{quote}&rdquo;
        </p>
        <p
          style={{
            fontSize: 72,
            fontWeight: 500,
            marginTop: 80,
            color: "#cbd5e1",
            letterSpacing: 4,
          }}
        >
          — {author}
        </p>
      </div>
    </AbsoluteFill>
  );
};
