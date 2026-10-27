#!/usr/bin/env python3
"""Render the demo window to screenshots/ (for the README).

Without arguments both themes are rendered: ``main.png`` (dark) and
``main-light.png``.  Pass ``dark`` or ``light`` to render a single one.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_SCALE_FACTOR", "1")

from PyQt6.QtWidgets import QApplication

from jimezrestart.demo import demo_data
from jimezrestart.ui.main_window import MainWindow
from jimezrestart.ui.theme import MODE_DARK, MODE_LIGHT, apply_theme, set_theme

TARGETS = {MODE_DARK: "main.png", MODE_LIGHT: "main-light.png"}


def render(app: QApplication, mode: str, target: Path) -> int:
    set_theme(mode, app)
    window = MainWindow(*demo_data(), demo=True)
    window.resize(840, 900)
    window.show()
    app.processEvents()
    ok = window.grab().save(str(target), "PNG")
    window.close()
    window.deleteLater()
    app.processEvents()
    if not ok:
        print(f"failed to save {target}", file=sys.stderr)
        return 1
    print(target)
    return 0


def main(argv: list[str]) -> int:
    app = QApplication([argv[0]])
    apply_theme(app)
    wanted = [argv[1]] if len(argv) > 1 else list(TARGETS)
    out_dir = Path(__file__).resolve().parent.parent / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    status = 0
    for mode in wanted:
        status |= render(app, mode, out_dir / TARGETS[mode])
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
