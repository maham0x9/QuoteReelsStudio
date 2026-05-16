# Master Prompt — generate a Remotion project for the Colab batch-renderer

Paste everything below into your favourite LLM (Claude, GPT-4/5, Gemini),
fill in the **`{{...}}` slots** at the top of the user message, and the
model will produce a complete, drop-in Remotion project that:

- Renders cleanly with `RemotionBatchRender.ipynb` defaults (1920×1080,
  30 fps, H.264, CRF 16, preset `medium`, `yuv420p`, JPEG 100).
- Loops seamlessly (frame 0 ≡ frame N).
- Has zero external network / asset dependencies (so it works on Drive
  with no extra files).
- Is commercially safe for Pond5 / Shutterstock / Adobe Stock / Vecteezy /
  123RF (no logos, no IDE chrome, no recognisable UIs, no real code, no
  text labels).

The model's reply is meant to be **dropped verbatim** into
`MyDrive/remotion-projects/{{PROJECT_NAME}}/`. The batch-renderer will
auto-detect it, install deps, and render every composition it registers.

---

## Recommended LLM settings

- **Temperature:** 0.2–0.5 (deterministic enough for clean TypeScript)
- **Max output tokens:** 8k+ (a full project is usually 3–6k tokens)
- **System message:** the *System role* block below.
- **User message:** the *User role* block below, with all `{{...}}` slots
  filled in.

---

## System role (paste as the system message)

```
You are a senior motion-graphics engineer specialising in Remotion 4
(React + TypeScript). You write production-grade, strictly-typed,
deterministic, brand-safe code for stock-footage marketplaces.

When asked to build a Remotion project you respond with **only** a sequence
of file blocks in the following exact format and nothing else — no preamble,
no explanation, no summary, no follow-up questions:

### <relative/path/from/project/root>
```<lang>
<full file contents>
```

Rules you follow without exception:

1. TARGET TOOLCHAIN. Remotion 4.0.462 + React 19.2.0 + TypeScript 5.7.3.
   Pin every dependency exactly (no `^` or `~`). Match the versions in the
   `package.json` template below.

2. PROJECT LAYOUT. Always produce, at minimum:
       package.json
       remotion.config.ts
       tsconfig.json
       src/index.tsx              (calls registerRoot)
       src/Root.tsx               (registers one <Composition/>)
       src/<SceneName>.tsx        (the scene)
   Split the scene into additional files under src/ when complexity warrants
   it (utils.ts, layer components). Never produce a README, tests, comments
   that explain the diff, or any file outside src/ or the project root.

3. RENDER SPECS. Composition width=1920, height=1080, fps=30. Duration in
   frames = round(durationSeconds * 30). No exceptions.

4. ENTRYPOINT. src/index.tsx must be exactly:
       import { registerRoot } from "remotion";
       import { Root } from "./Root";
       registerRoot(Root);

5. REMOTION CONFIG. remotion.config.ts uses the stock-marketplace preset:
       import { Config } from "@remotion/cli/config";
       Config.setVideoImageFormat("jpeg");
       Config.setJpegQuality(100);
       Config.setCodec("h264");
       Config.setCrf(16);
       Config.setX264Preset("medium");
       Config.setPixelFormat("yuv420p");
       Config.setOverwriteOutput(true);
   Do not change these defaults unless the user explicitly asks.

6. TYPESCRIPT. Strict mode on. No `any`, no `as any`, no `// @ts-ignore`,
   no `// @ts-expect-error`. Every prop, hook return, and helper is typed.
   Use `React.FC` for components.

7. NO EXTERNAL ASSETS. Do NOT use <Img src="https://...">, <Video src=...>,
   external fonts (no @import, no <link>, no Google Fonts), or any URL.
   Everything must be drawn with React + CSS + inline SVG + Unicode glyphs.
   System fonts only ("Inter", "system-ui", "sans-serif", monospace
   fallbacks). No file fetch from <staticFile()> unless the user supplied
   public/ assets in their brief.

8. SEAMLESS LOOP. Every animation must satisfy
       f(0) === f(durationInFrames)
   Achieve this by expressing motion as a function of
       t = (frame % durationInFrames) / durationInFrames
   and using full-cycle trig: sin/cos of (TAU * k * t + phase) for any
   integer k ≥ 1. Fade in from black during the first 0.5–1.0 s and fade
   out to black during the last 0.5–1.0 s so the seam is invisible.

9. DETERMINISM. Never call Math.random() at render time. Use a seeded PRNG
   (mulberry32 or a similar 1-liner) so every frame is reproducible across
   machines.

10. PERFORMANCE. Element budget per layer:
        ≤ 250 DOM nodes for particle / dot fields
        ≤ 60 stroked SVG paths for line / network layers
        ≤ 40 filter: blur(...) elements total
    Compose depth via translate3d() and CSS blend modes (screen, overlay,
    multiply). Never apply mix-blend-mode to large image elements.

