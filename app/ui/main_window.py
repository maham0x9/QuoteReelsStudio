"""Main application window — wires every panel + workers together."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.api import BackgroundManager
from app.config import get_config
from app.models import Project, Quote, StylePreset, TextLayer, VideoSettings
from app.render import RenderPipeline
from app.store import ProjectStore, TemplateStore

from .backgrounds_panel import BackgroundsPanel
from .editor_canvas import EditorCanvas
from .quotes_panel import QuotesPanel
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
        self.resize(1500, 900)
        self.setStyleSheet(DARK_QSS)

        self.cfg = get_config()
        self.project = Project()
        self.project_store = ProjectStore(self.cfg)
        self.template_store = TemplateStore(self.cfg)
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
        self._build_menu()

        if not self.bg_manager.is_configured:
            QMessageBox.information(
                self, "API keys missing",
                "Set Pexels and/or Pixabay keys in config.json or via the "
                "PEXELS_API_KEY / PIXABAY_API_KEY environment variables to "
                "enable automatic background search.",
            )

    # ---------------------------------------------------------------- layout
    def _build_ui(self) -> None:
        # left
        self.quotes_panel = QuotesPanel(self.project, self.project_store.recent())
        # center: canvas + bg row
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)
        self.canvas = EditorCanvas(canvas_size=self.project.resolution)
        cv.addWidget(self.canvas, 5)
        self.backgrounds_panel = BackgroundsPanel()
        cv.addWidget(self.backgrounds_panel, 2)
        # right
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
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
        h_split.setSizes([320, 800, 360])

        self.timeline = Timeline()

        v_split = QSplitter(Qt.Vertical)
        v_split.addWidget(h_split)
        v_split.addWidget(self.timeline)
        v_split.setStretchFactor(0, 8)
        v_split.setStretchFactor(1, 1)
        v_split.setSizes([700, 200])

        self.setCentralWidget(v_split)
        self.setStatusBar(QStatusBar())

        # signals
        self.quotes_panel.quote_selected.connect(self._on_quote_selected)
        self.quotes_panel.quotes_changed.connect(self._on_quotes_changed)
        self.quotes_panel.new_project_requested.connect(self._new_project)
        self.quotes_panel.open_project_requested.connect(self._open_project)
        self.backgrounds_panel.option_selected.connect(self._on_option_selected)
        self.backgrounds_panel.regenerate_requested.connect(self._regenerate_current)
        self.text_controls.layer_changed.connect(self._on_layer_changed)
        self.text_controls.auto_center_requested.connect(self._auto_center)
        self.video_controls.settings_changed.connect(self._on_video_changed)
        self.canvas.layer_changed.connect(self._on_canvas_layer_changed)
        self.timeline.export_requested.connect(self._export_batch)
        self.timeline.cancel_requested.connect(self._cancel_render)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")
        new_act = QAction("&New project", self, shortcut=QKeySequence.New, triggered=self._new_project)
        open_act = QAction("&Open project…", self, shortcut=QKeySequence.Open, triggered=self._open_project_dialog)
        save_act = QAction("&Save", self, shortcut=QKeySequence.Save, triggered=self._save_project)
        save_as_act = QAction("Save &As…", self, shortcut=QKeySequence("Ctrl+Shift+S"), triggered=self._save_project_as)
        quit_act = QAction("&Quit", self, shortcut=QKeySequence.Quit, triggered=self.close)
        for a in (new_act, open_act, save_act, save_as_act):
            file_menu.addAction(a)
        file_menu.addSeparator()
        file_menu.addAction(quit_act)

        proj_menu = bar.addMenu("&Project")
        proj_menu.addAction(QAction("Fetch backgrounds for &all", self,
                                    shortcut=QKeySequence("Ctrl+Shift+B"),
                                    triggered=self._search_all))
        proj_menu.addAction(QAction("&Apply template to all…", self,
                                    triggered=self._apply_template_to_all))
        proj_menu.addAction(QAction("&Save current as template…", self,
                                    triggered=self._save_template))
        proj_menu.addSeparator()
        proj_menu.addAction(QAction("&Export batch…", self,
                                    shortcut=QKeySequence("Ctrl+E"),
                                    triggered=self._export_batch))

        help_menu = bar.addMenu("&Help")
        help_menu.addAction(QAction("Open project folder", self,
                                    triggered=lambda: self._open_path(self.cfg.projects_path)))
        help_menu.addAction(QAction("Open cache folder", self,
                                    triggered=lambda: self._open_path(self.cfg.cache_path)))
        help_menu.addAction(QAction("About", self, triggered=self._about))

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

    # ---------------------------------------------------------------- project
    def _new_project(self) -> None:
        if self.project.quotes:
            ans = QMessageBox.question(
                self, "New project",
                "Discard current project? Unsaved changes will be lost.",
            )
            if ans != QMessageBox.Yes:
                return
        self.project = Project()
        self.bg_manager.reset_dedupe()
        self.quotes_panel.set_project(self.project)
        self.timeline.set_project(self.project)
        self._active_quote_id = ""
        self._set_status("New project")

    def _open_project_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open project", str(self.cfg.projects_path),
            "Project (*.json);;All files (*)",
        )
        if path:
            self._open_project(path)

    def _open_project(self, path: str) -> None:
        try:
            self.project = self.project_store.load(path)
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))
            return
        self.bg_manager.reset_dedupe()
        self.quotes_panel.set_project(self.project)
        self.quotes_panel.set_recent(self.project_store.recent())
        self.timeline.set_project(self.project)
        if self.project.quotes:
            self._on_quote_selected(self.project.quotes[0].id)
        self._set_status(f"Opened {Path(path).name}")

    def _save_project(self) -> None:
        if not self.project.name or self.project.name == "Untitled Project":
            self._save_project_as()
            return
        path = self.project_store.save(self.project)
        self.quotes_panel.set_recent(self.project_store.recent())
        self._set_status(f"Saved {path.name}")

    def _save_project_as(self) -> None:
        name, ok = QInputDialog.getText(self, "Save project", "Project name:",
                                        text=self.project.name)
        if not ok or not name.strip():
            return
        self.project.name = name.strip()
        self._save_project()

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

    def _search_all(self) -> None:
        if not self.bg_manager.is_configured:
            QMessageBox.warning(self, "API keys missing",
                                "Add Pexels/Pixabay keys to config.json first.")
            return
        self.bg_manager.reset_dedupe()
        for q in self.project.quotes:
            q.options.clear()
            q.selected_index = 0
            self._search_for_quote(q)

    def _regenerate_current(self) -> None:
        q = self._current_quote()
        if not q:
            return
        if not self.bg_manager.is_configured:
            QMessageBox.warning(self, "API keys missing",
                                "Add Pexels/Pixabay keys to config.json first.")
            return
        q.options.clear()
        q.selected_index = 0
        self.backgrounds_panel.show_loading()
        self._search_for_quote(q)

    def _search_for_quote(self, quote: Quote) -> None:
        worker = SearchWorker(self.bg_manager, quote, count=5)
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
    def _on_layer_changed(self, layer: TextLayer) -> None:
        self._refresh_timer.start(60)

    def _on_canvas_layer_changed(self, layer: TextLayer) -> None:
        self.text_controls.bind(layer)

    def _refresh_canvas_text(self) -> None:
        self.canvas.refresh_text()

    def _on_video_changed(self, _settings: VideoSettings) -> None:
        self.timeline.set_project(self.project)

    def _auto_center(self) -> None:
        self.canvas.auto_center_in_safe_zone()

    # ---------------------------------------------------------------- templates
    def _apply_template_to_all(self) -> None:
        presets = self.template_store.list()
        if not presets:
            QMessageBox.information(self, "Templates", "No templates saved yet.")
            return
        names = [p.name for p in presets]
        name, ok = QInputDialog.getItem(self, "Apply template", "Pick:", names, 0, False)
        if not ok:
            return
        preset = next(p for p in presets if p.name == name)
        for q in self.project.quotes:
            q.text_layer = TextLayer.from_dict(preset.text_layer.to_dict())
            q.text_layer.text = q.text
            q.video = VideoSettings.from_dict(preset.video.to_dict())
        if self._active_quote_id:
            self._on_quote_selected(self._active_quote_id)
        self.timeline.set_project(self.project)
        self._set_status(f"Applied template: {name}")

    def _save_template(self) -> None:
        q = self._current_quote()
        if not q:
            return
        name, ok = QInputDialog.getText(self, "Save template", "Name:")
        if not ok or not name.strip():
            return
        preset = StylePreset(
            name=name.strip(),
            text_layer=TextLayer.from_dict(q.text_layer.to_dict()),
            video=VideoSettings.from_dict(q.video.to_dict()),
        )
        self.template_store.save(preset)
        self._set_status(f"Saved template '{name}'")

    # ---------------------------------------------------------------- export
    def _export_batch(self) -> None:
        if not self.project.quotes:
            QMessageBox.information(self, "Export", "Add quotes first.")
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
        out_path = Path(out_dir) / f"{self.project.name or 'export'}"
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

    def _about(self) -> None:
        QMessageBox.information(
            self, "QuoteReelsStudio",
            "QuoteReelsStudio\n\n"
            "Mass-produce vertical quote videos using Pexels + Pixabay backgrounds.\n"
            "FFmpeg-backed render. Built with PySide6.",
        )

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
