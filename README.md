# Ballbreaker 🍒

Ballbreaker is a modern Linux GUI and CLI application for installing and managing desktop entries for software distributed as tarballs. 

It safely extracts tarballs to system paths (like `/opt`) or custom directory hierarchies (like `~/Apps`), creates symbolic links for executable files, and generates compliant `.desktop` launch entries registered with your desktop environment.

## Features
- **Aesthetic GUI**: Modern dark-theme PySide6 interface.
- **Configurable Paths**: Choose where tarballs are extracted and where desktop shortcuts are saved.
- **Elevation Support**: Prompts for password authorization using standard system-wide Polkit (`pkexec`) / `sudo` only when writing to root-protected directories.
- **Drag and Drop**: Drag a `.tar.gz`, `.tar.xz`, or `.tar.bz2` file directly into the application window.
- **Auto-Icon Resolution**: Extracts icons packaged with the tarball or lets you select/generate one.
- **Headless CLI Mode**: Automate installations from shell script workflows.

## Getting Started

### Prerequisites
- Python 3.14+
- `uv` (recommended)

### Run the App
To run the GUI:
```bash
uv run python -m ballbreaker
```

To run the CLI:
```bash
uv run python -m ballbreaker --cli --tarball /path/to/archive.tar.gz
```

### Run Tests
```bash
uv run pytest
```
