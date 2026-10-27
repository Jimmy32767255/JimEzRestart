"""Theme switching: system following, manual override and the toolbar button."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from jimezrestart.demo import demo_data  # noqa: E402
from jimezrestart.ui.main_window import MainWindow  # noqa: E402
from jimezrestart.ui.theme import (  # noqa: E402
    DARK,
    LIGHT,
    MODE_DARK,
    MODE_LIGHT,
    MODE_SYSTEM,
    MODES,
    PALETTES,
    apply_theme,
    current_mode,
    current_palette,
    next_mode,
    resolved_mode,
    set_theme,
)

_app = QApplication.instance() or QApplication([])


class ThemeModeTests(unittest.TestCase):
    def setUp(self):
        apply_theme(_app, MODE_SYSTEM)

    def tearDown(self):
        apply_theme(_app, MODE_SYSTEM)

    def test_next_mode_cycles_through_all_three(self):
        self.assertEqual(next_mode(MODE_SYSTEM), MODE_DARK)
        self.assertEqual(next_mode(MODE_DARK), MODE_LIGHT)
        self.assertEqual(next_mode(MODE_LIGHT), MODE_SYSTEM)
        self.assertEqual(set(MODES), {MODE_SYSTEM, MODE_DARK, MODE_LIGHT})

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            set_theme("solarized")

    def test_system_mode_resolves_to_a_concrete_palette(self):
        set_theme(MODE_SYSTEM)
        self.assertEqual(current_mode(), MODE_SYSTEM)
        self.assertIn(resolved_mode(), (MODE_DARK, MODE_LIGHT))
        self.assertEqual(current_palette().mode, resolved_mode())

    def test_manual_light_and_dark_are_absolute(self):
        set_theme(MODE_LIGHT)
        self.assertEqual(current_palette().mode, MODE_LIGHT)
        self.assertEqual(current_palette().background, LIGHT.background)
        set_theme(MODE_DARK)
        self.assertEqual(current_palette().mode, MODE_DARK)
        self.assertEqual(current_palette().background, DARK.background)

    def test_style_sheet_is_regenerated_per_palette(self):
        set_theme(MODE_DARK)
        dark_sheet = _app.styleSheet()
        set_theme(MODE_LIGHT)
        light_sheet = _app.styleSheet()
        self.assertNotEqual(dark_sheet, light_sheet)
        self.assertIn(DARK.background, dark_sheet)
        self.assertIn(LIGHT.background, light_sheet)

    def test_palettes_define_every_accent(self):
        for palette in PALETTES.values():
            for name in ("green", "orange", "yellow", "blue", "red"):
                self.assertTrue(palette.accent(name).startswith("#"))

    def test_light_palette_is_lighter_than_dark(self):
        self.assertGreater(LIGHT.background, "#000000")
        self.assertNotEqual(LIGHT.text, DARK.text)
        self.assertNotEqual(LIGHT.surface, DARK.surface)


class ThemeButtonTests(unittest.TestCase):
    def setUp(self):
        apply_theme(_app, MODE_SYSTEM)
        system, desktop, kernels = demo_data()
        self.window = MainWindow(system, desktop, kernels, demo=True)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        _app.processEvents()

    def test_button_starts_on_system_and_names_the_resolved_theme(self):
        label = self.window.theme_button.text()
        self.assertIn("跟随系统", label)
        self.assertIn(
            "深色" if resolved_mode() == MODE_DARK else "浅色", label
        )

    def test_click_cycles_and_updates_button_text(self):
        button = self.window.theme_button
        expected = [MODE_DARK, MODE_LIGHT, MODE_SYSTEM]
        for target in expected:
            button.click()
            self.assertEqual(current_mode(), target)
            self.assertIn(
                {MODE_DARK: "深色", MODE_LIGHT: "浅色", MODE_SYSTEM: "跟随系统"}[target],
                button.text(),
            )

    def test_button_has_accessible_name(self):
        button = self.window.theme_button
        self.assertTrue(button.accessibleName())
        self.assertNotEqual(button.focusPolicy(), Qt.FocusPolicy.NoFocus)


if __name__ == "__main__":
    unittest.main()
