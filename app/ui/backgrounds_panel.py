"""Background option grid for a single quote."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models import BackgroundOption


class _OptionTile(QFrame):
    clicked = Signal(int)

    def __init__(self, index: int, opt: BackgroundOption, parent=None):
        super().__init__(parent)
        self.index = index
        self.opt = opt
        self.setObjectName("Card")
        self.setFixedSize(120, 200)
        self.setCursor(Qt.PointingHandCursor)
        v = QVBoxLayout(self)
        v.setContentsMargins(4, 4, 4, 4)
        self.thumb = QLabel("loading…")
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setFixedSize(112, 168)
        self.thumb.setStyleSheet("background:#15171B; border-radius:6px;")
        v.addWidget(self.thumb)
        meta = QLabel(f"{opt.provider} · {int(opt.duration)}s")
        meta.setObjectName("Hint")
        meta.setAlignment(Qt.AlignCenter)
        v.addWidget(meta)
        self._refresh_thumb()

    def _refresh_thumb(self) -> None:
        if self.opt.thumb_path:
            pm = QPixmap(self.opt.thumb_path)
            if not pm.isNull():
                self.thumb.setPixmap(
                    pm.scaled(self.thumb.size(), Qt.KeepAspectRatioByExpanding,
                              Qt.SmoothTransformation)
                )

    def mark_selected(self, selected: bool) -> None:
        self.setStyleSheet(
            "QFrame#Card { border: 2px solid #5C7CFA; }" if selected else ""
        )

    def mousePressEvent(self, _ev) -> None:
        self.clicked.emit(self.index)


class BackgroundsPanel(QWidget):
    option_selected = Signal(int)
    regenerate_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tiles: list[_OptionTile] = []
        self._build()

    def _build(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Backgrounds</b>"))
        header.addStretch(1)
        self.regen_btn = QPushButton("Regenerate")
        self.regen_btn.clicked.connect(self.regenerate_requested.emit)
        header.addWidget(self.regen_btn)
        v.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.row_host = QWidget()
        self.row = QHBoxLayout(self.row_host)
        self.row.setContentsMargins(4, 4, 4, 4)
        self.row.setSpacing(8)
        self.row.addStretch(1)
        self.scroll.setWidget(self.row_host)
        v.addWidget(self.scroll)

        self.empty_label = QLabel("Add quotes and they will get backgrounds here.")
        self.empty_label.setObjectName("Hint")
        self.empty_label.setAlignment(Qt.AlignCenter)
        v.addWidget(self.empty_label)

    # ------------------------------------------------------------------ ops
    def show_loading(self) -> None:
        self._clear_tiles()
        self.empty_label.setText("Searching backgrounds…")
        self.empty_label.setStyleSheet("")
        self.empty_label.show()

    def show_error(self, message: str) -> None:
        self._clear_tiles()
        self.empty_label.setText(message)
        self.empty_label.setStyleSheet("color:#FF8B8B;")
        self.empty_label.show()

    def set_options(self, options: list[BackgroundOption], selected_index: int = 0) -> None:
        self._clear_tiles()
        if not options:
            self.empty_label.setText("No backgrounds found. Try regenerating.")
            self.empty_label.show()
            return
        self.empty_label.hide()
        for i, opt in enumerate(options):
            tile = _OptionTile(i, opt)
            tile.clicked.connect(self.option_selected.emit)
            self.row.insertWidget(self.row.count() - 1, tile)
            self.tiles.append(tile)
        self.set_selected(selected_index)

    def set_selected(self, index: int) -> None:
        for i, t in enumerate(self.tiles):
            t.mark_selected(i == index)

    def _clear_tiles(self) -> None:
        for t in self.tiles:
            self.row.removeWidget(t)
            t.deleteLater()
        self.tiles.clear()
