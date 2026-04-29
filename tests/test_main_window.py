"""Smoke test that the full Qt UI imports + instantiates head-less."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_constructs(qapp, monkeypatch):
    # Skip the "API keys missing" modal so the test is non-interactive.
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **kw: QMessageBox.Ok)

    from app.ui import MainWindow

    win = MainWindow()
    assert win.windowTitle() == "QuoteReelsStudio"
    win.close()
