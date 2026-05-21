import shutil
import subprocess
from pathlib import Path
from typing import Optional, List

class LauncherError(Exception):
    """Base exception for launcher configuration errors."""
    pass


def create_desktop_entry(
    name: str,
    exec_path: Path,
    icon_path: Optional[Path] = None,
    comment: Optional[str] = None,
    terminal: bool = False,
    categories: Optional[List[str]] = None,
    target_dir: Optional[Path] = None,
    filename: Optional[str] = None
) -> Path:
    """
    Generate and save a standard Linux .desktop entry file.
    """
    # Resolve target directory (default to ~/.local/share/applications)
    if target_dir is None:
        target_dir = Path.home() / ".local" / "share" / "applications"
    
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize and create standard filename if not provided
    if filename is None:
        # Convert to lowercase, replace spaces with dashes
        sanitized_name = name.lower().replace(" ", "-")
        filename = f"{sanitized_name}.desktop"
    elif not filename.endswith(".desktop"):
        filename = f"{filename}.desktop"
        
    desktop_file_path = target_dir / filename

    # Categories string
    categories_str = ""
    if categories:
        categories_str = ";".join(categories) + ";"
    else:
        categories_str = "Utility;Development;"

    # Compile the .desktop file content
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={name}",
        f"Exec={exec_path.resolve()}",
        f"Terminal={'true' if terminal else 'false'}",
        f"Categories={categories_str}"
    ]

    if icon_path:
        lines.append(f"Icon={icon_path.resolve()}")
    if comment:
        lines.append(f"Comment={comment}")

    # Write content to file
    try:
        with open(desktop_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        
        # Ensure correct executable/readable permissions
        desktop_file_path.chmod(0o755)
        
        return desktop_file_path
    except Exception as e:
        raise LauncherError(f"Failed to create desktop entry file: {e}")


def create_symlink(
    src_path: Path,
    link_name: str,
    bin_dir: Optional[Path] = None,
    use_elevation: bool = False
) -> Path:
    """
    Create a symbolic link for the binary in a standard bin directory.
    Default bin directory is ~/.local/bin.
    If the target bin directory is not writable and use_elevation is True, use pkexec/sudo.
    """
    if bin_dir is None:
        bin_dir = Path.home() / ".local" / "bin"

    # Ensure source path is absolute
    src_path = src_path.resolve()
    
    # Target symlink path
    link_path = bin_dir / link_name
    
    # Check writability
    from ballbreaker.core.extractor import is_writable
    writable = is_writable(bin_dir)
    
    if not writable:
        if not use_elevation:
            raise LauncherError(
                f"Directory '{bin_dir}' is not writable. Elevation required for symlink."
            )
        else:
            _create_symlink_elevated(src_path, link_path)
            return link_path

    # Normal user symlink
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
        # Remove existing symlink or file if present
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(src_path)
        return link_path
    except Exception as e:
        raise LauncherError(f"Failed to create symbolic link: {e}")


def _create_symlink_elevated(src_path: Path, link_path: Path) -> None:
    """
    Create a symbolic link in a system path requiring elevation.
    """
    pkexec = shutil.which("pkexec")
    sudo = shutil.which("sudo")
    elevator = pkexec if pkexec else sudo
    
    if not elevator:
        raise LauncherError(
            "Administrative privileges required to write symlink, but neither pkexec nor sudo is available."
        )

    # Ensure parent dir exists
    parent_dir = link_path.parent
    cmd_mkdir = [elevator, "mkdir", "-p", str(parent_dir)]
    res_mkdir = subprocess.run(cmd_mkdir, capture_output=True, text=True)
    if res_mkdir.returncode != 0:
        raise LauncherError(f"Failed to create directory {parent_dir}: {res_mkdir.stderr}")

    # Remove existing link if present
    # Using 'rm -f' with elevator to avoid failures
    cmd_rm = [elevator, "rm", "-f", str(link_path)]
    subprocess.run(cmd_rm, capture_output=True)

    # Create link
    cmd_ln = [elevator, "ln", "-sf", str(src_path), str(link_path)]
    res_ln = subprocess.run(cmd_ln, capture_output=True, text=True)
    
    if res_ln.returncode != 0:
        raise LauncherError(f"Failed to create elevated symbolic link: {res_ln.stderr}")
