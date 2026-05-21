from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Signal, Qt
from pathlib import Path


class DropZone(QFrame):
    fileDropped = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSpacing(10)

        # Icon/Symbol label (emoji or text)
        self.icon_label = QLabel("📦", self)
        self.icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Primary prompt
        self.text_label = QLabel("Drag & Drop Tarball Here", self)
        self.text_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Secondary prompt
        self.sub_label = QLabel("or click to browse from files", self)
        self.sub_label.setStyleSheet(
            "font-size: 12px; color: #a1a1aa; background: transparent;"
        )
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.icon_label)
        self.main_layout.addWidget(self.text_label)
        self.main_layout.addWidget(self.sub_label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                # Basic check if it's a file
                path = Path(urls[0].toLocalFile())
                suffixes = [".tar", ".gz", ".xz", ".bz2", ".tgz"]
                if any(path.name.endswith(s) for s in suffixes):
                    event.acceptProposedAction()
                    self.setProperty("hovered", "true")
                    self.style().unpolish(self)
                    self.style().polish(self)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("hovered", "false")
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event):
        self.setProperty("hovered", "false")
        self.style().unpolish(self)
        self.style().polish(self)

        urls = event.mimeData().urls()
        if urls:
            file_path = Path(urls[0].toLocalFile())
            self.fileDropped.emit(file_path)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path_str, _ = QFileDialog.getOpenFileName(
                self,
                "Select Tarball",
                "",
                "Tarballs (*.tar.gz *.tar.xz *.tar.bz2 *.tar *.tgz)",
            )
            if file_path_str:
                self.fileDropped.emit(Path(file_path_str))
            event.accept()
        else:
            super().mousePressEvent(event)
