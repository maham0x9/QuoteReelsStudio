"""Bottom action bar — minimal: status, progress, export."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import Project
from app.utils import humanize_seconds


class Timeline(QWidget):
    export_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 8, 12, 12)
        v.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(10)
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
