import tarfile
import pytest
from pathlib import Path
from ballbreaker.core.extractor import (
    check_tarball,
    extract_tarball,
    find_executables,
    is_writable,
    list_tarball_executables,
)


@pytest.fixture
def dummy_tarball(tmp_path) -> Path:
    """Creates a temporary tarball for testing."""
    archive_path = tmp_path / "test_app.tar.gz"
    app_dir = tmp_path / "test-app"
    app_dir.mkdir()

    # Create an executable script in root
    run_script = app_dir / "run.sh"
    run_script.write_text("#!/bin/sh\necho 'hello'", encoding="utf-8")
    run_script.chmod(0o755)

    # Create a non-executable file
    readme = app_dir / "README.md"
    readme.write_text("info file", encoding="utf-8")
    readme.chmod(0o644)

    # Create an executable inside bin/
    bin_dir = app_dir / "bin"
    bin_dir.mkdir()
    bin_helper = bin_dir / "helper"
    bin_helper.write_text("#!/bin/sh\necho 'helper'", encoding="utf-8")
    bin_helper.chmod(0o755)

    # Build tar.gz
    with tarfile.open(archive_path, "w:gz") as tar:
        # Add files relative to tmp_path to preserve "test-app/..." structure
        tar.add(run_script, arcname="test-app/run.sh")
        tar.add(readme, arcname="test-app/README.md")
        tar.add(bin_helper, arcname="test-app/bin/helper")

    return archive_path


def test_check_tarball(dummy_tarball):
    is_valid, top_level = check_tarball(dummy_tarball)
    assert is_valid is True
    assert top_level == "test-app"


def test_check_tarball_invalid(tmp_path):
    bad_file = tmp_path / "not_tar.tar.gz"
    bad_file.write_text("definitely not a tar", encoding="utf-8")
    is_valid, top_level = check_tarball(bad_file)
    assert is_valid is False
    assert top_level is None


def test_extract_tarball(dummy_tarball, tmp_path):
    target = tmp_path / "installed_app"
    extract_tarball(dummy_tarball, target)

    assert target.exists()
    assert (target / "test-app" / "run.sh").exists()
    assert (target / "test-app" / "README.md").exists()
    assert (target / "test-app" / "bin" / "helper").exists()


def test_find_executables(dummy_tarball, tmp_path):
    target = tmp_path / "installed_app"
    extract_tarball(dummy_tarball, target)

    # Scan the extracted files
    execs = find_executables(target)

    # Execs should contain relative paths to 'installed_app'
    # Wait, the structure inside is test-app/run.sh and test-app/bin/helper
    # Let's map them to strings for easier matching
    exec_strings = [p.as_posix() for p in execs]

    assert "test-app/run.sh" in exec_strings
    assert "test-app/bin/helper" in exec_strings
    assert "test-app/README.md" not in exec_strings

    # The sorting should put the root executable first
    assert exec_strings[0] == "test-app/run.sh"
    assert exec_strings[1] == "test-app/bin/helper"


def test_is_writable(tmp_path):
    assert is_writable(tmp_path) is True
    # A path that doesn't exist yet but parent does
    assert is_writable(tmp_path / "new_dir" / "sub_dir") is True


def test_list_tarball_executables(dummy_tarball):
    execs = list_tarball_executables(dummy_tarball)
    assert "test-app/run.sh" in execs
    assert "test-app/bin/helper" in execs
    assert "test-app/README.md" not in execs

    # Verify sorting
    assert execs[0] == "test-app/run.sh"
    assert execs[1] == "test-app/bin/helper"
