import os
import tempfile
import unittest
from unittest import mock
from dataclasses import replace
from pathlib import Path

from jimezrestart.detect import (
    SYSTEMD_SOFT_REBOOT_VERSION,
    DesktopInfo,
    DesktopMethod,
    SystemInfo,
    detect_desktop,
    detect_system,
    guess_pkgbase,
    init_display_name,
    kernel_pretty_name,
    kernel_version,
    parse_os_release,
    parse_version,
    read_lockdown,
    read_pkgbase,
    current_kernel_display,
)


class ParseTests(unittest.TestCase):
    def test_os_release_quotes_and_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "os-release"
            path.write_text(
                "# comment\nNAME=Arch Linux\nPRETTY_NAME=\"Arch Linux\"\n"
                "ID=arch\nEMPTY=\n",
                encoding="utf-8",
            )
            data = parse_os_release(path)
        self.assertEqual(data["NAME"], "Arch Linux")
        self.assertEqual(data["PRETTY_NAME"], "Arch Linux")
        self.assertEqual(data["EMPTY"], "")
        self.assertNotIn("# comment", data)

    def test_parse_version(self):
        self.assertEqual(parse_version("systemd 262 (262.3-1-arch)"), (262,))
        self.assertEqual(parse_version("6.18.58-1-lts"), (6, 18, 58))
        self.assertIsNone(parse_version("no version here"))

    def test_pkgbase_helpers(self):
        self.assertEqual(guess_pkgbase("6.18.58-1-lts"), "linux-lts")
        self.assertEqual(guess_pkgbase("6.18.58-1-zen"), "linux-zen")
        self.assertEqual(guess_pkgbase("6.18.58-1-hardened"), "linux-hardened")
        self.assertEqual(guess_pkgbase("6.18.58-1-arch1-1"), "linux")
        self.assertEqual(kernel_pretty_name("linux-lts"), "Linux-LTS")
        self.assertEqual(kernel_pretty_name(None), "Linux")
        self.assertEqual(kernel_version("6.18.58-1-lts"), "6.18.58")

    def test_read_pkgbase_and_display(self):
        with tempfile.TemporaryDirectory() as tmp:
            modules = Path(tmp)
            release = "6.18.58-1-lts"
            (modules / release).mkdir()
            (modules / release / "pkgbase").write_text("linux-lts\n", encoding="utf-8")
            self.assertEqual(read_pkgbase(release, modules), "linux-lts")
            self.assertEqual(
                current_kernel_display(release, modules), "Linux-LTS 6.18.58"
            )

    def test_read_lockdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lockdown"
            path.write_text("none [integrity] confidentiality\n", encoding="utf-8")
            self.assertEqual(read_lockdown(path), "integrity")
            path.write_text("[none] integrity confidentiality\n", encoding="utf-8")
            self.assertIsNone(read_lockdown(path))
            path.write_text("", encoding="utf-8")
            self.assertIsNone(read_lockdown(path))


class DetectSystemTests(unittest.TestCase):
    def test_detect_system_with_fake_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            os_release = root / "os-release"
            os_release.write_text(
                'NAME="Arch Linux"\nPRETTY_NAME="Arch Linux"\n', encoding="utf-8"
            )
            comm = root / "comm"
            comm.write_text("systemd\n", encoding="utf-8")
            modules = root / "modules"
            release = os.uname().release
            (modules / release).mkdir(parents=True)
            (modules / release / "pkgbase").write_text("linux-lts\n", encoding="utf-8")
            trigger = root / "sysrq-trigger"
            trigger.write_text("", encoding="utf-8")
            sysrq = root / "sysrq"
            sysrq.write_text("1\n", encoding="utf-8")
            lockdown = root / "lockdown"
            lockdown.write_text("[none] integrity confidentiality\n", encoding="utf-8")

            info = detect_system(
                os_release_path=os_release,
                proc_comm_path=comm,
                modules_dir=modules,
                sysrq_trigger=trigger,
                sysrq_value_path=sysrq,
                lockdown_path=lockdown,
            )

        self.assertEqual(info.distro_pretty, "Arch Linux")
        self.assertTrue(info.is_systemd)
        self.assertEqual(info.init_display, "systemd")
        self.assertTrue(info.has_sysrq)
        self.assertEqual(info.sysrq_value, 1)
        self.assertIsNone(info.lockdown)
        self.assertTrue(info.kernel_display.startswith("Linux-LTS "))
        if info.systemd_version is not None:
            self.assertEqual(
                info.has_soft_reboot,
                info.systemd_version >= SYSTEMD_SOFT_REBOOT_VERSION,
            )


    def test_init_display_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comm = root / "comm"
            for value, expected in (
                ("systemd", "systemd"),
                ("openrc-init", "OpenRC"),
                ("runit", "runit"),
                ("s6-svscan", "s6"),
                ("dinit", "dinit"),
                ("shepherd", "GNU Shepherd"),
                ("init", "SysV init"),
                ("bwrap", "未知"),
                ("", "未知"),
            ):
                comm.write_text(value, encoding="utf-8")
                self.assertEqual(init_display_name(value, comm), expected)

            comm.write_text("init", encoding="utf-8")
            (root / "exe").symlink_to("/bin/busybox")
            self.assertEqual(init_display_name("init", comm), "BusyBox init")

    def test_non_systemd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "comm").write_text("bwrap\n", encoding="utf-8")
            info = detect_system(
                os_release_path=root / "missing",
                proc_comm_path=root / "comm",
                modules_dir=root / "modules",
                sysrq_trigger=root / "missing",
                sysrq_value_path=root / "missing",
                lockdown_path=root / "missing",
            )
        self.assertFalse(info.is_systemd)
        self.assertFalse(info.has_soft_reboot)
        self.assertFalse(info.has_sysrq)
        self.assertEqual(info.init_display, "未知")


