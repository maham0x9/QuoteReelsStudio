"""Reusable style presets stored as JSON files."""
from __future__ import annotations

import json
from pathlib import Path

from app.config import AppConfig, get_config
from app.models import StylePreset, TextLayer, VideoSettings


def _default_presets() -> list[StylePreset]:
    return [
        StylePreset(
            name="Bold White Center",
            text_layer=TextLayer(
                font_family="Inter", font_size=72, color="#FFFFFF",
                bold=True, shadow=True, stroke_width=0, alignment="center",
                width=0.84, height=0.3, x=0.08, y=0.36,
            ),
            video=VideoSettings(blur_bg=False, dark_overlay=0.35, mute_original=True),
        ),
        StylePreset(
            name="Blurred BG, Stroke",
            text_layer=TextLayer(
                font_family="Inter", font_size=68, color="#FFFFFF", bold=True,
                stroke_width=2, stroke_color="#000000",
                width=0.86, height=0.28, x=0.07, y=0.4, alignment="center",
            ),
            video=VideoSettings(blur_bg=True, blur_strength=14, dark_overlay=0.25),
        ),
        StylePreset(
            name="Minimal Yellow",
            text_layer=TextLayer(
                font_family="Inter", font_size=64, color="#FFD23F", bold=True,
                shadow=True, alignment="center",
                width=0.84, height=0.26, x=0.08, y=0.42,
            ),
            video=VideoSettings(blur_bg=False, dark_overlay=0.45),
        ),
    ]


class TemplateStore:
    def __init__(self, cfg: AppConfig | None = None):
        self.cfg = cfg or get_config()

    @property
    def root(self) -> Path:
        p = self.cfg.projects_path / "templates"
        p.mkdir(parents=True, exist_ok=True)
        if not any(p.glob("*.json")):
            for preset in _default_presets():
                self._write(preset, p)
        return p

    def list(self) -> list[StylePreset]:
        out: list[StylePreset] = []
        for f in sorted(self.root.glob("*.json")):
            try:
                out.append(StylePreset.from_dict(json.loads(f.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, KeyError):
                continue
        return out

    def save(self, preset: StylePreset) -> Path:
        return self._write(preset, self.root)

    @staticmethod
    def _write(preset: StylePreset, root: Path) -> Path:
        safe = "".join(c for c in preset.name if c.isalnum() or c in "-_ ").strip() or "preset"
        path = root / f"{safe}.json"
        path.write_text(json.dumps(preset.to_dict(), indent=2), encoding="utf-8")
        return path

    def delete(self, name: str) -> bool:
        for f in self.root.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if data.get("name") == name:
                f.unlink()
                return True
        return False
