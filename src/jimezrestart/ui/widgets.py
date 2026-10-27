"""Reusable widgets that give JimEzRestart its look."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .theme import ACCENTS, PALETTE


def repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class AccentBar(QFrame):
    """The thin coloured bar on the left edge of a card."""

    def __init__(self, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(4)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        color = ACCENTS[accent]
        self.setStyleSheet(
            f"background: {color}; border: none; border-radius: 2px;"
        )


class Card(QFrame):
    """A surface with a coloured accent bar and a vertical body layout."""

    def __init__(self, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.accent = accent

        outer = QHBoxLayout(self)
        outer.setContentsMargins(13, 11, 15, 11)
        outer.setSpacing(13)

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
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {PALETTE.border}; border: none;")
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
        self.accent = PALETTE.green

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1.5, 1.5, 15, 15)
        if not self.isEnabled():
            border = QColor("#333a47")
            fill = QColor("#1a1f27") if self.checked else QColor(0, 0, 0, 0)
        elif self.checked:
            border = QColor(self.accent)
            fill = QColor(self.accent)
        else:
            border = QColor(PALETTE.border_strong if self.hover else "#414b5d")
            fill = QColor("#1d232d")
        painter.setPen(QPen(border, 1.4))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 4, 4)
        if self.checked:
            pen = QPen(QColor("#0d1a14" if self.isEnabled() else "#6a7280"), 2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            from PyQt6.QtCore import QPointF
            from PyQt6.QtGui import QPolygonF

            painter.drawPolyline(
                QPolygonF(
                    [
                        QPointF(4.8, 9.2),
                        QPointF(7.7, 12.0),
                        QPointF(13.0, 6.0),
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
        self.indicator.accent = ACCENTS[accent]
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

    def set_alt(self, alt: bool) -> None:
        if alt == self._alt:
            return
        self._alt = alt
        self.setText(self.alt_text if alt else self.normal_text)

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
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {PALETTE.border}; border: none;")


def logo_label(size: int = 44) -> QLabel:
    from .theme import app_icon

    label = QLabel()
    pixmap = app_icon().pixmap(QSize(size, size))
    label.setPixmap(pixmap)
    label.setFixedSize(size, size)
    label.setScaledContents(True)
    return label
