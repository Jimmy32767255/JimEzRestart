"""Construction and execution of the commands behind every button.

The GUI never runs privileged commands itself: it validates the arguments,
then asks the fixed helper script to perform the operation through ``pkexec``.
The helper repeats every check, so a compromised GUI cannot ask it to run an
arbitrary command.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import paths
from .kernels import KernelInfo

ACTION_SOFT_REBOOT = "soft-reboot"
ACTION_KEXEC_LOAD = "kexec-load"
ACTION_KEXEC_NATIVE = "kexec-native"
ACTION_REBOOT = "reboot"
ACTION_HARD_REBOOT = "hard-reboot"

HELPER_ACTIONS = frozenset(
    {
        ACTION_SOFT_REBOOT,
        ACTION_KEXEC_LOAD,
        ACTION_KEXEC_NATIVE,
        ACTION_REBOOT,
        ACTION_HARD_REBOOT,
    }
)

MODULES_ROOT = Path("/usr/lib/modules")
BOOT_ROOT = Path("/boot")


class ActionError(Exception):
    """Raised when an action cannot be constructed or executed."""


@dataclass(frozen=True)
class PreparedCommand:
    """A command line that is ready to be executed."""

    argv: tuple[str, ...]
    description: str
    detached: bool = False


def _real(path: Path) -> Path:
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise ActionError(f"路径不可用：{path}") from error


def validate_kernel(kernel: KernelInfo) -> tuple[Path, Path]:
    """Return the resolved kernel and initramfs paths after strict checks."""

    kernel_path = _real(kernel.kernel)
    if MODULES_ROOT not in kernel_path.parents or kernel_path.name != "vmlinuz":
        raise ActionError(f"内核路径不在 {MODULES_ROOT} 下：{kernel_path}")

    if kernel.initrd is None:
        raise ActionError("该内核没有匹配的 initramfs。")
    initrd_path = _real(kernel.initrd)
    if BOOT_ROOT not in initrd_path.parents or not initrd_path.name.startswith("initramfs-"):
        raise ActionError(f"initramfs 路径不在 {BOOT_ROOT} 下：{initrd_path}")
    if not initrd_path.name.endswith(".img"):
        raise ActionError(f"initramfs 文件名异常：{initrd_path.name}")

    return kernel_path, initrd_path


def _kexec_args(action: str, kernel: KernelInfo) -> list[str]:
    kernel_path, initrd_path = validate_kernel(kernel)
    return [action, "--kernel", str(kernel_path), "--initrd", str(initrd_path)]


def helper_argv(action: str, kernel: KernelInfo | None = None) -> list[str]:
    """Build the full ``pkexec <helper> ...`` argument vector."""

    helper = paths.helper_path()
    if not helper.is_file():
        raise ActionError(f"找不到特权助手：{helper}")
    if action not in HELPER_ACTIONS:
        raise ActionError(f"未知的特权操作：{action}")

    if action in (ACTION_KEXEC_LOAD, ACTION_KEXEC_NATIVE):
        if kernel is None:
            raise ActionError("该操作需要一个内核。")
        args = _kexec_args(action, kernel)
    else:
        args = [action]

    return ["pkexec", str(helper), *args]


def prepare_helper(action: str, kernel: KernelInfo | None = None) -> PreparedCommand:
    descriptions = {
        ACTION_SOFT_REBOOT: "通过 systemctl soft-reboot 重启用户空间",
        ACTION_KEXEC_LOAD: "载入内核后通过 systemd kexec 重启",
        ACTION_KEXEC_NATIVE: "载入内核后直接以原生 kexec 重启",
        ACTION_REBOOT: "通过 reboot 进行标准重启",
        ACTION_HARD_REBOOT: "通过 SysRq 强制硬重启",
    }
    return PreparedCommand(
        argv=tuple(helper_argv(action, kernel)),
        description=descriptions[action],
    )


_UNIT_RE = re.compile(r"^[A-Za-z0-9:_.@\\-]+\.service$")


def desktop_unit_argv(unit: str) -> list[str]:
    if (
        not unit
        or len(unit) > 255
        or unit.startswith("-")
        or "/" in unit
        or _UNIT_RE.fullmatch(unit) is None
    ):
        raise ActionError(f"非法的 systemd 单元：{unit!r}")
    return ["systemctl", "--user", "restart", unit]


def desktop_command_argv(command: tuple[str, ...]) -> list[str]:
    if not command:
        raise ActionError("桌面重启命令为空。")
    return list(command)


def run_detached(argv: list[str]) -> None:
    """Start *argv* in its own session and do not wait for it."""

    try:
        subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as error:
        raise ActionError(str(error)) from error


def run_sync(argv: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    """Run *argv* and capture its output; used for the desktop unit restart."""

    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ},
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ActionError(str(error)) from error
