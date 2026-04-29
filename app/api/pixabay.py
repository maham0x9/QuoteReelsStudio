"""Pixabay Video API client.

Docs: https://pixabay.com/api/docs/#api_videos
"""
from __future__ import annotations

import logging

import requests

from app.models import BackgroundOption

from .base import BackgroundProvider

LOG = logging.getLogger(__name__)
PIXABAY_VIDEOS = "https://pixabay.com/api/videos/"


class PixabayClient(BackgroundProvider):
    name = "pixabay"

    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self.timeout = timeout
        self.last_error: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, per_page: int = 10) -> list[BackgroundOption]:
        if not self.is_configured:
            return []
        # pixabay requires per_page >= 3
        per_page = max(3, min(per_page, 200))
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "video_type": "all",
            "safesearch": "true",
        }
        self.last_error = ""
        try:
            r = requests.get(PIXABAY_VIDEOS, params=params, timeout=self.timeout)
            if r.status_code in (400, 401, 403):
                self.last_error = (
                    f"Pixabay rejected the key ({r.status_code}). "
                    "Open Settings and verify the Pixabay API key."
                )
                LOG.warning(self.last_error)
                return []
            r.raise_for_status()
        except requests.RequestException as e:
            self.last_error = f"Pixabay: {e}"
            LOG.warning("Pixabay search failed for %r: %s", query, e)
            return []
        data = r.json()
        out: list[BackgroundOption] = []
        for v in data.get("hits", []):
            videos = v.get("videos", {})
            # Pick best quality but prefer portrait when available
            best = None
            best_score = -1
            for q_name in ("large", "medium", "small", "tiny"):
                f = videos.get(q_name)
                if not f or not f.get("url"):
                    continue
                h = int(f.get("height") or 0)
                w = int(f.get("width") or 0)
                portrait_bonus = 1.5 if h >= w else 1.0
                score = h * w * portrait_bonus
                if score > best_score:
                    best_score = score
                    best = f
            if not best:
                continue
            preview = best.get("thumbnail") or ""
            if not preview:
                pic = v.get("picture_id")
                if pic:
                    preview = f"https://i.vimeocdn.com/video/{pic}_295x166.jpg"
            out.append(
                BackgroundOption(
                    provider=self.name,
                    video_id=str(v.get("id")),
                    preview_url=preview,
                    download_url=best["url"],
                    width=int(best.get("width") or 1080),
                    height=int(best.get("height") or 1920),
                    duration=float(v.get("duration") or 0.0),
                )
            )
        return out
