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

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # PowerShell:  .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### API keys

Either set environment variables:

```powershell
$env:PEXELS_API_KEY  = "…"
$env:PIXABAY_API_KEY = "…"
```

…or open `config.json` and fill the matching fields. A sibling
`config.local.json` (gitignored) is also merged if present.

* Pexels: free key at <https://www.pexels.com/api/>
* Pixabay: free key at <https://pixabay.com/api/docs/>

### Run

```bash
python main.py
```

### Build standalone Windows .exe

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

## License

MIT
