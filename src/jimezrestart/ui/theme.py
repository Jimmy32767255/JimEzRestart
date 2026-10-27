"""Colours and Qt style sheet for JimEzRestart.

The style sheet is generated from a :class:`Palette`, so the same rules produce
a dark and a light theme.  The application starts out following the desktop's
colour scheme and the toolbar button can pin either theme by hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import QApplication

from .. import paths

MODE_SYSTEM = "system"
MODE_DARK = "dark"
MODE_LIGHT = "light"
MODES = (MODE_SYSTEM, MODE_DARK, MODE_LIGHT)

MODE_LABELS = {MODE_SYSTEM: "跟随系统", MODE_DARK: "深色", MODE_LIGHT: "浅色"}
MODE_GLYPHS = {MODE_SYSTEM: "◐", MODE_DARK: "☾", MODE_LIGHT: "☀"}


@dataclass(frozen=True)
class Tone:
    """One accent colour and the surfaces derived from it."""

    bg: str
    hover: str
    border: str
    fg: str
    tint: str
    tint_border: str
    tint_fg: str


@dataclass(frozen=True)
class Palette:
    mode: str
    gradient: tuple[str, str, str]
    background: str
    surface: str
    surface_alt: str
    surface_raised: str
    border: str
    border_strong: str
    text: str
    text_soft: str
    muted: str
    faint: str
    heading: str
    control_fg: str

    green: str
    orange: str
    yellow: str
    blue: str
    red: str

    scroll_handle: str
    scroll_handle_hover: str

    badge_bg: str
    badge_border: str
    badge_fg: str

    action_hover: str
    action_pressed: str
    disabled_bg: str
    disabled_border: str
    disabled_fg: str

    method_checked_bg: str
    method_checked_border: str
    method_checked_fg: str
    secondary_hover: str

    kernel_hover: str
    kernel_checked_bg: str
    kernel_checked_border: str
    kernel_checked_fg: str

    menu_bg: str
    menu_border: str
    menu_selected_bg: str
    menu_selected_fg: str
    menu_disabled_fg: str
    menu_separator: str

    tooltip_bg: str
    tooltip_fg: str
    tooltip_border: str

    code_bg: str
    code_border: str
    code_fg: str
    progress_bg: str

    check_fill: str
    check_border: str
    check_disabled_fill: str
    check_disabled_border: str
    check_mark: str
    check_mark_disabled: str

    tones: dict[str, Tone] = field(default_factory=dict)

    def accent(self, name: str) -> str:
        return {
            "green": self.green,
            "orange": self.orange,
            "yellow": self.yellow,
            "blue": self.blue,
            "red": self.red,
        }[name]


DARK = Palette(
    mode=MODE_DARK,
    gradient=("#0c0e12", "#101318", "#12161d"),
    background="#0e1014",
    surface="#171a20",
    surface_alt="#1b1f27",
    surface_raised="#212631",
    border="#282e39",
    border_strong="#394253",
    text="#e9ecf2",
    text_soft="#c3cad8",
    muted="#929bad",
    faint="#7a8394",
    heading="#f4f6fa",
    control_fg="#aeb7c8",
    green="#34d399",
    orange="#fb923c",
    yellow="#facc15",
    blue="#60a5fa",
    red="#f87171",
    scroll_handle="#333b48",
    scroll_handle_hover="#46505f",
    badge_bg="#222833",
    badge_border="#2f3745",
    badge_fg="#aab3c4",
    action_hover="#2a3140",
    action_pressed="#1d222c",
    disabled_bg="#181c23",
    disabled_border="#242a34",
    disabled_fg="#666e80",
    method_checked_bg="#1d232d",
    method_checked_border="#4a566a",
    method_checked_fg="#f0f4fa",
    secondary_hover="#232936",
    kernel_hover="#202631",
    kernel_checked_bg="#152233",
    kernel_checked_border="#2f5b8a",
    kernel_checked_fg="#eaf4ff",
    menu_bg="#1b2029",
    menu_border="#353e4d",
    menu_selected_bg="#2a3240",
    menu_selected_fg="#ffffff",
    menu_disabled_fg="#5c6474",
    menu_separator="#2c3340",
    tooltip_bg="#232a35",
    tooltip_fg="#e9ecf2",
    tooltip_border="#3b4557",
    code_bg="#14202e",
    code_border="#24384f",
    code_fg="#cfe6ff",
    progress_bg="#151920",
    check_fill="#1d232d",
    check_border="#414b5d",
    check_disabled_fill="#1a1f27",
    check_disabled_border="#333a47",
    check_mark="#0d1a14",
    check_mark_disabled="#6a7280",
    tones={
        "green": Tone(
            bg="#143429",
            hover="#194434",
            border="#2c6c51",
            fg="#c9f7df",
            tint="#14291f",
            tint_border="#285943",
            tint_fg="#8fe8be",
        ),
        "orange": Tone(
            bg="#3a2513",
            hover="#4a2e17",
            border="#7a4a22",
            fg="#ffd9b8",
            tint="#2a1d12",
            tint_border="#5e3a1e",
            tint_fg="#f8bd8a",
        ),
        "yellow": Tone(
            bg="#332c0d",
            hover="#433913",
            border="#6e5c19",
            fg="#fbeaa3",
            tint="#2a250f",
            tint_border="#5b4d16",
            tint_fg="#f3dd83",
        ),
        "blue": Tone(
            bg="#142a44",
            hover="#1a3555",
            border="#2f5b8a",
            fg="#cfe6ff",
            tint="#152233",
            tint_border="#2b4c73",
            tint_fg="#9dc9fb",
        ),
        "red": Tone(
            bg="#3b1a1d",
            hover="#4a2024",
            border="#7d3339",
            fg="#ffc9cc",
            tint="#2a1618",
            tint_border="#5c2a2f",
            tint_fg="#f3b6ba",
        ),
    },
)


LIGHT = Palette(
    mode=MODE_LIGHT,
    gradient=("#ffffff", "#f8fafc", "#eef2f8"),
    background="#f4f6f9",
    surface="#ffffff",
    surface_alt="#f3f5f9",
    surface_raised="#eaeef4",
    border="#d9dfe8",
    border_strong="#b7c1d0",
    text="#1c2330",
    text_soft="#3b4553",
    muted="#5f6b7c",
    faint="#6b7684",
    heading="#131a24",
    control_fg="#43505f",
    green="#12a06b",
    orange="#d9701f",
    yellow="#c08a05",
    blue="#2f7fd0",
    red="#d24c4c",
    scroll_handle="#c3ccd9",
    scroll_handle_hover="#a3aebe",
    badge_bg="#eef1f6",
    badge_border="#d6dde7",
    badge_fg="#4c5766",
    action_hover="#e4e9f1",
    action_pressed="#dbe1eb",
    disabled_bg="#eef1f5",
    disabled_border="#e2e7ee",
    disabled_fg="#939cab",
    method_checked_bg="#eef2f8",
    method_checked_border="#a9b6c8",
    method_checked_fg="#131a24",
    secondary_hover="#e9edf4",
    kernel_hover="#eef1f7",
    kernel_checked_bg="#e2eefc",
    kernel_checked_border="#9dc0e8",
    kernel_checked_fg="#10395e",
    menu_bg="#ffffff",
    menu_border="#d5dce6",
    menu_selected_bg="#e2eefc",
    menu_selected_fg="#10395e",
    menu_disabled_fg="#a7b0bd",
    menu_separator="#e5e9f0",
    tooltip_bg="#ffffff",
    tooltip_fg="#1c2330",
    tooltip_border="#cfd7e2",
    code_bg="#e8f1fd",
    code_border="#b6d0ec",
    code_fg="#14456f",
    progress_bg="#eef1f6",
    check_fill="#ffffff",
    check_border="#b6c0ce",
    check_disabled_fill="#f0f2f6",
    check_disabled_border="#d7dde6",
    check_mark="#ffffff",
    check_mark_disabled="#a8b1be",
    tones={
        "green": Tone(
            bg="#dcf5e8",
            hover="#cdeedd",
            border="#86cfae",
            fg="#14563a",
            tint="#e6f7ee",
            tint_border="#a9d9c3",
            tint_fg="#1a6b47",
        ),
        "orange": Tone(
            bg="#fdeedd",
            hover="#fbe2c8",
            border="#e7b184",
            fg="#7a4110",
            tint="#fdf1e4",
            tint_border="#edc39c",
            tint_fg="#8a4a12",
        ),
        "yellow": Tone(
            bg="#fdf6d9",
            hover="#f9edc1",
            border="#ddc25f",
            fg="#6b5609",
            tint="#fdf9e3",
            tint_border="#e5d489",
            tint_fg="#77600c",
        ),
        "blue": Tone(
            bg="#e2eefc",
            hover="#d3e5fa",
            border="#9dc0e8",
            fg="#14456f",
            tint="#e8f1fd",
            tint_border="#b6d0ec",
            tint_fg="#1a5183",
        ),
        "red": Tone(
            bg="#fce4e4",
            hover="#f9d6d6",
            border="#e09b9b",
            fg="#7d1f1f",
            tint="#fdeaea",
            tint_border="#eeb6b6",
            tint_fg="#8a2424",
        ),
    },
)

PALETTES = {MODE_DARK: DARK, MODE_LIGHT: LIGHT}


class ThemeBus(QObject):
    """Announces the resolved colour scheme whenever it actually changes."""

    changed = pyqtSignal(str)


_BUS = ThemeBus()
_active_mode = MODE_SYSTEM
_active_palette = DARK


def theme_bus() -> ThemeBus:
    return _BUS


def current_palette() -> Palette:
    return _active_palette


def current_mode() -> str:
    """The user-visible choice: ``system``, ``dark`` or ``light``."""
    return _active_mode


def resolved_mode() -> str:
    """The theme actually in use, with ``system`` already resolved."""
    return _active_palette.mode


def next_mode(mode: str) -> str:
    return MODES[(MODES.index(mode) + 1) % len(MODES)]


def _system_scheme(app: QApplication) -> str:
    hints = app.styleHints()
    scheme = None
    if hasattr(hints, "colorScheme"):
        try:
            scheme = hints.colorScheme()
        except (AttributeError, RuntimeError):
            scheme = None
    if scheme is not None:
        name = str(scheme).rsplit(".", 1)[-1]
        if name == "Light":
            return MODE_LIGHT
        if name == "Dark":
            return MODE_DARK
    window = app.palette().color(QPalette.ColorRole.Window)
    return MODE_DARK if window.lightness() < 128 else MODE_LIGHT


def _resolve(mode: str, app: QApplication | None = None) -> str:
    if mode in (MODE_DARK, MODE_LIGHT):
        return mode
    app = app if app is not None else QApplication.instance()
    if app is None:
        return MODE_DARK
    return _system_scheme(app)


def set_theme(mode: str, app: QApplication | None = None) -> None:
    """Switch to ``mode`` and restyle every widget."""
    global _active_mode, _active_palette

    if mode not in MODES:
        raise ValueError(f"unknown theme mode: {mode!r}")
    app = app if app is not None else QApplication.instance()
    _active_mode = mode
    _active_palette = PALETTES[_resolve(mode, app)]
    if app is not None:
        app.setStyleSheet(_qss(_active_palette))
    _BUS.changed.emit(_active_palette.mode)


def _on_system_scheme_changed() -> None:
    if _active_mode == MODE_SYSTEM:
        set_theme(MODE_SYSTEM)


def app_icon() -> QIcon:
    return QIcon(str(paths.icon_path()))


def _qss(p: Palette) -> str:
    g = p.tones["green"]
    o = p.tones["orange"]
    y = p.tones["yellow"]
    b = p.tones["blue"]
    r = p.tones["red"]
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
                                stop:0 {p.gradient[0]}, stop:0.55 {p.gradient[1]}, stop:1 {p.gradient[2]});
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QWidget#scrollContent {{
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
    background: {p.scroll_handle};
    min-height: 32px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p.scroll_handle_hover};
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
QFrame#accentBar {{
    border: none;
    border-radius: 2px;
}}
QFrame#accentBar[accent="green"] {{ background: {p.green}; }}
QFrame#accentBar[accent="orange"] {{ background: {p.orange}; }}
QFrame#accentBar[accent="yellow"] {{ background: {p.yellow}; }}
QFrame#accentBar[accent="blue"] {{ background: {p.blue}; }}
QFrame#rule, QFrame#divider {{
    background: {p.border};
    border: none;
}}
QLabel {{
    background: transparent;
}}
QLabel#appTitle {{
    font-size: 21px;
    font-weight: 700;
    color: {p.heading};
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {p.faint};
}}
QLabel#versionBadge {{
    background: {p.badge_bg};
    border: 1px solid {p.badge_border};
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
    color: {p.heading};
}}
QLabel#badge {{
    background: {p.badge_bg};
    border: 1px solid {p.badge_border};
    border-radius: 9px;
    padding: 2px 9px;
    color: {p.badge_fg};
    font-size: 10.5px;
    font-weight: 600;
}}
QLabel#badge[accent="green"] {{ color: {g.tint_fg}; border-color: {g.tint_border}; background: {g.tint}; }}
QLabel#badge[accent="orange"] {{ color: {o.tint_fg}; border-color: {o.tint_border}; background: {o.tint}; }}
QLabel#badge[accent="yellow"] {{ color: {y.tint_fg}; border-color: {y.tint_border}; background: {y.tint}; }}
QLabel#badge[accent="blue"] {{ color: {b.tint_fg}; border-color: {b.tint_border}; background: {b.tint}; }}
QLabel#hint {{
    color: {p.muted};
    font-size: 11.5px;
    font-style: italic;
}}
QLabel#finePrint {{
    color: {p.faint};
    font-size: 10.5px;
}}
QLabel#footerNote {{
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
    color: {p.heading};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#dialogBody {{
    color: {p.text_soft};
    font-size: 13px;
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
    color: {p.code_fg};
    background: {p.code_bg};
    border: 1px solid {p.code_border};
    border-radius: 5px;
    padding: 3px 7px;
    font-family: "JetBrains Mono", "Noto Sans Mono", monospace;
    font-size: 11.5px;
}}
QFrame#warningBox {{
    background: {r.tint};
    border: 1px solid {r.tint_border};
    border-radius: 10px;
}}
QFrame#warningBox QLabel {{
    color: {r.tint_fg};
}}
QLabel#warningIcon {{
    font-size: 18px;
    color: {p.red};
}}
QFrame#infoBox {{
    background: {b.tint};
    border: 1px solid {b.tint_border};
    border-radius: 10px;
}}
QFrame#infoBox QLabel {{
    color: {b.tint_fg};
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
    background: {p.action_hover};
}}
QPushButton#actionButton:pressed {{
    background: {p.action_pressed};
}}
QPushButton#actionButton[accent="green"] {{
    background: {g.bg};
    border-color: {g.border};
    color: {g.fg};
}}
QPushButton#actionButton[accent="green"]:hover {{ background: {g.hover}; }}
QPushButton#actionButton[accent="orange"] {{
    background: {o.bg};
    border-color: {o.border};
    color: {o.fg};
}}
QPushButton#actionButton[accent="orange"]:hover {{ background: {o.hover}; }}
QPushButton#actionButton[accent="yellow"] {{
    background: {y.bg};
    border-color: {y.border};
    color: {y.fg};
}}
QPushButton#actionButton[accent="yellow"]:hover {{ background: {y.hover}; }}
QPushButton#actionButton[accent="blue"] {{
    background: {b.bg};
    border-color: {b.border};
    color: {b.fg};
}}
QPushButton#actionButton[accent="blue"]:hover {{ background: {b.hover}; }}
QPushButton#actionButton[accent="red"] {{
    background: {r.bg};
    border-color: {r.border};
    color: {r.fg};
}}
QPushButton#actionButton[accent="red"]:hover {{ background: {r.hover}; }}
QPushButton#actionButton:disabled {{
    background: {p.disabled_bg};
    border-color: {p.disabled_border};
    color: {p.disabled_fg};
}}
QPushButton#actionButton:focus {{
    border: 2px solid {p.blue};
}}
QPushButton#actionButton[accent="green"]:focus {{ border-color: {p.green}; }}
QPushButton#actionButton[accent="orange"]:focus {{ border-color: {p.orange}; }}
QPushButton#actionButton[accent="yellow"]:focus {{ border-color: {p.yellow}; }}
QPushButton#actionButton[accent="blue"]:focus {{ border-color: {p.blue}; }}
QPushButton#actionButton[accent="red"]:focus {{ border-color: {p.red}; }}
QPushButton#actionButton:disabled:focus {{
    border: 1px solid {p.disabled_border};
}}

QPushButton#methodButton {{
    text-align: left;
    padding: 8px 11px;
    border-radius: 9px;
    background: {p.surface_alt};
    border: 1px solid {p.border};
    color: {p.control_fg};
    font-size: 12px;
}}
QPushButton#methodButton:hover {{
    border-color: {p.border_strong};
    color: {p.text_soft};
}}
QPushButton#methodButton:checked {{
    background: {p.method_checked_bg};
    border-color: {p.method_checked_border};
    color: {p.method_checked_fg};
}}
QPushButton#methodButton[accent="green"]:checked {{ border-color: {g.border}; background: {g.tint}; }}
QPushButton#methodButton[accent="orange"]:checked {{ border-color: {o.border}; background: {o.tint}; }}
QPushButton#methodButton[accent="yellow"]:checked {{ border-color: {y.border}; background: {y.tint}; }}
QPushButton#methodButton[accent="blue"]:checked {{ border-color: {b.border}; background: {b.tint}; }}
QPushButton#methodButton:focus {{
    border: 2px solid {p.blue};
}}
QPushButton#methodButton:disabled {{
    background: {p.disabled_bg};
    border-color: {p.disabled_border};
    color: {p.disabled_fg};
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
    background: {p.secondary_hover};
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
    background: {p.kernel_hover};
}}
QPushButton#kernelButton:checked {{
    border-color: {p.kernel_checked_border};
    background: {p.kernel_checked_bg};
    color: {p.kernel_checked_fg};
}}
QPushButton#kernelButton:focus {{
    border: 2px solid {p.blue};
    color: {p.text};
}}
QPushButton#kernelButton:disabled {{
    color: {p.disabled_fg};
    background: {p.disabled_bg};
    border-color: {p.disabled_border};
}}

QToolButton#menuButton, QToolButton#themeButton {{
    color: {p.muted};
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 5px 9px;
    font-size: 12px;
    background: transparent;
}}
QToolButton#menuButton:hover, QToolButton#themeButton:hover {{
    background: {p.secondary_hover};
    color: {p.text_soft};
}}
QToolButton#menuButton:pressed, QToolButton#themeButton:pressed {{
    background: {p.action_pressed};
}}
QToolButton#menuButton:disabled, QToolButton#themeButton:disabled {{
    color: {p.disabled_fg};
}}
QToolButton#menuButton:focus, QToolButton#themeButton:focus {{
    border: 2px solid {p.blue};
    color: {p.text_soft};
}}
QToolButton#menuButton::menu-indicator {{ image: none; width: 0px; }}

QMenu {{
    background: {p.menu_bg};
    border: 1px solid {p.menu_border};
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
    background: {p.menu_selected_bg};
    color: {p.menu_selected_fg};
}}
QMenu::item:disabled {{
    color: {p.menu_disabled_fg};
}}
QMenu::separator {{
    height: 1px;
    background: {p.menu_separator};
    margin: 5px 8px;
}}
QMenu::indicator {{
    width: 14px;
    height: 14px;
    left: 8px;
}}

QToolTip {{
    background: {p.tooltip_bg};
    color: {p.tooltip_fg};
    border: 1px solid {p.tooltip_border};
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
QMessageBox QPushButton:hover {{ background: {p.action_hover}; }}
QMessageBox QPushButton:default {{
    border-color: {g.border};
    background: {g.bg};
    color: {g.fg};
}}

QProgressBar {{
    border: 1px solid {p.border};
    border-radius: 4px;
    background: {p.progress_bg};
    max-height: 7px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {p.green};
    border-radius: 3px;
}}
"""


def apply_theme(app: QApplication, mode: str = MODE_SYSTEM) -> None:
    """Install the style sheet and start tracking the desktop colour scheme."""
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())
    set_theme(mode, app)
    hints = app.styleHints()
    if hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(lambda *_args: _on_system_scheme_changed())


def icon_path() -> Path:
    return paths.icon_path()
