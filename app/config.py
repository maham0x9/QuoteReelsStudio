"""Application configuration loader.

Reads ``config.json`` next to the project root and overlays environment
variables (``PEXELS_API_KEY``, ``PIXABAY_API_KEY``, ``QRS_FFMPEG_PATH``).
A ``config.local.json`` next to ``config.json`` is also merged when present
so users can keep secrets out of source control.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class AppConfig:
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    default_resolution: tuple[int, int] = (1080, 1920)
    default_fps: int = 30
    default_bitrate: str = "8M"
    default_clip_duration: float = 8.0
    ffmpeg_path: str = ""
    music_dir: str = "app/assets/music"
    fonts_dir: str = "app/assets/fonts"
    projects_dir: str = "projects"
    cache_dir: str = "cache"
    _path: Path = field(default_factory=lambda: _project_root() / "config.json")

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        cfg_path = path or (_project_root() / "config.json")
        data: dict[str, Any] = {}
        if cfg_path.exists():
            data.update(json.loads(cfg_path.read_text(encoding="utf-8")))
        local = cfg_path.with_name("config.local.json")
        if local.exists():
            data.update(json.loads(local.read_text(encoding="utf-8")))

        # env overrides
        env_map = {
            "PEXELS_API_KEY": "pexels_api_key",
            "PIXABAY_API_KEY": "pixabay_api_key",
            "QRS_FFMPEG_PATH": "ffmpeg_path",
        }
        for env_key, field_name in env_map.items():
            val = os.environ.get(env_key)
            if val:
                data[field_name] = val

        if "default_resolution" in data and isinstance(data["default_resolution"], list):
            data["default_resolution"] = tuple(data["default_resolution"])  # type: ignore[assignment]

        known = {f for f in cls.__dataclass_fields__ if not f.startswith("_")}
        clean = {k: v for k, v in data.items() if k in known}
        cfg = cls(**clean)
        cfg._path = cfg_path
        return cfg

    def save(self) -> None:
        out = {k: v for k, v in asdict(self).items() if not k.startswith("_")}
        out["default_resolution"] = list(out["default_resolution"])
        self._path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # absolute paths derived from project root
    def abs_path(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (_project_root() / p)

    @property
    def music_path(self) -> Path:
        p = self.abs_path(self.music_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def fonts_path(self) -> Path:
        p = self.abs_path(self.fonts_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def projects_path(self) -> Path:
        p = self.abs_path(self.projects_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cache_path(self) -> Path:
        p = self.abs_path(self.cache_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


_CONFIG: AppConfig | None = None


def get_config() -> AppConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = AppConfig.load()
    return _CONFIG


def reload_config() -> AppConfig:
    global _CONFIG
    _CONFIG = AppConfig.load()
    return _CONFIG
