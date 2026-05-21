import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QFileDialog,
    QGroupBox,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import QThread, Signal

from ballbreaker.core.extractor import (
    check_tarball,
    extract_tarball,
    list_tarball_executables,
    is_writable,
)
from ballbreaker.core.desktop_entry import create_desktop_entry, create_symlink
from ballbreaker.core.config import load_config, save_config
from ballbreaker.gui.widgets.dropzone import DropZone
from ballbreaker.gui.stylesheet import STYLE


class InstallWorker(QThread):
    """
    Worker thread to run the installation process in the background.
    Prevents the main GUI from freezing during extraction.
    """

    status_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(
        self,
        tarball_path: Path,
        app_name: str,
        target_dir: Path,
        bin_dir: Path,
        desktop_dir: Path,
        exec_rel: Path,
        icon_path: Optional[Path],
        elevate: bool,
        terminal: bool,
    ):
        super().__init__()
        self.tarball_path = tarball_path
        self.app_name = app_name
        self.target_dir = target_dir
        self.bin_dir = bin_dir
        self.desktop_dir = desktop_dir
        self.exec_rel = exec_rel
        self.icon_path = icon_path
        self.elevate = elevate
        self.terminal = terminal

    def run(self):
        try:
            # 1. Extract tarball
            self.status_signal.emit(f"Extracting tarball to {self.target_dir}...")
            extract_tarball(
                archive_path=self.tarball_path,
                target_dir=self.target_dir,
                use_elevation=self.elevate,
            )

            # Resolve the main executable absolute path
            # If the tarball has a single root dir (e.g. firefox/), the relative path is firefox/firefox
            # We already have the relative path from the tarball members.
            main_exec = self.target_dir / self.exec_rel

            # Ensure permissions are correct on the extracted binary
            # Especially if extracted via pkexec, normal users might need exec bits.
            # But if extracted elevated, standard tar preserves bits. Let's make sure it's runnable.

            # 2. Create symbolic link in bin dir
            self.status_signal.emit("Creating symbolic link...")
            link_name = self.app_name.lower().replace(" ", "-")

            try:
                link_path = create_symlink(
                    src_path=main_exec,
                    link_name=link_name,
                    bin_dir=self.bin_dir,
                    use_elevation=self.elevate,
                )
                self.status_signal.emit(f"Symbolic link created at {link_path}")
                exec_for_desktop = link_path
            except Exception as e:
                self.status_signal.emit(
                    f"Warning: Symlink failed ({e}). Desktop entry will link directly."
                )
                exec_for_desktop = main_exec

            # 3. Create desktop launcher entry
            self.status_signal.emit("Generating desktop entry...")
            desktop_path = create_desktop_entry(
                name=self.app_name,
                exec_path=exec_for_desktop,
                icon_path=self.icon_path,
                terminal=self.terminal,
                categories=["Utility"],
                target_dir=self.desktop_dir,
            )

            self.status_signal.emit(f"Desktop launcher created at {desktop_path}")
            self.finished_signal.emit(
                True,
                f"Successfully installed {self.app_name}!\n\nLauncher: {desktop_path.name}",
            )

        except Exception as e:
            self.finished_signal.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ballbreaker 🍒")
        self.resize(560, 680)
        self.setStyleSheet(STYLE)

        self.selected_tarball: Optional[Path] = None
        self.worker: Optional[InstallWorker] = None
        self.config = load_config()

        self.init_ui()

    def init_ui(self):
        # Main widget & layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header layout
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()

        title_label = QLabel("Ballbreaker 🍒", self)
        title_label.setObjectName("HeaderTitle")
        subtitle_label = QLabel(
            "Linux Tarball Installer & Desktop Shortcut Generator", self
        )
        subtitle_label.setObjectName("HeaderSubtitle")

        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Drop Zone
        self.drop_zone = DropZone(self)
        self.drop_zone.fileDropped.connect(self.on_file_selected)
        main_layout.addWidget(self.drop_zone, stretch=1)

        # Details Group Box (Initially disabled)
        self.details_group = QGroupBox("Application Configuration", self)
        self.details_group.setEnabled(False)

        group_layout = QGridLayout(self.details_group)
        group_layout.setContentsMargins(15, 20, 15, 15)
        group_layout.setSpacing(12)

        # App Name
        group_layout.addWidget(QLabel("App Name:", self), 0, 0)
        self.name_edit = QLineEdit(self)
        self.name_edit.textChanged.connect(self.update_default_paths)
        group_layout.addWidget(self.name_edit, 0, 1, 1, 2)

        # Target Install Location
        group_layout.addWidget(QLabel("Install Directory:", self), 1, 0)
        self.target_edit = QLineEdit(self)
        self.target_btn = QPushButton("Browse...", self)
        self.target_btn.clicked.connect(self.browse_target_dir)
        group_layout.addWidget(self.target_edit, 1, 1)
        group_layout.addWidget(self.target_btn, 1, 2)

        # Executable Dropdown
        group_layout.addWidget(QLabel("Main Executable:", self), 2, 0)
        self.exec_combo = QComboBox(self)
        group_layout.addWidget(self.exec_combo, 2, 1, 1, 2)

        # Symlink Directory
        group_layout.addWidget(QLabel("Symlink Path:", self), 3, 0)
        self.bin_edit = QLineEdit(self)
        self.bin_edit.setText(self.config["bin_dir"])
        self.bin_btn = QPushButton("Browse...", self)
        self.bin_btn.clicked.connect(self.browse_bin_dir)
        group_layout.addWidget(self.bin_edit, 3, 1)
        group_layout.addWidget(self.bin_btn, 3, 2)

        # Desktop Entry Location
        group_layout.addWidget(QLabel("Shortcut Location:", self), 4, 0)
        self.desktop_edit = QLineEdit(self)
        self.desktop_edit.setText(self.config["desktop_dir"])
        self.desktop_btn = QPushButton("Browse...", self)
        self.desktop_btn.clicked.connect(self.browse_desktop_dir)
        group_layout.addWidget(self.desktop_edit, 4, 1)
        group_layout.addWidget(self.desktop_btn, 4, 2)

        # Icon Location
        group_layout.addWidget(QLabel("Icon File:", self), 5, 0)
        self.icon_edit = QLineEdit(self)
        self.icon_btn = QPushButton("Browse...", self)
        self.icon_btn.clicked.connect(self.browse_icon)
        group_layout.addWidget(self.icon_edit, 5, 1)
        group_layout.addWidget(self.icon_btn, 5, 2)

        # Privilege Elevation Checkbox
        self.elevate_check = QCheckBox(
            "Request system administrative privileges (pkexec/sudo) if needed", self
        )
        self.elevate_check.setChecked(self.config["elevate"])
        group_layout.addWidget(self.elevate_check, 6, 0, 1, 3)

        # Terminal Checkbox
        self.terminal_check = QCheckBox(
            "Run application inside a terminal window (Terminal=true)", self
        )
        self.terminal_check.setChecked(False)
        group_layout.addWidget(self.terminal_check, 7, 0, 1, 3)

        # Save Defaults Button
        self.save_defaults_btn = QPushButton("Save Paths as Defaults", self)
        self.save_defaults_btn.clicked.connect(self.save_current_as_defaults)
        group_layout.addWidget(self.save_defaults_btn, 8, 0, 1, 3)

        main_layout.addWidget(self.details_group)

        # Install Button & Progress Bar
        self.install_btn = QPushButton("Install Application", self)
        self.install_btn.setObjectName("PrimaryButton")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.start_install)
        main_layout.addWidget(self.install_btn)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status Bar
        self.statusBar().showMessage("Ready. Drop a tarball to get started.")

    def on_file_selected(self, file_path: Path):
        self.selected_tarball = file_path
        self.statusBar().showMessage(f"Loaded: {file_path.name}")

        # Check tarball validity
        is_valid, top_level = check_tarball(file_path)
        if not is_valid:
            QMessageBox.critical(
                self,
                "Invalid File",
                f"The file '{file_path.name}' is not a valid or readable tarball archive.",
            )
            self.selected_tarball = None
            self.statusBar().showMessage("Ready.")
            return

        # Derive initial App Name
        app_name = ""
        if top_level:
            # e.g., firefox-124.0.1 -> Firefox 124.0.1
            app_name = top_level.replace("-", " ").title()
        else:
            name = file_path.name
            for suffix in [".tar.gz", ".tar.xz", ".tar.bz2", ".tar", ".tgz"]:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break
            app_name = name.replace("-", " ").title()

        self.name_edit.setText(app_name)

        # Populate executables dropdown
        self.exec_combo.clear()
        executables = list_tarball_executables(file_path)
        if executables:
            self.exec_combo.addItems(executables)
            self.exec_combo.setCurrentIndex(0)
        else:
            self.exec_combo.addItem("(No executables found in archive index)")

        # Try to locate icon files inside tarball
        icon_candidates = [
            e for e in executables if e.lower().endswith((".png", ".svg"))
        ]
        if icon_candidates:
            # We can't link directly to the icon file until it is extracted!
            # So we set it to a future extracted path: target_dir / candidate
            # Let's save the first candidate as our guessed icon relative path
            # The actual path will update once install starts.
            # But let's show the user we found something.
            pass

        # Enable config and install
        self.details_group.setEnabled(True)
        self.install_btn.setEnabled(True)

        # Force default path updates
        self.update_default_paths(app_name)

    def update_default_paths(self, app_name: str):
        if not app_name:
            return

        # Clean folder name
        folder_name = app_name.lower().replace(" ", "-")

        # If target has not been manually changed, update it
        # Default to install_dir/folder_name from config
        self.target_edit.setText(str(Path(self.config["install_dir"]) / folder_name))

    # File browsing utilities
    def browse_target_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Install Directory", self.target_edit.text()
        )
        if dir_path:
            self.target_edit.setText(dir_path)

    def browse_bin_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Symlink Directory", self.bin_edit.text()
        )
        if dir_path:
            self.bin_edit.setText(dir_path)

    def browse_desktop_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Launcher Directory", self.desktop_edit.text()
        )
        if dir_path:
            self.desktop_edit.setText(dir_path)

    def browse_icon(self):
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon File",
            self.icon_edit.text(),
            "Image Files (*.png *.svg *.jpg *.xpm)",
        )
        if file_path_str:
            self.icon_edit.setText(file_path_str)

    # Start installation
    def start_install(self):
        if not self.selected_tarball:
            return

        app_name = self.name_edit.text().strip()
        if not app_name:
            QMessageBox.warning(
                self, "Validation Error", "Application name cannot be empty."
            )
            return

        target_dir = Path(self.target_edit.text().strip())
        bin_dir = Path(self.bin_edit.text().strip())
        desktop_dir = Path(self.desktop_edit.text().strip())

        # Selected executable
        exec_text = self.exec_combo.currentText()
        if not exec_text or exec_text.startswith("("):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select or specify a valid executable path.",
            )
            return

        exec_rel = Path(exec_text)

        # Icon
        icon_path_str = self.icon_edit.text().strip()
        icon_path = Path(icon_path_str) if icon_path_str else None

        # If the icon path is relative and we found it inside the tarball, resolve it relative to target_dir
        if icon_path and not icon_path.is_absolute():
            icon_path = target_dir / icon_path

        elevate = self.elevate_check.isChecked()

        # Check if we need root elevation and warn user
        need_opt_write = not is_writable(target_dir)
        need_bin_write = not is_writable(bin_dir)

        if (need_opt_write or need_bin_write) and not elevate:
            res = QMessageBox.question(
                self,
                "Permission Warning",
                "Writing to the target locations requires administrative privileges, but elevation is disabled.\n\nWould you like to enable elevation and proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if res == QMessageBox.StandardButton.Yes:
                self.elevate_check.setChecked(True)
                elevate = True
            else:
                return

        # Disable UI elements during install
        self.details_group.setEnabled(False)
        self.install_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Busy indicator
        self.drop_zone.setEnabled(False)

        # Setup and start background thread worker
        self.worker = InstallWorker(
            tarball_path=self.selected_tarball,
            app_name=app_name,
            target_dir=target_dir,
            bin_dir=bin_dir,
            desktop_dir=desktop_dir,
            exec_rel=exec_rel,
            icon_path=icon_path,
            elevate=elevate,
            terminal=self.terminal_check.isChecked(),
        )
        self.worker.status_signal.connect(self.on_worker_status)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_status(self, message: str):
        self.statusBar().showMessage(message)

    def on_worker_finished(self, success: bool, message: str):
        # Restore UI
        self.progress_bar.setVisible(False)
        self.install_btn.setVisible(True)
        self.details_group.setEnabled(True)
        self.drop_zone.setEnabled(True)

        if success:
            QMessageBox.information(self, "Installation Complete", message)
            self.statusBar().showMessage("Install completed successfully.")
            # Clear/reset file choice
            self.selected_tarball = None
            self.name_edit.clear()
            self.target_edit.clear()
            self.exec_combo.clear()
            self.icon_edit.clear()
            self.terminal_check.setChecked(False)
            self.details_group.setEnabled(False)
            self.install_btn.setEnabled(False)
        else:
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"An error occurred during installation:\n\n{message}",
            )
            self.statusBar().showMessage("Install failed.")

        # Clean up worker thread
        self.worker = None

    def save_current_as_defaults(self):
        """
        Saves the current paths and options in details form as defaults
        to ~/.config/ballbreaker/config.json.
        """
        target_dir = Path(self.target_edit.text().strip())
        app_folder_name = self.name_edit.text().strip().lower().replace(" ", "-")

        # If the target dir matches the app folder name pattern, extract its parent dir
        if app_folder_name and target_dir.name == app_folder_name:
            install_dir = target_dir.parent
        else:
            install_dir = target_dir

        new_config = {
            "install_dir": str(install_dir),
            "bin_dir": self.bin_edit.text().strip(),
            "desktop_dir": self.desktop_edit.text().strip(),
            "elevate": self.elevate_check.isChecked(),
        }

        if save_config(new_config):
            self.config = new_config
            QMessageBox.information(
                self,
                "Defaults Saved",
                "Your directory paths and permission preferences have been saved as defaults successfully!",
            )
            self.statusBar().showMessage("Default configurations saved successfully.")
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save configuration defaults to ~/.config/ballbreaker/config.json",
            )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
