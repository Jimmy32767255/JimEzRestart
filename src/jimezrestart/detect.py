"""Detection of the operating system, init system and desktop environment.

Nothing in this module imports Qt: the UI layer only consumes the dataclasses
below, and the unit tests can exercise the detection logic on any machine.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

KERNEL_PRETTY_NAMES = {
    "linux": "Linux",
    "linux-lts": "Linux-LTS",
    "linux-zen": "Linux-Zen",
    "linux-hardened": "Linux-Hardened",
    "linux-rt": "Linux-RT",
    "linux-rt-lts": "Linux-RT-LTS",
    "linux-git": "Linux-Git",
}

SYSTEMD_SOFT_REBOOT_VERSION = (254,)


@dataclass(frozen=True)
class SystemInfo:
    """Facts about the running system that the UI needs."""

    distro: str
    distro_pretty: str
    kernel_release: str
    kernel_display: str
    init_name: str
    init_display: str
    is_systemd: bool
    systemd_version: tuple[int, ...] | None
    has_soft_reboot: bool
    has_kexec_tools: bool
    has_pkexec: bool
    has_reboot: bool
    has_sysrq: bool
    sysrq_value: int | None
    lockdown: str | None


@dataclass(frozen=True)
class DesktopMethod:
    """One way of restarting the desktop shell."""

    mode: str
    label: str
    available: bool
    reason: str = ""
    unit: str | None = None
    command: tuple[str, ...] | None = None
    hint: str = ""


@dataclass(frozen=True)
class DesktopInfo:
    """Detected desktop environment plus the restart methods it supports."""

    key: str
    name: str
    process: str
    session_type: str
    process_running: bool
    unit_method: DesktopMethod
    command_method: DesktopMethod

    @property
    def note(self) -> str:
        if self.key == "unknown":
            return "未检测到受支持的桌面环境。"
        suffix = "" if self.process_running else "，进程未运行"
        return f"检测到当前桌面：{self.name}（{self.process}{suffix}）"


@dataclass(frozen=True)
class _DesktopSpec:
    key: str
    name: str
    process: str
    unit: str | None
    command: tuple[str, ...] | None
    hint: str
    required: tuple[str, ...] = ()
    wayland_command: bool = True
    reason: str = ""


_DESKTOP_SPECS: tuple[_DesktopSpec, ...] = (
    _DesktopSpec(
        key="kde",
        name="KDE Plasma",
        process="plasmashell",
        unit="plasma-plasmashell.service",
        command=(
            "sh",
            "-c",
            "kquitapp6 plasmashell >/dev/null 2>&1; sleep 1; "
            "setsid plasmashell >/dev/null 2>&1 </dev/null &",
        ),
        hint="kquitapp6 plasmashell && plasmashell",
        required=("kquitapp6", "plasmashell"),
    ),
    _DesktopSpec(
        key="gnome",
        name="GNOME",
        process="gnome-shell",
        unit=None,
        command=("gnome-shell", "--replace"),
        hint="gnome-shell --replace",
        required=("gnome-shell",),
        wayland_command=False,
        reason="Wayland 会话下无法在不注销的情况下重启 GNOME Shell。",
    ),
    _DesktopSpec(
        key="xfce",
        name="Xfce",
        process="xfce4-panel",
        unit=None,
        command=("xfce4-panel", "-r"),
        hint="xfce4-panel -r",
        required=("xfce4-panel",),
    ),
    _DesktopSpec(
        key="cinnamon",
        name="Cinnamon",
        process="cinnamon",
        unit=None,
        command=("cinnamon", "--replace"),
        hint="cinnamon --replace",
        required=("cinnamon",),
        wayland_command=False,
        reason="Wayland 会话下无法在不注销的情况下重启 Cinnamon。",
    ),
    _DesktopSpec(
        key="mate",
        name="MATE",
        process="mate-panel",
        unit=None,
        command=("mate-panel", "--replace"),
        hint="mate-panel --replace",
        required=("mate-panel",),
    ),
    _DesktopSpec(
        key="sway",
        name="Sway",
        process="sway",
        unit=None,
        command=None,
        hint="",
        reason="Sway 是 Wayland 合成器，重启桌面等同于重新登录。",
    ),
    _DesktopSpec(
        key="hyprland",
        name="Hyprland",
        process="Hyprland",
        unit=None,
        command=None,
        hint="",
        reason="Hyprland 是 Wayland 合成器，重启桌面等同于重新登录。",
    ),
)

_TOKEN_ALIASES = {
    "KDE": "kde",
    "PLASMA": "kde",
    "GNOME": "gnome",
    "UNITY": "gnome",
    "XFCE": "xfce",
    "X-CINNAMON": "cinnamon",
    "CINNAMON": "cinnamon",
    "MATE": "mate",
    "SWAY": "sway",
    "HYPRLAND": "hyprland",
}


# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------


def parse_os_release(path: Path | str = Path("/etc/os-release")) -> dict[str, str]:
    """Parse the shell-like key=value file at *path*."""

    data: dict[str, str] = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return data

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def parse_version(text: str) -> tuple[int, ...] | None:
    """Extract the first dotted numeric version from arbitrary text."""

    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def guess_pkgbase(release: str) -> str:
    """Best-effort mapping from an uname release to an Arch kernel package."""

    for suffix, pkgbase in (
        ("-rt-lts", "linux-rt-lts"),
        ("-lts", "linux-lts"),
        ("-zen", "linux-zen"),
        ("-hardened", "linux-hardened"),
        ("-rt", "linux-rt"),
    ):
        if release.endswith(suffix):
            return pkgbase
    return "linux"


def read_pkgbase(release: str, modules_dir: Path | str = Path("/usr/lib/modules")) -> str | None:
    """Read /usr/lib/modules/<release>/pkgbase when it exists."""

    try:
        value = (Path(modules_dir) / release / "pkgbase").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def kernel_pretty_name(pkgbase: str | None) -> str:
    if not pkgbase:
        return "Linux"
    return KERNEL_PRETTY_NAMES.get(pkgbase, pkgbase)


def kernel_version(release: str) -> str:
    return release.split("-", 1)[0]


def current_kernel_display(
    release: str | None = None,
    modules_dir: Path | str = Path("/usr/lib/modules"),
) -> str:
    release = release or os.uname().release
    pkgbase = read_pkgbase(release, modules_dir) or guess_pkgbase(release)
    return f"{kernel_pretty_name(pkgbase)} {kernel_version(release)}"


def _read_text(path: Path | str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def systemd_version() -> tuple[int, ...] | None:
    """Return the installed systemd version, or None when it is unavailable."""

    try:
        result = subprocess.run(
            ["systemctl", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"systemd\s+(\d+(?:\.\d+)*)", result.stdout)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def read_lockdown(
    path: Path | str = Path("/sys/kernel/security/lockdown"),
) -> str | None:
    """Return the active kernel lockdown mode, or None when it is disabled."""

    text = _read_text(path)
    for token in text.split():
        if token.startswith("[") and token.endswith("]"):
            value = token[1:-1]
            return None if value == "none" else value
    return None


def user_unit_exists(unit: str, home: Path | None = None) -> bool:
    home = home or Path.home()
    for base in (
        Path("/usr/lib/systemd/user"),
        Path("/etc/systemd/user"),
        home / ".config/systemd/user",
    ):
        if (base / unit).exists():
            return True
    return False


def _process_running(name: str, proc_dir: Path | str = Path("/proc")) -> bool:
    try:
        entries = Path(proc_dir).iterdir()
    except OSError:
        return False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        if _read_text(entry / "comm") == name:
            return True
        # Some compositors change their comm; cmdline is a useful fallback.
        cmdline = _read_text(entry / "cmdline")
        if cmdline and name in cmdline.split("\0")[0].rsplit("/", 1)[-1]:
            return True
    return False


def _env_tokens(env: dict[str, str]) -> list[str]:
    tokens: list[str] = []
    for key in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"):
        raw = env.get(key, "")
        for token in re.split(r"[:;]", raw):
            token = token.strip().upper()
            if token:
                tokens.append(token)
    return tokens


def _spec_from_token(token: str) -> _DesktopSpec | None:
    key = _TOKEN_ALIASES.get(token)
    if key is None:
        return None
    for spec in _DESKTOP_SPECS:
        if spec.key == key:
            return spec
    return None


def _spec_from_process(proc_dir: Path | str) -> _DesktopSpec | None:
    for spec in _DESKTOP_SPECS:
        if _process_running(spec.process, proc_dir):
            return spec
    return None


# ---------------------------------------------------------------------------
# Public detection entry points
# ---------------------------------------------------------------------------


def detect_system(
    os_release_path: Path | str = Path("/etc/os-release"),
    proc_comm_path: Path | str = Path("/proc/1/comm"),
    modules_dir: Path | str = Path("/usr/lib/modules"),
    sysrq_trigger: Path | str = Path("/proc/sysrq-trigger"),
    sysrq_value_path: Path | str = Path("/proc/sys/kernel/sysrq"),
    lockdown_path: Path | str = Path("/sys/kernel/security/lockdown"),
) -> SystemInfo:
    """Collect information about the host system."""

    osr = parse_os_release(os_release_path)
    release = os.uname().release
    comm = _read_text(proc_comm_path) or "unknown"
    is_systemd = comm == "systemd"
    sd_version = systemd_version() if is_systemd else None

    distro = osr.get("NAME", "未知发行版")
    pretty = osr.get("PRETTY_NAME", distro)
    sysrq_exists = Path(sysrq_trigger).exists()
    try:
        sysrq_value: int | None = int(_read_text(sysrq_value_path))
    except ValueError:
        sysrq_value = None

    return SystemInfo(
        distro=distro,
        distro_pretty=pretty,
        kernel_release=release,
        kernel_display=current_kernel_display(release, modules_dir),
        init_name=comm,
        init_display="systemd" if is_systemd else f"非 systemd（{comm}）",
        is_systemd=is_systemd,
        systemd_version=sd_version,
        has_soft_reboot=bool(
            is_systemd
            and sd_version is not None
            and sd_version >= SYSTEMD_SOFT_REBOOT_VERSION
        ),
        has_kexec_tools=shutil.which("kexec") is not None,
        has_pkexec=shutil.which("pkexec") is not None,
        has_reboot=shutil.which("reboot") is not None,
        has_sysrq=sysrq_exists,
        sysrq_value=sysrq_value,
        lockdown=read_lockdown(lockdown_path),
    )


def detect_desktop(
    system: SystemInfo,
    env: dict[str, str] | None = None,
    proc_dir: Path | str = Path("/proc"),
    home: Path | None = None,
    which=shutil.which,
) -> DesktopInfo:
    """Detect the desktop shell and which restart methods it supports."""

    env = dict(os.environ if env is None else env)
    token_spec = None
    for token in _env_tokens(env):
        token_spec = _spec_from_token(token)
        if token_spec is not None:
            break
    spec = token_spec or _spec_from_process(proc_dir)
    session_type = env.get("XDG_SESSION_TYPE", "unknown").lower()

    if spec is None:
        unavailable = "未检测到受支持的桌面环境。"
        return DesktopInfo(
            key="unknown",
            name="未知桌面",
            process="—",
            session_type=session_type,
            process_running=False,
            unit_method=DesktopMethod(
                mode="unit", label="以 systemd 单元重启（默认）", available=False, reason=unavailable
            ),
            command_method=DesktopMethod(
                mode="command", label="以命令重启（不推荐）", available=False, reason=unavailable
            ),
        )

    unit_reason = ""
    unit_available = False
    if spec.unit is None:
        unit_reason = "当前桌面没有可用的 systemd 用户单元。"
    elif not system.is_systemd:
        unit_reason = "当前 init 不是 systemd，无法使用 systemd 用户单元。"
    elif not user_unit_exists(spec.unit, home):
        unit_reason = f"未找到 systemd 用户单元 {spec.unit}。"
    else:
        unit_available = True

    command_reason = ""
    command_available = False
    if spec.command is None:
        command_reason = spec.reason or "当前桌面没有可用的重启命令。"
    elif session_type == "wayland" and not spec.wayland_command:
        command_reason = spec.reason
    else:
        missing = [name for name in spec.required if which(name) is None]
        if missing:
            command_reason = "未找到命令：" + "、".join(missing)
        else:
            command_available = True

    unit_method = DesktopMethod(
        mode="unit",
        label="以 systemd 单元重启（默认）",
        available=unit_available,
        reason=unit_reason,
        unit=spec.unit,
        hint=f"systemctl --user restart {spec.unit}" if spec.unit else "",
    )
    command_method = DesktopMethod(
        mode="command",
        label="以命令重启（不推荐）",
        available=command_available,
        reason=command_reason,
        command=spec.command,
        hint=spec.hint,
    )

    return DesktopInfo(
        key=spec.key,
        name=spec.name,
        process=spec.process,
        session_type=session_type,
        process_running=_process_running(spec.process, proc_dir),
        unit_method=unit_method,
        command_method=command_method,
    )
