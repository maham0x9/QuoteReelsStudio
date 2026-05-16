# Remotion Batch Renderer for Google Colab

Render every Remotion project under a Google Drive folder to high-quality
**1920x1080 H.264 MP4** files, sequentially and unattended. Designed to
survive Colab idle disconnects, retry transient failures, and produce
stock-marketplace-ready output (Shutterstock / Adobe Stock / Pond5 /
Vecteezy / 123RF).

## Files

| File                                  | Purpose                                                                 |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `RemotionBatchRender.ipynb`           | The Colab notebook. Open it in Colab and run cells top to bottom.       |
| `build_notebook.py`                   | Generator that produced the notebook. Edit cell sources here, not the .ipynb. |
| `sample-project/`                     | A minimal valid Remotion project used by the notebook's "sample" cell.  |

## Quick start

1. Upload **`RemotionBatchRender.ipynb`** to Google Colab (File → Upload notebook).
2. Run the first cell to mount Google Drive.
3. Run the install cell. Node 20 LTS, FFmpeg, and Chrome libs install in ~30s.
4. Edit the `CONFIG` cell if you want to change paths, render specs, project
   selection, retries, or webhook URL.
5. Run the rest of the cells. Outputs appear in
   `MyDrive/remotion-renders/<project>/<composition>.mp4`.

If you don't have any projects on Drive yet, scroll to the
**"Optional — Write a sample project to Drive"** cell and run it. It writes a
ready-to-render `SampleProject` to your Drive so you can confirm the pipeline
works end-to-end.

## Folder structure (on Drive)

```
MyDrive/
├── remotion-projects/
│   ├── ProjectA/
│   │   ├── package.json           # MUST list `remotion` in dependencies
│   │   ├── remotion.config.ts     # optional
│   │   ├── tsconfig.json          # optional
│   │   ├── src/
│   │   │   ├── index.tsx          # entry: must call registerRoot(...)
│   │   │   ├── Root.tsx
│   │   │   └── Composition.tsx
│   │   ├── public/                # optional; served by Remotion
│   │   └── assets/                # optional
│   └── ProjectB/...
└── remotion-renders/              # created automatically
    └── ProjectA/SampleScene.mp4
```

A folder counts as a valid project iff its `package.json` declares
`remotion` (or `@remotion/cli`) as a dependency. Anything else is skipped
with a warning.

## What the notebook does

1. **Mount Drive** — `google.colab.drive.mount('/content/drive')`.
2. **Install system deps** — Node 20 LTS, FFmpeg, Chrome runtime libraries
   (`libnss3`, `libgtk-3-0`, `libgbm1`, …) that Remotion's headless Chrome
   shell links against on Ubuntu/Debian.
3. **`CONFIG`** — single dict of constants: paths, render specs, concurrency,
   GL backend, NVENC toggle, project/composition selection, retry count,
   timeout, webhook URL.
4. **Detect projects** — lists every valid project folder under
   `projects_root`. Honors `CONFIG["only"]` for filtering.
5. **Install per-project deps** — `npm ci` (preferred) or `npm install`.
   Cached by SHA of `package-lock.json` so re-running is a no-op when
   nothing changed.
6. **List + render compositions** — `npx remotion compositions` to discover
   every comp, then `npx remotion render` per comp with the flags from
   `CONFIG`. Streams progress to the cell output once per second.
7. **Retry + continue** — on failure, retries once (configurable). A failed
   project never blocks the rest of the batch.
8. **Webhook (optional)** — POSTs to a Slack/Discord incoming-webhook URL on
   every success/failure and on batch completion.
9. **Summary** — final table with per-render duration, attempts, and output
   path. All rendered MP4s are already on Drive, so a runtime kill at the
   end doesn't lose work.

## Defaults

| Setting        | Value         | Notes                                                  |
| -------------- | ------------- | ------------------------------------------------------ |
| Resolution     | 1920x1080     | Override via `CONFIG["width"]`, `CONFIG["height"]`     |
| FPS            | 30            |                                                        |
| Codec          | `h264`        |                                                        |
| CRF            | 16            | 14–18 is visually lossless for stock                   |
| x264 preset    | `medium`      | `slow` produces smaller files, slower                  |
| Pixel format   | `yuv420p`     | Required by Shutterstock / Adobe Stock                 |
| JPEG quality   | 100           | Frame source quality (no banding)                      |
| Concurrency    | `cpu_count()` | Bump on Colab Pro / Pro+                               |
| GL backend     | `swangle`     | Stable in Colab; try `angle` on a GPU runtime          |
| NVENC          | auto-detected | Only if `ffmpeg -encoders` lists `h264_nvenc`          |
| Retry          | 1 extra       | After the first failure                                |
| Per-render TTL | 90 min        | Hard timeout; kills the renderer                       |
| Skip existing  | True          | Re-runs are incremental                                |

## Performance

| Runtime           | 20s 1080p clip      | Notes                              |
| ----------------- | ------------------- | ---------------------------------- |
| Free (2 vCPU)     | ~12–18 min          | preset=medium, crf=16              |
| Colab Pro (4 vCPU)| ~6–10 min           | bump `concurrency` to 4            |
| GPU (T4)          | similar to Pro      | speeds up Chrome render, not x264  |

The H.264 encoder is CPU-bound. A GPU runtime helps with the *Chrome*
rendering side (`gl_backend="angle"`), but won't speed up x264 unless
`h264_nvenc` is available (rare on Colab — Remotion will use software x264
either way).

## Editing the notebook

Don't hand-edit `RemotionBatchRender.ipynb` — its cells are long Python
strings and the JSON escaping is painful. Edit `build_notebook.py` instead
and regenerate:

```bash
python build_notebook.py
```

`build_notebook.py` writes a valid Jupyter notebook compatible with both
Google Colab and standard Jupyter.

## Sample project

`sample-project/` is the same minimal scene that the
"Write a sample project to Drive" cell writes. You can copy it into your
own Drive folder structure as a starting point:

```
remotion/colab/sample-project/
├── package.json
├── remotion.config.ts
├── tsconfig.json
└── src/
    ├── index.tsx
    ├── Root.tsx
    └── Composition.tsx
```

## Commercial safety

All sample assets in this folder are original geometric / gradient motion —
no logos, brand names, trademarks, IDE chrome, or copyrighted UI elements.
Your own projects are your responsibility; the renderer doesn't inspect
them.

## License & support

Same license as the repo root. Open an issue on the repo for bugs or feature
requests.
