import { Composition } from "remotion";
import { AutonomousDevMatrix } from "./AutonomousDevMatrix/AutonomousDevMatrix";
import {
  DURATION_FRAMES as ADM_DURATION_FRAMES,
  VIDEO_FPS as ADM_FPS,
  VIDEO_HEIGHT as ADM_HEIGHT,
  VIDEO_WIDTH as ADM_WIDTH,
} from "./AutonomousDevMatrix/utils";
import { QuoteScene, quoteSceneSchema } from "./Composition";

// 4K UHD, 16:9, 30 fps, hard cap of 20 seconds (600 frames).
export const VIDEO_WIDTH = 3840;
export const VIDEO_HEIGHT = 2160;
export const VIDEO_FPS = 30;
export const MAX_DURATION_SECONDS = 20;
export const MAX_DURATION_FRAMES = VIDEO_FPS * MAX_DURATION_SECONDS;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Landscape4k"
        component={QuoteScene}
        durationInFrames={MAX_DURATION_FRAMES}
        fps={VIDEO_FPS}
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
        schema={quoteSceneSchema}
        defaultProps={{
          quote: "The best way to predict the future is to invent it.",
          author: "Alan Kay",
        }}
      />
      {/* AutonomousDevMatrix — 1920x1080, 30 fps, 20s seamless loop. */}
      <Composition
        id="AutonomousDevMatrix"
        component={AutonomousDevMatrix}
        durationInFrames={ADM_DURATION_FRAMES}
        fps={ADM_FPS}
        width={ADM_WIDTH}
        height={ADM_HEIGHT}
      />
    </>
  );
};
