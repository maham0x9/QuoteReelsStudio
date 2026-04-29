"""Main application window — minimal version.

Three-pane layout (quotes / canvas+backgrounds / text+video controls) plus
a thin top toolbar (Settings) and a bottom action bar (export + progress).
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.api import BackgroundManager
from app.config import get_config
from app.models import Project, Quote, TextLayer, VideoSettings
from app.render import RenderPipeline

from .backgrounds_panel import BackgroundsPanel
from .editor_canvas import EditorCanvas
from .quotes_panel import QuotesPanel
from .settings_dialog import SettingsDialog
from .styles import DARK_QSS
from .text_controls import TextControls
from .timeline import Timeline
from .video_controls import VideoControls
from .workers import DownloadWorker, RenderBatchWorker, SearchWorker, run_in_thread

LOG = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuoteReelsStudio")
        self.resize(1400, 880)
        self.setStyleSheet(DARK_QSS)

        self.cfg = get_config()
        self.project = Project()
        self.bg_manager = BackgroundManager(self.cfg)
        self.pipeline = RenderPipeline(self.cfg)

        self._active_quote_id: str = ""
        self._search_threads: list[QThread] = []
        self._render_thread: QThread | None = None
        self._render_worker: RenderBatchWorker | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._refresh_canvas_text)

        self._build_ui()
        self._build_toolbar()

        QTimer.singleShot(150, self._maybe_prompt_for_keys)

    # ---------------------------------------------------------------- layout
    def _build_ui(self) -> None:
        # left
        self.quotes_panel = QuotesPanel(self.project)

        # center
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(8)
        self.canvas = EditorCanvas(canvas_size=self.project.resolution)
        cv.addWidget(self.canvas, 5)
        self.backgrounds_panel = BackgroundsPanel()
        cv.addWidget(self.backgrounds_panel, 2)

        # right
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)
        self.text_controls = TextControls()
        rv.addWidget(self.text_controls, 3)
        self.video_controls = VideoControls()
        rv.addWidget(self.video_controls, 2)

        h_split = QSplitter(Qt.Horizontal)
        h_split.addWidget(self.quotes_panel)
        h_split.addWidget(center)
        h_split.addWidget(right)
        h_split.setStretchFactor(0, 2)
        h_split.setStretchFactor(1, 5)
        h_split.setStretchFactor(2, 2)
        h_split.setSizes([300, 780, 320])

        self.timeline = Timeline()

        root = QWidget()
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(h_split, 1)
        rl.addWidget(self.timeline)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

        # signals
        self.quotes_panel.quote_selected.connect(self._on_quote_selected)
        self.quotes_panel.quotes_changed.connect(self._on_quotes_changed)
        self.backgrounds_panel.option_selected.connect(self._on_option_selected)
        self.backgrounds_panel.regenerate_requested.connect(self._regenerate_current)
        self.text_controls.layer_changed.connect(self._on_layer_changed)
        self.video_controls.settings_changed.connect(self._on_video_changed)
        self.canvas.layer_changed.connect(self._on_canvas_layer_changed)
        self.timeline.export_requested.connect(self._export_batch)
        self.timeline.cancel_requested.connect(self._cancel_render)

    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(self._icon_size())
        self.addToolBar(Qt.TopToolBarArea, tb)

        title = QLabel("  QuoteReelsStudio  ")
        title.setStyleSheet(
            "color:#FFFFFF; font-weight:700; font-size:15px;"
            "padding: 4px 12px;"
        )
        tb.addWidget(title)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        settings_act = QAction("⚙  Settings", self)
        settings_act.setToolTip("Set Pexels and Pixabay API keys")
        settings_act.triggered.connect(self._open_settings)
        tb.addAction(settings_act)

    @staticmethod
    def _icon_size():
        from PySide6.QtCore import QSize
        return QSize(18, 18)

    # ---------------------------------------------------------------- helpers
    def _current_quote(self) -> Quote | None:
        for q in self.project.quotes:
            if q.id == self._active_quote_id:
                return q
        return self.project.quotes[0] if self.project.quotes else None

    def _set_status(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 5000)

    def _open_path(self, path: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as e:  # pragma: no cover
            self._set_status(f"Could not open {path}: {e}")

    # ---------------------------------------------------------------- settings
    def _maybe_prompt_for_keys(self) -> None:
        if not self.bg_manager.is_configured:
            QMessageBox.information(
                self, "Set API keys",
                "Add your Pexels and/or Pixabay API key from Settings to enable "
                "automatic background search.\n\nBoth are free.",
            )

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            # rebuild manager so new keys take effect
            self.bg_manager = BackgroundManager(self.cfg)
            if self.bg_manager.is_configured:
                self._set_status("API keys saved")
                QTimer.singleShot(50, self._search_missing)
            else:
                self._set_status("API keys cleared")

    # ---------------------------------------------------------------- quotes
    def _on_quotes_changed(self) -> None:
        self.timeline.set_project(self.project)
        if self.project.quotes and not self._active_quote_id:
            self._on_quote_selected(self.project.quotes[0].id)
        if self.bg_manager.is_configured:
            QTimer.singleShot(50, self._search_missing)

    def _on_quote_selected(self, quote_id: str) -> None:
        self._active_quote_id = quote_id
        q = self._current_quote()
        if not q:
            return
        if not q.text_layer.text:
            q.text_layer.text = q.text
        self.canvas.bind_quote(q)
        self.text_controls.bind(q.text_layer)
        self.video_controls.bind(q.video)
        opt = q.selected_option()
        if opt and opt.thumb_path:
            self.canvas.set_background_thumb(opt.thumb_path)
        else:
            self.canvas.set_background_thumb("")
        self.backgrounds_panel.set_options(q.options, q.selected_index)

    def _on_option_selected(self, index: int) -> None:
        q = self._current_quote()
        if not q or index < 0 or index >= len(q.options):
            return
        q.selected_index = index
        self.backgrounds_panel.set_selected(index)
        opt = q.options[index]
        if opt.thumb_path:
            self.canvas.set_background_thumb(opt.thumb_path)
        QTimer.singleShot(0, lambda: self._ensure_downloaded(q.id, opt))

    def _ensure_downloaded(self, quote_id: str, opt) -> None:
        if opt.local_path and Path(opt.local_path).exists():
            return
        worker = DownloadWorker(self.bg_manager, quote_id, opt)
        worker.finished.connect(lambda qid, p: self._set_status(f"Downloaded background for {qid}"))
        worker.failed.connect(lambda qid, msg: self._set_status(f"Download failed: {msg}"))
        self._search_threads.append(run_in_thread(worker))

    # ---------------------------------------------------------------- search
    def _search_missing(self) -> None:
        if not self.bg_manager.is_configured:
            return
        for q in self.project.quotes:
            if not q.options:
                self._search_for_quote(q)

    def _regenerate_current(self) -> None:
        q = self._current_quote()
        if not q:
            return
        if not self.bg_manager.is_configured:
            QMessageBox.warning(self, "API keys missing",
                                "Open Settings and add your Pexels or Pixabay key.")
            return
        q.options.clear()
        q.selected_index = 0
        self.backgrounds_panel.show_loading()
        self._search_for_quote(q)

    def _search_for_quote(self, quote: Quote) -> None:
        worker = SearchWorker(self.bg_manager, quote, count=4)
        worker.finished.connect(self._on_search_finished)
        worker.failed.connect(lambda qid, msg: self._set_status(f"Search failed for {qid}: {msg}"))
        self._search_threads.append(run_in_thread(worker))

    def _on_search_finished(self, quote_id: str, options: list) -> None:
        for q in self.project.quotes:
            if q.id == quote_id:
                q.options = options
                q.selected_index = 0
                if quote_id == self._active_quote_id:
                    self.backgrounds_panel.set_options(options, 0)
                    if options and options[0].thumb_path:
                        self.canvas.set_background_thumb(options[0].thumb_path)
                if options:
                    self._ensure_downloaded(quote_id, options[0])
                break

    # ---------------------------------------------------------------- editing
    def _on_layer_changed(self, _layer: TextLayer) -> None:
        self._refresh_timer.start(60)

    def _on_canvas_layer_changed(self, layer: TextLayer) -> None:
        self.text_controls.bind(layer)

    def _refresh_canvas_text(self) -> None:
        self.canvas.refresh_text()

    def _on_video_changed(self, _settings: VideoSettings) -> None:
        self.timeline.set_project(self.project)

    # ---------------------------------------------------------------- export
    def _export_batch(self) -> None:
        if not self.project.quotes:
            QMessageBox.information(self, "Export", "Add at least one quote first.")
            return
        missing = [q for q in self.project.quotes if not (q.selected_option() and q.selected_option().local_path)]
        if missing:
            ans = QMessageBox.question(
                self, "Backgrounds pending",
                f"{len(missing)} quote(s) still need backgrounds. Export anyway "
                "(those will be skipped)?",
            )
            if ans != QMessageBox.Yes:
                return
        out_dir = QFileDialog.getExistingDirectory(self, "Choose export folder",
                                                   str(self.cfg.projects_path))
        if not out_dir:
            return
        out_path = Path(out_dir) / (self.project.name or "export")
        jobs = self.pipeline.jobs_for_project(self.project, out_path)
        if not jobs:
            QMessageBox.warning(self, "Export", "Nothing to render.")
            return
        worker = RenderBatchWorker(self.pipeline, jobs)
        worker.progress.connect(self.timeline.set_progress)
        worker.finished.connect(self._on_render_finished)
        worker.failed.connect(self._on_render_failed)
        self._render_worker = worker
        self.timeline.set_running(True)
        self._render_thread = run_in_thread(worker)

    def _cancel_render(self) -> None:
        if self._render_worker:
            self._render_worker.cancel()
        self.timeline.set_running(False)

    def _on_render_finished(self, outputs: list) -> None:
        self.timeline.set_running(False)
        self.timeline.set_progress(1.0, f"Done · {len(outputs)} clip(s) exported")
        if outputs:
            self._open_path(Path(outputs[0]).parent)

    def _on_render_failed(self, msg: str) -> None:
        self.timeline.set_running(False)
        QMessageBox.warning(self, "Render failed", msg)

    # ---------------------------------------------------------------- close
    def closeEvent(self, ev) -> None:
        for t in list(self._search_threads):
            try:
                t.quit()
                t.wait(500)
            except RuntimeError:
                pass
        if self._render_worker:
            self._render_worker.cancel()
        if self._render_thread:
            try:
                self._render_thread.quit()
                self._render_thread.wait(2000)
            except RuntimeError:
                pass
        super().closeEvent(ev)
