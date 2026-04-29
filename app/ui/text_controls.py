"""Right-side text style controls panel."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models import TextLayer


class _ColorButton(QPushButton):
    color_changed = Signal(str)

    def __init__(self, label: str, initial: str = "#FFFFFF"):
        super().__init__(label)
        self._color = initial
        self._refresh()
        self.clicked.connect(self._pick)

    def color(self) -> str:
        return self._color

    def setColor(self, hex_color: str) -> None:
        if hex_color and hex_color != self._color:
            self._color = hex_color
            self._refresh()

    def _pick(self) -> None:
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._refresh()
            self.color_changed.emit(self._color)

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._color}; color: #000; font-weight: 600;"
        )


class TextControls(QWidget):
    layer_changed = Signal(object)
    auto_center_requested = Signal()

    ALIGNMENTS = ["left", "center", "right"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layer: TextLayer | None = None
        self._suppress = False
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.addWidget(QLabel("<b>Text</b>"))

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Quote text…")
        self.text_edit.setFixedHeight(96)
        v.addWidget(self.text_edit)

        gb = QGroupBox("Style")
        form = QFormLayout(gb)
        form.setLabelAlignment(Qt.AlignRight)

        self.font_combo = QComboBox()
        families = QFontDatabase.families()
        # Push a few common families to the top for convenience
        prefs = [f for f in ("Inter", "Segoe UI", "Arial", "Helvetica", "Roboto") if f in families]
        self.font_combo.addItems(prefs + [f for f in families if f not in prefs])
        form.addRow("Font", self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(12, 240)
        self.size_spin.setValue(64)
        form.addRow("Size", self.size_spin)

        self.color_btn = _ColorButton("Color", "#FFFFFF")
        form.addRow("Color", self.color_btn)

        self.bold_cb = QCheckBox("Bold")
        self.bold_cb.setChecked(True)
        self.italic_cb = QCheckBox("Italic")
        bi_row = QHBoxLayout()
        bi_row.addWidget(self.bold_cb)
        bi_row.addWidget(self.italic_cb)
        bi_w = QFrame()
        bi_w.setLayout(bi_row)
        form.addRow("Weight", bi_w)

        self.shadow_cb = QCheckBox("Shadow")
        self.shadow_cb.setChecked(True)
        self.shadow_offset = QSpinBox()
        self.shadow_offset.setRange(0, 30)
        self.shadow_offset.setValue(4)
        self.shadow_blur = QSpinBox()
        self.shadow_blur.setRange(0, 60)
        self.shadow_blur.setValue(8)
        sh_row = QHBoxLayout()
        sh_row.addWidget(self.shadow_cb)
        sh_row.addWidget(QLabel("offset"))
        sh_row.addWidget(self.shadow_offset)
        sh_row.addWidget(QLabel("blur"))
        sh_row.addWidget(self.shadow_blur)
        sh_w = QFrame()
        sh_w.setLayout(sh_row)
        form.addRow("Shadow", sh_w)

        self.stroke_w = QSpinBox()
        self.stroke_w.setRange(0, 20)
        self.stroke_w.setValue(0)
        self.stroke_color_btn = _ColorButton("Stroke", "#000000")
        st_row = QHBoxLayout()
        st_row.addWidget(self.stroke_w)
        st_row.addWidget(self.stroke_color_btn)
        st_w = QFrame()
        st_w.setLayout(st_row)
        form.addRow("Stroke", st_w)

        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(10, 100)
        self.opacity.setValue(100)
        form.addRow("Opacity", self.opacity)

        self.align_combo = QComboBox()
        self.align_combo.addItems(self.ALIGNMENTS)
        self.align_combo.setCurrentText("center")
        form.addRow("Alignment", self.align_combo)

        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(-180.0, 180.0)
        self.rotation.setValue(0.0)
        form.addRow("Rotation", self.rotation)

        v.addWidget(gb)

        self.auto_center_btn = QPushButton("Auto-center in safe zone")
        self.auto_center_btn.clicked.connect(self.auto_center_requested.emit)
        v.addWidget(self.auto_center_btn)

        v.addStretch(1)

        # signals
        self.text_edit.textChanged.connect(self._emit)
        self.font_combo.currentTextChanged.connect(self._emit)
        self.size_spin.valueChanged.connect(self._emit)
        self.color_btn.color_changed.connect(self._emit)
        self.bold_cb.toggled.connect(self._emit)
        self.italic_cb.toggled.connect(self._emit)
        self.shadow_cb.toggled.connect(self._emit)
        self.shadow_offset.valueChanged.connect(self._emit)
        self.shadow_blur.valueChanged.connect(self._emit)
        self.stroke_w.valueChanged.connect(self._emit)
        self.stroke_color_btn.color_changed.connect(self._emit)
        self.opacity.valueChanged.connect(self._emit)
        self.align_combo.currentTextChanged.connect(self._emit)
        self.rotation.valueChanged.connect(self._emit)

    def bind(self, layer: TextLayer) -> None:
        self._layer = layer
        self._suppress = True
        self.text_edit.setPlainText(layer.text)
        idx = self.font_combo.findText(layer.font_family)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        self.size_spin.setValue(layer.font_size)
        self.color_btn.setColor(layer.color)
        self.bold_cb.setChecked(layer.bold)
        self.italic_cb.setChecked(layer.italic)
        self.shadow_cb.setChecked(layer.shadow)
        self.shadow_offset.setValue(layer.shadow_offset)
        self.shadow_blur.setValue(layer.shadow_blur)
        self.stroke_w.setValue(layer.stroke_width)
        self.stroke_color_btn.setColor(layer.stroke_color)
        self.opacity.setValue(int(layer.opacity * 100))
        self.align_combo.setCurrentText(layer.alignment)
        self.rotation.setValue(layer.rotation)
        self._suppress = False

    def _emit(self, *_args) -> None:
        if self._suppress or not self._layer:
            return
        layer = self._layer
        layer.text = self.text_edit.toPlainText()
        layer.font_family = self.font_combo.currentText()
        layer.font_size = self.size_spin.value()
        layer.color = self.color_btn.color()
        layer.bold = self.bold_cb.isChecked()
        layer.italic = self.italic_cb.isChecked()
        layer.shadow = self.shadow_cb.isChecked()
        layer.shadow_offset = self.shadow_offset.value()
        layer.shadow_blur = self.shadow_blur.value()
        layer.stroke_width = self.stroke_w.value()
        layer.stroke_color = self.stroke_color_btn.color()
        layer.opacity = self.opacity.value() / 100.0
        layer.alignment = self.align_combo.currentText()
        layer.rotation = self.rotation.value()
        self.layer_changed.emit(layer)
