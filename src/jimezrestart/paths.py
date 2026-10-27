"""Locations of the helper, icons and other installed resources."""

from __future__ import annotations

from pathlib import Path

INSTALLED_HELPER = Path("/usr/lib/jimezrestart/jimezrestart-helper")
INSTALLED_ICON = Path("/usr/share/icons/hicolor/scalable/apps/jimezrestart.svg")
INSTALLED_ICON_FALLBACK = Path("/usr/share/jimezrestart/jimezrestart.svg")


def project_root() -> Path | None:
    """Return the source checkout root when running from a checkout."""

    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "data" / "icons" / "jimezrestart.svg").is_file():
        return candidate
    return None


def helper_path() -> Path:
    """Absolute path of the privileged helper script."""

    if INSTALLED_HELPER.is_file():
        return INSTALLED_HELPER
    root = project_root()
    if root is not None:
        return root / "helper" / "jimezrestart-helper"
    return INSTALLED_HELPER


def icon_path() -> Path:
    """Absolute path of the application icon."""

    root = project_root()
    if root is not None:
        return root / "data" / "icons" / "jimezrestart.svg"
    if INSTALLED_ICON.is_file():
        return INSTALLED_ICON
    return INSTALLED_ICON_FALLBACK
