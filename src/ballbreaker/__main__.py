import sys
from ballbreaker.cli import run_cli


def main():
    # If the user explicitly asks for CLI mode or passes CLI-specific arguments, run in CLI mode.
    # Otherwise, default to starting the PySide6 GUI application.
    if "--cli" in sys.argv or "-c" in sys.argv:
        args = [arg for arg in sys.argv[1:] if arg not in ("--cli", "-c")]
        sys.exit(run_cli(args))
    elif len(sys.argv) > 1 and any(
        arg in sys.argv for arg in ("-t", "--tarball", "-h", "--help")
    ):
        # If they specify tarball options or standard help, run the CLI
        sys.exit(run_cli(sys.argv[1:]))
    else:
        try:
            from ballbreaker.gui.app import main as gui_main

            gui_main()
        except ImportError as e:
            print(f"Error starting GUI: {e}", file=sys.stderr)
            print("Falling back to CLI mode...", file=sys.stderr)
            sys.exit(run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
