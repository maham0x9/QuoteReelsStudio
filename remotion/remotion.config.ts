import { Config } from "@remotion/cli/config";

// Project defaults: 4K (3840x2160) 16:9, H.264, up to 20s at 30fps.
// Per-composition `width`/`height`/`fps`/`durationInFrames` are sourced from
// the Composition definitions in src/Root.tsx; the values here only affect
// CLI-driven renders.
Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setConcurrency(1);
Config.setOverwriteOutput(true);