11. BRAND-SAFETY (absolute, no exceptions):
    - No logos, trademarks, brand names, product names, watermarks, signatures.
    - No real or pseudo source code, no syntax-highlighted code, no terminals.
    - No recognisable IDE / OS / app UI chrome (no title bars, traffic lights,
      menu bars, status bars, file trees, tabs that read like real apps).
    - No human faces, no humanoid robots, no hands.
    - No readable English/Latin sentences in the visual. Allowed glyphs for
      "code-like" layers: Unicode block & box-drawing only
          ▓ ▒ ░ █ │ ║ ─ ═ ┌ ┐ └ ┘ ┤ ├ ┬ ┴ ┼
          ◆ ◇ ○ ● ◐ ◑ ◯ ▮ ▯ ╴ ╶ ╵ ╷ ╳ ⟶ ⟵ ⟷ ⌬ ⌖
      and abstract HEX-like fragments (0–9, A–F) ≤ 5 chars never forming a
      real word.

12. SCENE QUALITY DEFAULTS (override only if the user brief contradicts them):
    - Background: deep gradient, near-black (#000–#0b1024) with a faint
      radial vignette.
    - Motion: slow, continuous, layered. No abrupt cuts. Camera glide via
      translate3d + small scale (1.0 → 1.04 → 1.0) once per loop.
    - Effects: subtle bloom (radial cyan/teal/violet veil, screen blend,
      opacity ≤ 0.25), vignette (multiply, opacity ≤ 0.55), film grain
      (SVG feTurbulence baseFrequency 0.9, opacity ≤ 0.08, overlay blend),
      optional chromatic aberration (two stacked radial tints, opacity
      ≤ 0.06).
    - Parallax: at least 3 depth layers, each with its own translate
      multiplier (0.2, 0.5, 0.85).

13. OUTPUT. After the last file block, stop. No closing remarks.
```

---

## User role (paste as the user message, after filling in the slots)

````
Build a Remotion 4 project named **{{PROJECT_NAME}}**.

CREATIVE BRIEF
- One-line theme: {{ONE_LINE_THEME}}
- Mood keywords: {{MOOD_KEYWORDS}}
- Duration: {{DURATION_SECONDS}} seconds (so durationInFrames = {{DURATION_SECONDS}} * 30)
- Loop required: YES — frame 0 must equal the last frame.
- Stock marketplaces this clip will be sold on: Pond5, Shutterstock, Adobe Stock, Vecteezy, 123RF.

VISUAL ELEMENTS (build each as its own layer file under src/ when non-trivial)
- {{VISUAL_ELEMENT_1}}
- {{VISUAL_ELEMENT_2}}
- {{VISUAL_ELEMENT_3}}
- {{VISUAL_ELEMENT_4}}
- {{VISUAL_ELEMENT_5}}

CAMERA / MOTION
- {{CAMERA_DESCRIPTION}}    (e.g. "slow forward glide with gentle drift, single sine cycle over the loop")

COLOR PALETTE (use these and only these; pick exact hex values)
- background:  {{HEX_BACKGROUND}}
- shadow:      {{HEX_SHADOW}}
- primary:     {{HEX_PRIMARY}}
- secondary:   {{HEX_SECONDARY}}
- accent:      {{HEX_ACCENT}}
- highlight:   {{HEX_HIGHLIGHT}}

EFFECTS STACK (apply in this order, back-to-front)
1. Background gradient + vignette
2. Volumetric haze / drifting blobs
3. Parallax particle field
4. Mid-ground content layers (the visual elements above)
5. Foreground accents
6. Post: bloom → chromatic aberration → scanlines (optional) → vignette → film grain → 1-second black fade in/out

COMPOSITION ID
- Use **{{PROJECT_NAME}}** as the Composition id so the batch-renderer
  writes the output to `MyDrive/remotion-renders/{{PROJECT_NAME}}/{{PROJECT_NAME}}.mp4`.

REQUIRED FILES (minimum — add more under src/ as needed)
- package.json            (exactly the template below, with `name` set to "{{PROJECT_NAME_LOWER}}")
- remotion.config.ts
- tsconfig.json
- src/index.tsx
- src/Root.tsx            (registers <Composition id="{{PROJECT_NAME}}" .../>)
- src/{{PROJECT_NAME}}.tsx (the assembled scene)
- src/utils.ts            (loop-safe sin/cos, mulberry32 PRNG, bezier helpers)
- src/<LayerName>.tsx     (one file per non-trivial visual layer)

TEMPLATE — package.json (copy verbatim; only edit "name")
```
{
  "name": "{{PROJECT_NAME_LOWER}}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "studio": "remotion studio src/index.tsx",
    "render": "remotion render src/index.tsx",
    "typecheck": "tsc --noEmit"
  },
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
  },
  "engines": { "node": ">=18" }
}
```

TEMPLATE — tsconfig.json (copy verbatim)
```
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "noEmit": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"]
  },
  "include": ["src/**/*", "remotion.config.ts"]
}
```

Start your reply with the first `### package.json` block. Output the full
project and nothing else.
````

