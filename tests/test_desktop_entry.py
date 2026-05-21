import pytest
from pathlib import Path
from ballbreaker.core.desktop_entry import (
    create_desktop_entry,
    create_symlink,
    LauncherError,
)


def test_create_desktop_entry(tmp_path):
    exec_path = tmp_path / "bin" / "myexec"
    exec_path.parent.mkdir()
    exec_path.touch()

    icon_path = tmp_path / "assets" / "icon.png"
    icon_path.parent.mkdir()
    icon_path.touch()

    desktop_dir = tmp_path / "desktop"

    file_path = create_desktop_entry(
        name="Test Application",
        exec_path=exec_path,
        icon_path=icon_path,
        comment="This is a test comment",
        terminal=True,
        categories=["Office", "Finance"],
        target_dir=desktop_dir,
    )

    assert file_path.name == "test-application.desktop"
    assert file_path.exists()

    # Read the file content
    content = file_path.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in content
    assert "Type=Application" in content
    assert "Name=Test Application" in content
    assert f"Exec={exec_path.resolve()}" in content
    assert f"Icon={icon_path.resolve()}" in content
    assert "Terminal=true" in content
    assert "Comment=This is a test comment" in content
    assert "Categories=Office;Finance;" in content


def test_create_symlink(tmp_path):
    src_bin = tmp_path / "src_app" / "bin_file"
    src_bin.parent.mkdir()
    src_bin.touch()

    bin_dir = tmp_path / "bin"

    link_path = create_symlink(src_path=src_bin, link_name="app-link", bin_dir=bin_dir)

    assert link_path.name == "app-link"
    assert link_path.is_symlink()
    assert link_path.resolve() == src_bin.resolve()
