"""Dark theme QSS shared by the main window."""

DARK_QSS = """
QWidget {
    color: #E6E6E6;
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog { background-color: #1B1D22; }
QWidget#CenterPane, QWidget#SidePane { background-color: #1B1D22; }

/* -------- group boxes -------- */
QGroupBox {
    background-color: #23262C;
    border: 1px solid #2E323A;
    border-radius: 8px;
    margin-top: 18px;       /* room above for the floating title */
    padding: 18px 10px 10px 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 2px 8px;
    color: #C9CDD6;
    background-color: #23262C;
}
QFrame#Card {
    background-color: #23262C;
    border: 1px solid #2E323A;
    border-radius: 8px;
}

/* -------- buttons -------- */
QPushButton {
    background-color: #2E3340;
    color: #FFFFFF;
    border: 1px solid #3A4050;
    padding: 7px 14px;
    border-radius: 6px;
    min-height: 22px;
}
QPushButton:hover { background-color: #38405A; border-color: #5765A0; }
QPushButton:pressed { background-color: #2A3048; }
QPushButton:disabled { color: #6A6F7A; background-color: #262830; border-color: #2E323A; }
QPushButton#PrimaryBtn {
    background-color: #5C7CFA; border-color: #5C7CFA; color: #FFFFFF; font-weight: 600;
}
QPushButton#PrimaryBtn:hover { background-color: #748DFB; border-color: #748DFB; }
QPushButton#PrimaryBtn:pressed { background-color: #4D6BE8; }
QPushButton#DangerBtn {
    background-color: #D9534F; border-color: #D9534F; color: #FFFFFF; font-weight: 600;
}
QPushButton#DangerBtn:hover { background-color: #E26A66; border-color: #E26A66; }

/* -------- inputs -------- */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1F2228;
    border: 1px solid #2E323A;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #5C7CFA;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #5C7CFA; }

QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1F2228;
    border: 1px solid #2E323A;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
    color: #E6E6E6;
}
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #5C7CFA; }
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    background-color: #2A2E36;
    border-left: 1px solid #2E323A;
    border-top-right-radius: 6px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    background-color: #2A2E36;
    border-left: 1px solid #2E323A;
    border-bottom-right-radius: 6px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #38405A;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #C9CDD6;
    width: 0; height: 0;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #C9CDD6;
    width: 0; height: 0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2E323A;
    background-color: #2A2E36;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #C9CDD6;
    width: 0; height: 0;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1F2228;
    border: 1px solid #2E323A;
    color: #E6E6E6;
    selection-background-color: #5C7CFA;
    selection-color: #FFFFFF;
    outline: 0;
}

/* -------- check / radio -------- */
QCheckBox, QRadioButton { spacing: 8px; padding: 2px; color: #E6E6E6; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #4A5060;
    background-color: #1F2228;
    border-radius: 3px;
}
QRadioButton::indicator { border-radius: 8px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: #5C7CFA; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #5C7CFA;
    border-color: #5C7CFA;
    image: none;
}
QCheckBox::indicator:checked {
    /* a simple "filled" look — a smaller inner square via box-shadow isn't
       supported in QSS, so we just show a solid coloured square. */
}
QCheckBox:disabled, QRadioButton:disabled { color: #6A6F7A; }

/* -------- lists / trees -------- */
QListWidget, QTreeView, QTableView {
    background-color: #1F2228;
    border: 1px solid #2E323A;
    border-radius: 6px;
    alternate-background-color: #232730;
    outline: 0;
}
QListWidget::item { padding: 6px 8px; }
QListWidget::item:selected { background: #38405A; color: #FFFFFF; }
QListWidget::item:hover { background: #2A3048; }

/* -------- splitter -------- */
QSplitter::handle { background: #2E323A; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical { height: 4px; }

/* -------- slider -------- */
QSlider::groove:horizontal {
    background: #2E323A; height: 6px; border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #5C7CFA; height: 6px; border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #5C7CFA;
    width: 14px; height: 14px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #E5EAFF; }

/* -------- progress -------- */
QProgressBar {
    background: #1F2228; border: 1px solid #2E323A;
    border-radius: 6px; text-align: center; color: #E6E6E6;
    min-height: 18px;
}
QProgressBar::chunk {
    background-color: #5C7CFA; border-radius: 5px;
}

/* -------- statusbar / menu -------- */
QStatusBar { background: #15171B; color: #B6BAC4; }
QMenuBar { background: #1B1D22; color: #E6E6E6; }
QMenuBar::item { padding: 4px 10px; background: transparent; }
QMenuBar::item:selected { background: #2E3340; }
QMenu { background: #23262C; border: 1px solid #2E323A; color: #E6E6E6; }
QMenu::item { padding: 6px 18px; }
QMenu::item:selected { background: #38405A; }

/* -------- scrollbars -------- */
QScrollBar:vertical {
    background: #1B1D22; width: 10px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #3A4050; border-radius: 5px; min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #4A5266; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal {
    background: #1B1D22; height: 10px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #3A4050; border-radius: 5px; min-width: 28px;
}
QScrollBar::handle:horizontal:hover { background: #4A5266; }

/* -------- toolbar -------- */
QToolBar { background: #1B1D22; border: none; spacing: 6px; }

/* -------- helpers -------- */
QLabel#Hint { color: #8A8F9C; }
QLabel#SectionHeader {
    color: #FFFFFF; font-weight: 700; font-size: 14px;
    padding: 2px 0;
}
"""
