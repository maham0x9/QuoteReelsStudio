"""Bottom timeline + render-progress strip.

It is intentionally lightweight — we render full clips per quote, so the
timeline visualizes the per-quote duration plus the (single) music track
underneath, and shows render progress.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models import Project
from app.utils import humanize_seconds


class _TimelineStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._project: Project | None = None
        self._music_path: str = ""

    def set_project(self, project: Project, music_path: str = "") -> None:
        self._project = project
        self._music_path = music_path
        self.update()

    def paintEvent(self, _ev):
        from PySide6.QtGui import QColor, QPainter, QPen

        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#15171B"))
        if not self._project or not self._project.quotes:
            p.setPen(QPen(QColor("#6A6F7A")))
            p.drawText(self.rect(), Qt.AlignCenter, "Add quotes to see timeline")
            return
        durations = [q.video.duration for q in self._project.quotes]
        total = sum(durations) or 1.0
        x = 8
        w = self.width() - 16
        h = 22
        y = 8
        for i, d in enumerate(durations):
            seg_w = max(8, int(w * (d / total)))
            color = QColor("#5C7CFA") if i % 2 == 0 else QColor("#7E94FB")
            p.fillRect(x, y, seg_w - 2, h, color)
            label = f"#{i+1} {humanize_seconds(d)}"
            p.setPen(QPen(QColor("#FFFFFF")))
            p.drawText(x + 4, y + 16, label)
            x += seg_w
        # music track
        my = y + h + 6
        p.fillRect(8, my, w, 18, QColor("#262830"))
        if self._music_path:
            p.fillRect(8, my, w, 18, QColor("#3FB57F"))
            p.setPen(QPen(QColor("#FFFFFF")))
            p.drawText(12, my + 14, f"♪ {self._music_path.split('/')[-1].split(chr(92))[-1]}")
        else:
            p.setPen(QPen(QColor("#6A6F7A")))
            p.drawText(12, my + 14, "(no music)")


class Timeline(QWidget):
    export_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 4, 8, 8)

        self.strip = _TimelineStrip()
        v.addWidget(self.strip)

        row = QHBoxLayout()
        self.duration_label = QLabel("0 quotes · 0:00 total")
        row.addWidget(self.duration_label)
        row.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(280)
        row.addWidget(self.progress)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setObjectName("DangerBtn")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        row.addWidget(self.cancel_btn)
        self.export_btn = QPushButton("Export Batch")
        self.export_btn.setObjectName("PrimaryBtn")
        self.export_btn.clicked.connect(self.export_requested.emit)
        row.addWidget(self.export_btn)
        v.addLayout(row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Hint")
        v.addWidget(self.status_label)

    def set_project(self, project: Project) -> None:
        music = ""
        if project.quotes:
            music = project.quotes[0].video.music_path
        self.strip.set_project(project, music)
        total = sum(q.video.duration for q in project.quotes)
        self.duration_label.setText(
            f"{len(project.quotes)} quote{'s' if len(project.quotes) != 1 else ''} · "
            f"{humanize_seconds(total)} total"
        )

    def set_progress(self, value: float, message: str = "") -> None:
        self.progress.setValue(max(0, min(100, int(value * 100))))
        if message:
            self.status_label.setText(message)

    def set_running(self, running: bool) -> None:
        self.cancel_btn.setVisible(running)
        self.export_btn.setEnabled(not running)
