from pathlib import Path
from unittest.mock import patch
from ballbreaker.cli import run_cli, parse_args


def test_parse_args():
    args = parse_args(
        [
            "-t",
            "test.tar.gz",
            "-n",
            "My App",
            "-d",
            "/custom/opt",
            "-b",
            "/custom/bin",
            "-s",
            "/custom/shortcuts",
            "-x",
            "bin/start",
            "-e",
            "--icon",
            "/custom/icon.png",
            "--run-in-terminal",
        ]
    )

    assert args.tarball == Path("test.tar.gz")
    assert args.name == "My App"
    assert args.target_dir == Path("/custom/opt")
    assert args.bin_dir == Path("/custom/bin")
    assert args.desktop_dir == Path("/custom/shortcuts")
    assert args.exec_rel == Path("bin/start")
    assert args.elevate is True
    assert args.icon == Path("/custom/icon.png")
    assert args.run_in_terminal is True


@patch("ballbreaker.cli.check_tarball")
@patch("ballbreaker.cli.extract_tarball")
@patch("ballbreaker.cli.find_executables")
@patch("ballbreaker.cli.create_symlink")
@patch("ballbreaker.cli.create_desktop_entry")
def test_run_cli_success(
    mock_create_desktop,
    mock_create_symlink,
    mock_find_executables,
    mock_extract_tarball,
    mock_check_tarball,
    tmp_path,
):
    # Setup mocks
    tarball = tmp_path / "test.tar.gz"
    tarball.touch()

    mock_check_tarball.return_return = (True, "test-app")
    mock_check_tarball.return_value = (True, "test-app")

    # Return mock executable relative paths
    mock_find_executables.return_value = [Path("test-app/run.sh")]

    mock_create_symlink.return_value = tmp_path / "bin" / "test-app"
    mock_create_desktop.return_value = tmp_path / "shortcuts" / "test-app.desktop"

    # Run CLI
    status = run_cli(
        [
            "-t",
            str(tarball),
            "-n",
            "Test App",
            "-d",
            str(tmp_path / "opt"),
            "-b",
            str(tmp_path / "bin"),
            "-s",
            str(tmp_path / "shortcuts"),
            "--run-in-terminal",
        ]
    )

    assert status == 0
    mock_check_tarball.assert_called_once()
    mock_extract_tarball.assert_called_once_with(
        tarball.resolve(), tmp_path / "opt", use_elevation=False
    )
    mock_find_executables.assert_called_once()
    mock_create_symlink.assert_called_once()
    mock_create_desktop.assert_called_once_with(
        name="Test App",
        exec_path=tmp_path / "bin" / "test-app",
        icon_path=None,
        terminal=True,
        categories=["Utility"],
        target_dir=tmp_path / "shortcuts",
    )
