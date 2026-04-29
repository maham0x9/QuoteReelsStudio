"""Left-side panel: minimal quote input + list."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import Project, Quote
from app.utils import parse_quotes


class QuotesPanel(QWidget):
    quote_selected = Signal(str)
    quotes_changed = Signal()

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QLabel("Quotes")
        header.setObjectName("SectionHeader")
        layout.addWidget(header)

        self.quote_input = QPlainTextEdit()
        self.quote_input.setPlaceholderText(
            "Paste one or more quotes.\n"
            "Separate multiple quotes with a blank line."
        )
        self.quote_input.setFixedHeight(120)
        layout.addWidget(self.quote_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("PrimaryBtn")
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("DangerBtn")
        btn_row.addWidget(self.add_btn, 1)
        btn_row.addWidget(self.clear_btn)
        layout.addLayout(btn_row)

        self.quotes_list = QListWidget()
        self.quotes_list.setAlternatingRowColors(True)
        layout.addWidget(self.quotes_list, 1)

        self.add_btn.clicked.connect(self._on_add)
        self.clear_btn.clicked.connect(self._on_clear)
        self.quotes_list.currentItemChanged.connect(self._on_select_quote)

        self.refresh_quotes()

    # ------------------------------------------------------------------ ops
    def set_project(self, project: Project) -> None:
        self.project = project
        self.refresh_quotes()

    def refresh_quotes(self) -> None:
        self.quotes_list.clear()
        for q in self.project.quotes:
            preview = (q.text[:64] + "…") if len(q.text) > 64 else q.text
            it = QListWidgetItem(preview or "(empty)")
            it.setData(Qt.UserRole, q.id)
            self.quotes_list.addItem(it)
        if self.project.quotes:
            self.quotes_list.setCurrentRow(0)

    def select_quote(self, quote_id: str) -> None:
        for i in range(self.quotes_list.count()):
            if self.quotes_list.item(i).data(Qt.UserRole) == quote_id:
                self.quotes_list.setCurrentRow(i)
                return

    # ------------------------------------------------------------------ actions
    def _on_add(self) -> None:
        text = self.quote_input.toPlainText()
        new_quotes = [Quote(text=t) for t in parse_quotes(text)]
        if not new_quotes:
            return
        self.project.quotes.extend(new_quotes)
        self.quote_input.clear()
        self.refresh_quotes()
        self.quotes_changed.emit()

    def _on_clear(self) -> None:
        self.project.quotes.clear()
        self.refresh_quotes()
        self.quotes_changed.emit()

    def _on_select_quote(self, current, _previous) -> None:
        if current is None:
            return
        qid = current.data(Qt.UserRole)
        if qid:
            self.quote_selected.emit(qid)
