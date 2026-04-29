"""Dark theme QSS shared by the main window."""

DARK_QSS = """
* { color: #E6E6E6; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
QMainWindow, QDialog, QWidget { background-color: #1B1D22; }
QFrame#Card, QGroupBox {
    background-color: #23262C; border: 1px solid #2E323A; border-radius: 8px;
}
QGroupBox { margin-top: 14px; padding: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #B6BAC4; }
QPushButton {
    background-color: #2E3340; color: #FFFFFF; border: 1px solid #3A4050;
    padding: 6px 12px; border-radius: 6px;
}
QPushButton:hover { background-color: #38405A; border-color: #5765A0; }
QPushButton:disabled { color: #6A6F7A; background-color: #262830; }
QPushButton#PrimaryBtn { background-color: #5C7CFA; border-color: #5C7CFA; }
QPushButton#PrimaryBtn:hover { background-color: #748DFB; }
QPushButton#DangerBtn  { background-color: #D9534F; border-color: #D9534F; }
QPushButton#DangerBtn:hover { background-color: #E26A66; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1F2228; border: 1px solid #2E323A; border-radius: 6px;
    padding: 4px 6px; selection-background-color: #5C7CFA;
}
QListWidget, QTreeView, QTableView {
    background-color: #1F2228; border: 1px solid #2E323A; border-radius: 6px;
    alternate-background-color: #232730;
}
QListWidget::item:selected { background: #38405A; color: #FFFFFF; }
QSplitter::handle { background: #2E323A; }
QSlider::groove:horizontal { background: #2E323A; height: 4px; border-radius: 2px; }
QSlider::handle:horizontal { background: #5C7CFA; width: 14px; margin: -6px 0; border-radius: 7px; }
QStatusBar { background: #15171B; color: #B6BAC4; }
QProgressBar { background: #1F2228; border: 1px solid #2E323A; border-radius: 6px; text-align: center; }
QProgressBar::chunk { background-color: #5C7CFA; border-radius: 6px; }
QToolBar { background: #1B1D22; border: none; spacing: 6px; }
QLabel#Hint { color: #8A8F9C; }
"""
