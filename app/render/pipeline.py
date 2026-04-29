"""High-level FFmpeg render pipeline.

Each ``RenderJob`` becomes a single FFmpeg invocation that:
  1. Loops + scales + center-crops the background to the project canvas
  2. (optional) Box-blurs the background
  3. (optional) Adds a translucent black overlay for readability
  4. Applies playback speed
  5. Overlays a Pillow-rendered transparent text PNG
  6. Mixes original audio (or mutes) with optional music track

We drive a single ``ffmpeg`` process per video instead of MoviePy's per-frame
Python loop because it is dramatically faster for batch workloads.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.config import AppConfig, get_config
from app.models import Project, Quote

from .ffmpeg import find_ffmpeg, probe_duration, run_ffmpeg
from .overlay import render_text_to_png

LOG = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], None]


@dataclass
class RenderJob:
    quote: Quote
    background_path: str
    output_path: Path
    canvas_size: tuple[int, int] = (1080, 1920)
    fps: int = 30
    bitrate: str = "8M"


class RenderPipeline:
    def __init__(self, cfg: AppConfig | None = None):
        self.cfg = cfg or get_config()
        self.ffmpeg_path = ""
        try:
            self.ffmpeg_path = find_ffmpeg(self.cfg.ffmpeg_path)
        except RuntimeError as e:
            LOG.warning("FFmpeg not yet available: %s", e)

    # ------------------------------------------------------------------ jobs
    def jobs_for_project(self, project: Project, out_dir: Path) -> list[RenderJob]:
        out_dir.mkdir(parents=True, exist_ok=True)
        jobs: list[RenderJob] = []
        for i, q in enumerate(project.quotes, start=1):
            opt = q.selected_option()
            if not opt or not opt.local_path:
                LOG.warning("Skipping quote %s — no downloaded background", q.id)
                continue
            safe = "".join(c for c in (q.text[:32] or q.id) if c.isalnum() or c in "-_ ").strip() or q.id
            out_path = out_dir / f"{i:03d}_{safe}.mp4"
            jobs.append(
                RenderJob(
                    quote=q,
                    background_path=opt.local_path,
                    output_path=out_path,
                    canvas_size=project.resolution,
                    fps=project.fps,
                    bitrate=project.bitrate,
                )
            )
        return jobs

    # ------------------------------------------------------------------ render
    def render(self, job: RenderJob, progress_cb: ProgressCb | None = None) -> Path:
        if not self.ffmpeg_path:
            self.ffmpeg_path = find_ffmpeg(self.cfg.ffmpeg_path)

        q = job.quote
        v = q.video
        cw, ch = job.canvas_size

        # 1. Build text overlay PNG at canvas size.
        if progress_cb:
            progress_cb(0.05, "Rendering text overlay")
        with tempfile.TemporaryDirectory(prefix="qrs_") as tmpdir:
            tmp = Path(tmpdir)
            text_png = tmp / "text.png"
            render_text_to_png(q.text_layer, (cw, ch), text_png)

            # 2. Prepare ffmpeg args.
            duration = max(0.5, float(v.duration))
            bg_dur = probe_duration(job.background_path, self.ffmpeg_path)

            args: list[str] = []
            # input 0 — background, optionally trimmed/looped
            if v.trim_start > 0:
                args += ["-ss", f"{v.trim_start:.3f}"]
            need_loop = v.loop_short and bg_dur > 0 and bg_dur < (
                duration * v.speed + v.trim_start
            )
            if need_loop:
                args += ["-stream_loop", "-1"]
            args += ["-i", job.background_path]

            # input 1 — text overlay
            args += ["-loop", "1", "-t", f"{duration:.3f}", "-i", str(text_png)]

            # input 2 — music (optional)
            has_music = bool(v.music_path) and Path(v.music_path).exists()
            if has_music:
                args += ["-stream_loop", "-1", "-i", v.music_path]

            # video filter graph
            scale = (
                f"scale={cw}:{ch}:force_original_aspect_ratio=increase,"
                f"crop={cw}:{ch}"
            )
            blur = f",boxblur={v.blur_strength}:1" if v.blur_bg else ""
            speed = f",setpts=PTS/{v.speed}" if abs(v.speed - 1.0) > 1e-3 else ""
            fade = (
                f",drawbox=x=0:y=0:w={cw}:h={ch}:"
                f"color=black@{max(0.0, min(1.0, v.dark_overlay)):.3f}:t=fill"
                if v.dark_overlay > 0 else ""
            )
            vf = (
                f"[0:v]{scale}{blur}{speed}{fade}[bg];"
                f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
            )

            # audio filter graph
            audio_inputs = []
            if not v.mute_original:
                audio_inputs.append("[0:a]")
            if has_music:
                vol_idx = 2 if not v.mute_original else 2  # music is always input 2
                audio_inputs.append(f"[{vol_idx}:a]volume={v.music_volume:.3f}[m];[m]")
            af = ""
            if audio_inputs:
                if len(audio_inputs) == 1:
                    af = f"{audio_inputs[0]}aresample=44100,asetpts=N/SR/TB[a]"
                else:
                    af = (
                        f"{audio_inputs[0]}aresample=44100[a0];"
                        f"{audio_inputs[1]}aresample=44100[a1];"
                        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0,"
                        f"asetpts=N/SR/TB[a]"
                    )
                fc = f"{vf};{af}"
                map_args = ["-map", "[v]", "-map", "[a]"]
            else:
                fc = vf
                map_args = ["-map", "[v]"]

            args += ["-filter_complex", fc]
            args += map_args
            args += [
                "-r", str(job.fps),
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                "-b:v", job.bitrate,
                "-movflags", "+faststart",
            ]
            if audio_inputs:
                args += ["-c:a", "aac", "-b:a", "192k"]
            else:
                args += ["-an"]

            job.output_path.parent.mkdir(parents=True, exist_ok=True)
            args += [str(job.output_path)]

            if progress_cb:
                progress_cb(0.15, f"Encoding {job.output_path.name}")
            run_ffmpeg(args, ffmpeg_path=self.ffmpeg_path, check=True)

        if progress_cb:
            progress_cb(1.0, "Done")
        return job.output_path

    # ------------------------------------------------------------------ batch
    def render_batch(
        self,
        jobs: list[RenderJob],
        progress_cb: ProgressCb | None = None,
        cancel_event: threading.Event | None = None,
    ) -> list[Path]:
        outputs: list[Path] = []
        total = len(jobs)
        for i, job in enumerate(jobs):
            if cancel_event and cancel_event.is_set():
                break

            def _per_job_progress(p: float, msg: str, _i=i):
                if progress_cb:
                    overall = (_i + p) / max(1, total)
                    progress_cb(overall, f"[{_i + 1}/{total}] {msg}")

            try:
                outputs.append(self.render(job, progress_cb=_per_job_progress))
            except Exception as e:  # pragma: no cover - reported up the stack
                LOG.exception("Render failed for job %s: %s", job.output_path, e)
        return outputs

    # ------------------------------------------------------------------ misc
    def export_to_folder(self, jobs: list[Path], dest_dir: Path) -> list[Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        out: list[Path] = []
        for src in jobs:
            d = dest_dir / src.name
            shutil.copy2(src, d)
            out.append(d)
        return out


# Convenience wrapper used by tests / CLI
def render_project(project: Project, out_dir: str | os.PathLike) -> list[Path]:
    pipe = RenderPipeline()
    jobs = pipe.jobs_for_project(project, Path(out_dir))
    return pipe.render_batch(jobs)
