"""Left-side panel: quotes list, projects list, import buttons."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.models import Project, Quote
from app.utils import import_quotes_from_path, parse_quotes


class QuotesPanel(QWidget):
    quote_selected = Signal(str)         # quote_id
    project_selected = Signal(str)       # project_path
    quotes_changed = Signal()            # quote list mutated
    new_project_requested = Signal()
    open_project_requested = Signal(str)

    def __init__(self, project: Project, recent: list[dict], parent=None):
        super().__init__(parent)
        self.project = project
        self._build(recent)

    # ------------------------------------------------------------------ build
    def _build(self, recent: list[dict]) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Vertical)

        # --- Quotes section --------------------------------------------------
        quotes_box = QWidget()
        ql = QVBoxLayout(quotes_box)
        ql.setContentsMargins(0, 0, 0, 0)
        ql.addWidget(QLabel("<b>Quotes</b>"))

        self.quote_input = QPlainTextEdit()
        self.quote_input.setPlaceholderText(
            "Paste one or more quotes.\nSeparate with blank lines.\n"
            "Lines starting with # are ignored."
        )
        self.quote_input.setFixedHeight(120)
        ql.addWidget(self.quote_input)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("PrimaryBtn")
        self.import_btn = QPushButton("Import TXT/CSV…")
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("DangerBtn")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.import_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.clear_btn)
        ql.addLayout(btn_row)

        self.quotes_list = QListWidget()
        self.quotes_list.setAlternatingRowColors(True)
        ql.addWidget(self.quotes_list, 1)

        splitter.addWidget(quotes_box)

        # --- Projects section ------------------------------------------------
        proj_box = QWidget()
        pl = QVBoxLayout(proj_box)
        pl.setContentsMargins(0, 8, 0, 0)
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Recent Projects</b>"))
        header.addStretch(1)
        self.new_proj_btn = QPushButton("New")
        self.open_proj_btn = QPushButton("Open…")
        header.addWidget(self.new_proj_btn)
        header.addWidget(self.open_proj_btn)
        pl.addLayout(header)

        self.projects_list = QListWidget()
        self.projects_list.setAlternatingRowColors(True)
        pl.addWidget(self.projects_list, 1)
        splitter.addWidget(proj_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

        # --- wiring ---------------------------------------------------------
        self.add_btn.clicked.connect(self._on_add)
        self.import_btn.clicked.connect(self._on_import)
        self.clear_btn.clicked.connect(self._on_clear)
        self.quotes_list.currentItemChanged.connect(self._on_select_quote)
        self.new_proj_btn.clicked.connect(self.new_project_requested.emit)
        self.open_proj_btn.clicked.connect(self._on_open_project)
        self.projects_list.itemActivated.connect(
            lambda it: self.open_project_requested.emit(it.data(Qt.UserRole))
        )

        self.refresh_quotes()
        self.set_recent(recent)

    # ------------------------------------------------------------------ ops
    def set_project(self, project: Project) -> None:
        self.project = project
        self.refresh_quotes()

    def set_recent(self, entries: list[dict]) -> None:
        self.projects_list.clear()
        for e in entries:
            it = QListWidgetItem(e.get("name", "Untitled"))
            it.setData(Qt.UserRole, e.get("path", ""))
            self.projects_list.addItem(it)

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

    # ------------------------------------------------------------------ slots
    def _on_add(self) -> None:
        text = self.quote_input.toPlainText()
        quotes = parse_quotes(text)
        if not quotes:
            return
        for t in quotes:
            self.project.quotes.append(Quote(text=t))
        self.quote_input.clear()
        self.refresh_quotes()
        self.quotes_changed.emit()

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import quotes", "",
            "Text or CSV (*.txt *.csv);;All files (*)",
        )
        if not path:
            return
        try:
            quotes = import_quotes_from_path(Path(path))
        except OSError as e:
            QMessageBox.warning(self, "Import failed", str(e))
            return
        if not quotes:
            QMessageBox.information(self, "Import", "No quotes found in file.")
            return
        for t in quotes:
            self.project.quotes.append(Quote(text=t))
        self.refresh_quotes()
        self.quotes_changed.emit()

    def _on_clear(self) -> None:
        if not self.project.quotes:
            return
        ans = QMessageBox.question(
            self, "Clear quotes",
            f"Remove all {len(self.project.quotes)} quotes from this project?",
        )
        if ans != QMessageBox.Yes:
            return
        self.project.quotes.clear()
        self.refresh_quotes()
        self.quotes_changed.emit()

    def _on_select_quote(self, current, _previous) -> None:
        if current:
            self.quote_selected.emit(current.data(Qt.UserRole))

    def _on_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open project", "",
            "Project files (*.json);;All files (*)",
        )
        if path:
            self.open_project_requested.emit(path)
