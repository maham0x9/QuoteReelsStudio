"""Generate RemotionBatchRender.ipynb — a Google Colab notebook that
batch-renders Remotion projects stored in Google Drive.

Run from this directory:

    python build_notebook.py

The notebook itself is self-contained; this script only exists to keep the
cell sources readable (long Python strings inside JSON are painful to edit
by hand).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

CellType = Literal["markdown", "code"]


def cell(kind: CellType, source: str) -> dict:
    """Build a single Jupyter/Colab cell. Source is stored as a list of lines
    with trailing newlines (the format Jupyter/Colab expect)."""
    lines = source.splitlines(keepends=True)
    base = {"cell_type": kind, "metadata": {}, "source": lines}
    if kind == "code":
        base["execution_count"] = None
        base["outputs"] = []
    return base


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------

CELLS: list[dict] = []

CELLS.append(
    cell(
        "markdown",
        """# Remotion Batch Renderer for Google Colab

Render every Remotion project under a Google Drive folder to high-quality
**1920x1080 H.264 MP4** files, sequentially and unattended.

**What this notebook does**

1. Mounts your Google Drive
2. Installs Node.js LTS, FFmpeg, and the Chrome libs Remotion needs
3. Detects every Remotion project under `MyDrive/remotion-projects/`
4. Runs `npm install` per project (cached by `package-lock.json`)
5. Lists each project's compositions and renders them with sane stock-footage
   defaults (CRF 16, preset `medium`, `yuv420p`, JPEG quality 100)
6. Writes the MP4s to `MyDrive/remotion-renders/<project>/<comp>.mp4`
7. Auto-retries failed renders once, prints a final summary, and (optionally)
   pings a Slack/Discord webhook when each project finishes

**Designed for Colab.** Survives idle disconnects (output goes to Drive so a
runtime kill doesn't lose finished renders), supports CPU parallelism on the
Chrome side, optional GPU rendering via `--gl=angle`, project filtering, and
queueing.
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Expected folder structure on Google Drive

```
MyDrive/
├── remotion-projects/
│   ├── MyFirstVideo/
│   │   ├── package.json          # must declare `remotion` in dependencies
│   │   ├── remotion.config.ts    # optional; sensible defaults applied otherwise
│   │   ├── tsconfig.json         # optional
│   │   ├── src/
│   │   │   ├── index.tsx         # entry: must call registerRoot(...)
│   │   │   ├── Root.tsx
│   │   │   └── Composition.tsx
│   │   ├── public/               # optional; served at /<file> by Remotion
│   │   └── assets/               # optional
│   ├── SecondVideo/
│   │   └── ...
│   └── ThirdVideo/
│       └── ...
└── remotion-renders/             # created automatically; outputs land here
    ├── MyFirstVideo/
    │   └── SampleScene.mp4
    └── ...
```

The renderer treats a folder as a valid Remotion project if it contains a
`package.json` whose dependencies include `remotion` (or `@remotion/cli`).
Anything else is skipped with a warning.

If you don't have any projects yet, jump to the **"Write a sample project to
Drive"** cell near the bottom — it creates one for you.""",
    )
)

CELLS.append(cell("markdown", "## Step 1 — Mount Google Drive"))

CELLS.append(
    cell(
        "code",
        """from google.colab import drive

drive.mount('/content/drive')
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 2 — Install Node.js, FFmpeg, and Chrome libraries

Remotion bundles its own Chrome Headless Shell but requires the system shared
libraries it links against. We also install Node 20 LTS and FFmpeg.

Idempotent — safe to re-run.""",
    )
)

