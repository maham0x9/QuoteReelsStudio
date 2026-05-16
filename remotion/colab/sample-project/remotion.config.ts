import { Config } from "@remotion/cli/config";

// High-quality H.264 settings tuned for stock-footage marketplaces
// (Shutterstock / Adobe Stock / Pond5 / Vecteezy / 123RF).
// These can all be overridden by the Colab batch-renderer via CLI flags.
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(100);
Config.setCodec("h264");
Config.setCrf(16);
Config.setX264Preset("medium");
Config.setPixelFormat("yuv420p");
Config.setConcurrency(1);
Config.setOverwriteOutput(true);
