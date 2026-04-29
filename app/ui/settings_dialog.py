"""Settings dialog: configure Pexels / Pixabay API keys from inside the app.

Keys are persisted to ``config.local.json`` next to ``config.json`` so they
override committed defaults without ending up in source control.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.config import AppConfig, reload_config


class SettingsDialog(QDialog):
    """Two-field dialog for Pexels + Pixabay keys."""

    def __init__(self, cfg: AppConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(520, 220)

        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 14)
        v.setSpacing(12)

        intro = QLabel(
            "Paste your stock-footage API keys below.\n"
            "Both are free — get a key in under a minute."
        )
        intro.setObjectName("Hint")
        v.addWidget(intro)

        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.pexels_edit = QLineEdit(cfg.pexels_api_key)
        self.pexels_edit.setEchoMode(QLineEdit.Password)
        self.pexels_edit.setPlaceholderText("Pexels API key")
        pexels_link = QLabel(
            '<a href="https://www.pexels.com/api/" '
            'style="color:#7E94FB;">Get key</a>'
        )
        pexels_link.setOpenExternalLinks(True)
        prow = QHBoxLayout()
        prow.addWidget(self.pexels_edit, 1)
        prow.addWidget(pexels_link)
        form.addRow("Pexels", _wrap(prow))

        self.pixabay_edit = QLineEdit(cfg.pixabay_api_key)
        self.pixabay_edit.setEchoMode(QLineEdit.Password)
        self.pixabay_edit.setPlaceholderText("Pixabay API key")
        pixabay_link = QLabel(
            '<a href="https://pixabay.com/api/docs/" '
            'style="color:#7E94FB;">Get key</a>'
        )
        pixabay_link.setOpenExternalLinks(True)
        xrow = QHBoxLayout()
        xrow.addWidget(self.pixabay_edit, 1)
        xrow.addWidget(pixabay_link)
        form.addRow("Pixabay", _wrap(xrow))

        v.addLayout(form)

        # show / hide toggle
        toggle_row = QHBoxLayout()
        self.show_btn = QPushButton("Show keys")
        self.show_btn.setCheckable(True)
        self.show_btn.toggled.connect(self._toggle_visibility)
        toggle_row.addWidget(self.show_btn)
        toggle_row.addStretch(1)
        v.addLayout(toggle_row)

        v.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)

    def _toggle_visibility(self, on: bool) -> None:
        mode = QLineEdit.Normal if on else QLineEdit.Password
        self.pexels_edit.setEchoMode(mode)
        self.pixabay_edit.setEchoMode(mode)
        self.show_btn.setText("Hide keys" if on else "Show keys")

    def _save_and_accept(self) -> None:
        pex = self.pexels_edit.text().strip()
        pix = self.pixabay_edit.text().strip()
        local_path = Path(self.cfg._path).with_name("config.local.json")
        data: dict = {}
        if local_path.exists():
            try:
                data = json.loads(local_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data["pexels_api_key"] = pex
        data["pixabay_api_key"] = pix
        local_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # propagate to live config so the running app sees them immediately
        self.cfg.pexels_api_key = pex
        self.cfg.pixabay_api_key = pix
        reload_config()
        self.accept()


def _wrap(layout):
    from PySide6.QtWidgets import QWidget

    w = QWidget()
    layout.setContentsMargins(0, 0, 0, 0)
    w.setLayout(layout)
    return w
