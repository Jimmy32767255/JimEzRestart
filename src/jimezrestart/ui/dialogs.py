"""Dialogs: destructive confirmations and the kernel picker."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..kernels import KernelInfo
from .widgets import FinePrint, HintLabel, PrimaryButton


class ConfirmDialog(QDialog):
    """A confirmation dialog with an optional delayed confirm button."""

    def __init__(
        self,
        title: str,
        heading: str,
        body: str,
        confirm_text: str,
        accent: str = "red",
        warning: str | None = None,
        countdown: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setSizeGripEnabled(False)

        self._countdown = countdown
        self._remaining = countdown
        self._timer: QTimer | None = None
        self._confirm_text = confirm_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 20)
        layout.setSpacing(14)

        title_label = QLabel(heading, self)
        title_label.setObjectName("dialogTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        message = QLabel(body, self)
        message.setObjectName("dialogBody")
        message.setWordWrap(True)
        message.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(message)

        if warning:
            box = QFrame(self)
            box.setObjectName("warningBox")
            box_layout = QHBoxLayout(box)
            box_layout.setContentsMargins(14, 12, 14, 12)
            box_layout.setSpacing(10)
            icon = QLabel("⚠", box)
            icon.setObjectName("warningIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignTop)
            box_layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
            warning_label = QLabel(warning, box)
            warning_label.setWordWrap(True)
            box_layout.addWidget(warning_label, 1)
            layout.addWidget(box)

        layout.addSpacing(4)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)

        self.confirm_button = PrimaryButton(confirm_text, accent, self)
        self.confirm_button.setMinimumWidth(150)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.clicked.connect(self.accept)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)

        self.cancel_button.setFocus(Qt.FocusReason.OtherFocusReason)
        self.cancel_button.setAccessibleDescription("按钮，按回车键执行")
        self.confirm_button.setAccessibleDescription("按钮，按回车键执行")

        if countdown > 0:
            self.confirm_button.setEnabled(False)
            self.confirm_button.setText(f"{confirm_text}（{countdown} 秒）")
            self._timer = QTimer(self)
            self._timer.setInterval(1000)
            self._timer.timeout.connect(self._tick)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().showEvent(event)
        if self._timer is not None and not self._timer.isActive():
            self._timer.start()

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining > 0:
            self.confirm_button.setText(f"{self._confirm_text}（{self._remaining} 秒）")
            return
        if self._timer is not None:
            self._timer.stop()
        self.confirm_button.setText(self._confirm_text)
        self.confirm_button.setEnabled(True)


class KernelDialog(QDialog):
    """Pick an installed kernel to boot with kexec."""

    def __init__(
        self,
        kernels: list[KernelInfo],
        current_release: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("切换操作系统内核")
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setMinimumHeight(420)
        self.setSizeGripEnabled(False)

        self._kernels = kernels
        self._current_release = current_release
        self.selected: KernelInfo | None = None

        others = [kernel for kernel in kernels if kernel.release != current_release]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 20)
        layout.setSpacing(12)

        heading = QLabel("切换操作系统内核", self)
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)

        intro = HintLabel(
            "选择一个已安装的内核，通过 <b>kexec</b> 直接启动它，"
            "无需重新经过主板自检。切换会终止当前会话，请先保存工作。",
            self,
        )
        layout.addWidget(intro)

        if not others:
            layout.addSpacing(8)
            layout.addWidget(self._empty_state(others))
            layout.addStretch(1)
            close_row = QHBoxLayout()
            close_row.addStretch(1)
            close = QPushButton("关闭", self)
            close.setObjectName("secondaryButton")
            close.setCursor(Qt.CursorShape.PointingHandCursor)
            close.clicked.connect(self.reject)
            close_row.addWidget(close)
            layout.addLayout(close_row)
            self.confirm_button = None
            return

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("scrollContent")
        list_layout = QVBoxLayout(content)
        list_layout.setContentsMargins(0, 2, 4, 2)
        list_layout.setSpacing(7)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._buttons: dict[int, QPushButton] = {}
        for index, kernel in enumerate(kernels):
            button = self._kernel_button(kernel)
            self.group.addButton(button, index)
            self._buttons[index] = button
            list_layout.addWidget(button)
            if kernel.release == current_release:
                button.setChecked(True)
        list_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.details = FinePrint("", self)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.details)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = QPushButton("取消", self)
        cancel.setObjectName("secondaryButton")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.confirm_button = PrimaryButton("重启到所选内核", "yellow", self)
        self.confirm_button.setMinimumWidth(170)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self._accept_selection)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)

        self.group.idClicked.connect(self._on_selected)

        # 让方向键像单选组一样在内核之间移动，Tab 则在卡片、按钮之间移动。
        usable = [button for button in self._buttons.values() if button.isEnabled()]
        for index, button in enumerate(usable):
            button.installEventFilter(self)
            if index + 1 < len(usable):
                QWidget.setTabOrder(button, usable[index + 1])
        if usable:
            usable[0].setFocus(Qt.FocusReason.OtherFocusReason)
            QWidget.setTabOrder(usable[-1], self.confirm_button)

    def eventFilter(self, obj, event):  # noqa: N802 - Qt naming
        if event.type() == QEvent.Type.KeyPress and event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            step = -1 if event.key() == Qt.Key.Key_Up else 1
            if self._step_selection(obj, step):
                return True
        return super().eventFilter(obj, event)

    def _step_selection(self, current, step: int) -> bool:
        usable = [button for button in self._buttons.values() if button.isEnabled()]
        try:
            index = usable.index(current)
        except ValueError:
            return False
        target = usable[(index + step) % len(usable)]
        target.setFocus(Qt.FocusReason.TabFocusReason)
        target.setChecked(True)
        for button in usable:
            if button is not target:
                button.setChecked(False)
        self._on_selected(self.group.id(target))
        return True

    def _kernel_button(self, kernel: KernelInfo) -> QPushButton:
        is_current = kernel.release == self._current_release
        if is_current:
            status = "当前运行"
        elif not kernel.available:
            status = kernel.reason or "不可用"
        else:
            status = "可切换"
        text = f"{kernel.name}  {kernel.version}\n{kernel.release}  ·  {status}"
        button = QPushButton(text, self)
        button.setObjectName("kernelButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(56)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if is_current:
            button.setEnabled(False)
            button.setToolTip("这是当前正在运行的内核。")
        elif not kernel.available:
            button.setEnabled(False)
            button.setToolTip(kernel.reason or "该内核不可用。")
        else:
            button.setToolTip(f"{kernel.kernel}\n{kernel.initrd}")
        return button

    def _empty_state(self, others: list[KernelInfo]) -> QWidget:
        box = QFrame(self)
        box.setObjectName("infoBox")
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(9)

        title = QLabel("没有其它可切换的内核", box)
        title.setObjectName("emptyTitle")
        layout.addWidget(title)

        body = QLabel("当前系统只检测到一个可启动内核。请先用包管理器安装另一个内核，例如：", box)
        body.setWordWrap(True)
        body.setObjectName("emptyBody")
        layout.addWidget(body)

        for command in ("sudo pacman -S linux", "sudo pacman -S linux-lts"):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            code = QLabel(command, box)
            code.setObjectName("code")
            code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(code, 0)
            row.addStretch(1)
            layout.addLayout(row)

        note = QLabel("安装完成后重新打开本程序，新内核会自动出现在列表中。", box)
        note.setWordWrap(True)
        note.setObjectName("emptyBody")
        layout.addWidget(note)
        return box

    def _on_selected(self, index: int) -> None:
        kernel = self._kernels[index]
        if kernel.release == self._current_release or not kernel.available:
            return
        self.selected = kernel
        self.confirm_button.setEnabled(True)
        initrd = str(kernel.initrd) if kernel.initrd else "—"
        self.details.setText(
            f"内核镜像：{kernel.kernel}    initramfs：{initrd}"
        )

    def _accept_selection(self) -> None:
        if self.selected is not None and self.selected.available:
            self.accept()


def show_error(parent: QWidget | None, title: str, message: str, detail: str = "") -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    if detail:
        box.setDetailedText(detail.strip())
    box.setStandardButtons(QMessageBox.StandardButton.Close)
    box.exec()
