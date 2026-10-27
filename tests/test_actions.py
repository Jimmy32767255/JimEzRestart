import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jimezrestart import actions
from jimezrestart.actions import (
    ACTION_HARD_REBOOT,
    ACTION_KEXEC_LOAD,
    ACTION_REBOOT,
    ActionError,
    desktop_command_argv,
    desktop_unit_argv,
    prepare_helper,
    run_detached,
    run_sync,
    validate_kernel,
)
from jimezrestart.kernels import KernelInfo


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.modules = self.root / "modules"
        self.boot = self.root / "boot"
        self.module = self.modules / "6.18.58-1-lts"
        self.module.mkdir(parents=True)
        self.boot.mkdir()
        self.kernel = self.module / "vmlinuz"
        self.kernel.write_bytes(b"kernel")
        self.initrd = self.boot / "initramfs-linux-lts.img"
        self.initrd.write_bytes(b"initrd")
        self.patches = [
            mock.patch.object(actions, "MODULES_ROOT", self.modules),
            mock.patch.object(actions, "BOOT_ROOT", self.boot),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.tmp.cleanup()

    def kernel_info(self, **overrides) -> KernelInfo:
        values = dict(
            release="6.18.58-1-lts",
            pkgbase="linux-lts",
            name="Linux-LTS",
            version="6.18.58",
            kernel=self.kernel,
            initrd=self.initrd,
            is_current=True,
        )
        values.update(overrides)
        return KernelInfo(**values)

    def test_validate_kernel(self):
        kernel, initrd = validate_kernel(self.kernel_info())
        self.assertEqual(kernel, self.kernel.resolve())
        self.assertEqual(initrd, self.initrd.resolve())

    def test_validate_rejects_outside_module_root(self):
        outside = self.root / "vmlinuz"
        outside.write_bytes(b"x")
        with self.assertRaises(ActionError):
            validate_kernel(self.kernel_info(kernel=outside))

    def test_validate_rejects_symlink_outside_module_root(self):
        outside = self.root / "outside-vmlinuz"
        outside.write_bytes(b"x")
        link = self.module / "vmlinuz"
        link.unlink()
        link.symlink_to(outside)
        with self.assertRaises(ActionError):
            validate_kernel(self.kernel_info())

    def test_validate_rejects_bad_initrd_name(self):
        bad = self.boot / "not-an-initramfs.img"
        bad.write_bytes(b"x")
        with self.assertRaises(ActionError):
            validate_kernel(self.kernel_info(initrd=bad))

    def test_validate_rejects_missing_initrd(self):
        with self.assertRaises(ActionError):
            validate_kernel(self.kernel_info(initrd=None))

    def test_helper_argv_kexec(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = Path(tmp) / "helper"
            helper.write_text("#!/bin/sh\n", encoding="utf-8")
            with mock.patch.object(actions.paths, "helper_path", return_value=helper):
                prepared = prepare_helper(ACTION_KEXEC_LOAD, self.kernel_info())
        self.assertEqual(prepared.argv[0], "pkexec")
        self.assertEqual(prepared.argv[1], str(helper))
        self.assertEqual(prepared.argv[2], ACTION_KEXEC_LOAD)
        self.assertEqual(
            prepared.argv[3:],
            (
                "--kernel",
                str(self.kernel.resolve()),
                "--initrd",
                str(self.initrd.resolve()),
            ),
        )

    def test_helper_argv_requires_kernel(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = Path(tmp) / "helper"
            helper.write_text("#!/bin/sh\n", encoding="utf-8")
            with mock.patch.object(actions.paths, "helper_path", return_value=helper):
                with self.assertRaises(ActionError):
                    prepare_helper(ACTION_KEXEC_LOAD)
                with self.assertRaises(ActionError):
                    prepare_helper("rm -rf /")

    def test_desktop_unit_argv(self):
        self.assertEqual(
            desktop_unit_argv("plasma-plasmashell.service"),
            ["systemctl", "--user", "restart", "plasma-plasmashell.service"],
        )
        for value in ("", "../evil", "a/b", "x;reboot"):
            with self.assertRaises(ActionError):
                desktop_unit_argv(value)

    def test_desktop_command_argv(self):
        self.assertEqual(desktop_command_argv(("gnome-shell", "--replace")), ["gnome-shell", "--replace"])
        with self.assertRaises(ActionError):
            desktop_command_argv(())

    def test_run_sync(self):
        result = run_sync(["/bin/sh", "-c", "exit 3"])
        self.assertEqual(result.returncode, 3)
        result = run_sync(["/bin/echo", "hello"])
        self.assertEqual(result.stdout.strip(), "hello")

    def test_run_detached(self):
        with mock.patch("jimezrestart.actions.subprocess.Popen") as popen:
            run_detached(["/bin/true"])
        popen.assert_called_once()
        with self.assertRaises(ActionError):
            run_detached(["/definitely/not/a/command"])

    def test_hard_reboot_constant_is_known(self):
        self.assertEqual(ACTION_HARD_REBOOT, "hard-reboot")
        self.assertEqual(ACTION_REBOOT, "reboot")
        self.assertIn("reboot", actions.HELPER_ACTIONS)


if __name__ == "__main__":
    unittest.main()
