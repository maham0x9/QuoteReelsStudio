# QuoteReelsStudio

A lightweight Windows desktop app that mass-produces vertical quote videos
(TikTok / Reels / Shorts, 1080×1920) from text input. It auto-fetches stock
backgrounds from **Pexels** and **Pixabay**, lets you visually edit the
overlaid text Canva-style, and exports finished MP4s in batch via a single
FFmpeg invocation per video.

## Highlights

- **Quote input** — paste single or multiple quotes (blank-line separated)
  or import from `.txt` / `.csv`.
- **Auto background search** — every quote gets up to 5 *different*
  vertical clips. Cross-quote dedupe is on by default.
- **Canva-style editor** — drag, resize, rotate; full font / size / color /
  bold / shadow / stroke / opacity / alignment / rotation controls. A safe
  zone is overlaid so text stays clear of TikTok / Reels chrome.
- **Video controls** — trim, loop short clips, blur background, dark
  overlay, playback speed, music track + volume, mute originals.
- **Templates** — save reusable style presets and apply them to every
  quote in one click.
- **Timeline** — see per-quote duration plus the music track at the bottom,
  with batch render progress.
- **FFmpeg-backed render** — one ffmpeg process per clip via a complex
  filtergraph for speed; falls back to the bundled `imageio-ffmpeg` binary
  when no system FFmpeg is on PATH.
- **Standalone Windows build** — `python scripts/build_exe.py` produces a
  one-folder `.exe` distribution under `dist/QuoteReelsStudio/`.

## Project layout

```
QuoteReelsStudio/
├── main.py                 # entry point (python main.py)
├── config.json             # API keys + defaults (also reads PEXELS_API_KEY / PIXABAY_API_KEY env vars)
├── QuoteReelsStudio.spec   # PyInstaller spec
├── scripts/build_exe.py    # one-line Windows build
├── app/
│   ├── api/                # Pexels + Pixabay clients + dedupe manager
│   ├── render/             # FFmpeg pipeline + Pillow text overlay
│   ├── store/              # JSON projects + style presets
│   ├── ui/                 # PySide6 panels (quotes / canvas / text / video / timeline)
│   └── assets/             # bundled fonts + music
└── projects/               # per-user JSON projects (gitignored)
```

## Setup (Windows, one-click)

1. Copy `.env.example` to `.env` and paste in your **Pexels** + **Pixabay**
   API keys.
2. Double-click **`run.bat`**. The first launch creates a local `.venv`,
   installs the Python dependencies, then opens the app. Subsequent
   launches skip straight to the app.

### Setup (manual)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PEXELS_API_KEY  = "…"
$env:PIXABAY_API_KEY = "…"
python main.py
```

You can also fill `config.json` (or a sibling `config.local.json`) with the
keys instead of using environment variables.

* Pexels: free key at <https://www.pexels.com/api/>
* Pixabay: free key at <https://pixabay.com/api/docs/>

### Build standalone Windows .exe

Double-click **`build.bat`**, or run manually:

```powershell
pip install pyinstaller
python scripts/build_exe.py
```

The bundle lands in `dist/QuoteReelsStudio/QuoteReelsStudio.exe` and ships
with the `imageio-ffmpeg` FFmpeg binary so end users do not need to install
anything else.

## Workflow

1. Paste / import quotes in the **left panel** (one per blank-line block).
2. The app searches Pexels + Pixabay and shows 3-5 background tiles per
   quote in the bottom-center strip. Click any tile to preview.
3. Edit text on the **center canvas** — drag, resize, rotate; tweak the
   style on the **right panel**.
4. Configure clip duration, blur, dark overlay, music, etc. on the
   **right-bottom Video panel**.
5. (Optional) `Project → Save current as template` and
   `Project → Apply template to all` for batch consistency.
6. Hit **Export Batch** in the bottom strip — choose an output folder and
   each quote renders to its own `001_*.mp4`, `002_*.mp4`, …

## Tests

```bash
QT_QPA_PLATFORM=offscreen pytest -q
```

CI runs lint (`ruff`) + the head-less Qt smoke test on every push.

## Remotion (4K 16:9 landscape videos)

A separate Remotion (Node) sub-project lives under `remotion/` for programmatic
4K landscape (3840×2160, 16:9) renders up to 20 seconds. It is independent of
the PySide6 app and does not affect the vertical TikTok/Reels pipeline.

```bash
cd remotion
npm install
npm run studio        # open Remotion Studio in the browser
npm run render        # render the Landscape4k composition to out/video.mp4
npm run typecheck     # tsc --noEmit
```

The composition defaults are configured in `remotion/src/Root.tsx`:
`Landscape4k` — 3840×2160, 30 fps, 600 frames (20 seconds).

## License

MIT
