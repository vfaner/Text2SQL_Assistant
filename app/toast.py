"""
Vue element-plus style toast notifications.

- Slides in from the top-right of the parent window
- Color coded: success (green), error (red), warning (orange), info (blue)
- Auto-dismisses after a timeout; can also be clicked-to-close
- Multiple toasts stack vertically
"""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QToolButton, QWidget,
)


# ---------- Theme ----------

_THEMES = {
    "success": {"bg": "#f0f9eb", "border": "#e1f3d8", "fg": "#67c23a", "text": "#3d7d1f"},
    "error":   {"bg": "#fef0f0", "border": "#fde2e2", "fg": "#f56c6c", "text": "#a02b2b"},
    "warning": {"bg": "#fdf6ec", "border": "#faecd8", "fg": "#e6a23c", "text": "#8a5a10"},
    "info":    {"bg": "#eef4fd", "border": "#dfe9f8", "fg": "#409eff", "text": "#1a5fbf"},
}


def _make_glyph_icon(kind: str, size: int, color: str) -> QIcon:
    """Draw a small filled-circle-with-glyph icon so no external assets are needed."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    # Colored disc
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(0, 0, size, size)

    # White glyph on top
    p.setBrush(Qt.NoBrush)
    from PySide6.QtGui import QPen
    pen = QPen(QColor("#ffffff"))
    pen.setWidthF(max(1.6, size * 0.14))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    m = size * 0.28
    if kind == "success":
        # Check mark
        p.drawLine(int(size * 0.28), int(size * 0.52),
                   int(size * 0.44), int(size * 0.68))
        p.drawLine(int(size * 0.44), int(size * 0.68),
                   int(size * 0.74), int(size * 0.34))
    elif kind == "error":
        p.drawLine(int(m), int(m), int(size - m), int(size - m))
        p.drawLine(int(size - m), int(m), int(m), int(size - m))
    elif kind == "warning":
        # Exclamation
        cx = size / 2
        p.drawLine(int(cx), int(size * 0.24), int(cx), int(size * 0.58))
        p.drawPoint(int(cx), int(size * 0.74))
    else:  # info
        cx = size / 2
        p.drawLine(int(cx), int(size * 0.36), int(cx), int(size * 0.36))
        p.drawLine(int(cx), int(size * 0.46), int(cx), int(size * 0.74))
    p.end()
    return QIcon(pix)


def _make_close_icon(size: int, color: str) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    from PySide6.QtGui import QPen
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    m = size * 0.28
    p.drawLine(int(m), int(m), int(size - m), int(size - m))
    p.drawLine(int(size - m), int(m), int(m), int(size - m))
    p.end()
    return QIcon(pix)


# ---------- Toast widget ----------

class Toast(QFrame):
    """One toast card. Shown by NotificationManager.

    Lifecycle:
        show_animated() -> fade + slide in
        (timer) or manual close -> dismiss() -> fade out -> deleteLater
    """

    dismissed = Signal(object)   # emits self when the widget has been removed

    def __init__(self, parent: QWidget, level: str, message: str,
                 duration_ms: int = 3200, width: int = 340):
        super().__init__(parent)
        theme = _THEMES.get(level, _THEMES["info"])
        self._level = level
        self._closed = False
        self._duration_ms = int(duration_ms)

        self.setObjectName("toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        # We size ourselves rather than relying on layout of parent
        self.setFixedWidth(width)
        self.setMinimumHeight(56)

        # Card style — rounded, subtle shadow via border
        self.setStyleSheet(f"""
            QFrame#toast {{
                background: {theme['bg']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
            }}
            QLabel#toastText {{
                color: {theme['text']};
                font-size: 13px;
                background: transparent;
                border: none;
            }}
            QToolButton#toastClose {{
                background: transparent;
                border: none;
                padding: 2px;
                border-radius: 4px;
            }}
            QToolButton#toastClose:hover {{
                background: rgba(0,0,0,0.06);
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 8, 10)
        row.setSpacing(10)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(20, 20)
        icon = _make_glyph_icon(level, 20, theme["fg"])
        self._icon_label.setPixmap(icon.pixmap(20, 20))
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        row.addWidget(self._icon_label, 0, Qt.AlignTop)

        self._text_label = QLabel(message)
        self._text_label.setObjectName("toastText")
        self._text_label.setWordWrap(True)
        row.addWidget(self._text_label, 1)

        self._btn_close = QToolButton()
        self._btn_close.setObjectName("toastClose")
        self._btn_close.setIcon(_make_close_icon(14, theme["text"]))
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.dismiss)
        row.addWidget(self._btn_close, 0, Qt.AlignTop)

        # Opacity effect for fades
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        # Auto-close timer (armed after show)
        self._auto_close = QTimer(self)
        self._auto_close.setSingleShot(True)
        self._auto_close.timeout.connect(self.dismiss)

    # ----- animations -----
    def show_animated(self, target_pos: QPoint) -> None:
        """Slide + fade in to `target_pos` (in parent-window coords)."""
        # Start slightly above / to the right of the target
        start_pos = QPoint(target_pos.x() + 24, target_pos.y() - 10)
        self.move(start_pos)
        self.show()

        # Fade opacity
        self._fade_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_in.setDuration(220)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)

        # Slide position
        self._slide_in = QPropertyAnimation(self, b"pos", self)
        self._slide_in.setDuration(260)
        self._slide_in.setStartValue(start_pos)
        self._slide_in.setEndValue(target_pos)
        self._slide_in.setEasingCurve(QEasingCurve.OutCubic)

        self._fade_in.start()
        self._slide_in.start()

        if self._duration_ms > 0:
            self._auto_close.start(self._duration_ms)

    def move_animated(self, target_pos: QPoint) -> None:
        """Animate to a new stack position (used when toasts above are removed)."""
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(200)
        anim.setStartValue(self.pos())
        anim.setEndValue(target_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._reposition_anim = anim  # keep ref

    def dismiss(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._auto_close.stop()

        anim = QPropertyAnimation(self._opacity, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(self._opacity.opacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self._on_faded_out)
        anim.start()
        self._fade_out = anim

    def _on_faded_out(self) -> None:
        self.dismissed.emit(self)
        self.deleteLater()

    # Hover pauses the auto-close timer, leaving gives it back.
    def enterEvent(self, e):
        if self._auto_close.isActive():
            self._remaining = self._auto_close.remainingTime()
            self._auto_close.stop()
        super().enterEvent(e)

    def leaveEvent(self, e):
        remaining = getattr(self, "_remaining", 0)
        if not self._closed and remaining > 0:
            self._auto_close.start(remaining)
        super().leaveEvent(e)


# ---------- Manager ----------

class NotificationManager(QObject):
    """Stacks toasts in the top-right corner of a host widget (usually the main window)."""

    TOP_OFFSET = 60      # px below top of parent (leaves space for our custom title bar)
    RIGHT_OFFSET = 20    # px from the right edge
    GAP = 10             # vertical gap between stacked toasts

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._toasts: List[Toast] = []
        # Listen to resize events so toasts reposition
        host.installEventFilter(self)

    # ----- Public API -----
    def notify(self, message: str, level: str = "info",
               duration_ms: int = 3200) -> Toast:
        toast = Toast(self._host, level, message, duration_ms)
        toast.dismissed.connect(self._on_dismissed)
        self._toasts.append(toast)
        self._relayout(animated=False, newest=toast)
        return toast

    def success(self, message: str, duration_ms: int = 3200) -> Toast:
        return self.notify(message, "success", duration_ms)

    def error(self, message: str, duration_ms: int = 5000) -> Toast:
        return self.notify(message, "error", duration_ms)

    def warning(self, message: str, duration_ms: int = 4000) -> Toast:
        return self.notify(message, "warning", duration_ms)

    def info(self, message: str, duration_ms: int = 3200) -> Toast:
        return self.notify(message, "info", duration_ms)

    # ----- internals -----
    def _target_pos(self, index: int, height_before: int) -> QPoint:
        host_w = self._host.width()
        toast_w = self._toasts[index].width()
        x = host_w - toast_w - self.RIGHT_OFFSET
        y = self.TOP_OFFSET + height_before
        return QPoint(x, y)

    def _relayout(self, animated: bool = True, newest: Optional[Toast] = None) -> None:
        heights_before = 0
        for i, t in enumerate(self._toasts):
            target = self._target_pos(i, heights_before)
            heights_before += t.height() + self.GAP
            if t is newest:
                t.show_animated(target)
            elif animated:
                t.move_animated(target)
            else:
                t.move(target)

    def _on_dismissed(self, toast: Toast) -> None:
        try:
            self._toasts.remove(toast)
        except ValueError:
            return
        self._relayout(animated=True)

    def eventFilter(self, obj, event):
        if obj is self._host and event.type() == QEvent.Resize:
            self._relayout(animated=False)
        return super().eventFilter(obj, event)


# ---------- Convenience: attach to a widget & find upward ----------

def install(host: QWidget) -> NotificationManager:
    """Attach a NotificationManager to `host` (typically the main window)."""
    mgr = NotificationManager(host)
    host._notifier = mgr  # type: ignore[attr-defined]
    return mgr


def notifier_of(widget: QWidget) -> Optional[NotificationManager]:
    """Walk up the parent chain to find a widget with `_notifier`."""
    w: Optional[QWidget] = widget
    while w is not None:
        mgr = getattr(w, "_notifier", None)
        if mgr is not None:
            return mgr
        w = w.parentWidget() if hasattr(w, "parentWidget") else None
    return None


# ---------- Sugar API used across pages ----------

def toast(widget: QWidget, message: str, level: str = "info",
          duration_ms: Optional[int] = None) -> None:
    """Show a toast on the widget's toplevel window. Falls back silently if none installed."""
    mgr = notifier_of(widget)
    if mgr is None:
        return
    if duration_ms is None:
        mgr.notify(message, level)
    else:
        mgr.notify(message, level, duration_ms)


def success(widget: QWidget, message: str) -> None:
    toast(widget, message, "success")


def error(widget: QWidget, message: str) -> None:
    toast(widget, message, "error")


def warning(widget: QWidget, message: str) -> None:
    toast(widget, message, "warning")


def info(widget: QWidget, message: str) -> None:
    toast(widget, message, "info")