def _system(is_systemd: bool = True) -> SystemInfo:
    return SystemInfo(
        distro="Arch Linux",
        distro_pretty="Arch Linux",
        kernel_release="6.18.58-1-lts",
        kernel_display="Linux-LTS 6.18.58",
        init_name="systemd" if is_systemd else "bwrap",
        init_display="systemd" if is_systemd else "未知",
        is_systemd=is_systemd,
        systemd_version=(262,) if is_systemd else None,
        has_soft_reboot=is_systemd,
        has_kexec_tools=True,
        has_pkexec=True,
        has_reboot=True,
        has_sysrq=True,
        sysrq_value=1,
        lockdown=None,
    )


class DetectDesktopTests(unittest.TestCase):
    def _env(self, desktop: str) -> dict[str, str]:
        return {
            "XDG_CURRENT_DESKTOP": desktop,
            "XDG_SESSION_TYPE": "wayland",
            "PATH": os.environ.get("PATH", ""),
        }

    def test_kde_unit_and_command_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            unit = home / ".config/systemd/user/plasma-plasmashell.service"
            unit.parent.mkdir(parents=True)
            unit.write_text("[Unit]\n", encoding="utf-8")
            pid = home / "proc/123"
            pid.mkdir(parents=True)
            (pid / "comm").write_text("plasmashell\n", encoding="utf-8")

            info = detect_desktop(
                _system(),
                env=self._env("KDE"),
                proc_dir=home / "proc",
                home=home,
                which=lambda name: f"/usr/bin/{name}",
            )

        self.assertEqual(info.key, "kde")
        self.assertTrue(info.process_running)
        self.assertTrue(info.unit_method.available)
        self.assertTrue(info.command_method.available)
        self.assertIn("plasma-plasmashell.service", info.unit_method.hint)

    def test_kde_unit_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with mock.patch(
                "jimezrestart.detect.user_unit_exists", return_value=False
            ):
                info = detect_desktop(
                    _system(),
                    env=self._env("KDE"),
                    proc_dir=home / "proc",
                    home=home,
                    which=lambda name: f"/usr/bin/{name}",
                )
        self.assertFalse(info.unit_method.available)
        self.assertIn("未找到", info.unit_method.reason)
        self.assertTrue(info.command_method.available)

    def test_gnome_wayland_command_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            info = detect_desktop(
                _system(),
                env=self._env("GNOME"),
                proc_dir=home / "proc",
                home=home,
                which=lambda name: f"/usr/bin/{name}",
            )
        self.assertFalse(info.unit_method.available)
        self.assertFalse(info.command_method.available)
        self.assertIn("Wayland", info.command_method.reason)

    def test_unknown_desktop(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            info = detect_desktop(
                _system(),
                env=self._env(""),
                proc_dir=home / "proc",
                home=home,
            )
        self.assertEqual(info.key, "unknown")
        self.assertFalse(info.unit_method.available)
        self.assertFalse(info.command_method.available)

    def test_non_systemd_disables_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            unit = home / ".config/systemd/user/plasma-plasmashell.service"
            unit.parent.mkdir(parents=True)
            unit.write_text("[Unit]\n", encoding="utf-8")
            info = detect_desktop(
                _system(False),
                env=self._env("KDE"),
                proc_dir=home / "proc",
                home=home,
                which=lambda name: f"/usr/bin/{name}",
            )
        self.assertFalse(info.unit_method.available)
        self.assertIn("不是 systemd", info.unit_method.reason)


if __name__ == "__main__":
    unittest.main()
