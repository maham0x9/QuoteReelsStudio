"""Domain models serialized to JSON project files."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class TextLayer:
    text: str = ""
    x: float = 0.1            # normalized 0..1 (left)
    y: float = 0.4            # normalized 0..1 (top)
    width: float = 0.8        # normalized 0..1
    height: float = 0.2       # normalized 0..1
    font_family: str = "Inter"
    font_size: int = 64       # rendered against a 1080x1920 canvas
    font_path: str = ""       # optional explicit ttf path
    color: str = "#FFFFFF"
    bold: bool = True
    italic: bool = False
    shadow: bool = True
    shadow_color: str = "#000000"
    shadow_offset: int = 4
    shadow_blur: int = 8
    stroke_width: int = 0
    stroke_color: str = "#000000"
    opacity: float = 1.0
    alignment: str = "center"  # left|center|right
    rotation: float = 0.0      # degrees
    line_spacing: float = 1.15

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TextLayer:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class BackgroundOption:
    provider: str            # "pexels" | "pixabay"
    video_id: str
    preview_url: str         # remote thumb / small clip
    download_url: str        # remote full HD vertical
    width: int = 1080
    height: int = 1920
    duration: float = 0.0
    local_path: str = ""     # filled after download
    thumb_path: str = ""     # local cached thumb

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BackgroundOption:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class VideoSettings:
    trim_start: float = 0.0
    trim_end: float = 0.0       # 0 means use full clip
    duration: float = 8.0       # final clip duration
    loop_short: bool = True
    blur_bg: bool = False
    blur_strength: int = 12
    dark_overlay: float = 0.35  # 0..1
    speed: float = 1.0
    music_path: str = ""
    music_volume: float = 0.6
    mute_original: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VideoSettings:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Quote:
    id: str = field(default_factory=_new_id)
    text: str = ""
    options: list[BackgroundOption] = field(default_factory=list)
    selected_index: int = 0
    text_layer: TextLayer = field(default_factory=TextLayer)
    video: VideoSettings = field(default_factory=VideoSettings)
    rendered_path: str = ""

    def selected_option(self) -> BackgroundOption | None:
        if not self.options:
            return None
        idx = max(0, min(self.selected_index, len(self.options) - 1))
        return self.options[idx]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "options": [o.to_dict() for o in self.options],
            "selected_index": self.selected_index,
            "text_layer": self.text_layer.to_dict(),
            "video": self.video.to_dict(),
            "rendered_path": self.rendered_path,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Quote:
        return cls(
            id=d.get("id", _new_id()),
            text=d.get("text", ""),
            options=[BackgroundOption.from_dict(o) for o in d.get("options", [])],
            selected_index=d.get("selected_index", 0),
            text_layer=TextLayer.from_dict(d.get("text_layer", {})),
            video=VideoSettings.from_dict(d.get("video", {})),
            rendered_path=d.get("rendered_path", ""),
        )


@dataclass
class Project:
    id: str = field(default_factory=_new_id)
    name: str = "Untitled Project"
    quotes: list[Quote] = field(default_factory=list)
    resolution: tuple[int, int] = (1080, 1920)
    fps: int = 30
    bitrate: str = "8M"
    template: str = ""           # name of saved template, if any
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "quotes": [q.to_dict() for q in self.quotes],
            "resolution": list(self.resolution),
            "fps": self.fps,
            "bitrate": self.bitrate,
            "template": self.template,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Project:
        return cls(
            id=d.get("id", _new_id()),
            name=d.get("name", "Untitled Project"),
            quotes=[Quote.from_dict(q) for q in d.get("quotes", [])],
            resolution=tuple(d.get("resolution", (1080, 1920))),  # type: ignore[arg-type]
            fps=d.get("fps", 30),
            bitrate=d.get("bitrate", "8M"),
            template=d.get("template", ""),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
        )


@dataclass
class StylePreset:
    name: str
    text_layer: TextLayer
    video: VideoSettings

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "text_layer": self.text_layer.to_dict(),
            "video": self.video.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StylePreset:
        return cls(
            name=d["name"],
            text_layer=TextLayer.from_dict(d.get("text_layer", {})),
            video=VideoSettings.from_dict(d.get("video", {})),
        )