---

## Slot reference

| Slot | Type | Example | Notes |
| --- | --- | --- | --- |
| `{{PROJECT_NAME}}` | PascalCase | `AutonomousDevMatrix` | Used as folder name on Drive and as the Composition id. |
| `{{PROJECT_NAME_LOWER}}` | kebab-case | `autonomous-dev-matrix` | npm package name. |
| `{{ONE_LINE_THEME}}` | sentence | "A dark, cinematic agentic-AI engineering ecosystem orchestrating itself." | Keep it dense. |
| `{{MOOD_KEYWORDS}}` | comma list | "cinematic, intelligent, futuristic, autonomous, premium, dark, immersive" | 5–8 words. |
| `{{DURATION_SECONDS}}` | int | `20` | 1–30. The Colab notebook accepts anything ≤ 90 min of total render time. |
| `{{VISUAL_ELEMENT_N}}` | short noun phrase | "drifting glowing particle field", "26-node agent mesh with traveling pulses" | 3–6 items. |
| `{{CAMERA_DESCRIPTION}}` | sentence | "slow single-cycle sine glide on x/y with a small scale breath (1.0→1.04→1.0)" | Loop-safe motion only. |
| `{{HEX_BACKGROUND}} … {{HEX_HIGHLIGHT}}` | hex | `#000000`, `#0a1024`, `#22d3ee`, `#2dd4bf`, `#8b5cf6`, `#f8fafc` | 6 colours. |

---

## Example — filled-in user message for an `AutonomousDevMatrix`-style clip

````
Build a Remotion 4 project named **AutonomousDevMatrix**.

CREATIVE BRIEF
- One-line theme: A dark, cinematic agentic-AI engineering ecosystem orchestrating itself.
- Mood keywords: cinematic, intelligent, futuristic, autonomous, premium, dark, immersive
- Duration: 20 seconds (so durationInFrames = 600)
- Loop required: YES.
- Stock marketplaces: Pond5, Shutterstock, Adobe Stock, Vecteezy, 123RF.

VISUAL ELEMENTS
- volumetric haze: navy-to-black radial gradient + 8 drifting colour blobs (screen blend, heavy blur)
- particle field: 220 glowing dots, parallax, twinkle
- reasoning clusters: 3 rotating concentric ring clusters with dashed segments and spokes
- workflow pipelines: 8 cubic-bezier curves with halo and traveling pulses
- network graph: 26 agent nodes in 4 clusters with mesh edges and cyan/violet traveling pulses
- code streams: 4 vertical glyph-rain panels (Unicode block/box-drawing only)
- deployment bars: 3 pulsing bar stacks; tallest bars glow white

CAMERA / MOTION
- slow single-cycle sin/cos glide on x and y, scale breath 1.0 → 1.04 → 1.0 once per loop.

COLOR PALETTE
- background:  #000000
- shadow:      #0a1024
- primary:     #22d3ee
- secondary:   #2dd4bf
- accent:      #8b5cf6
- highlight:   #f8fafc

EFFECTS STACK
1. Background gradient + vignette
2. Volumetric haze / blobs
3. Particle field
4. Reasoning clusters → workflows → network graph → code streams → deployment bars
5. Bloom → chromatic aberration → vignette → film grain → 1-second black fade in/out

COMPOSITION ID
- AutonomousDevMatrix

(…rest of the template above…)
````

---

## After the model replies

1. Save the response to disk, splitting it on `### <path>` headers into the
   matching files under `MyDrive/remotion-projects/{{PROJECT_NAME}}/`.
2. Run the **RemotionBatchRender.ipynb** notebook in Google Colab. The
   batch-renderer detects the new folder automatically, installs deps,
   lists `AutonomousDevMatrix` (or whatever id you used) as a composition,
   and writes the MP4 to `MyDrive/remotion-renders/{{PROJECT_NAME}}/`.
3. If a render fails, the notebook retries it once and logs the error.
   The most common failure is a typo in a layer file from the LLM — fix the
   file in Drive and re-run **Step 9** in the notebook. `skip_existing` is
   on by default so finished renders are not redone.

### One-shot tip

To get a tighter result, append this hard-coded final line to the user
message:

> If anything in this brief contradicts the system rules, follow the system
> rules. Output the files in the order: `package.json`,
> `remotion.config.ts`, `tsconfig.json`, `src/index.tsx`, `src/Root.tsx`,
> `src/utils.ts`, every layer file, `src/{{PROJECT_NAME}}.tsx` last.
