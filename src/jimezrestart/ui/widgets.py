"""Reusable widgets that give JimEzRestart its look."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    MODE_GLYPHS,
    MODE_LABELS,
    MODE_LIGHT,
    MODE_SYSTEM,
    current_mode,
    current_palette,
    next_mode,
    resolved_mode,
    set_theme,
    theme_bus,
)


def repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class AccentBar(QFrame):
    """The thin coloured bar on the left edge of a card."""

    def __init__(self, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("accentBar")
        self.setProperty("accent", accent)
        self.setFixedWidth(4)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)


class Card(QFrame):
    """A surface with a coloured accent bar and a vertical body layout."""

    def __init__(self, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.accent = accent

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 12, 8)
        outer.setSpacing(10)

        self.bar = AccentBar(accent, self)
        outer.addWidget(self.bar)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(7)
        outer.addLayout(self.body, 1)

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self.body.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0) -> None:
        self.body.addLayout(layout, stretch)


class CardHeader(QWidget):
    """Title, optional badges and right-aligned menu buttons."""

    def __init__(self, title: str, accent: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.title = QLabel(title, self)
        self.title.setObjectName("cardTitle")
        row.addWidget(self.title)

        self.badges = QHBoxLayout()
        self.badges.setContentsMargins(0, 0, 0, 0)
        self.badges.setSpacing(6)
        row.addLayout(self.badges)

        row.addStretch(1)

        self.menus = QHBoxLayout()
        self.menus.setContentsMargins(0, 0, 0, 0)
        self.menus.setSpacing(2)
        row.addLayout(self.menus)

        if accent:
            self.title.setStyleSheet("")

    def add_badge(self, text: str, accent: str | None = None) -> QLabel:
        badge = QLabel(text, self)
        badge.setObjectName("badge")
        if accent:
            badge.setProperty("accent", accent)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badges.addWidget(badge)
        return badge

    def add_menu(self, button: QToolButton) -> QToolButton:
        self.menus.addWidget(button)
        return button


class HintLabel(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("hint")
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)


class FinePrint(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("finePrint")
        self.setWordWrap(True)


class SectionTitle(QWidget):
    """Small muted heading, with an optional trailing rule."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(2, 0, 0, 0)
        row.setSpacing(10)
        label = QLabel(text, self)
        label.setObjectName("sectionTitle")
        row.addWidget(label)
        line = QFrame(self)
        line.setObjectName("rule")
        line.setFixedHeight(1)
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(line, 1)


