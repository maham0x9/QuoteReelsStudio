"""Pexels Video API client.

Docs: https://www.pexels.com/api/documentation/#videos
"""
from __future__ import annotations

import logging

import requests

from app.models import BackgroundOption

from .base import BackgroundProvider

LOG = logging.getLogger(__name__)
PEXELS_SEARCH = "https://api.pexels.com/videos/search"


class PexelsClient(BackgroundProvider):
    name = "pexels"

    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, per_page: int = 10) -> list[BackgroundOption]:
        if not self.is_configured:
            return []
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "portrait",
            "size": "medium",
        }
        try:
            r = requests.get(PEXELS_SEARCH, headers=headers, params=params, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            LOG.warning("Pexels search failed for %r: %s", query, e)
            return []
        data = r.json()
        out: list[BackgroundOption] = []
        for v in data.get("videos", []):
            files = v.get("video_files", [])
            # pick the highest-resolution portrait .mp4 we can
            portrait = [f for f in files if (f.get("height") or 0) >= (f.get("width") or 0)]
            files_sorted = sorted(
                portrait or files,
                key=lambda f: (f.get("height") or 0) * (f.get("width") or 0),
                reverse=True,
            )
            best = files_sorted[0] if files_sorted else None
            if not best or not best.get("link"):
                continue
            pic = v.get("image") or ""
            out.append(
                BackgroundOption(
                    provider=self.name,
                    video_id=str(v.get("id")),
                    preview_url=pic,
                    download_url=best["link"],
                    width=int(best.get("width") or 1080),
                    height=int(best.get("height") or 1920),
                    duration=float(v.get("duration") or 0.0),
                )
            )
        return out
