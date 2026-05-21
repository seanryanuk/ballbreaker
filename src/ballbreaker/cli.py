import sys
import argparse
from pathlib import Path
from ballbreaker.core.extractor import (
    check_tarball,
    extract_tarball,
    find_executables,
    is_writable,
    ExtractorError,
    PermissionRequiredError
)
from ballbreaker.core.desktop_entry import (
    create_desktop_entry,
    create_symlink,
    LauncherError
)
from ballbreaker.core.config import load_config

def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Ballbreaker - Install tarballs and create desktop entries."
    )
    parser.add_argument(
        "-t", "--tarball",
        required=True,
        type=Path,
        help="Path to the tarball archive."
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        help="Display name of the application (defaults to tarball folder/file name)."
    )
    parser.add_argument(
        "-d", "--target-dir",
        type=Path,
        help="Target folder for extraction (defaults to /opt/APPNAME)."
    )
    config = load_config()
    parser.add_argument(
        "-b", "--bin-dir",
        type=Path,
        default=Path(config["bin_dir"]),
        help=f"Directory to create the symbolic link in (default: {config['bin_dir']})."
    )
    parser.add_argument(
        "-s", "--desktop-dir",
        type=Path,
        default=Path(config["desktop_dir"]),
        help=f"Directory to place the .desktop entry (default: {config['desktop_dir']})."
    )
    parser.add_argument(
        "-x", "--exec-rel",
        type=Path,
        help="Relative path to the main executable inside the tarball (e.g., 'bin/my-app')."
    )
    parser.add_argument(
        "-e", "--elevate",
        action="store_true",
        help="Use elevation (pkexec/sudo) if permissions are needed."
    )
    parser.add_argument(
        "--icon",
        type=Path,
        help="Path to an icon file for the desktop entry."
    )
    parser.add_argument(
        "--run-in-terminal",
        action="store_true",
        help="Run the application in a terminal window (sets Terminal=true)."
    )
    return parser.parse_args(args)



def run_cli(args=None) -> int:
    parsed = parse_args(args)
    
    tarball_path: Path = parsed.tarball.resolve()
    if not tarball_path.exists():
        print(f"Error: Tarball not found: {tarball_path}", file=sys.stderr)
        return 1

    # Check tarball
    is_valid, top_level = check_tarball(tarball_path)
    if not is_valid:
        print(f"Error: Invalid tarball or corrupted archive: {tarball_path}", file=sys.stderr)
        return 1
        
    # Derive name
    app_name = parsed.name
    if not app_name:
        if top_level:
            app_name = top_level
        else:
            # strip suffix like .tar.gz, .tar.xz
            name = tarball_path.name
            for suffix in ['.tar.gz', '.tar.xz', '.tar.bz2', '.tar', '.tgz']:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            app_name = name

    # target-dir default
    target_dir = parsed.target_dir
    if not target_dir:
        config = load_config()
        # Default to install_dir/app_name
        target_dir = Path(config["install_dir"]) / app_name.lower().replace(" ", "-")

    print(f"Extracting '{tarball_path.name}' to '{target_dir}'...")

    try:
        extract_tarball(tarball_path, target_dir, use_elevation=parsed.elevate)
    except PermissionRequiredError:
        print(f"Permission denied to write to '{target_dir}'.", file=sys.stderr)
        print("Please rerun with --elevate flag or run as superuser.", file=sys.stderr)
        return 1
    except ExtractorError as e:
        print(f"Extraction Error: {e}", file=sys.stderr)
        return 1

    # Find executables
    executables = find_executables(target_dir)
    if not executables:
        print("Warning: No executable files found in the extracted directory.", file=sys.stderr)
        main_exec = None
    else:
        # If user specified executable path, check if it exists
        if parsed.exec_rel:
            full_exec_path = target_dir / parsed.exec_rel
            if not full_exec_path.exists() or not os.access(full_exec_path, os.X_OK):
                print(f"Error: Specified executable '{parsed.exec_rel}' not found or not executable.", file=sys.stderr)
                return 1
            main_exec = full_exec_path
        else:
            # Pick first candidate
            selected = executables[0]
            main_exec = target_dir / selected
            print(f"Detected main executable candidate: {selected}")
            if len(executables) > 1:
                print(f"Other candidates found: {[e.as_posix() for e in executables[1:]]}")

    if main_exec:
        # Create symlink
        link_name = app_name.lower().replace(" ", "-")
        try:
            link_path = create_symlink(
                src_path=main_exec,
                link_name=link_name,
                bin_dir=parsed.bin_dir,
                use_elevation=parsed.elevate
            )
            print(f"Created symbolic link: {link_path} -> {main_exec}")
            exec_for_desktop = link_path
        except Exception as e:
            print(f"Warning: Failed to create symbolic link: {e}. Desktop entry will point directly to binary.", file=sys.stderr)
            exec_for_desktop = main_exec

        # Create desktop entry
        try:
            desktop_path = create_desktop_entry(
                name=app_name,
                exec_path=exec_for_desktop,
                icon_path=parsed.icon,
                terminal=parsed.run_in_terminal,
                categories=["Utility"],
                target_dir=parsed.desktop_dir
            )
            print(f"Created desktop entry: {desktop_path}")
        except LauncherError as e:
            print(f"Error creating desktop entry: {e}", file=sys.stderr)
            return 1
            
    print(f"Successfully installed '{app_name}'!")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
