"""Kernel enumeration for the warm-reboot kernel picker.

Arch installs its kernel images as ``/usr/lib/modules/<release>/vmlinuz`` and
the matching initramfs as ``/boot/initramfs-<pkgbase>.img``.  Only kernels for
which both files exist are considered bootable via kexec.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .detect import guess_pkgbase, kernel_pretty_name, kernel_version, read_pkgbase


@dataclass(frozen=True)
class KernelInfo:
    release: str
    pkgbase: str
    name: str
    version: str
    kernel: Path
    initrd: Path | None
    is_current: bool
    reason: str = ""

    @property
    def available(self) -> bool:
        return self.initrd is not None and not self.reason


def find_initrd(boot_dir: Path, pkgbase: str, release: str) -> Path | None:
    """Find the initramfs that belongs to a kernel package."""

    candidates = [
        boot_dir / f"initramfs-{pkgbase}.img",
        boot_dir / f"initramfs-{pkgbase}-fallback.img",
    ]
    if release:
        candidates.append(boot_dir / f"initramfs-{release}.img")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def enumerate_kernels(
    modules_dir: Path | str = Path("/usr/lib/modules"),
    boot_dir: Path | str = Path("/boot"),
    current_release: str | None = None,
) -> list[KernelInfo]:
    """Return every installed kernel that has a vmlinuz image."""

    modules_dir = Path(modules_dir)
    boot_dir = Path(boot_dir)
    current_release = current_release or os.uname().release

    kernels: list[KernelInfo] = []
    seen: set[tuple[str, str]] = set()

    try:
        module_dirs = sorted(modules_dir.iterdir())
    except OSError:
        module_dirs = []

    for module_dir in module_dirs:
        if not module_dir.is_dir():
            continue
        kernel = module_dir / "vmlinuz"
        if not kernel.is_file():
            continue
        release = module_dir.name
        pkgbase = read_pkgbase(release, modules_dir) or guess_pkgbase(release)
        key = (pkgbase, release)
        if key in seen:
            continue
        seen.add(key)
        initrd = find_initrd(boot_dir, pkgbase, release)
        reason = "" if initrd is not None else "未找到匹配的 initramfs。"
        kernels.append(
            KernelInfo(
                release=release,
                pkgbase=pkgbase,
                name=kernel_pretty_name(pkgbase),
                version=kernel_version(release),
                kernel=kernel,
                initrd=initrd,
                is_current=release == current_release,
                reason=reason,
            )
        )

    kernels.sort(key=lambda kernel: (not kernel.is_current, kernel.name.lower(), kernel.release))
    return kernels


def current_kernel(kernels: list[KernelInfo], release: str | None = None) -> KernelInfo | None:
    release = release or os.uname().release
    for kernel in kernels:
        if kernel.release == release:
            return kernel
    return None


def other_kernels(kernels: list[KernelInfo], release: str | None = None) -> list[KernelInfo]:
    release = release or os.uname().release
    return [kernel for kernel in kernels if kernel.release != release]