CELLS.append(
    cell(
        "code",
        """%%bash
set -euo pipefail

# Node.js 20 LTS (only install if missing or wrong major)
NODE_MAJOR=$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\\1/' || echo 0)
if [ "$NODE_MAJOR" -lt 18 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - >/dev/null
  sudo apt-get install -y nodejs >/dev/null
fi

# FFmpeg
if ! command -v ffmpeg >/dev/null; then
  sudo apt-get update -y >/dev/null
  sudo apt-get install -y ffmpeg >/dev/null
fi

# Chrome / Remotion runtime libs
sudo apt-get install -y --no-install-recommends \\
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 libxtst6 \\
  libxrandr2 libpangocairo-1.0-0 libgtk-3-0 libgbm1 libxshmfence1 \\
  libxcomposite1 libxdamage1 fonts-liberation libxkbcommon0 \\
  libasound2t64 2>/dev/null || sudo apt-get install -y --no-install-recommends libasound2 >/dev/null

echo
echo "node:    $(node -v)"
echo "npm:     $(npm -v)"
echo "ffmpeg:  $(ffmpeg -version | head -1)"
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 3 — Configuration

Tweak these and re-run the rest of the notebook. Everything downstream reads
from `CONFIG`.""",
    )
)

CELLS.append(
    cell(
        "code",
        """import os
from pathlib import Path

CONFIG = {
    # --- Drive paths -------------------------------------------------------
    "projects_root": Path("/content/drive/MyDrive/remotion-projects"),
    "output_root":   Path("/content/drive/MyDrive/remotion-renders"),

    # --- Render specs (overrides per-project remotion.config.ts) ----------
    "width":         1920,
    "height":        1080,
    "fps":           30,
    "codec":         "h264",
    "crf":           16,           # 14-18 = visually lossless for stock
    "x264_preset":   "medium",     # ultrafast..veryslow
    "pixel_format":  "yuv420p",    # required by most stock marketplaces
    "jpeg_quality":  100,

    # --- Performance -------------------------------------------------------
    # Remotion's --concurrency controls how many Chrome tabs render frames
    # in parallel. Colab usually has 2 vCPUs (free) or 4 (Pro), so 2 is a
    # safe default. Bump on bigger runtimes.
    "concurrency":   max(1, (os.cpu_count() or 2) // 1),
    # Use ANGLE (software GL) for stability in Colab. Set to "angle" or
    # "swangle". Set "egl" if you actually have a working GPU (rare in Colab).
    "gl_backend":    "swangle",
    # Try GPU H.264 encoder if available (NVENC). Auto-detected below.
    "use_nvenc":     True,

    # --- Selection / queueing ---------------------------------------------
    # If None, render every project under projects_root. Else, a list of
    # folder names (relative to projects_root) to render.
    "only":          None,            # e.g. ["AutonomousDevMatrix", "Promo2"]
    # If None, render every composition each project registers. Else, dict
    # mapping project name -> list of composition ids (or single id string).
    "compositions":  None,            # e.g. {"AutonomousDevMatrix": "AutonomousDevMatrix"}
    # Skip projects whose output MP4 already exists. Set False to force.
    "skip_existing": True,

    # --- Stability ---------------------------------------------------------
    "retries":       1,               # extra attempts after the first failure
    "per_render_timeout_min": 90,     # kill render if it exceeds this

    # --- Notifications -----------------------------------------------------
    # Set to a Slack incoming-webhook URL (or Discord, etc.). None disables.
    "webhook_url":   None,
    "webhook_name":  "Remotion Batch Render",
}

# Make sure output folder exists.
CONFIG["output_root"].mkdir(parents=True, exist_ok=True)

print("projects_root:", CONFIG["projects_root"])
print("output_root:  ", CONFIG["output_root"])
print("concurrency:  ", CONFIG["concurrency"])
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 4 — Helpers (logging, webhook, GPU detection)""",
    )
)

CELLS.append(
    cell(
        "code",
        """import json
import shutil
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class RenderResult:
    project: str
    composition: str
    output: str
    ok: bool
    seconds: float
    attempts: int
    error: str = ""

def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

@contextmanager
def step(title: str):
    log(f"▶ {title}")
    t0 = time.time()
    try:
        yield
    finally:
        log(f"  done in {time.time() - t0:0.1f}s")

def notify(text: str) -> None:
    \"\"\"Post a message to the configured webhook (Slack / Discord). Silent
    on failure so a webhook problem never breaks a render.\"\"\"
    url = CONFIG.get("webhook_url")
    if not url:
        return
    payload = {"text": text, "username": CONFIG.get("webhook_name", "Remotion")}
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        log(f"  webhook failed: {e}")

def detect_nvenc() -> bool:
    \"\"\"Return True if ffmpeg has h264_nvenc available (NVIDIA GPU runtime).\"\"\"
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, check=False,
        ).stdout
        return "h264_nvenc" in out
    except Exception:
        return False

NVENC_AVAILABLE = CONFIG["use_nvenc"] and detect_nvenc()
log(f"GPU encoder (h264_nvenc) detected: {NVENC_AVAILABLE}")
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 5 — Detect Remotion projects in Drive

A folder counts as a project if it has a `package.json` whose dependencies
include `remotion` or `@remotion/cli`. Anything else is skipped.""",
    )
)

