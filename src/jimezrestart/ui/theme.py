"""Colours and Qt style sheet for JimEzRestart."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .. import paths


@dataclass(frozen=True)
class Palette:
    background: str = "#0e1014"
    surface: str = "#171a20"
    surface_alt: str = "#1b1f27"
    surface_raised: str = "#212631"
    border: str = "#282e39"
    border_strong: str = "#394253"
    text: str = "#e9ecf2"
    text_soft: str = "#c3cad8"
    muted: str = "#929bad"
    faint: str = "#687183"
    green: str = "#34d399"
    orange: str = "#fb923c"
    yellow: str = "#facc15"
    blue: str = "#60a5fa"
    red: str = "#f87171"
    green_tint: str = "#123127"
    orange_tint: str = "#33220f"
    yellow_tint: str = "#302a0c"
    blue_tint: str = "#14283f"


PALETTE = Palette()

ACCENTS = {
    "green": PALETTE.green,
    "orange": PALETTE.orange,
    "yellow": PALETTE.yellow,
    "blue": PALETTE.blue,
}

ACCENT_TINTS = {
    "green": PALETTE.green_tint,
    "orange": PALETTE.orange_tint,
    "yellow": PALETTE.yellow_tint,
    "blue": PALETTE.blue_tint,
}


def app_icon() -> QIcon:
    return QIcon(str(paths.icon_path()))


def _qss() -> str:
    p = PALETTE
    return f"""
QWidget {{
    background: transparent;
    color: {p.text};
    font-family: "Noto Sans CJK SC", "Noto Sans", "Source Han Sans SC", "DejaVu Sans", sans-serif;
    font-size: 12.5px;
}}
QMainWindow, QDialog {{
    background: {p.background};
}}
QWidget#root {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0c0e12, stop:0.55 #101318, stop:1 #12161d);
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 4px 2px 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #333b48;
    min-height: 32px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: #46505f;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0px;
    background: transparent;
}}

QFrame#card {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: 14px;
}}
QLabel {{
    background: transparent;
}}
QLabel#appTitle {{
    font-size: 21px;
    font-weight: 700;
    color: #f4f6fa;
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {p.faint};
}}
QLabel#versionBadge {{
    background: #1c222c;
    border: 1px solid #303948;
    border-radius: 10px;
    padding: 3px 10px;
    color: {p.muted};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#sectionTitle {{
    font-size: 12px;
    font-weight: 700;
    color: {p.muted};
    padding-left: 2px;
}}
QLabel#cardTitle {{
    font-size: 16px;
    font-weight: 700;
    color: #f1f4f9;
}}
QLabel#badge {{
    background: #222833;
    border: 1px solid #2f3745;
    border-radius: 9px;
    padding: 2px 9px;
    color: #aab3c4;
    font-size: 10.5px;
    font-weight: 600;
}}
QLabel#badge[accent="green"] {{ color: #8fe8be; border-color: #285943; background: #14291f; }}
QLabel#badge[accent="orange"] {{ color: #f8bd8a; border-color: #5e3a1e; background: #2a1d12; }}
QLabel#badge[accent="yellow"] {{ color: #f3dd83; border-color: #5b4d16; background: #2a250f; }}
QLabel#badge[accent="blue"] {{ color: #9dc9fb; border-color: #2b4c73; background: #152233; }}
QLabel#hint {{
    color: {p.muted};
    font-size: 11.5px;
    font-style: italic;
}}
QLabel#finePrint {{
    color: {p.faint};
    font-size: 10.5px;
}}
QLabel#fieldLabel {{
    color: {p.faint};
    font-size: 12px;
}}
QLabel#fieldValue {{
    color: {p.text_soft};
    font-size: 12.5px;
    font-weight: 500;
}}
QLabel#checkLabel {{
    color: {p.text_soft};
    font-size: 12.5px;
}}
QLabel#checkLabel:disabled {{
    color: {p.faint};
}}
QLabel#dialogTitle {{
    color: #f4f6fa;
    font-size: 20px;
    font-weight: 700;
}}
QLabel#emptyTitle {{
    color: {p.text};
    font-size: 16px;
    font-weight: 600;
}}
QLabel#emptyBody {{
    color: {p.muted};
    font-size: 12.5px;
}}
QLabel#code {{
    color: #cfe6ff;
    background: #14202e;
    border: 1px solid #24384f;
    border-radius: 5px;
    padding: 3px 7px;
    font-family: "JetBrains Mono", "Noto Sans Mono", monospace;
    font-size: 11.5px;
}}
QFrame#warningBox {{
    background: #2a1618;
    border: 1px solid #5c2a2f;
    border-radius: 10px;
}}
QFrame#warningBox QLabel {{
    color: #f3b6ba;
}}
QFrame#infoBox {{
    background: #152233;
    border: 1px solid #28425f;
    border-radius: 10px;
}}
QFrame#infoBox QLabel {{
    color: #b9d5f5;
}}
QLabel#status {{
    color: {p.muted};
    font-size: 11.5px;
}}
QLabel#status[level="error"] {{ color: {p.red}; }}
QLabel#status[level="ok"] {{ color: {p.green}; }}

