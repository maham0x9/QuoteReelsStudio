import { AbsoluteFill, useCurrentFrame } from "remotion";
import { CodeStreams } from "./CodeStreams";
import { DeploymentGraphs } from "./DeploymentGraphs";
import {
  Bloom,
  ChromaticAberration,
  FilmGrain,
  LoopSeamFade,
  Scanlines,
  Vignette,
} from "./Effects";
import { NetworkGraph } from "./NetworkGraph";
import { ParticleField } from "./ParticleField";
import { ReasoningClusters } from "./ReasoningClusters";
import {
  DURATION_FRAMES,
  PALETTE,
  TAU,
  VIDEO_HEIGHT,
  VIDEO_WIDTH,
  loopSin,
} from "./utils";
import { VolumetricHaze } from "./VolumetricHaze";
import { Workflows } from "./Workflows";

// The whole scene scales/translates very slightly so the camera feels like
// it is gliding through the environment. Every animation in this file is
// expressed as a function of (frame / DURATION_FRAMES) so the final frame
// loops cleanly back to frame 0.
export const AutonomousDevMatrix: React.FC = () => {
  const frame = useCurrentFrame();
  const t = (frame % DURATION_FRAMES) / DURATION_FRAMES;

  // Cinematic camera glide. Uses single-cycle sin/cos so the start and end
  // are identical (perfect loop). The amplitudes are intentionally small —
  // the scene should feel like a slow steady drift, not a tour.
  const cameraX = Math.sin(TAU * t) * 60;
  const cameraY = Math.cos(TAU * t) * 38;
  const cameraScale = 1.04 + Math.cos(TAU * t) * 0.04;

  // Activity envelopes for the scene flow described in the brief:
  // 1) dark env fades in
  // 2) autonomous coding activates
  // 3) multi-agent workflows connect
  // 4) deployment + reasoning intensify
  // 5) full ecosystem stabilizes
  // 6) seamless loop
  //
  // Each layer's `intensity` is a 0..1 number that rides on a loop-safe
  // cosine curve. Different layers peak at different points of the loop so
  // attention cycles through the scene.
  const codeIntensity = 0.55 + 0.45 * (0.5 + 0.5 * loopSin(frame, 1, -0.6));
  const networkIntensity = 0.55 + 0.45 * (0.5 + 0.5 * loopSin(frame, 1, 0.3));
  const reasoningIntensity = 0.55 + 0.45 * (0.5 + 0.5 * loopSin(frame, 1, 1.4));
  const deploymentIntensity = 0.5 + 0.5 * (0.5 + 0.5 * loopSin(frame, 1, 2.5));
  const workflowIntensity = 0.6 + 0.4 * (0.5 + 0.5 * loopSin(frame, 1, 1.0));
  const bloomIntensity = 0.4 + 0.6 * (0.5 + 0.5 * loopSin(frame, 1, 0.8));

  // Chromatic aberration also breathes — sits at ~1.2px with brief bumps.
  const chroma = 1.0 + 0.8 * (0.5 + 0.5 * loopSin(frame, 1, 1.7));

  return (
    <AbsoluteFill style={{ background: PALETTE.black, overflow: "hidden" }}>
      {/* Camera transform */}
      <AbsoluteFill
        style={{
          width: VIDEO_WIDTH,
          height: VIDEO_HEIGHT,
          transform: `translate3d(${-cameraX * 0.5}px, ${-cameraY * 0.5}px, 0) scale(${cameraScale})`,
          transformOrigin: "50% 50%",
        }}
      >
        {/* Background haze + base gradient */}
        <VolumetricHaze parallaxX={cameraX * 0.2} parallaxY={cameraY * 0.2} />

        {/* Far parallax: ambient particles drifting */}
        <ParticleField parallaxX={cameraX * 0.4} parallaxY={cameraY * 0.4} />

        {/* Mid parallax: reasoning halos behind everything */}
        <ReasoningClusters
          parallaxX={cameraX * 0.6}
          parallaxY={cameraY * 0.6}
          intensity={reasoningIntensity}
        />

        {/* Mid: workflow pipelines crossing the frame */}
        <Workflows
          parallaxX={cameraX * 0.7}
          parallaxY={cameraY * 0.7}
          intensity={workflowIntensity}
        />

        {/* Mid-front: the agent network graph */}
        <NetworkGraph
          parallaxX={cameraX * 0.85}
          parallaxY={cameraY * 0.85}
          intensity={networkIntensity}
        />

        {/* Front: abstract code-rain panels */}
        <CodeStreams
          parallaxX={cameraX}
          parallaxY={cameraY}
          intensity={codeIntensity}
        />

        {/* Front: deployment / metric bar stacks */}
        <DeploymentGraphs
          parallaxX={cameraX}
          parallaxY={cameraY}
          intensity={deploymentIntensity}
        />
      </AbsoluteFill>

      {/* Cinematic post: bloom, chromatic split, scanlines, vignette, grain */}
      <Bloom intensity={bloomIntensity} />
      <ChromaticAberration amount={chroma} />
      <Scanlines />
      <Vignette />
      <FilmGrain />

      {/* Seam fade so the loop point isn't visible. Black at frame 0 and the
          last frame, so concatenating the clip to itself is invisible. */}
      <LoopSeamFade />
    </AbsoluteFill>
  );
};
