"""Mixes the Pexels + Pixabay providers, dedupes results across quotes,
and handles cached downloads of preview thumbs and full clips.
"""
from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path

import requests

from app.config import AppConfig, get_config
from app.models import BackgroundOption

from .base import BackgroundProvider, extract_keywords
from .pexels import PexelsClient
from .pixabay import PixabayClient

LOG = logging.getLogger(__name__)


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


class BackgroundManager:
    """High-level interface used by the UI / batch worker."""

    def __init__(self, cfg: AppConfig | None = None):
        self.cfg = cfg or get_config()
        self.providers: list[BackgroundProvider] = []
        if self.cfg.pexels_api_key:
            self.providers.append(PexelsClient(self.cfg.pexels_api_key))
        if self.cfg.pixabay_api_key:
            self.providers.append(PixabayClient(self.cfg.pixabay_api_key))
        self._used_ids: set[tuple[str, str]] = set()
        self._lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        return any(p.is_configured for p in self.providers)

    def last_errors(self) -> str:
        """Return a joined human-readable string of the last error for each provider."""
        msgs = [getattr(p, "last_error", "") for p in self.providers]
        return " · ".join(m for m in msgs if m)

    def reset_dedupe(self) -> None:
        with self._lock:
            self._used_ids.clear()

    def search(
        self,
        quote_text: str,
        count: int = 5,
        avoid_duplicates: bool = True,
        extra_keywords: str = "",
    ) -> list[BackgroundOption]:
        keywords = extract_keywords(quote_text)
        query = f"{keywords} {extra_keywords}".strip()
        results: list[BackgroundOption] = []
        for provider in self.providers:
            try:
                results.extend(provider.search(query, per_page=count * 2))
            except Exception as e:  # pragma: no cover - network errors
                LOG.exception("Provider %s failed: %s", provider.name, e)
        if not results:
            return []

        # interleave providers so we don't return only Pexels then only Pixabay
        by_provider: dict[str, list[BackgroundOption]] = {}
        for r in results:
            by_provider.setdefault(r.provider, []).append(r)
        interleaved: list[BackgroundOption] = []
        max_len = max((len(v) for v in by_provider.values()), default=0)
        for i in range(max_len):
            for prov in by_provider:
                bucket = by_provider[prov]
                if i < len(bucket):
                    interleaved.append(bucket[i])

        out: list[BackgroundOption] = []
        with self._lock:
            for opt in interleaved:
                key = (opt.provider, opt.video_id)
                if avoid_duplicates and key in self._used_ids:
                    continue
                out.append(opt)
                self._used_ids.add(key)
                if len(out) >= count:
                    break
        return out

    # --- caching / downloads ------------------------------------------------
    def cache_thumb(self, opt: BackgroundOption) -> str:
        if opt.thumb_path and Path(opt.thumb_path).exists():
            return opt.thumb_path
        if not opt.preview_url:
            return ""
        ext = ".jpg"
        name = f"{opt.provider}_{opt.video_id}{ext}"
        dest = self.cfg.cache_path / "thumbs" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            try:
                r = requests.get(opt.preview_url, timeout=6)
                r.raise_for_status()
                dest.write_bytes(r.content)
            except requests.RequestException as e:
                LOG.warning("Thumb download failed for %s: %s", opt.preview_url, e)
                return ""
        opt.thumb_path = str(dest)
        return opt.thumb_path

    def download(self, opt: BackgroundOption, progress_cb=None) -> str:
        if opt.local_path and Path(opt.local_path).exists():
            return opt.local_path
        url = opt.download_url
        ext = ".mp4"
        name = f"{opt.provider}_{opt.video_id}_{_hash(url)}{ext}"
        dest = self.cfg.cache_path / "clips" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0:
            opt.local_path = str(dest)
            return opt.local_path
        tmp = dest.with_suffix(".part")
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                done = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue
                        f.write(chunk)
                        done += len(chunk)
                        if progress_cb and total:
                            progress_cb(done / total)
            tmp.replace(dest)
        except requests.RequestException as e:
            LOG.error("Clip download failed for %s: %s", url, e)
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            return ""
        opt.local_path = str(dest)
        return opt.local_path