QPushButton#actionButton {{
    border-radius: 9px;
    padding: 0 18px;
    min-height: 38px;
    font-size: 13.5px;
    font-weight: 600;
    border: 1px solid {p.border_strong};
    background: {p.surface_raised};
    color: {p.text};
}}
QPushButton#actionButton:hover {{
    background: #2a3140;
}}
QPushButton#actionButton:pressed {{
    background: #1d222c;
}}
QPushButton#actionButton[accent="green"] {{
    background: #143429;
    border-color: #2c6c51;
    color: #c9f7df;
}}
QPushButton#actionButton[accent="green"]:hover {{ background: #194434; }}
QPushButton#actionButton[accent="orange"] {{
    background: #3a2513;
    border-color: #7a4a22;
    color: #ffd9b8;
}}
QPushButton#actionButton[accent="orange"]:hover {{ background: #4a2e17; }}
QPushButton#actionButton[accent="yellow"] {{
    background: #332c0d;
    border-color: #6e5c19;
    color: #fbeaa3;
}}
QPushButton#actionButton[accent="yellow"]:hover {{ background: #433913; }}
QPushButton#actionButton[accent="blue"] {{
    background: #142a44;
    border-color: #2f5b8a;
    color: #cfe6ff;
}}
QPushButton#actionButton[accent="blue"]:hover {{ background: #1a3555; }}
QPushButton#actionButton[accent="red"] {{
    background: #3b1a1d;
    border-color: #7d3339;
    color: #ffc9cc;
}}
QPushButton#actionButton[accent="red"]:hover {{ background: #4a2024; }}
QPushButton#actionButton:disabled {{
    background: #181c23;
    border-color: #242a34;
    color: #5b6374;
}}
QPushButton#actionButton:focus {{
    border: 2px solid {p.blue};
}}
QPushButton#actionButton[accent="green"]:focus {{ border-color: {p.green}; }}
QPushButton#actionButton[accent="orange"]:focus {{ border-color: {p.orange}; }}
QPushButton#actionButton[accent="yellow"]:focus {{ border-color: {p.yellow}; }}
QPushButton[accent="blue"]:focus {{ border-color: {p.blue}; }}
QPushButton[accent="red"]:focus {{ border-color: {p.red}; }}
QPushButton#actionButton:disabled:focus {{
    border: 1px solid #242a34;
}}

