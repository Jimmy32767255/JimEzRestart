import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, Qt  # noqa: E402
from PyQt6.QtGui import QKeyEvent  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication, QDialog, QLabel  # noqa: E402

from jimezrestart.actions import ACTION_REBOOT  # noqa: E402
from jimezrestart.demo import demo_data  # noqa: E402
from jimezrestart.ui.dialogs import ConfirmDialog, KernelDialog  # noqa: E402
from jimezrestart.ui.main_window import MainWindow  # noqa: E402


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        system, desktop, kernels = demo_data()
        self.system = system
        self.desktop = desktop
        self.kernels = kernels
        self.window = MainWindow(system, desktop, kernels, demo=True)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_initial_texts_and_modes(self):
        titles = [
            label.text()
            for label in self.window.findChildren(QLabel)
            if label.objectName() == "cardTitle"
        ]
        self.assertIn("暖重启", titles)
        self.assertNotIn("温重启", titles)
        self.assertEqual(self.window.desktop_button.text(), "重启桌面")
        self.assertEqual(self.window.warm_button.text(), "重启当前内核")
        self.assertEqual(self.window.cold_button.text(), "标准重启")
        self.assertEqual(self.window.desktop_mode, "unit")
        self.assertEqual(self.window.warm_mode, "restart")
        self.assertEqual(self.window.cold_mode, "reboot")
        self.assertTrue(self.window.warm_button.isEnabled())

    def test_status_returns_to_ready_after_a_while(self):
        self.window._set_status("桌面已重启。", "ok")
        self.assertEqual(self.window.status.text(), "桌面已重启。")
        self.assertTrue(self.window._status_timer.isActive())
        self.window._reset_status()
        self.assertEqual(self.window.status.text(), "就绪")
        self.assertEqual(self.window.status.property("level"), "")
        self.assertFalse(self.window._status_timer.isActive())

        self.window._set_busy(True)
        self.window._set_status("正在执行…")
        self.assertFalse(self.window._status_timer.isActive())
        self.window._reset_status()
        self.assertEqual(self.window.status.text(), "正在执行…")

    def test_alt_changes_all_three_main_buttons(self):
        self.window._set_alt(True)
        self.assertEqual(self.window.desktop_button.text(), "以命令重启桌面")
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")
        self.assertEqual(self.window.cold_button.text(), "硬重启")
        self.assertEqual(self.window.cold_button.property("accent"), "red")

        self.window._set_alt(False)
        self.assertEqual(self.window.desktop_button.text(), "重启桌面")
        self.assertEqual(self.window.warm_button.text(), "重启当前内核")
        self.assertEqual(self.window.cold_button.text(), "标准重启")
        self.assertEqual(self.window.cold_button.property("accent"), "blue")

    def test_alt_stays_active_while_key_is_held(self):
        QTest.keyPress(self.window, Qt.Key.Key_Alt)
        self.assertTrue(self.window._alt)
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")

        QTest.qWait(300)
        self.assertTrue(self.window._alt)
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")

        QTest.keyRelease(self.window, Qt.Key.Key_Alt)
        self.assertFalse(self.window._alt)
        self.assertEqual(self.window.warm_button.text(), "重启当前内核")

    def test_alt_release_ignores_stale_modifier_state(self):
        QTest.keyPress(self.window, Qt.Key.Key_Alt)
        QTest.keyRelease(self.window, Qt.Key.Key_Alt)
        self.assertFalse(self.window._alt)

        # A stale cached modifier, or an auto-repeat press queued after the
        # release, must not switch the labels back on.
        with mock.patch.object(
            QApplication,
            "keyboardModifiers",
            return_value=Qt.KeyboardModifier.AltModifier,
        ), mock.patch.object(
            QApplication,
            "queryKeyboardModifiers",
            return_value=Qt.KeyboardModifier.AltModifier,
        ):
            self.window._poll_alt()
        # Even after a clean no-Alt frame has re-armed polling, a repeat
        # queued after release must not switch the labels back on.
        with mock.patch.object(
            QApplication,
            "keyboardModifiers",
            return_value=Qt.KeyboardModifier.NoModifier,
        ), mock.patch.object(
            QApplication,
            "queryKeyboardModifiers",
            return_value=Qt.KeyboardModifier.NoModifier,
        ):
            self.window._poll_alt()
        auto_repeat = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Alt,
            Qt.KeyboardModifier.AltModifier,
            "",
            True,
        )
        QApplication.sendEvent(self.window, auto_repeat)
        with mock.patch.object(
            QApplication,
            "keyboardModifiers",
            return_value=Qt.KeyboardModifier.AltModifier,
        ), mock.patch.object(
            QApplication,
            "queryKeyboardModifiers",
            return_value=Qt.KeyboardModifier.AltModifier,
        ):
            self.window._poll_alt()
        self.assertFalse(self.window._alt)
        self.assertEqual(self.window.warm_button.text(), "重启当前内核")

        # A real new press must still work after the stale frame.
        QTest.keyPress(self.window, Qt.Key.Key_Alt)
        self.assertTrue(self.window._alt)
        QTest.keyRelease(self.window, Qt.Key.Key_Alt)

    def test_convert_menu_is_independent_of_alt(self):
        self.window._set_warm_mode("switch")
        self.assertEqual(self.window.warm_mode, "switch")
        self.assertFalse(self.window.warm_switch_action.isCheckable())
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")

        self.window._set_alt(True)
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")
        self.window._set_alt(False)
        self.assertEqual(self.window.warm_button.text(), "切换操作系统内核")

        self.window._set_warm_mode("restart")
        self.assertEqual(self.window.warm_button.text(), "重启当前内核")

    def test_choice_menus_are_plain_actions(self):
        for action in (
            self.window.unit_action,
            self.window.command_action,
            self.window.warm_restart_action,
            self.window.warm_switch_action,
            self.window.cold_reboot_action,
            self.window.cold_hard_action,
        ):
            self.assertFalse(action.isCheckable(), action.text())
        self.assertTrue(self.window.native_action.isCheckable())

    def visible_menu_texts(self, menu):
        return [
            action.text()
            for action in menu.actions()
            if not action.isSeparator() and action.isVisible()
        ]

    def test_options_only_exist_in_menus(self):
        self.assertFalse(hasattr(self.window, "unit_method_button"))
        self.assertFalse(hasattr(self.window, "command_method_button"))
        self.assertFalse(hasattr(self.window, "native_check"))
        self.assertEqual(
            self.visible_menu_texts(self.window.desktop_menu),
            ["以命令重启（不推荐）"],
        )
        self.assertIn(
            "使用原生 kexec",
            self.window.native_action.text(),
        )

    def test_menus_hide_the_active_main_action(self):
        self.assertEqual(
            self.visible_menu_texts(self.window.warm_menu),
            ["切换操作系统内核"],
        )
        self.assertEqual(
            self.visible_menu_texts(self.window.cold_menu),
            ["硬重启（⚠️ 谨慎使用）"],
        )

        self.window._set_warm_mode("switch")
        self.assertEqual(
            self.visible_menu_texts(self.window.warm_menu),
            ["重启当前内核"],
        )
        self.window._set_cold_mode("hard")
        self.assertEqual(
            self.visible_menu_texts(self.window.cold_menu),
            ["标准重启"],
        )
        self.window._set_desktop_mode("command")
        self.assertEqual(
            self.visible_menu_texts(self.window.desktop_menu),
            ["以 systemd 单元重启（默认）"],
        )

    def test_desktop_command_mode(self):
        self.window._set_desktop_mode("command")
        self.assertEqual(self.window.desktop_mode, "command")
        self.assertFalse(self.window.command_action.isCheckable())
        self.assertEqual(self.window.desktop_button.text(), "以命令重启桌面")
        self.assertIn("命令", self.window.desktop_hint.text())

    def test_cold_hard_mode_switches_accent(self):
        self.window._set_cold_mode("hard")
        self.assertEqual(self.window.cold_mode, "hard")
        self.assertEqual(self.window.cold_button.text(), "硬重启")
        self.assertEqual(self.window.cold_button.property("accent"), "red")
        self.assertFalse(self.window.cold_hard_action.isCheckable())

    def test_hard_reboot_countdown(self):
        dialog = ConfirmDialog(
            "确认硬重启",
            "硬重启",
            "系统将立即重启。",
            "硬重启",
            accent="red",
            warning="可能损坏文件系统。",
            countdown=5,
        )
        self.assertFalse(dialog.confirm_button.isEnabled())
        self.assertIn("5 秒", dialog.confirm_button.text())
        for remaining in (4, 3, 2, 1):
            dialog._tick()
            self.assertFalse(dialog.confirm_button.isEnabled())
            self.assertIn(f"{remaining} 秒", dialog.confirm_button.text())
        dialog._tick()
        self.assertTrue(dialog.confirm_button.isEnabled())
        self.assertEqual(dialog.confirm_button.text(), "硬重启")
        dialog.deleteLater()

    def test_kernel_dialog_selection(self):
        dialog = KernelDialog(self.kernels, self.system.kernel_release)
        self.assertFalse(dialog._buttons[0].isEnabled())
        self.assertTrue(dialog._buttons[1].isEnabled())
        self.assertFalse(dialog.confirm_button.isEnabled())

        dialog._on_selected(1)
        self.assertIsNotNone(dialog.selected)
        self.assertEqual(dialog.selected.release, "6.18.42-1-lts")
        self.assertTrue(dialog.confirm_button.isEnabled())

        dialog._accept_selection()
        self.assertEqual(dialog.result(), int(QDialog.DialogCode.Accepted))
        dialog.deleteLater()

    def test_kernel_dialog_empty_state(self):
        current = next(k for k in self.kernels if k.release == self.system.kernel_release)
        dialog = KernelDialog([current], self.system.kernel_release)
        self.assertIsNone(dialog.confirm_button)
        dialog.deleteLater()

    def test_non_systemd_disables_soft_and_warm_until_native(self):
        system = replace(
            self.system,
            init_name="bwrap",
            init_display="未知",
            is_systemd=False,
            systemd_version=None,
            has_soft_reboot=False,
        )
        window = MainWindow(system, self.desktop, self.kernels, demo=True)
        try:
            self.assertFalse(window.hot_button.isEnabled())
            self.assertIn("不是 systemd", window.hot_button.toolTip())
            self.assertFalse(window.warm_button.isEnabled())
            self.assertIn("原生 kexec", window.warm_button.toolTip())
            self.assertTrue(window.native_action.isEnabled())

            window.native_action.setChecked(True)
            self.assertTrue(window.native_kexec)
            self.assertTrue(window.warm_button.isEnabled())
            self.assertEqual(window.warm_button.text(), "重启当前内核")
            window._set_alt(True)
            self.assertEqual(window.warm_button.text(), "切换操作系统内核")
            window._set_alt(False)
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()

    def test_non_systemd_disables_unit_method(self):
        system = replace(
            self.system,
            is_systemd=False,
            systemd_version=None,
            has_soft_reboot=False,
        )
        window = MainWindow(system, self.desktop, self.kernels, demo=True)
        try:
            self.assertEqual(window.desktop_mode, "command")
            self.assertFalse(window.unit_action.isEnabled())
            self.assertIn("systemd", window.unit_action.toolTip())
            self.assertTrue(window.desktop_button.isEnabled())
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()

    def test_missing_kexec_disables_every_kexec_path(self):
        system = replace(self.system, has_kexec_tools=False)
        window = MainWindow(system, self.desktop, self.kernels, demo=True)
        try:
            self.assertFalse(window.warm_button.isEnabled())
            self.assertIn("kexec-tools", window.warm_button.toolTip())
            self.assertFalse(window.native_action.isEnabled())
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()

    def test_demo_actions_never_spawn_a_process(self):
        self.window._run_helper(ACTION_REBOOT)
        self.assertIn("演示模式", self.window.status.text())
        self.window._set_desktop_mode("command")
        self.window._on_desktop_clicked()
        self.assertIn("演示模式", self.window.status.text())


if __name__ == "__main__":
    unittest.main()
