import os
import tarfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


class ExtractorError(Exception):
    """Base exception for extraction errors."""

    pass


class PermissionRequiredError(ExtractorError):
    """Raised when target path is not writable and elevation is required."""

    pass


def is_writable(path: Path) -> bool:
    """
    Check if a path (or its nearest existing parent) is writable.
    """
    current = path
    while not current.exists():
        if current.parent == current:  # reached root
            return False
        current = current.parent
    return os.access(current, os.W_OK)


def check_tarball(archive_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Verify if the file is a valid tarball and return its structure details.
    Returns (is_valid, top_level_dir_name).
    """
    if not archive_path.exists() or not archive_path.is_file():
        return False, None

    try:
        if not tarfile.is_tarfile(str(archive_path)):
            return False, None

        with tarfile.open(archive_path, "r") as tar:
            members = tar.getmembers()
            if not members:
                return True, None

            # Check if all files are under a single top-level directory
            # e.g., firefox/firefox, firefox/browser/etc.
            first_member_parts = Path(members[0].name).parts
            if not first_member_parts:
                return True, None

            top_level = first_member_parts[0]
            for member in members:
                parts = Path(member.name).parts
                if not parts or parts[0] != top_level:
                    return True, None  # No single top-level directory

            return True, top_level
    except Exception:
        return False, None


def extract_tarball(
    archive_path: Path, target_dir: Path, use_elevation: bool = False
) -> None:
    """
    Extract a tarball to the target directory.
    If the directory is not writable and use_elevation is True, uses pkexec/sudo.
    """
    if not archive_path.exists():
        raise ExtractorError(f"Archive not found: {archive_path}")

    # Ensure target directory path
    target_dir = target_dir.resolve()

    # If the target path exists and is not empty, raise error or let user handle it.
    # For now, let's create the folder if it does not exist.
    writable = is_writable(target_dir)

    if not writable:
        if not use_elevation:
            raise PermissionRequiredError(
                f"Target directory '{target_dir}' is not writable. Elevation required."
            )
        else:
            _extract_elevated(archive_path, target_dir)
            return

    # Normal user extraction
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r") as tar:
            # Safer extraction to prevent path traversal (zip slip / tar slip)
            # In Python 3.12+, extractall has filter parameters. We can use a basic sanitation.
            def is_safe_path(base_dir: Path, target_path: Path) -> bool:
                try:
                    # Check if resolved path is inside base_dir
                    resolved_target = (base_dir / target_path).resolve()
                    return (
                        base_dir.resolve() in resolved_target.parents
                        or base_dir.resolve() == resolved_target
                    )
                except Exception:
                    return False

            safe_members = []
            for member in tar.getmembers():
                if is_safe_path(target_dir, Path(member.name)):
                    safe_members.append(member)
                else:
                    print(f"Skipping potentially unsafe path: {member.name}")

            tar.extractall(
                path=target_dir,
                members=safe_members,
                filter="fully_trusted" if hasattr(tarfile, "fully_trusted") else None,
            )
    except Exception as e:
        raise ExtractorError(f"Failed to extract tarball: {e}")


def _extract_elevated(archive_path: Path, target_dir: Path) -> None:
    """
    Extract a tarball to a system location requiring root privileges.
    Copies tarball to /tmp, creates directory using pkexec, extracts it, and cleans up.
    """
    pkexec = shutil.which("pkexec")
    sudo = shutil.which("sudo")
    elevator = pkexec if pkexec else sudo

    if not elevator:
        raise ExtractorError(
            "Administrative privileges required but neither pkexec nor sudo is installed."
        )

    # Create temporary path in /tmp readable/writable by everyone
    temp_archive = Path("/tmp") / f"ballbreaker_{os.getpid()}_{archive_path.name}"
    try:
        shutil.copy2(archive_path, temp_archive)
        # Ensure it's readable
        temp_archive.chmod(0o644)
    except Exception as e:
        raise ExtractorError(f"Failed to copy archive to temporary directory: {e}")

    try:
        # Step 1: Create target directory
        cmd_mkdir = [elevator, "mkdir", "-p", str(target_dir)]
        res_mkdir = subprocess.run(cmd_mkdir, capture_output=True, text=True)
        if res_mkdir.returncode != 0:
            raise ExtractorError(
                f"Failed to create target directory: {res_mkdir.stderr}"
            )

        # Step 2: Extract tarball using system tar
        # --strip-components option is useful, but let's let tar extract normally.
        # We can extract directly inside target_dir.
        cmd_tar = [elevator, "tar", "-xf", str(temp_archive), "-C", str(target_dir)]
        res_tar = subprocess.run(cmd_tar, capture_output=True, text=True)
        if res_tar.returncode != 0:
            raise ExtractorError(f"Extraction failed: {res_tar.stderr}")

    finally:
        if temp_archive.exists():
            try:
                temp_archive.unlink()
            except Exception:
                pass


def find_executables(directory: Path) -> List[Path]:
    """
    Find all executable files in the target directory.
    Returns list of paths relative to the input directory.
    """
    executables = []
    directory_resolved = directory.resolve()

    # We walk the directory and find files that are executable.
    for root, dirs, files in os.walk(directory_resolved):
        for file in files:
            full_path = Path(root) / file
            # Check executable bit
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                # Save path relative to directory
                executables.append(full_path.relative_to(directory_resolved))

    # Sort executables: put root files first, then bin/ files, then others
    def sort_key(p: Path) -> Tuple[int, int, str]:
        parts = p.parts
        # Files directly in the root of the extract folder are highly likely main binaries
        if len(parts) == 1:
            return (0, 0, p.name)
        # Files in 'bin/' are next
        if parts[0] == "bin":
            return (1, len(parts), p.name)
        # Others
        return (2, len(parts), p.name)

    executables.sort(key=sort_key)
    return executables


def list_tarball_executables(archive_path: Path) -> List[str]:
    """
    List relative paths of executable files inside the tarball without extracting.
    """
    execs = []
    try:
        with tarfile.open(archive_path, "r") as tar:
            members = tar.getmembers()
            for m in members:
                # Check if it is a regular file
                if m.isreg():
                    # Check if executable permission bit is set
                    is_exec = (m.mode & 0o111) != 0
                    is_script = m.name.endswith(".sh")
                    parts = Path(m.name).parts
                    in_bin = "bin" in parts

                    if is_exec or is_script or in_bin:
                        execs.append(m.name)
    except Exception:
        pass

    # Sort executables by likelihood
    def sort_key(s: str) -> Tuple[int, int, str]:
        p = Path(s)
        parts = p.parts
        # If there is a top-level directory (which is very common), strip it for likelihood sorting
        sub_parts = parts[1:] if len(parts) > 1 else parts

        if len(sub_parts) == 1:
            return (0, 0, p.name)
        if len(sub_parts) == 2 and sub_parts[0] == "bin":
            return (0, 1, p.name)
        if "bin" in sub_parts:
            return (1, len(sub_parts), p.name)
        return (2, len(sub_parts), p.name)

    execs.sort(key=sort_key)
    return execs
