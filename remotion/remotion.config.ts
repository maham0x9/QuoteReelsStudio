import { Config } from "@remotion/cli/config";

// Per-composition `width`/`height`/`fps`/`durationInFrames` are sourced from
// the Composition definitions in src/Root.tsx; the values here only affect
// CLI-driven renders.
//
// Tuned for high-quality H.264 MP4 output suitable for stock-footage upload
// (Pond5, Adobe Stock, Shutterstock, etc.):
//   - jpeg frames at quality 100 (Remotion's preferred path; lossless PNG is
//     slower without a visible benefit for live-action-style renders)
//   - x264 with crf=14 and preset=slow → visually lossless, sane file sizes
//   - concurrency=1 keeps memory usage predictable on this VM; bump locally
//     with `--concurrency=<n>` if you want faster renders.
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(100);
Config.setCodec("h264");
Config.setCrf(14);
Config.setX264Preset("slow");
Config.setPixelFormat("yuv420p");
Config.setConcurrency(1);
Config.setOverwriteOutput(true);