CELLS.append(
    cell(
        "code",
        """def is_remotion_project(folder: Path) -> bool:
    pkg = folder / "package.json"
    if not pkg.is_file():
        return False
    try:
        data = json.loads(pkg.read_text())
    except Exception:
        return False
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return "remotion" in deps or "@remotion/cli" in deps

def find_entry(project: Path) -> Path | None:
    \"\"\"Find the file to pass to `remotion render`. Falls back through the
    common entry-point names.\"\"\"
    for rel in ("src/index.tsx", "src/index.ts",
                "src/Root.tsx",  "src/Root.ts",
                "remotion/src/index.tsx", "remotion/index.tsx"):
        p = project / rel
        if p.is_file():
            return p
    return None

def detect_projects() -> list[Path]:
    root = CONFIG["projects_root"]
    if not root.is_dir():
        raise FileNotFoundError(
            f"{root} does not exist on Drive. Create it and put your projects "
            f"there, or run the 'Write a sample project to Drive' cell below."
        )
    folders = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    only = CONFIG.get("only")
    if only:
        wanted = set(only)
        folders = [p for p in folders if p.name in wanted]
        missing = wanted - {p.name for p in folders}
        if missing:
            log(f"WARNING: requested project(s) not found under {root}: {sorted(missing)}")
    valid, skipped = [], []
    for f in folders:
        (valid if is_remotion_project(f) else skipped).append(f)
    if skipped:
        log(f"Skipping {len(skipped)} non-Remotion folder(s): {[p.name for p in skipped]}")
    return valid

projects = detect_projects()
log(f"Found {len(projects)} Remotion project(s):")
for p in projects:
    log(f"  - {p.name}  ({p})")
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 6 — Per-project: install npm dependencies

Caches by the SHA of `package-lock.json`. If the lockfile hasn't changed
since the last install, this is a no-op.""",
    )
)

CELLS.append(
    cell(
        "code",
        """import hashlib

def _lock_hash(project: Path) -> str:
    lock = project / "package-lock.json"
    if lock.is_file():
        return hashlib.sha256(lock.read_bytes()).hexdigest()
    pkg = project / "package.json"
    return hashlib.sha256(pkg.read_bytes()).hexdigest() if pkg.is_file() else ""

def ensure_project_installed(project: Path) -> None:
    node_modules = project / "node_modules"
    stamp = node_modules / ".colab_install_hash"
    want = _lock_hash(project)
    have = stamp.read_text().strip() if stamp.is_file() else ""
    if node_modules.is_dir() and want and want == have:
        log(f"  npm: cache hit ({project.name})")
        return
    log(f"  npm: installing dependencies in {project.name} (this can take a few minutes)")
    cmd = ["npm", "ci"] if (project / "package-lock.json").is_file() else ["npm", "install"]
    cmd.extend(["--no-audit", "--no-fund", "--prefer-offline"])
    subprocess.run(cmd, cwd=project, check=True)
    try:
        stamp.write_text(want)
    except OSError:
        pass  # Drive race conditions are non-fatal
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 7 — Render a single composition

Builds a `npx remotion render` command from `CONFIG`, supervises it with a
timeout, parses progress, and returns a structured result.""",
    )
)

