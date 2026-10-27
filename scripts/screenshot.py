#!/usr/bin/env python3
"""Render the demo window to screenshots/main.png (for the README)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication

from jimezrestart.demo import demo_data
from jimezrestart.ui.main_window import MainWindow
from jimezrestart.ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    apply_theme(app)
    window = MainWindow(*demo_data(), demo=True)
    window.resize(840, 1000)
    window.show()
    app.processEvents()
    target = Path(__file__).resolve().parent.parent / "screenshots" / "main.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not window.grab().save(str(target), "PNG"):
        print("failed to save screenshot", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
