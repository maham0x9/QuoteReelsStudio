"""QThread workers wrapping the background API + render pipeline.

Keeping these in a dedicated module makes it easy to unit-test the
non-Qt logic without spinning up the GUI.
"""
from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, QThread, Signal

from app.api import BackgroundManager
from app.models import BackgroundOption, Quote
from app.render import RenderJob, RenderPipeline

LOG = logging.getLogger(__name__)


class SearchWorker(QObject):
    """Searches for backgrounds for a single quote."""
    finished = Signal(str, list)  # quote_id, list[BackgroundOption]
    failed = Signal(str, str)

    def __init__(self, manager: BackgroundManager, quote: Quote, count: int = 5):
        super().__init__()
        self.manager = manager
        self.quote = quote
        self.count = count

    def run(self) -> None:
        try:
            opts = self.manager.search(self.quote.text, count=self.count)
        except Exception as e:  # pragma: no cover
            LOG.exception("SearchWorker.search raised: %s", e)
            self.failed.emit(self.quote.id, str(e))
            return
        if not opts:
            err = self.manager.last_errors() or (
                "No results returned. Verify your Pexels / Pixabay API keys "
                "in Settings."
            )
            self.failed.emit(self.quote.id, err)
            return
        # Cache thumbs in parallel with a hard time budget so the UI never
        # hangs on a slow / unreachable preview server.
        from concurrent.futures import ThreadPoolExecutor, wait
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(self.manager.cache_thumb, o) for o in opts]
            wait(futs, timeout=8.0)
        self.finished.emit(self.quote.id, opts)


class DownloadWorker(QObject):
    progress = Signal(str, float)  # quote_id, 0..1
    finished = Signal(str, str)    # quote_id, local_path
    failed = Signal(str, str)

    def __init__(self, manager: BackgroundManager, quote_id: str, option: BackgroundOption):
        super().__init__()
        self.manager = manager
        self.quote_id = quote_id
        self.option = option

    def run(self) -> None:
        try:
            path = self.manager.download(
                self.option,
                progress_cb=lambda p: self.progress.emit(self.quote_id, p),
            )
            if path:
                self.finished.emit(self.quote_id, path)
            else:
                self.failed.emit(self.quote_id, "Download returned no path")
        except Exception as e:  # pragma: no cover
            LOG.exception("DownloadWorker failed: %s", e)
            self.failed.emit(self.quote_id, str(e))


class RenderBatchWorker(QObject):
    progress = Signal(float, str)
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, pipeline: RenderPipeline, jobs: list[RenderJob]):
        super().__init__()
        self.pipeline = pipeline
        self.jobs = jobs
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            outputs = self.pipeline.render_batch(
                self.jobs,
                progress_cb=lambda p, msg: self.progress.emit(p, msg),
                cancel_event=self.cancel_event,
            )
            self.finished.emit([str(p) for p in outputs])
        except Exception as e:  # pragma: no cover
            LOG.exception("RenderBatchWorker failed: %s", e)
            self.failed.emit(str(e))


def run_in_thread(worker: QObject, slot_name: str = "run") -> QThread:
    """Move ``worker`` to a fresh QThread, wire ``finished`` cleanup, and start."""
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(getattr(worker, slot_name))
    # Best-effort cleanup once worker emits a 'finished' signal
    if hasattr(worker, "finished"):
        worker.finished.connect(thread.quit)  # type: ignore[attr-defined]
    if hasattr(worker, "failed"):
        worker.failed.connect(thread.quit)  # type: ignore[attr-defined]
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
