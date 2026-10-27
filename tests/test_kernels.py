import tempfile
import unittest
from pathlib import Path

from jimezrestart.kernels import (
    KernelInfo,
    current_kernel,
    enumerate_kernels,
    find_initrd,
    other_kernels,
)


class KernelTests(unittest.TestCase):
    def _tree(self, root: Path) -> tuple[Path, Path]:
        modules = root / "modules"
        boot = root / "boot"
        boot.mkdir()
        for release, pkgbase in (
            ("6.18.58-1-lts", "linux-lts"),
            ("6.18.42-1-lts", "linux-lts"),
            ("6.1.0-zen1-1-zen", "linux-zen"),
            ("6.0.0-broken", "linux-broken"),
        ):
            directory = modules / release
            directory.mkdir(parents=True)
            (directory / "vmlinuz").write_bytes(b"kernel")
            (directory / "pkgbase").write_text(pkgbase + "\n", encoding="utf-8")
        # Not a kernel: no vmlinuz.
        (modules / "empty").mkdir()
        # A kernel with no initramfs is still listed, but unavailable.
        (boot / "initramfs-linux-lts.img").write_bytes(b"initrd")
        (boot / "initramfs-linux-zen-fallback.img").write_bytes(b"initrd")
        return modules, boot

    def test_enumerate(self):
        with tempfile.TemporaryDirectory() as tmp:
            modules, boot = self._tree(Path(tmp))
            kernels = enumerate_kernels(modules, boot, "6.18.58-1-lts")

        self.assertEqual(len(kernels), 4)
        self.assertEqual(kernels[0].release, "6.18.58-1-lts")
        self.assertTrue(kernels[0].is_current)
        self.assertTrue(kernels[0].available)
        self.assertEqual(kernels[0].name, "Linux-LTS")
        self.assertEqual(kernels[0].version, "6.18.58")

        by_release = {kernel.release: kernel for kernel in kernels}
        self.assertTrue(by_release["6.18.42-1-lts"].available)
        self.assertEqual(
            by_release["6.18.42-1-lts"].initrd,
            boot / "initramfs-linux-lts.img",
        )
        self.assertTrue(by_release["6.1.0-zen1-1-zen"].available)
        self.assertEqual(by_release["6.1.0-zen1-1-zen"].name, "Linux-Zen")
        self.assertFalse(by_release["6.0.0-broken"].available)
        self.assertIn("initramfs", by_release["6.0.0-broken"].reason)
        self.assertNotIn("empty", by_release)

    def test_find_initrd_prefers_normal(self):
        with tempfile.TemporaryDirectory() as tmp:
            boot = Path(tmp)
            (boot / "initramfs-linux.img").write_bytes(b"normal")
            (boot / "initramfs-linux-fallback.img").write_bytes(b"fallback")
            self.assertEqual(find_initrd(boot, "linux", "6.1.0"), boot / "initramfs-linux.img")

    def test_current_and_other(self):
        first = KernelInfo("1", "linux", "Linux", "1", Path("/a"), Path("/b"), True)
        second = KernelInfo("2", "linux", "Linux", "2", Path("/c"), Path("/d"), False)
        self.assertIs(current_kernel([first, second], "2"), second)
        self.assertIsNone(current_kernel([first], "3"))
        self.assertEqual(other_kernels([first, second], "1"), [second])

    def test_available_requires_initrd_and_no_reason(self):
        good = KernelInfo("1", "linux", "Linux", "1", Path("/a"), Path("/b"), False)
        no_initrd = KernelInfo("2", "linux", "Linux", "2", Path("/c"), None, False)
        reason = KernelInfo("3", "linux", "Linux", "3", Path("/d"), Path("/e"), False, "bad")
        self.assertTrue(good.available)
        self.assertFalse(no_initrd.available)
        self.assertFalse(reason.available)


if __name__ == "__main__":
    unittest.main()
