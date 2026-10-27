"""Sample data so the interface can be inspected without touching the system."""

from __future__ import annotations

from pathlib import Path

from .detect import DesktopInfo, DesktopMethod, SystemInfo
from .kernels import KernelInfo


def demo_data() -> tuple[SystemInfo, DesktopInfo, list[KernelInfo]]:
    system = SystemInfo(
        distro="Arch Linux",
        distro_pretty="Arch Linux",
        kernel_release="6.18.58-1-lts",
        kernel_display="Linux-LTS 6.18.58",
        init_name="systemd",
        init_display="systemd",
        is_systemd=True,
        systemd_version=(262, 3, 1),
        has_soft_reboot=True,
        has_kexec_tools=True,
        has_pkexec=True,
        has_reboot=True,
        has_sysrq=True,
        sysrq_value=1,
        lockdown=None,
    )

    desktop = DesktopInfo(
        key="kde",
        name="KDE Plasma",
        process="plasmashell",
        session_type="wayland",
        process_running=True,
        unit_method=DesktopMethod(
            mode="unit",
            label="以 systemd 单元重启（默认）",
            available=True,
            unit="plasma-plasmashell.service",
            hint="systemctl --user restart plasma-plasmashell.service",
        ),
        command_method=DesktopMethod(
            mode="command",
            label="以命令重启（不推荐）",
            available=True,
            command=(
                "sh",
                "-c",
                "kquitapp6 plasmashell >/dev/null 2>&1; sleep 1; "
                "setsid plasmashell >/dev/null 2>&1 </dev/null &",
            ),
            hint="kquitapp6 plasmashell && plasmashell",
        ),
    )

    kernels = [
        KernelInfo(
            release="6.18.58-1-lts",
            pkgbase="linux-lts",
            name="Linux-LTS",
            version="6.18.58",
            kernel=Path("/usr/lib/modules/6.18.58-1-lts/vmlinuz"),
            initrd=Path("/boot/initramfs-linux-lts.img"),
            is_current=True,
        ),
        KernelInfo(
            release="6.18.42-1-lts",
            pkgbase="linux-lts",
            name="Linux-LTS",
            version="6.18.42",
            kernel=Path("/usr/lib/modules/6.18.42-1-lts/vmlinuz"),
            initrd=Path("/boot/initramfs-linux-lts-fallback.img"),
            is_current=False,
        ),
        KernelInfo(
            release="7.1.6-arch1-1",
            pkgbase="linux",
            name="Linux",
            version="7.1.6",
            kernel=Path("/usr/lib/modules/7.1.6-arch1-1/vmlinuz"),
            initrd=Path("/boot/initramfs-linux.img"),
            is_current=False,
        ),
    ]
    return system, desktop, kernels


if __name__ == "__main__":
    from .app import main

    raise SystemExit(main([__file__, "--demo"]))