class MenuButton(QToolButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("menuButton")
        self.setText(f"{text}  ▾")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(text)
        self.setAccessibleDescription("菜单按钮，按空格键或回车键打开，方向键选择")


class ThemeButton(QToolButton):
    """Cycles 跟随系统 → 深色 → 浅色 and shows the current choice."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("themeButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("切换界面主题：跟随系统、深色、浅色")
        self.clicked.connect(self._cycle)
        theme_bus().changed.connect(self._on_theme_changed)
        self._sync()

    def _cycle(self) -> None:
        set_theme(next_mode(current_mode()))

    def _on_theme_changed(self, _mode: str) -> None:
        self._sync()

    def _sync(self) -> None:
        mode = current_mode()
        label = MODE_LABELS[mode]
        glyph = MODE_GLYPHS[mode]
        text = f"{glyph}  {label}"
        if mode == MODE_SYSTEM:
            text += f"（{'深色' if resolved_mode() != MODE_LIGHT else '浅色'}）"
        self.setText(text)
        self.setAccessibleName(f"主题：{label}")
        self.setAccessibleDescription(
            "按钮，按空格键或回车键在跟随系统、深色、浅色之间切换"
        )


class MethodButton(QPushButton):
    """A radio-like full-width button used for the restart-method choices."""

    def __init__(self, text: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("methodButton")
        self.setProperty("accent", accent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggled.connect(lambda _checked: self._refresh_text())
        self._refresh_text()

    def _refresh_text(self) -> None:
        prefix = "●  " if self.isChecked() else "○  "
        self.setText(prefix + self._text)


class _CheckIndicator(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.checked = False
        self.hover = False
        self.focus = False
        self.accent_name = "green"

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        p = current_palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.focus and self.isEnabled():
            ring = QRectF(0.6, 0.6, 16.8, 16.8)
            painter.setPen(QPen(QColor(p.blue), 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(ring, 5, 5)
        rect = QRectF(2.6, 2.6, 12.8, 12.8)
        accent = p.accent(self.accent_name)
        if not self.isEnabled():
            border = QColor(p.check_disabled_border)
            fill = QColor(p.check_disabled_fill) if self.checked else QColor(0, 0, 0, 0)
        elif self.checked:
            border = QColor(accent)
            fill = QColor(accent)
        else:
            border = QColor(p.border_strong if self.hover else p.check_border)
            fill = QColor(p.check_fill)
        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 4, 4)
        if self.checked:
            mark = p.check_mark if self.isEnabled() else p.check_mark_disabled
            pen = QPen(QColor(mark), 2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            from PyQt6.QtCore import QPointF
            from PyQt6.QtGui import QPolygonF

            painter.drawPolyline(
                QPolygonF(
                    [
                        QPointF(5.4, 9.0),
                        QPointF(7.8, 11.5),
                        QPointF(12.4, 6.4),
                    ]
                )
            )
        painter.end()


class CheckRow(QWidget):
    """A check box with a large hit area and a themed indicator."""

    toggled = pyqtSignal(bool)

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._checked = False
        self._hover = False

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(9)
        self.indicator = _CheckIndicator(self)
        row.addWidget(self.indicator, 0, Qt.AlignmentFlag.AlignVCenter)
        self.label = QLabel(text, self)
        self.label.setObjectName("checkLabel")
        row.addWidget(self.label, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        self.text = text
        self.setAccessibleName(text)
        self.setAccessibleDescription("复选框，按空格键切换")
        self.setToolTip(text)

    def _sync_indicator_focus(self) -> None:
        self.indicator.focus = self.hasFocus()
        self.indicator.update()

    def focusInEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().focusInEvent(event)
        self._sync_indicator_focus()

    def focusOutEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().focusOutEvent(event)
        self._sync_indicator_focus()

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt naming
        hint = super().sizeHint()
        return QSize(hint.width(), max(hint.height(), 22))

    def isChecked(self) -> bool:  # noqa: N802 - Qt naming
        return self._checked

    def setChecked(self, checked: bool) -> None:  # noqa: N802 - Qt naming
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        self.indicator.checked = checked
        self.indicator.update()
        self.toggled.emit(checked)

    def set_accent(self, accent: str) -> None:
        self.indicator.accent_name = accent
        self.indicator.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setChecked(not self._checked)
            event.accept()
            return
        super().keyPressEvent(event)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._hover = True
        self.indicator.hover = True
        self.indicator.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._hover = False
        self.indicator.hover = False
        self.indicator.update()
        super().leaveEvent(event)

    def changeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self.indicator.setEnabled(self.isEnabled())
            self.label.setEnabled(self.isEnabled())
            self.setCursor(
                Qt.CursorShape.PointingHandCursor
                if self.isEnabled()
                else Qt.CursorShape.ArrowCursor
            )


class DualActionButton(QPushButton):
    """Primary action button whose label flips while Alt is held."""

    def __init__(
        self,
        normal_text: str,
        alt_text: str,
        accent: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(normal_text, parent)
        self.setObjectName("actionButton")
        self.setProperty("accent", accent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(190)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.normal_text = normal_text
        self.alt_text = alt_text
        self._alt = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(normal_text)
        self.setAccessibleDescription(
            f"按钮，不按 Alt 时执行“{normal_text}”，按住 Alt 时执行“{alt_text}”"
        )

    def set_alt(self, alt: bool) -> None:
        if alt == self._alt:
            return
        self._alt = alt
        self.setText(self.alt_text if alt else self.normal_text)
        self.setAccessibleName(self.alt_text if alt else self.normal_text)

    @property
    def alt_active(self) -> bool:
        return self._alt


class PrimaryButton(QPushButton):
    def __init__(self, text: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("actionButton")
        self.setProperty("accent", accent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(190)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(text)


class InfoRow(QWidget):
    def __init__(self, label: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(14)
        key = QLabel(label, self)
        key.setObjectName("fieldLabel")
        key.setFixedWidth(132)
        row.addWidget(key, 0, Qt.AlignmentFlag.AlignTop)
        self.value = QLabel(value, self)
        self.value.setObjectName("fieldValue")
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value.setWordWrap(True)
        row.addWidget(self.value, 1)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


class Divider(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFixedHeight(1)


def logo_label(size: int = 44) -> QLabel:
    from .theme import app_icon

    label = QLabel()
    pixmap = app_icon().pixmap(QSize(size, size))
    label.setPixmap(pixmap)
    label.setFixedSize(size, size)
    label.setScaledContents(True)
    return label
