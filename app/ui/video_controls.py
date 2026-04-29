"""Right-side video controls — minimal version.

Exposes only: clip duration, dark overlay slider, music selector. Other
``VideoSettings`` fields keep their defaults (loop short clips, mute original
audio, no blur, 1.0× speed).
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.config import get_config
from app.models import VideoSettings


class VideoControls(QWidget):
    settings_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings: VideoSettings | None = None
        self._suppress = False
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(10)

        header = QLabel("Video")
        header.setObjectName("SectionHeader")
        v.addWidget(header)

        gb = QGroupBox("Settings")
        f = QFormLayout(gb)
        f.setContentsMargins(10, 10, 10, 10)
        f.setHorizontalSpacing(10)
        f.setVerticalSpacing(10)
        f.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.duration = QDoubleSpinBox()
        self.duration.setRange(3.0, 60.0)
        self.duration.setSingleStep(1.0)
        self.duration.setSuffix(" s")
        self.duration.setValue(8.0)
        f.addRow("Duration", self.duration)

        self.dark = QSlider(Qt.Horizontal)
        self.dark.setRange(0, 80)
        self.dark.setValue(35)
        self.dark.setMinimumHeight(24)
        f.addRow("Dark overlay", self.dark)

        self.music_combo = QComboBox()
        self.music_combo.setEditable(False)
        self.refresh_music_list()
        self.music_browse = QPushButton("Browse…")
        self.music_browse.clicked.connect(self._on_browse_music)
        m_row = QHBoxLayout()
        m_row.addWidget(self.music_combo, 1)
        m_row.addWidget(self.music_browse)
        m_w = QWidget()
        m_w.setLayout(m_row)
        f.addRow("Music", m_w)

        v.addWidget(gb)
        v.addStretch(1)

        self.duration.valueChanged.connect(self._emit)
        self.dark.valueChanged.connect(self._emit)
        self.music_combo.currentIndexChanged.connect(self._emit)

    def refresh_music_list(self) -> None:
        cfg = get_config()
        prev = self.music_combo.currentData() if self.music_combo.count() else ""
        self.music_combo.blockSignals(True)
        self.music_combo.clear()
        self.music_combo.addItem("(no music)", "")
        for p in sorted(cfg.music_path.glob("*")):
            if p.suffix.lower() in {".mp3", ".m4a", ".wav", ".aac", ".ogg"}:
                self.music_combo.addItem(p.stem, str(p))
        if prev:
            idx = self.music_combo.findData(prev)
            if idx >= 0:
                self.music_combo.setCurrentIndex(idx)
        self.music_combo.blockSignals(False)

    # ------------------------------------------------------------------ binding
    def bind(self, settings: VideoSettings) -> None:
        self._settings = settings
        self._suppress = True
        self.duration.setValue(settings.duration)
        self.dark.setValue(int(settings.dark_overlay * 100))
        idx = self.music_combo.findData(settings.music_path)
        self.music_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._suppress = False

    def _emit(self) -> None:
        if self._suppress or not self._settings:
            return
        self._settings.duration = float(self.duration.value())
        self._settings.dark_overlay = self.dark.value() / 100.0
        self._settings.music_path = self.music_combo.currentData() or ""
        # silently keep sensible defaults
        self._settings.loop_short = True
        self._settings.mute_original = True
        self._settings.blur_bg = False
        self._settings.speed = 1.0
        self._settings.trim_start = 0.0
        self._settings.music_volume = 0.6
        self.settings_changed.emit(self._settings)

    # ------------------------------------------------------------------ actions
    def _on_browse_music(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose music file", "",
            "Audio (*.mp3 *.m4a *.wav *.aac *.ogg);;All files (*)",
        )
        if not path:
            return
        cfg = get_config()
        # If the user picked a file outside the music dir, copy a reference
        # link rather than the file itself (keeps things lightweight).
        existing = self.music_combo.findData(path)
        if existing >= 0:
            self.music_combo.setCurrentIndex(existing)
            return
        name = Path(path).stem
        self.music_combo.addItem(name, path)
        self.music_combo.setCurrentIndex(self.music_combo.count() - 1)
        _ = cfg  # silence unused warning; reserved for future copy-on-import
