"""Right-side video controls + music selector."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
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
        v.setContentsMargins(8, 8, 8, 8)
        v.addWidget(QLabel("<b>Video</b>"))

        gb_clip = QGroupBox("Clip")
        f1 = QFormLayout(gb_clip)
        self.duration = QDoubleSpinBox()
        self.duration.setRange(1.0, 60.0)
        self.duration.setSuffix(" s")
        self.duration.setValue(8.0)
        f1.addRow("Duration", self.duration)

        self.trim_start = QDoubleSpinBox()
        self.trim_start.setRange(0.0, 600.0)
        self.trim_start.setSuffix(" s")
        f1.addRow("Trim start", self.trim_start)

        self.loop_cb = QCheckBox("Loop short clips")
        self.loop_cb.setChecked(True)
        f1.addRow("Loop", self.loop_cb)

        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.25, 4.0)
        self.speed.setSingleStep(0.05)
        self.speed.setValue(1.0)
        f1.addRow("Speed", self.speed)
        v.addWidget(gb_clip)

        gb_look = QGroupBox("Look")
        f2 = QFormLayout(gb_look)
        self.blur_cb = QCheckBox("Blur background")
        self.blur_strength = QSpinBox()
        self.blur_strength.setRange(1, 40)
        self.blur_strength.setValue(12)
        blur_row = QHBoxLayout()
        blur_row.addWidget(self.blur_cb)
        blur_row.addWidget(QLabel("strength"))
        blur_row.addWidget(self.blur_strength)
        blur_w = QWidget()
        blur_w.setLayout(blur_row)
        f2.addRow("Blur", blur_w)

        self.dark = QSlider(Qt.Horizontal)
        self.dark.setRange(0, 80)
        self.dark.setValue(35)
        f2.addRow("Dark overlay", self.dark)
        v.addWidget(gb_look)

        gb_audio = QGroupBox("Audio")
        f3 = QFormLayout(gb_audio)
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
        f3.addRow("Music", m_w)

        self.music_vol = QSlider(Qt.Horizontal)
        self.music_vol.setRange(0, 100)
        self.music_vol.setValue(60)
        f3.addRow("Music volume", self.music_vol)

        self.mute_cb = QCheckBox("Mute original audio")
        self.mute_cb.setChecked(True)
        f3.addRow("Mute", self.mute_cb)
        v.addWidget(gb_audio)

        v.addStretch(1)

        for w in (
            self.duration, self.trim_start, self.speed, self.blur_strength, self.dark,
            self.music_vol,
        ):
            w.valueChanged.connect(self._emit)
        for cb in (self.loop_cb, self.blur_cb, self.mute_cb):
            cb.toggled.connect(self._emit)
        self.music_combo.currentTextChanged.connect(self._emit)

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

    def bind(self, settings: VideoSettings) -> None:
        self._settings = settings
        self._suppress = True
        self.duration.setValue(settings.duration)
        self.trim_start.setValue(settings.trim_start)
        self.loop_cb.setChecked(settings.loop_short)
        self.speed.setValue(settings.speed)
        self.blur_cb.setChecked(settings.blur_bg)
        self.blur_strength.setValue(settings.blur_strength)
        self.dark.setValue(int(settings.dark_overlay * 100))
        idx = self.music_combo.findData(settings.music_path)
        self.music_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.music_vol.setValue(int(settings.music_volume * 100))
        self.mute_cb.setChecked(settings.mute_original)
        self._suppress = False

    def _on_browse_music(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose music", "",
            "Audio (*.mp3 *.m4a *.wav *.aac *.ogg);;All files (*)",
        )
        if not path:
            return
        # copy / track absolute path; just add to combo dynamically
        name = Path(path).stem
        self.music_combo.addItem(name, path)
        self.music_combo.setCurrentIndex(self.music_combo.count() - 1)

    def _emit(self, *_args) -> None:
        if self._suppress or not self._settings:
            return
        s = self._settings
        s.duration = self.duration.value()
        s.trim_start = self.trim_start.value()
        s.loop_short = self.loop_cb.isChecked()
        s.speed = self.speed.value()
        s.blur_bg = self.blur_cb.isChecked()
        s.blur_strength = self.blur_strength.value()
        s.dark_overlay = self.dark.value() / 100.0
        s.music_path = self.music_combo.currentData() or ""
        s.music_volume = self.music_vol.value() / 100.0
        s.mute_original = self.mute_cb.isChecked()
        self.settings_changed.emit(s)
