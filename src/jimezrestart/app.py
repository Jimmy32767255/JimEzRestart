"""Application entry point."""

from __future__ import annotations

import argparse
import sys

from PyQt6.QtWidgets import QApplication

from . import APP_ID, APP_NAME, __version__
from .detect import detect_desktop, detect_system
from .kernels import enumerate_kernels
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jimezrestart",
        description="Restart the desktop, the running kernel or the whole system.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="show the interface with sample data and do not perform any action",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    parser = build_parser()
    args, qt_args = parser.parse_known_args(argv[1:])

    app = QApplication([argv[0], *qt_args])
    app.setApplicationName("jimezrestart")
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("jimezrestart")
    app.setOrganizationName("Jimmy32767255")
    app.setOrganizationDomain("github.com")
    apply_theme(app)

    if args.demo:
        from .demo import demo_data

        system, desktop, kernels = demo_data()
        window = MainWindow(system, desktop, kernels, demo=True)
    else:
        system = detect_system()
        desktop = detect_desktop(system)
        kernels = enumerate_kernels()
        window = MainWindow(system, desktop, kernels)

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
