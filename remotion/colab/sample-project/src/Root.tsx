import { Composition } from "remotion";
import { SampleScene } from "./Composition";

// Stock-marketplace-friendly defaults: 1920x1080, 30 fps, 10-second clip.
// Edit these to suit your project. The Colab batch-renderer reads dimensions
// from this Composition definition.
export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="SampleScene"
        component={SampleScene}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