QPushButton#methodButton {{
    text-align: left;
    padding: 8px 11px;
    border-radius: 9px;
    background: {p.surface_alt};
    border: 1px solid {p.border};
    color: #aeb7c8;
    font-size: 12px;
}}
QPushButton#methodButton:hover {{
    border-color: {p.border_strong};
    color: {p.text_soft};
}}
QPushButton#methodButton:checked {{
    background: #1d232d;
    border-color: #4a566a;
    color: #f0f4fa;
}}
QPushButton#methodButton[accent="green"]:checked {{ border-color: #2f7358; background: #15291f; }}
QPushButton#methodButton[accent="orange"]:checked {{ border-color: #7a4a22; background: #2a1d12; }}
QPushButton#methodButton[accent="yellow"]:checked {{ border-color: #6e5c19; background: #2a250f; }}
QPushButton#methodButton[accent="blue"]:checked {{ border-color: #2f5b8a; background: #152233; }}
QPushButton#methodButton:focus {{
    border: 2px solid {p.blue};
}}
QPushButton#methodButton:disabled {{
    background: #15181e;
    border-color: #222831;
    color: #5a6272;
}}

QPushButton#secondaryButton {{
    min-height: 38px;
    padding: 0 18px;
    border-radius: 8px;
    border: 1px solid {p.border_strong};
    background: transparent;
    color: {p.text_soft};
    font-size: 13px;
}}
QPushButton#secondaryButton:hover {{
    background: #232936;
    color: {p.text};
}}
QPushButton#secondaryButton:focus {{
    border: 2px solid {p.blue};
    color: {p.text};
}}

QPushButton#kernelButton {{
    text-align: left;
    padding: 11px 14px;
    border-radius: 9px;
    background: {p.surface_alt};
    border: 1px solid {p.border};
    color: {p.text_soft};
    font-size: 12.5px;
}}
QPushButton#kernelButton:hover {{
    border-color: {p.border_strong};
    background: #202631;
}}
QPushButton#kernelButton:checked {{
    border-color: #2f5b8a;
    background: #152233;
    color: #eaf4ff;
}}
QPushButton#kernelButton:focus {{
    border: 2px solid {p.blue};
    color: {p.text};
}}
QPushButton#kernelButton:disabled {{
    color: #5a6272;
    background: #15181e;
    border-color: #222831;
}}

QToolButton#menuButton {{
    color: {p.muted};
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 5px 9px;
    font-size: 12px;
    background: transparent;
}}
QToolButton#menuButton:hover {{
    background: #232936;
    color: {p.text_soft};
}}
QToolButton#menuButton:pressed {{
    background: #1b202a;
}}
QToolButton#menuButton:disabled {{
    color: #545c6b;
}}
QToolButton#menuButton:focus {{
    border: 2px solid {p.blue};
    color: {p.text_soft};
}}
QToolButton#menuButton::menu-indicator {{ image: none; width: 0px; }}

QMenu {{
    background: #1b2029;
    border: 1px solid #353e4d;
    border-radius: 9px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 26px 7px 28px;
    border-radius: 5px;
    color: {p.text_soft};
    font-size: 12.5px;
}}
QMenu::item:selected {{
    background: #2a3240;
    color: #ffffff;
}}
QMenu::item:disabled {{
    color: #5c6474;
}}
QMenu::separator {{
    height: 1px;
    background: #2c3340;
    margin: 5px 8px;
}}
QMenu::indicator {{
    width: 14px;
    height: 14px;
    left: 8px;
}}

QToolTip {{
    background: #232a35;
    color: #e9ecf2;
    border: 1px solid #3b4557;
    padding: 6px 8px;
    border-radius: 6px;
}}

QMessageBox {{
    background: {p.background};
}}
QMessageBox QLabel {{
    color: {p.text_soft};
}}
QMessageBox QPushButton {{
    min-width: 84px;
    min-height: 30px;
    padding: 0 14px;
    border-radius: 7px;
    border: 1px solid {p.border_strong};
    background: {p.surface_raised};
    color: {p.text};
}}
QMessageBox QPushButton:hover {{ background: #2a3140; }}
QMessageBox QPushButton:default {{
    border-color: #2c6c51;
    background: #143429;
    color: #c9f7df;
}}

QProgressBar {{
    border: 1px solid {p.border};
    border-radius: 4px;
    background: #151920;
    max-height: 7px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {p.green};
    border-radius: 3px;
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(_qss())
    app.setWindowIcon(app_icon())


def icon_path() -> Path:
    return paths.icon_path()
