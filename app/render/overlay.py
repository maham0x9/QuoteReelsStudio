"""Render a TextLayer to a transparent PNG suitable for FFmpeg overlay.

We generate the overlay at the project's full canvas size so the FFmpeg
filtergraph can drop it on top of the (cropped/blurred) background without
any further geometry math.
"""
from __future__ import annotations

import logging
import textwrap
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.config import get_config
from app.models import TextLayer

LOG = logging.getLogger(__name__)


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, max(0, min(255, int(alpha * 255))))
    return (255, 255, 255, max(0, min(255, int(alpha * 255))))


def _font_candidates(family: str, bold: bool) -> Iterable[Path]:
    cfg = get_config()
    fonts_dir = cfg.fonts_path
    family_low = family.lower().replace(" ", "")
    suffix_bold = "bold" if bold else "regular"
    if fonts_dir.exists():
        for p in fonts_dir.glob("*.ttf"):
            yield p
        for p in fonts_dir.glob("*.otf"):
            yield p
    # OS fallbacks (best-effort cross-platform)
    common_dirs = [
        Path("C:/Windows/Fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".fonts",
    ]
    likely = [
        f"{family}.ttf", f"{family}-{suffix_bold.title()}.ttf",
        f"{family_low}.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf", "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    for d in common_dirs:
        if not d.exists():
            continue
        for name in likely:
            p = d / name
            if p.exists():
                yield p
        for p in d.rglob("*.ttf"):
            yield p


def _load_font(layer: TextLayer) -> ImageFont.FreeTypeFont:
    if layer.font_path and Path(layer.font_path).exists():
        try:
            return ImageFont.truetype(layer.font_path, layer.font_size)
        except OSError:
            pass
    for cand in _font_candidates(layer.font_family, layer.bold):
        try:
            return ImageFont.truetype(str(cand), layer.font_size)
        except OSError:
            continue
    LOG.warning("No suitable font found for %r, using PIL default", layer.font_family)
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph.strip():
            lines.append("")
            continue
        # Greedy word wrap measured against the actual font.
        words = paragraph.split()
        current = ""
        for w in words:
            trial = (current + " " + w).strip()
            bbox = font.getbbox(trial)
            width = bbox[2] - bbox[0]
            if width <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
    if not lines:
        # very narrow box: hard wrap by characters
        approx = max(8, int(max_width / max(8, font.size // 2)))
        lines = textwrap.wrap(text, width=approx) or [text]
    return lines


def render_text_layer(layer: TextLayer, canvas_size: tuple[int, int]) -> Image.Image:
    """Render the styled text and return an RGBA Pillow image at canvas_size."""
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    if not layer.text.strip():
        return canvas

    cw, ch = canvas_size
    box_w = max(1, int(layer.width * cw))
    box_h = max(1, int(layer.height * ch))
    box_x = int(layer.x * cw)
    box_y = int(layer.y * ch)

    font = _load_font(layer)
    pad = max(8, font.size // 4)
    inner_w = max(1, box_w - 2 * pad)
    lines = _wrap(layer.text, font, inner_w)

    line_h = int(font.size * layer.line_spacing)
    text_h = line_h * len(lines)
    text_layer_img = Image.new("RGBA", (box_w, max(box_h, text_h + 2 * pad)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer_img)

    color = _hex_to_rgba(layer.color, layer.opacity)
    stroke = _hex_to_rgba(layer.stroke_color, layer.opacity)
    shadow = _hex_to_rgba(layer.shadow_color, layer.opacity * 0.7)

    y = pad
    for line in lines:
        bbox = font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        if layer.alignment == "left":
            x = pad
        elif layer.alignment == "right":
            x = box_w - pad - line_w
        else:
            x = (box_w - line_w) // 2

        if layer.shadow:
            sh_img = Image.new("RGBA", text_layer_img.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh_img).text(
                (x + layer.shadow_offset, y + layer.shadow_offset),
                line, font=font, fill=shadow,
            )
            if layer.shadow_blur > 0:
                sh_img = sh_img.filter(ImageFilter.GaussianBlur(layer.shadow_blur))
            text_layer_img.alpha_composite(sh_img)

        if layer.stroke_width > 0:
            draw.text(
                (x, y), line, font=font, fill=color,
                stroke_width=layer.stroke_width, stroke_fill=stroke,
            )
        else:
            draw.text((x, y), line, font=font, fill=color)
        y += line_h

    if layer.rotation:
        text_layer_img = text_layer_img.rotate(
            -layer.rotation, resample=Image.BICUBIC, expand=True,
        )

    # paste centered onto box position
    paste_x = box_x + (box_w - text_layer_img.width) // 2
    paste_y = box_y + (box_h - text_layer_img.height) // 2
    canvas.alpha_composite(text_layer_img, (paste_x, paste_y))
    return canvas


def render_text_to_png(layer: TextLayer, canvas_size: tuple[int, int], out_path: Path) -> Path:
    img = render_text_layer(layer, canvas_size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path
