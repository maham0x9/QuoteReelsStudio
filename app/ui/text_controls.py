"""Right-side text style controls — minimal version.

Exposes only: text, font size, color, bold. Other TextLayer fields keep their
defaults (centered alignment, soft drop shadow, no stroke, no rotation).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models import TextLayer


class _ColorButton(QPushButton):
    color_changed = Signal(str)

    def __init__(self, initial: str = "#FFFFFF"):
        super().__init__("")
        self._color = initial
        self.setMinimumHeight(28)
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
        self.setText(self._color.upper())
        self.setStyleSheet(
            f"background-color: {self._color}; color: #000; font-weight: 600;"
            "border-radius: 6px; padding: 4px 8px;"
        )


class TextControls(QWidget):
    layer_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layer: TextLayer | None = None
        self._suppress = False
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(10)

        header = QLabel("Text")
        header.setObjectName("SectionHeader")
        v.addWidget(header)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Quote text…")
        self.text_edit.setFixedHeight(110)
        v.addWidget(self.text_edit)

        gb = QGroupBox("Style")
        form = QFormLayout(gb)
        form.setContentsMargins(10, 10, 10, 10)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(24, 160)
        self.size_spin.setSingleStep(2)
        self.size_spin.setValue(64)
        self.size_spin.setSuffix(" px")
        form.addRow("Size", self.size_spin)

        self.color_btn = _ColorButton("#FFFFFF")
        form.addRow("Color", self.color_btn)

        self.bold_cb = QCheckBox("Bold")
        self.bold_cb.setChecked(True)
        bi = QHBoxLayout()
        bi.addWidget(self.bold_cb)
        bi.addStretch(1)
        bi_w = QWidget()
        bi_w.setLayout(bi)
        form.addRow("Weight", bi_w)

        v.addWidget(gb)
        v.addStretch(1)

        # signals
        self.text_edit.textChanged.connect(self._emit)
        self.size_spin.valueChanged.connect(self._emit)
        self.color_btn.color_changed.connect(lambda *_: self._emit())
        self.bold_cb.toggled.connect(self._emit)

    # ------------------------------------------------------------------ binding
    def bind(self, layer: TextLayer) -> None:
        self._layer = layer
        self._suppress = True
        self.text_edit.setPlainText(layer.text)
        self.size_spin.setValue(int(layer.font_size))
        self.color_btn.setColor(layer.color or "#FFFFFF")
        self.bold_cb.setChecked(layer.bold)
        self._suppress = False

    def _emit(self) -> None:
        if self._suppress or not self._layer:
            return
        self._layer.text = self.text_edit.toPlainText()
        self._layer.font_size = int(self.size_spin.value())
        self._layer.color = self.color_btn.color()
        self._layer.bold = self.bold_cb.isChecked()
        # silently keep sensible defaults
        self._layer.alignment = "center"
        self._layer.shadow = True
        self._layer.italic = False
        self._layer.stroke_width = 0
        self._layer.opacity = 1.0
        self._layer.rotation = 0.0
        self.layer_changed.emit(self._layer)
