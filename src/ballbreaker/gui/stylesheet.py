# Premium Dark QSS Stylesheet for Ballbreaker

STYLE = """
QMainWindow {
    background-color: #121214;
}

QWidget {
    color: #e4e4e7;
    font-family: 'Segoe UI', 'Inter', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

QLabel {
    color: #e4e4e7;
}

QLabel#HeaderTitle {
    font-size: 24px;
    font-weight: bold;
    color: #ffffff;
    background: transparent;
}

QLabel#HeaderSubtitle {
    font-size: 12px;
    color: #a1a1aa;
    background: transparent;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #2d2d34;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: #1a1a1e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 5px;
    color: #a78bfa;
}

QLineEdit {
    background-color: #222227;
    border: 1px solid #2d2d34;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #7c4dff;
}

QLineEdit:focus {
    border: 1px solid #7c4dff;
    background-color: #25252b;
}

QLineEdit:disabled {
    color: #71717a;
    background-color: #18181b;
    border-color: #27272a;
}

QPushButton {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e4e4e7;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3f3f46;
    border-color: #52525b;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #18181b;
}

QPushButton#PrimaryButton {
    background-color: #7c4dff;
    border: 1px solid #8c62ff;
    color: #ffffff;
}

QPushButton#PrimaryButton:hover {
    background-color: #9e7cff;
    border-color: #af92ff;
}

QPushButton#PrimaryButton:pressed {
    background-color: #5b35d9;
}

QPushButton#PrimaryButton:disabled {
    background-color: #3f3f46;
    border-color: #3f3f46;
    color: #a1a1aa;
}

QComboBox {
    background-color: #222227;
    border: 1px solid #2d2d34;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    combobox-popup: 0;
}

QComboBox:focus {
    border: 1px solid #7c4dff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
}

QComboBox QAbstractItemView {
    background-color: #222227;
    border: 1px solid #2d2d34;
    selection-background-color: #7c4dff;
    selection-color: #ffffff;
    color: #ffffff;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #2d2d34;
    border-radius: 4px;
    background-color: #222227;
}

QCheckBox::indicator:hover {
    border-color: #7c4dff;
}

QCheckBox::indicator:checked {
    background-color: #7c4dff;
    border-color: #7c4dff;
}

QProgressBar {
    border: 1px solid #2d2d34;
    border-radius: 6px;
    text-align: center;
    background-color: #18181b;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #7c4dff;
    border-radius: 5px;
}

QStatusBar {
    background-color: #1a1a1e;
    color: #a1a1aa;
    border-top: 1px solid #2d2d34;
}

QStatusBar QLabel {
    color: #a1a1aa;
}

/* Beautiful custom dropzone widget styling */
QFrame#DropZone {
    background-color: #16161a;
    border: 2px dashed #3f3f46;
    border-radius: 12px;
}

QFrame#DropZone[hovered="true"] {
    background-color: #1d1b26;
    border: 2px dashed #7c4dff;
}
"""