CELLS.append(
    cell(
        "code",
        """import re

PROGRESS_RE = re.compile(r"(Rendering frames|Encoding video)\\s+[^\\d]*([0-9]+)/([0-9]+)")

def list_compositions(project: Path, entry: Path) -> list[dict]:
    \"\"\"Run `npx remotion compositions` and parse out (id, fps, w, h, frames).
    Returns [{id, fps, width, height, frames}, ...].\"\"\"
    res = subprocess.run(
        ["npx", "--yes", "remotion", "compositions", str(entry.relative_to(project))],
        cwd=project, capture_output=True, text=True, check=False, timeout=300,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"`remotion compositions` failed for {project.name}:\\n{res.stderr or res.stdout}"
        )
    out = []
    # Lines look like: "MyComp    30      1920x1080      300 (10.00 sec)"
    for line in res.stdout.splitlines():
        m = re.match(r"^([A-Za-z0-9_\\-]+)\\s+(\\d+)\\s+(\\d+)x(\\d+)\\s+(\\d+)", line.strip())
        if m:
            out.append({
                "id":     m.group(1),
                "fps":    int(m.group(2)),
                "width":  int(m.group(3)),
                "height": int(m.group(4)),
                "frames": int(m.group(5)),
            })
    return out

def _build_render_cmd(project: Path, entry: Path, comp: str, output: Path) -> list[str]:
    cmd = [
        "npx", "--yes", "remotion", "render",
        str(entry.relative_to(project)), comp, str(output),
        "--codec", CONFIG["codec"],
        "--crf", str(CONFIG["crf"]),
        "--x264-preset", CONFIG["x264_preset"],
        "--pixel-format", CONFIG["pixel_format"],
        "--jpeg-quality", str(CONFIG["jpeg_quality"]),
        "--width", str(CONFIG["width"]),
        "--height", str(CONFIG["height"]),
        "--concurrency", str(CONFIG["concurrency"]),
        "--gl", CONFIG["gl_backend"],
        "--overwrite",
        "--log", "info",
    ]
    # FPS override only applies if the composition itself doesn't already
    # match; Remotion will warn otherwise but still produce a valid file.
    cmd.extend(["--fps", str(CONFIG["fps"])])
    return cmd

def _run_render(cmd: list[str], cwd: Path, timeout_s: int) -> tuple[int, str]:
    \"\"\"Stream stdout, echo progress lines, return (returncode, last_tail).\"\"\"
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    deadline = time.time() + timeout_s
    tail: list[str] = []
    last_print = 0.0
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            tail.append(line)
            if len(tail) > 50:
                tail = tail[-50:]
            # Throttle progress prints to once per second per phase
            m = PROGRESS_RE.search(line)
            now = time.time()
            if m and (now - last_print) > 1.0:
                phase, cur, total = m.group(1), m.group(2), m.group(3)
                pct = (int(cur) / int(total)) * 100
                log(f"    {phase}: {cur}/{total} ({pct:0.1f}%)")
                last_print = now
            elif not m and ("error" in line.lower() or "✘" in line):
                log(f"    {line}")
            if time.time() > deadline:
                proc.kill()
                raise TimeoutError(f"render exceeded {timeout_s}s")
    finally:
        proc.wait()
    return proc.returncode, "\\n".join(tail[-25:])

def render_composition(project: Path, entry: Path, comp: dict) -> RenderResult:
    out_dir = CONFIG["output_root"] / project.name
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{comp['id']}.mp4"

    if CONFIG["skip_existing"] and output.is_file() and output.stat().st_size > 0:
        log(f"  skip {project.name}/{comp['id']} (already rendered)")
        return RenderResult(project.name, comp["id"], str(output), True, 0.0, 0)

    timeout_s = CONFIG["per_render_timeout_min"] * 60
    attempts = 1 + CONFIG["retries"]
    last_err = ""
    t0 = time.time()
    for attempt in range(1, attempts + 1):
        cmd = _build_render_cmd(project, entry, comp["id"], output)
        log(f"  render {project.name}/{comp['id']} (attempt {attempt}/{attempts})")
        log(f"    cmd: {' '.join(cmd)}")
        try:
            rc, tail = _run_render(cmd, project, timeout_s)
            if rc == 0 and output.is_file() and output.stat().st_size > 0:
                dt = time.time() - t0
                log(f"  ✔ {project.name}/{comp['id']} in {dt:0.1f}s -> {output}")
                return RenderResult(project.name, comp["id"], str(output), True, dt, attempt)
            last_err = f"exit={rc}\\n{tail}"
            log(f"  ✘ attempt {attempt} failed:\\n{tail}")
        except TimeoutError as te:
            last_err = str(te)
            log(f"  ✘ attempt {attempt} timed out")
        # Brief cooldown before retry to let Chrome processes die.
        time.sleep(3)

    return RenderResult(
        project.name, comp["id"], str(output), False,
        time.time() - t0, attempts, error=last_err,
    )
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 8 — Batch runner

For each project: install deps, list compositions, render each one, retry on
failure, post webhook, continue on errors. Prints a final summary table.""",
    )
)

