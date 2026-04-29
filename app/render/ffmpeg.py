"""FFmpeg locator + thin subprocess wrapper.

Falls back to the binary bundled with ``imageio-ffmpeg`` so users on Windows
do not need a system install.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

LOG = logging.getLogger(__name__)


def _hide_window_kwargs() -> dict:
    if sys.platform.startswith("win"):
        si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
        return {"startupinfo": si, "creationflags": 0x08000000}  # CREATE_NO_WINDOW
    return {}


def find_ffmpeg(explicit: str = "") -> str:
    """Return an ffmpeg executable path, raising ``RuntimeError`` if none."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("QRS_FFMPEG_PATH") or os.environ.get("FFMPEG_BINARY")
    if env:
        candidates.append(env)
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        candidates.append(sys_ff)
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        candidates.append(get_ffmpeg_exe())
    except Exception:  # pragma: no cover
        pass
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError(
        "FFmpeg not found. Install ffmpeg and put it on PATH, set QRS_FFMPEG_PATH, "
        "or install the bundled imageio-ffmpeg dependency."
    )


def run_ffmpeg(args: list[str], ffmpeg_path: str = "", check: bool = True) -> subprocess.CompletedProcess:
    exe = ffmpeg_path or find_ffmpeg()
    cmd = [exe, "-hide_banner", "-loglevel", "error", "-y", *args]
    LOG.debug("ffmpeg cmd: %s", " ".join(cmd))
    proc = subprocess.run(
        cmd, capture_output=True, text=True, **_hide_window_kwargs()
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {proc.returncode}):\nSTDERR:\n{proc.stderr}"
        )
    return proc


def probe_duration(path: str, ffmpeg_path: str = "") -> float:
    """Return media duration in seconds, or 0 on failure."""
    exe = ffmpeg_path or find_ffmpeg()
    ffprobe = exe.replace("ffmpeg", "ffprobe")
    if not Path(ffprobe).exists():
        # fallback: parse ffmpeg -i stderr
        proc = subprocess.run(
            [exe, "-hide_banner", "-i", path],
            capture_output=True, text=True, **_hide_window_kwargs()
        )
        for line in proc.stderr.splitlines():
            line = line.strip()
            if line.startswith("Duration:"):
                try:
                    t = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = t.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    return 0.0
        return 0.0
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, **_hide_window_kwargs()
    )
    try:
        return float((proc.stdout or "0").strip())
    except ValueError:
        return 0.0
