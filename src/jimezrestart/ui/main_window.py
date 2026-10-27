"""The main window: layout, Alt behaviour and privileged execution."""

from __future__ import annotations

import os

from PyQt6.QtCore import QEvent, QProcess, Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, DISPLAY_VERSION
from ..actions import (
    ACTION_HARD_REBOOT,
    ACTION_KEXEC_LOAD,
    ACTION_KEXEC_NATIVE,
    ACTION_REBOOT,
    ACTION_SOFT_REBOOT,
    ActionError,
    PreparedCommand,
    desktop_command_argv,
    desktop_unit_argv,
    prepare_helper,
    run_detached,
)
from ..detect import DesktopInfo, SystemInfo
from ..kernels import KernelInfo, current_kernel
from .dialogs import ConfirmDialog, KernelDialog, show_error
from .theme import ACCENTS, PALETTE
from .widgets import (
    Card,
    CardHeader,
    Divider,
    DualActionButton,
    FinePrint,
    HintLabel,
    InfoRow,
    MenuButton,
    PrimaryButton,
    SectionTitle,
    logo_label,
    repolish,
)


STATUS_READY = "就绪"
STATUS_RESET_MS = 6000


class MainWindow(QMainWindow):
    def __init__(
        self,
        system: SystemInfo,
        desktop: DesktopInfo,
        kernels: list[KernelInfo],
        demo: bool = False,
    ) -> None:
        super().__init__()
        self.system = system
        self.desktop = desktop
        self.kernels = kernels
        self.demo = demo

        self.desktop_mode = (
            "unit" if desktop.unit_method.available and system.is_systemd else "command"
        )
        self.warm_mode = "restart"
        self.cold_mode = "reboot"
        self.native_kexec = False
        self._alt = False
        self._alt_down = False
        self._alt_poll_armed = True
        self._busy = False
        self._proc: QProcess | None = None
        self._aux_proc: QProcess | None = None
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.setInterval(STATUS_RESET_MS)
        self._status_timer.timeout.connect(self._reset_status)

        self.setWindowTitle(f"{APP_NAME} {DISPLAY_VERSION}")
        self.resize(840, 900)
        self.setMinimumSize(700, 720)
        self._build_ui()
        self._refresh_actions()
        self._center_on_screen()

        self._alt_timer = QTimer(self)
        self._alt_timer.setInterval(120)
        self._alt_timer.timeout.connect(self._poll_alt)
        self._alt_timer.start()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        scroll = QScrollArea(root)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root_layout.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        column = QWidget(content)
        column.setMaximumWidth(860)
        column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        centered = QHBoxLayout()
        centered.setContentsMargins(0, 0, 0, 0)
        centered.setSpacing(0)
        centered.addStretch(1)
        centered.addWidget(column, 1000)
        centered.addStretch(1)
        content_layout.addLayout(centered, 1)

        col = QVBoxLayout(column)
        col.setContentsMargins(16, 14, 16, 12)
        col.setSpacing(8)

        col.addLayout(self._build_header())
        col.addSpacing(2)

        col.addWidget(SectionTitle("桌面重启", column))
        col.addWidget(self._build_desktop_card())

        col.addSpacing(2)
        col.addWidget(SectionTitle("操作系统重启", column))
        col.addWidget(self._build_hot_card())
        col.addWidget(self._build_warm_card())
        col.addWidget(self._build_cold_card())

        col.addSpacing(2)
        col.addWidget(SectionTitle("检测信息", column))
        col.addWidget(self._build_info_card())

        col.addSpacing(2)
        col.addLayout(self._build_footer())
        col.addStretch(1)

        scroll.setWidget(content)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        row.addWidget(logo_label(42), 0, Qt.AlignmentFlag.AlignVCenter)

        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(1)
        title = QLabel(APP_NAME, self)
        title.setObjectName("appTitle")
        titles.addWidget(title)
        subtitle = QLabel("桌面 · 内核 · 系统重启控制台", self)
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(subtitle)
        row.addLayout(titles)

        row.addStretch(1)

        version = QLabel(DISPLAY_VERSION, self)
        version.setObjectName("versionBadge")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(version, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _build_desktop_card(self) -> Card:
        card = Card("green", self)
        header = CardHeader("重启桌面", "green", card)
        header.add_badge(self.desktop.name, "green")
        if self.desktop.session_type not in ("unknown", ""):
            header.add_badge(self.desktop.session_type.upper())

        menu = MenuButton("其它方式", card)
        menu.setMenu(QMenu(menu))
        menu.menu().setToolTipsVisible(True)
        self.desktop_menu = menu.menu()

        self.unit_action = QAction("以 systemd 单元重启（默认）", self)
        self.unit_action.triggered.connect(lambda: self._set_desktop_mode("unit"))
        menu.menu().addAction(self.unit_action)

        self.command_action = QAction("以命令重启（不推荐）", self)
        self.command_action.triggered.connect(lambda: self._set_desktop_mode("command"))
        menu.menu().addAction(self.command_action)
        header.add_menu(menu)
        card.add(header)

        self.desktop_note = HintLabel(self._desktop_note(), card)
        card.add(self.desktop_note)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 1, 0, 0)
        action_row.setSpacing(14)
        self.desktop_button = DualActionButton(
            "重启桌面", "以命令重启桌面", "green", card
        )
        self.desktop_button.clicked.connect(self._on_desktop_clicked)
        action_row.addWidget(self.desktop_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.desktop_hint = QLabel("", card)
        self.desktop_hint.setObjectName("finePrint")
        self.desktop_hint.setWordWrap(True)
        action_row.addWidget(self.desktop_hint, 1)
        card.add_layout(action_row)
        return card

    def _desktop_note(self) -> str:
        if self.desktop.key == "unknown":
            return "未检测到受支持的桌面环境。"
        suffix = "" if self.desktop.process_running else "，进程未运行"
        return f"检测到当前桌面：{self.desktop.name}（{self.desktop.process}{suffix}）"

    def _build_hot_card(self) -> Card:
        card = Card("orange", self)
        header = CardHeader("热重启", "orange", card)
        header.add_badge("soft-reboot", "orange")
        card.add(header)

        hint = HintLabel(
            "也叫软重启，使用 <span style=\"font-family:monospace; color:#f7c79b;\">"
            "systemctl soft-reboot</span>，需要使用 systemd 并且版本足够高。"
            "该方式只会重启用户空间，速度快，但不能解决内核相关问题。",
            card,
        )
        card.add(hint)

        row = QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 0)
        row.setSpacing(14)
        self.hot_button = PrimaryButton("热重启", "orange", card)
        self.hot_button.clicked.connect(self._on_hot_clicked)
        row.addWidget(self.hot_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.hot_hint = QLabel("", card)
        self.hot_hint.setObjectName("finePrint")
        self.hot_hint.setWordWrap(True)
        row.addWidget(self.hot_hint, 1)
        card.add_layout(row)
        return card

    def _build_warm_card(self) -> Card:
        card = Card("yellow", self)
        header = CardHeader("暖重启", "yellow", card)
        header.add_badge("kexec", "yellow")

        convert = MenuButton("转换…", card)
        convert.setMenu(QMenu(convert))
        self.warm_menu = convert.menu()

        self.warm_restart_action = QAction("重启当前内核", self)
        self.warm_restart_action.triggered.connect(lambda: self._set_warm_mode("restart"))
        convert.menu().addAction(self.warm_restart_action)

        self.warm_switch_action = QAction("切换操作系统内核", self)
        self.warm_switch_action.triggered.connect(lambda: self._set_warm_mode("switch"))
        convert.menu().addAction(self.warm_switch_action)
        header.add_menu(convert)

        options = MenuButton("选项…", card)
        options.setMenu(QMenu(options))
        options.menu().setToolTipsVisible(True)
        self.warm_options_menu = options.menu()
        self.native_action = QAction("使用原生 kexec（⚠️ 可能黑屏卡死）", self)
        self.native_action.setCheckable(True)
        self.native_action.setToolTip(
            "载入内核后直接执行 kexec -e，绕过 systemd；部分硬件上可能黑屏或卡死。"
        )
        self.native_action.toggled.connect(self._on_native_action_toggled)
        options.menu().addAction(self.native_action)
        options.menu().addSeparator()
        explain = QAction("关于 kexec 选项", self)
        explain.triggered.connect(self._show_kexec_help)
        options.menu().addAction(explain)
        header.add_menu(options)
        card.add(header)

        hint = HintLabel(
            "使用 <span style=\"font-family:monospace; color:#f2df8d;\">kexec -l</span> 和 "
            "<span style=\"font-family:monospace; color:#f2df8d;\">systemd kexec</span> "
            "重新运行内核，无需重新经过主板自检。",
            card,
        )
        card.add(hint)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 1, 0, 0)
        action_row.setSpacing(14)
        self.warm_button = DualActionButton(
            "重启当前内核", "切换操作系统内核", "yellow", card
        )
        self.warm_button.clicked.connect(self._on_warm_clicked)
        action_row.addWidget(self.warm_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.warm_hint = QLabel("", card)
        self.warm_hint.setObjectName("finePrint")
        self.warm_hint.setWordWrap(True)
        action_row.addWidget(self.warm_hint, 1)
        card.add_layout(action_row)
        return card

    def _build_cold_card(self) -> Card:
        card = Card("blue", self)
        header = CardHeader("冷重启", "blue", card)
        header.add_badge("reboot", "blue")

        convert = MenuButton("转换…", card)
        convert.setMenu(QMenu(convert))
        self.cold_menu = convert.menu()

        self.cold_reboot_action = QAction("标准重启", self)
        self.cold_reboot_action.triggered.connect(lambda: self._set_cold_mode("reboot"))
        convert.menu().addAction(self.cold_reboot_action)

        self.cold_hard_action = QAction("硬重启（⚠️ 谨慎使用）", self)
        self.cold_hard_action.triggered.connect(lambda: self._set_cold_mode("hard"))
        convert.menu().addAction(self.cold_hard_action)
        header.add_menu(convert)
        card.add(header)

        hint = HintLabel("使用 <span style=\"font-family:monospace; color:#b7d7fb;\">reboot</span> 完成标准重启。", card)
        card.add(hint)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 1, 0, 0)
        action_row.setSpacing(14)
        self.cold_button = DualActionButton("标准重启", "硬重启", "blue", card)
        self.cold_button.clicked.connect(self._on_cold_clicked)
        action_row.addWidget(self.cold_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.cold_hint = QLabel("", card)
        self.cold_hint.setObjectName("finePrint")
        self.cold_hint.setWordWrap(True)
        action_row.addWidget(self.cold_hint, 1)
        card.add_layout(action_row)
        return card

    def _build_info_card(self) -> Card:
        card = Card("blue", self)
        header = CardHeader("检测信息", "blue", card)
        header.add_badge("只读")
        card.add(header)

        self.info_distro = InfoRow("发行版名称", self.system.distro_pretty, card)
        self.info_kernel = InfoRow("正在运行的内核", self.system.kernel_display, card)
        self.info_init = InfoRow("初始化系统实现（init）", self.system.init_display, card)
        card.add(self.info_distro)
        card.add(self.info_kernel)
        card.add(self.info_init)

        details = []
        if self.system.systemd_version:
            details.append("systemd " + ".".join(map(str, self.system.systemd_version)))
        details.append("kexec-tools 已安装" if self.system.has_kexec_tools else "未安装 kexec-tools")
        if self.system.lockdown:
            details.append(f"lockdown={self.system.lockdown}")
        foot = FinePrint(" · ".join(details), card)
        foot.setStyleSheet(f"color: {PALETTE.faint}; font-size: 10.5px;")
        card.add(foot)
        return card

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(2, 2, 2, 0)
        row.setSpacing(12)
        self.status = QLabel(STATUS_READY, self)
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        row.addWidget(self.status, 1)
        hint = QLabel("按住 Alt 切换主操作 · GPL-3.0-only", self)
        hint.setObjectName("finePrint")
        hint.setToolTip("Alt 激活每个主按钮的第二种操作。也可以使用各卡片上的菜单手动切换。")
        row.addWidget(hint, 0, Qt.AlignmentFlag.AlignRight)
        return row

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _set_dual_text(self, button: DualActionButton, normal: str, alt: str) -> None:
        button.normal_text = normal
        button.alt_text = alt
        button.setText(alt if self._alt else normal)

    def _set_accent(self, button: QPushButton, accent: str) -> None:
        if button.property("accent") == accent:
            return
        button.setProperty("accent", accent)
        repolish(button)

    def _current_kernel(self) -> KernelInfo | None:
        return current_kernel(self.kernels, self.system.kernel_release)

    def _kexec_base_reason(self) -> str:
        """Reasons that block every kexec path, including native kexec."""

        if self.system.lockdown:
            return f"内核 lockdown（{self.system.lockdown}）已启用，kexec 被禁止。"
        if not self.system.has_kexec_tools:
            return "未安装 kexec-tools，无法使用 kexec。"
        if not self.system.has_pkexec:
            return "未找到 pkexec（polkit），无法执行需要特权的操作。"
        kernel = self._current_kernel()
        if kernel is None:
            return "未在 /usr/lib/modules 下找到当前内核。"
        if not kernel.available:
            return kernel.reason or "当前内核缺少匹配的 initramfs。"
        return ""

    def _kexec_systemd_reason(self) -> str:
        if not self.system.is_systemd:
            return "当前 init 不是 systemd；请勾选「使用原生 kexec」绕过 systemd。"
        return ""

    def _kexec_reason(self) -> str:
        base = self._kexec_base_reason()
        if base:
            return base
        return self._kexec_systemd_reason()

    def _privilege_reason(self) -> str:
        if not self.system.has_pkexec:
            return "未找到 pkexec（polkit），无法执行需要特权的操作。"
        return ""

    def _select_reason(self, available: bool, reason: str) -> str:
        if self._busy:
            return "正在执行上一个操作，请稍候。"
        if not available:
            return reason
        return ""

    def _refresh_actions(self) -> None:
        self._refresh_desktop()
        self._refresh_hot()
        self._refresh_warm()
        self._refresh_cold()

    def _refresh_desktop(self) -> None:
        unit = self.desktop.unit_method
        command = self.desktop.command_method
        selected = unit if self.desktop_mode == "unit" else command

        unit_available = unit.available and self.system.is_systemd
        if unit.available and not self.system.is_systemd:
            unit_reason = "当前 init 不是 systemd，无法使用 systemd 用户单元。"
        else:
            unit_reason = unit.reason

        # 菜单只保留与当前主按钮不同的选项，避免同一操作出现两次。
        self.unit_action.setVisible(self.desktop_mode != "unit")
        self.command_action.setVisible(self.desktop_mode != "command")
        self.unit_action.setEnabled(unit_available and not self._busy)
        self.command_action.setEnabled(command.available and not self._busy)
        self.unit_action.setToolTip(unit_reason if not unit_available else unit.hint)
        self.command_action.setToolTip(
            command.reason if not command.available else command.hint
        )

        self._set_dual_text(
            self.desktop_button,
            "重启桌面" if self.desktop_mode == "unit" else "以命令重启桌面",
            "以命令重启桌面" if self.desktop_mode == "unit" else "以命令重启桌面",
        )

        effective = command if self._alt else selected
        if not self._alt and self.desktop_mode == "unit":
            effective_available, effective_reason = unit_available, unit_reason
        else:
            effective_available, effective_reason = command.available, command.reason
        reason = self._select_reason(effective_available, effective_reason)
        self.desktop_button.setEnabled(not reason)
        self.desktop_button.setToolTip(reason or f"将执行：{effective.hint}")

        if self.desktop_mode == "unit":
            self.desktop_hint.setText(
                f"当前方式：systemd 用户单元 · {unit.hint or '—'}"
            )
        else:
            self.desktop_hint.setText("当前方式：命令 · 不经过 systemd 用户单元")

    def _refresh_hot(self) -> None:
        reason = self._soft_reason()
        self.hot_button.setEnabled(not reason)
        self.hot_button.setToolTip(reason or "将执行：systemctl soft-reboot")
        if reason:
            self.hot_hint.setText(reason)
        elif self.system.systemd_version:
            version = ".".join(map(str, self.system.systemd_version))
            self.hot_hint.setText(f"systemd {version} · 只重启用户空间")
        else:
            self.hot_hint.setText("只重启用户空间")

    def _soft_reason(self) -> str:
        privilege = self._privilege_reason()
        if privilege:
            return privilege
        if not self.system.is_systemd:
            return "当前 init 不是 systemd，soft-reboot 不可用。"
        if not self.system.has_soft_reboot:
            return "systemd 版本过低，soft-reboot 需要 systemd 254 或更高版本。"
        return ""

    def _refresh_warm(self) -> None:
        base = self._kexec_base_reason()
        systemd_ok = self.system.is_systemd and not base
        current = self._current_kernel()
        native_available = not base
        active_ok = native_available and (self.native_kexec or systemd_ok)
        restart_ok = active_ok and current is not None and current.available
        switch_ok = active_ok

        self.native_action.setEnabled(native_available and not self._busy)
        self.native_action.setChecked(self.native_kexec)
        if base:
            self.native_action.setToolTip(base)
        elif not self.system.is_systemd:
            self.native_action.setToolTip(
                "当前 init 不是 systemd；启用后使用 kexec -e 直接重启，无需 systemd。"
            )
        else:
            self.native_action.setToolTip(
                "载入内核后直接执行 kexec -e，绕过 systemd；部分硬件上可能黑屏或卡死。"
            )

        self.warm_restart_action.setVisible(self.warm_mode != "restart")
        self.warm_switch_action.setVisible(self.warm_mode != "switch")
        self.warm_restart_action.setEnabled(restart_ok and not self._busy)
        self.warm_switch_action.setEnabled(switch_ok and not self._busy)

        self._set_dual_text(
            self.warm_button,
            "重启当前内核" if self.warm_mode == "restart" else "切换操作系统内核",
            "切换操作系统内核",
        )
        effective_switch = self._alt or self.warm_mode == "switch"
        effective_ok = switch_ok if effective_switch else restart_ok
        if base:
            reason = base
        elif not self.native_kexec and not self.system.is_systemd:
            reason = self._kexec_systemd_reason()
        elif not effective_ok and current is not None and not current.available:
            reason = current.reason or "当前内核缺少匹配的 initramfs。"
        else:
            reason = ""
        reason = self._select_reason(not reason, reason)
        self.warm_button.setEnabled(not reason)
        self.warm_button.setToolTip(
            reason
            or (
                "将选择另一个已安装的内核并通过 kexec 启动。"
                if effective_switch
                else "将使用 kexec 重新启动当前内核。"
            )
        )

        if reason:
            self.warm_hint.setText(reason)
        elif effective_switch:
            self.warm_hint.setText("Alt：选择内核 · 会终止当前会话")
        elif self.native_kexec:
            self.warm_hint.setText("原生 kexec · kexec -l → kexec -e")
        else:
            self.warm_hint.setText("kexec -l → systemctl kexec")

    def _refresh_cold(self) -> None:
        privilege = self._privilege_reason()
        reboot_reason = privilege
        if not reboot_reason and not self.system.has_reboot:
            reboot_reason = "未找到 reboot 命令。"
        hard_reason = privilege
        if not hard_reason and not self.system.has_sysrq:
            hard_reason = "/proc/sysrq-trigger 不可用，无法执行 SysRq 硬重启。"

        self.cold_reboot_action.setVisible(self.cold_mode != "reboot")
        self.cold_hard_action.setVisible(self.cold_mode != "hard")
        self.cold_reboot_action.setEnabled(not reboot_reason and not self._busy)
        self.cold_hard_action.setEnabled(not hard_reason and not self._busy)

        effective_hard = self._alt or self.cold_mode == "hard"
        self._set_dual_text(
            self.cold_button,
            "标准重启" if self.cold_mode == "reboot" else "硬重启",
            "硬重启",
        )
        self._set_accent(self.cold_button, "red" if effective_hard else "blue")

        if effective_hard:
            reason = self._select_reason(not hard_reason, hard_reason)
        else:
            reason = self._select_reason(not reboot_reason, reboot_reason)
        self.cold_button.setEnabled(not reason)
        self.cold_button.setToolTip(
            reason
            or (
                "将执行：echo b | sudo tee /proc/sysrq-trigger（经由 pkexec 助手）"
                if effective_hard
                else "将执行：reboot"
            )
        )
        if reason:
            self.cold_hint.setText(reason)
        else:
            self.cold_hint.setText(
                "SysRq 硬重启 · 不会等待文件系统同步" if effective_hard else "标准 reboot"
            )

    # ------------------------------------------------------------------
    # Alt handling
    # ------------------------------------------------------------------

    def _poll_alt(self) -> None:
        # While a physical Alt press is down, never let a flaky modifier
        # query cancel it. After a release, ignore stale Alt readings until
        # the platform has reported one clean no-Alt frame; otherwise a
        # cached modifier state can switch the UI back on after release.
        if self._alt_down:
            return
        modifiers = (
            QApplication.queryKeyboardModifiers()
            | QApplication.keyboardModifiers()
        )
        if not (modifiers & Qt.KeyboardModifier.AltModifier):
            self._alt_poll_armed = True
            self._set_alt(False)
        elif self._alt_poll_armed:
            self._set_alt(True)

    def _set_alt(self, alt: bool) -> None:
        if alt == self._alt:
            return
        self._alt = alt
        self.desktop_button.set_alt(alt)
        self.warm_button.set_alt(alt)
        self.cold_button.set_alt(alt)
        self._refresh_actions()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 - Qt naming
        if isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Alt:
            if event.type() == QEvent.Type.KeyPress:
                if event.isAutoRepeat():
                    # A repeat queued after the release must not re-arm
                    # polling with a stale Alt modifier state.
                    if not self._alt_down:
                        self._alt_poll_armed = False
                else:
                    self._alt_down = True
                    self._alt_poll_armed = True
                    self._set_alt(True)
            elif event.type() == QEvent.Type.KeyRelease:
                self._alt_down = False
                self._alt_poll_armed = False
                self._set_alt(False)
        elif event.type() == QEvent.Type.ApplicationActivate:
            # Re-sync after returning from another application; a release
            # may have happened while we were not receiving key events.
            self._alt_down = False
            self._poll_alt()
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Mode selection
    # ------------------------------------------------------------------

    def _set_desktop_mode(self, mode: str) -> None:
        method = self.desktop.unit_method if mode == "unit" else self.desktop.command_method
        if not method.available:
            self._set_status(method.reason, "error")
            return
        if mode == "unit" and not self.system.is_systemd:
            self._set_status("当前 init 不是 systemd，无法使用 systemd 用户单元。", "error")
            return
        self.desktop_mode = mode
        self._refresh_actions()

    def _set_warm_mode(self, mode: str) -> None:
        reason = self._kexec_reason() if not self.native_kexec else self._kexec_base_reason()
        if mode == "switch" and reason:
            self._set_status(reason, "error")
            return
        self.warm_mode = mode
        self._refresh_actions()

    def _set_cold_mode(self, mode: str) -> None:
        self.cold_mode = mode
        self._refresh_actions()

    def _on_native_action_toggled(self, checked: bool) -> None:
        self.native_kexec = checked
        self._refresh_actions()

    def _show_kexec_help(self) -> None:
        QMessageBox.information(
            self,
            "关于 kexec 选项",
            "默认流程：先由助手执行 kexec -l 载入选定的内核，再调用 systemctl kexec。\n\n"
            "原生 kexec：载入内核后直接执行 kexec -e，不经过 systemd。"
            "它更接近底层，在部分硬件上可能导致黑屏或卡死，因此默认关闭。",
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_desktop_clicked(self) -> None:
        method = (
            self.desktop.command_method if self._alt else
            (self.desktop.unit_method if self.desktop_mode == "unit" else self.desktop.command_method)
        )
        if not method.available:
            self._set_status(method.reason, "error")
            return
        if self.demo:
            self._set_status("演示模式：未执行任何真实操作。", "ok")
            return
        if method.mode == "unit" and method.unit:
            self._run_unit_restart(method.unit)
        elif method.command:
            try:
                run_detached(desktop_command_argv(method.command))
            except ActionError as error:
                self._fail("无法重启桌面", str(error))
                return
            self._set_status("已发送桌面重启命令。", "ok")

    def _run_unit_restart(self, unit: str) -> None:
        try:
            argv = desktop_unit_argv(unit)
        except ActionError as error:
            self._fail("无法重启桌面", str(error))
            return
        proc = QProcess(self)
        proc.setProgram(argv[0])
        proc.setArguments(argv[1:])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.finished.connect(lambda code, _status: self._on_unit_finished(code))
        self._aux_proc = proc
        self._set_status(f"正在重启 {unit}…")
        proc.start()

    def _on_unit_finished(self, code: int) -> None:
        output = ""
        if self._aux_proc is not None:
            output = bytes(self._aux_proc.readAllStandardOutput()).decode(
                "utf-8", "replace"
            )
        self._aux_proc = None
        if code == 0:
            self._set_status("桌面已重启。", "ok")
        else:
            self._fail(
                "桌面重启失败",
                "systemctl --user restart 返回了错误。",
                output or f"退出码：{code}",
            )

    def _on_hot_clicked(self) -> None:
        reason = self._soft_reason()
        if reason:
            self._set_status(reason, "error")
            return
        dialog = ConfirmDialog(
            "热重启",
            "要热重启用户空间吗？",
            "将执行 <b>systemctl soft-reboot</b>。所有会话和未保存的工作都会丢失，"
            "但内核与固件不会被重新初始化。",
            "热重启",
            accent="orange",
            warning="热重启不会解决内核、驱动或固件相关的问题。",
            parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            self._run_helper(ACTION_SOFT_REBOOT)

    def _on_warm_clicked(self) -> None:
        effective_switch = self._alt or self.warm_mode == "switch"
        if effective_switch:
            self._switch_kernel()
            return
        reason = (
            self._kexec_base_reason()
            if self.native_kexec
            else self._kexec_reason()
        )
        if reason:
            self._set_status(reason, "error")
            return
        kernel = self._current_kernel()
        if kernel is None or not kernel.available:
            self._set_status(kernel.reason if kernel else "找不到当前内核。", "error")
            return
        mode = "原生 kexec" if self.native_kexec else "systemd kexec"
        dialog = ConfirmDialog(
            "暖重启",
            f"使用{mode}重启当前内核？",
            f"将重新启动 <b>{kernel.name} {kernel.version}</b>"
            f"（{kernel.release}），无需重新经过主板自检。",
            "重启内核",
            accent="yellow",
            warning="重启内核会终止所有会话，请先保存工作。"
            + ("原生 kexec 在部分硬件上可能导致黑屏或卡死。" if self.native_kexec else ""),
            parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            action = ACTION_KEXEC_NATIVE if self.native_kexec else ACTION_KEXEC_LOAD
            self._run_helper(action, kernel)

    def _switch_kernel(self) -> None:
        reason = (
            self._kexec_base_reason()
            if self.native_kexec
            else self._kexec_reason()
        )
        if reason:
            self._set_status(reason, "error")
            return
        dialog = KernelDialog(self.kernels, self.system.kernel_release, self)
        if dialog.exec() != KernelDialog.DialogCode.Accepted or dialog.selected is None:
            return
        action = ACTION_KEXEC_NATIVE if self.native_kexec else ACTION_KEXEC_LOAD
        self._run_helper(action, dialog.selected)

    def _on_cold_clicked(self) -> None:
        hard = self._alt or self.cold_mode == "hard"
        if hard:
            if not self.system.has_sysrq:
                self._set_status(
                    "/proc/sysrq-trigger 不可用，无法执行 SysRq 硬重启。", "error"
                )
                return
            dialog = ConfirmDialog(
                "硬重启",
                "确定要硬重启吗？",
                "将执行 <b>echo b | sudo tee /proc/sysrq-trigger</b>，"
                "立即强制重启，不等待文件系统同步。",
                "硬重启",
                accent="red",
                warning="可能造成数据丢失或文件系统损坏。只在系统完全无响应时使用。",
                countdown=5,
                parent=self,
            )
        else:
            dialog = ConfirmDialog(
                "标准重启",
                "要重启系统吗？",
                "将执行 <b>reboot</b>，所有会话和未保存的工作都会丢失。",
                "重启",
                accent="blue",
                warning="请确认已经保存所有工作。",
                parent=self,
            )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            self._run_helper(ACTION_HARD_REBOOT if hard else ACTION_REBOOT)

    # ------------------------------------------------------------------
    # Privileged helper
    # ------------------------------------------------------------------

    def _run_helper(self, action: str, kernel: KernelInfo | None = None) -> None:
        if self._busy:
            return
        if self.demo:
            self._set_status("演示模式：未执行任何真实操作。", "ok")
            return
        try:
            prepared = prepare_helper(action, kernel)
        except ActionError as error:
            self._fail("无法执行操作", str(error))
            return
        self._start_helper(prepared)

    def _start_helper(self, prepared: PreparedCommand) -> None:
        proc = QProcess(self)
        proc.setProgram(prepared.argv[0])
        proc.setArguments(list(prepared.argv[1:]))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.finished.connect(lambda code, _status: self._on_helper_finished(code))
        proc.errorOccurred.connect(self._on_helper_error)
        self._proc = proc
        self._set_busy(True)
        self._set_status(f"正在请求授权并执行：{prepared.description}…")
        proc.start()

    def _on_helper_finished(self, code: int) -> None:
        output = ""
        if self._proc is not None:
            output = bytes(self._proc.readAllStandardOutput()).decode("utf-8", "replace")
        self._proc = None
        self._set_busy(False)
        if code == 0:
            self._set_status("操作已提交，系统即将重启。", "ok")
            return
        if code == 126:
            message = "授权被取消，未执行任何操作。"
        elif code == 127:
            message = "未获得授权，或特权助手不可用。"
        else:
            message = f"特权操作失败（退出码 {code}）。"
        self._fail("操作失败", message, output)

    def _on_helper_error(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.ProcessError.FailedToStart:
            return
        self._proc = None
        self._set_busy(False)
        self._fail("无法启动 pkexec", "请确认 polkit 与 pkexec 已正确安装并在 PATH 中。")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._refresh_actions()

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    def _set_status(self, text: str, level: str = "") -> None:
        self.status.setText(text)
        self.status.setProperty("level", level)
        repolish(self.status)
        # Do not hide an in-progress operation behind a "ready" message.
        if self._busy:
            self._status_timer.stop()
        else:
            self._status_timer.start()

    def _reset_status(self) -> None:
        self._status_timer.stop()
        if self._busy:
            return
        self.status.setText(STATUS_READY)
        self.status.setProperty("level", "")
        repolish(self.status)

    def _fail(self, title: str, message: str, detail: str = "") -> None:
        self._set_status(message, "error")
        show_error(self, title, message, detail)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(area.center())
        self.move(frame.topLeft())

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt naming
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._alt_timer.stop()
        self._status_timer.stop()
        super().closeEvent(event)