CELLS.append(
    cell(
        "code",
        """def _picked_compositions(project_name: str, comps: list[dict]) -> list[dict]:
    pick = CONFIG.get("compositions")
    if not pick:
        return comps
    want = pick.get(project_name)
    if not want:
        return comps
    if isinstance(want, str):
        want = [want]
    by_id = {c["id"]: c for c in comps}
    out = []
    for cid in want:
        if cid in by_id:
            out.append(by_id[cid])
        else:
            log(f"  WARNING: requested comp '{cid}' not found in {project_name} "
                f"(available: {list(by_id)})")
    return out

def _clear_caches(project: Path) -> None:
    \"\"\"Drop the Remotion bundle cache between projects so we don't bloat the
    Drive folder or hit stale bundles after dependency upgrades.\"\"\"
    for c in (project / "node_modules" / ".cache",
              project / ".remotion",
              project / "build"):
        if c.is_dir():
            shutil.rmtree(c, ignore_errors=True)

def batch_render() -> list[RenderResult]:
    results: list[RenderResult] = []
    projects = detect_projects()
    if not projects:
        log("No projects to render. Aborting.")
        return results

    total_t0 = time.time()
    notify(f":movie_camera: Starting batch render of {len(projects)} project(s).")

    for i, project in enumerate(projects, 1):
        log("")
        log(f"=== [{i}/{len(projects)}] {project.name} ===")
        try:
            ensure_project_installed(project)
        except subprocess.CalledProcessError as e:
            err = f"npm install failed: {e}"
            log(f"  ✘ {err}")
            results.append(RenderResult(project.name, "", "", False, 0.0, 1, err))
            notify(f":x: `{project.name}` — npm install failed")
            continue

        entry = find_entry(project)
        if not entry:
            err = "No entry point found (looked for src/index.tsx, src/Root.tsx, ...)"
            log(f"  ✘ {err}")
            results.append(RenderResult(project.name, "", "", False, 0.0, 1, err))
            notify(f":x: `{project.name}` — {err}")
            continue
        log(f"  entry: {entry.relative_to(project)}")

        try:
            comps = list_compositions(project, entry)
        except Exception as e:
            err = f"`remotion compositions` failed: {e}"
            log(f"  ✘ {err}")
            results.append(RenderResult(project.name, "", "", False, 0.0, 1, err))
            notify(f":x: `{project.name}` — {err}")
            continue

        picked = _picked_compositions(project.name, comps)
        if not picked:
            log(f"  no compositions to render in {project.name}, skipping")
            continue
        log(f"  compositions: {[c['id'] for c in picked]}")

        for comp in picked:
            r = render_composition(project, entry, comp)
            results.append(r)
            if r.ok:
                notify(f":white_check_mark: `{r.project}/{r.composition}` -> {r.output}")
            else:
                notify(f":x: `{r.project}/{r.composition}` failed after "
                       f"{r.attempts} attempt(s):\\n```{r.error[:1500]}```")

        _clear_caches(project)

    dt = time.time() - total_t0
    ok = sum(1 for r in results if r.ok)
    bad = len(results) - ok
    log("")
    log("=" * 60)
    log(f"BATCH DONE in {timedelta(seconds=int(dt))} — {ok} ok, {bad} failed")
    for r in results:
        flag = "✔" if r.ok else "✘"
        log(f"  {flag} {r.project}/{r.composition}  {r.seconds:>6.1f}s  attempts={r.attempts}  -> {r.output}")
        if not r.ok and r.error:
            log(f"     last error: {r.error.splitlines()[-1] if r.error else ''}")
    notify(f":checkered_flag: Batch done in {timedelta(seconds=int(dt))} — {ok} ok, {bad} failed")
    return results
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Step 9 — Run it

Each completed render is written to Drive immediately, so even if Colab
disconnects mid-batch you keep the finished outputs.""",
    )
)

CELLS.append(
    cell(
        "code",
        """results = batch_render()
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Optional — Write a sample project to Drive

Useful if you just want to confirm the pipeline works end-to-end before you
upload your real projects. Creates `MyDrive/remotion-projects/SampleProject/`
with a tiny scene and the right `package.json` / `tsconfig.json`. After
running it, re-run **Step 9**.""",
    )
)

CELLS.append(
    cell(
        "code",
        """SAMPLE_FILES = {
    "package.json": '''{
  "name": "sample-remotion-project",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@remotion/cli": "4.0.462",
    "react": "19.2.0",
    "react-dom": "19.2.0",
    "remotion": "4.0.462"
  },
  "devDependencies": {
    "@types/node": "22.10.5",
    "@types/react": "19.0.7",
    "@types/react-dom": "19.0.3",
    "typescript": "5.7.3"
  }
}
''',
    "remotion.config.ts": '''import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(100);
Config.setCodec("h264");
Config.setCrf(16);
Config.setX264Preset("medium");
Config.setPixelFormat("yuv420p");
Config.setOverwriteOutput(true);
''',
    "tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "noEmit": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"]
  },
  "include": ["src/**/*", "remotion.config.ts"]
}
''',
    "src/index.tsx": '''import { registerRoot } from "remotion";
import { Root } from "./Root";

registerRoot(Root);
''',
    "src/Root.tsx": '''import { Composition } from "remotion";
import { SampleScene } from "./Composition";

export const Root: React.FC = () => (
  <Composition
    id="SampleScene"
    component={SampleScene}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
  />
);
''',
    "src/Composition.tsx": '''import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

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
''',
}

def write_sample_project(name: str = "SampleProject") -> Path:
    dest = CONFIG["projects_root"] / name
    dest.mkdir(parents=True, exist_ok=True)
    for rel, content in SAMPLE_FILES.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    log(f"Wrote sample project to {dest}")
    return dest

write_sample_project()
""",
    )
)

CELLS.append(
    cell(
        "markdown",
        """## Troubleshooting

- **"`remotion: command not found`"** — `npm install` didn't complete. Re-run
  Step 6 manually: `subprocess.run(["npm", "ci"], cwd=project, check=True)`.
- **Render dies with `Failed to launch the browser process`** — usually a
  missing system lib. Re-run Step 2; the apt install list covers the libs
  Remotion's Chrome shell needs on Ubuntu/Debian.
- **Render is slow** — bump `CONFIG["concurrency"]` if your runtime has more
  vCPUs (Colab Pro / Pro+). On a 2-vCPU free runtime, a 1080p 30fps 20s clip
  takes ~10–15 min depending on scene complexity. Switching to a GPU runtime
  speeds up the *Chrome rendering* side (`gl_backend="angle"`), but H.264
  encoding is CPU-bound unless `h264_nvenc` is available (rare on Colab).
- **"`Cannot find module 'X'`"** when listing compositions — usually a
  package-lock mismatch on Drive. Delete `node_modules/.colab_install_hash`
  in that project to force a clean `npm ci`.
- **Drive write errors mid-render** — Remotion writes the final MP4 in one
  shot, so a Drive hiccup near the end can leave a partial file. Re-running
  the batch will redo only the missing/empty outputs (because of
  `skip_existing`).
- **Colab disconnects** — you'll lose the runtime but every finished MP4 is
  already on Drive. Reconnect, re-mount Drive, re-run Step 9; finished
  projects are skipped automatically.
""",
    )
)


# ---------------------------------------------------------------------------
# Notebook envelope
# ---------------------------------------------------------------------------

NOTEBOOK = {
    "cells": CELLS,
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}


def main() -> None:
    out = Path(__file__).resolve().parent / "RemotionBatchRender.ipynb"
    out.write_text(json.dumps(NOTEBOOK, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {out} ({out.stat().st_size:,} bytes, {len(CELLS)} cells)")


if __name__ == "__main__":
    main()
