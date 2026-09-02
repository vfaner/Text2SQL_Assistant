"""Custom title bar with GitHub / donate / minimize / maximize / close icons."""
from __future__ import annotations

import os
import webbrowser
from typing import Optional

from PySide6.QtCore import QByteArray, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from .donate_dialog import DonateDialog
from .paths import resource_path


GITHUB_REPO_URL = "https://github.com/vfaner/Text2SQL_Assistant"

ASSETS_DIR = resource_path("assets")


# -------------- Icon drawing helpers --------------

def _render_svg_icon(svg_path: str, size: int = 20, color: str = "#ffffff") -> QIcon:
    """Load an SVG file, substitute `currentColor` with the given color, render to pixmap."""
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_text = f.read()
    except Exception:
        return QIcon()

    # SVG uses fill="currentColor"; QSvgRenderer doesn't understand that keyword,
    # so replace it with the concrete color we want to draw with.
    svg_text = svg_text.replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    if not renderer.isValid():
        return QIcon()

    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(p)
    p.end()
    return QIcon(pix)


def _make_github_icon(size: int = 20, color: str = "#ffffff") -> QIcon:
    """Real Octicon mark-github logo, loaded from assets/github.svg."""
    icon = _render_svg_icon(os.path.join(ASSETS_DIR, "github.svg"), size=size, color=color)
    if icon.isNull():
        # Fallback (shouldn't happen — the svg is bundled)
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, size, size)
        p.end()
        return QIcon(pix)
    return icon


def _make_donate_icon(size: int = 20, color: str = "#ffffff") -> QIcon:
    """Load the donate icon from assets/donate.png, tinted to `color`.

    The bundled PNG is a single-color glyph on a transparent background;
    we recolor it by painting `color` through its alpha channel so it stays
    legible on the blue title bar.
    """
    path = os.path.join(ASSETS_DIR, "donate.png")
    if os.path.exists(path):
        src = QPixmap(path)
        if not src.isNull():
            scaled = src.scaled(
                size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            tinted = QPixmap(scaled.size())
            tinted.fill(Qt.transparent)
            p = QPainter(tinted)
            p.setRenderHint(QPainter.Antialiasing)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            # Fill target color, then mask by the source's alpha.
            p.fillRect(tinted.rect(), QColor(color))
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawPixmap(0, 0, scaled)
            p.end()
            return QIcon(tinted)

    # Fallback: a simple white circle so the button still shows something.
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.end()
    return QIcon(pix)


def _make_glyph_icon(kind: str, size: int = 14, color: str = "#ffffff") -> QIcon:
    """Draw minimize / maximize / restore / close glyphs."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)

    m = size * 0.22   # margin
    if kind == "min":
        p.drawLine(int(m), int(size - m), int(size - m), int(size - m))
    elif kind == "max":
        p.drawRect(int(m), int(m), int(size - 2 * m), int(size - 2 * m))
    elif kind == "restore":
        # Two overlapping squares
        p.drawRect(int(m + 2), int(m - 1), int(size - 2 * m - 2), int(size - 2 * m - 2))
        p.drawRect(int(m - 1), int(m + 2), int(size - 2 * m - 2), int(size - 2 * m - 2))
    elif kind == "close":
        p.drawLine(int(m), int(m), int(size - m), int(size - m))
        p.drawLine(int(size - m), int(m), int(m), int(size - m))
    p.end()
    return QIcon(pix)


# -------------- Title bar widget --------------

class TitleBar(QWidget):
    """Custom draggable title bar."""

    minimize_requested = Signal()
    maximize_toggle_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent: QWidget, title: str = ""):
        super().__init__(parent)
        self._parent_window = parent
        self._drag_pos: Optional[QPoint] = None
        self.setObjectName("titleBar")
        self.setFixedHeight(42)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._build_ui(title)

    def _build_ui(self, title: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 4, 6, 4)
        row.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("color:#ffffff; font-weight:600; font-size:13px;")
        row.addWidget(self.title_label)

        row.addStretch(1)

        # --- GitHub button (icon + "项目地址" text, both clickable) ---
        self.btn_github = QToolButton()
        self.btn_github.setIcon(_make_github_icon(18))
        self.btn_github.setIconSize(QSize(18, 18))
        # Leading spaces reliably create a visual gap between icon and text on Qt
        self.btn_github.setText("  项目地址")
        self.btn_github.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_github.setToolTip("获取最新版本 (GitHub)")
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.setObjectName("titleIconBtn")
        self.btn_github.clicked.connect(self._on_github)
        row.addWidget(self.btn_github)

        # --- Donate button (icon + "捐赠" text, both clickable) ---
        self.btn_donate = QToolButton()
        self.btn_donate.setIcon(_make_donate_icon(18))
        self.btn_donate.setIconSize(QSize(18, 18))
        self.btn_donate.setText("  捐赠")
        self.btn_donate.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn_donate.setToolTip("赞助作者（打赏二维码）")
        self.btn_donate.setCursor(Qt.PointingHandCursor)
        self.btn_donate.setObjectName("titleIconBtn")
        self.btn_donate.clicked.connect(self._on_donate)
        row.addWidget(self.btn_donate)

        row.addSpacing(6)

        # --- Minimize / Maximize / Close ---
        self.btn_min = QToolButton()
        self.btn_min.setIcon(_make_glyph_icon("min", 14))
        self.btn_min.setIconSize(QSize(14, 14))
        self.btn_min.setToolTip("最小化")
        self.btn_min.setObjectName("titleWinBtn")
        self.btn_min.clicked.connect(self.minimize_requested.emit)
        row.addWidget(self.btn_min)

        self.btn_max = QToolButton()
        self.btn_max.setIcon(_make_glyph_icon("max", 14))
        self.btn_max.setIconSize(QSize(14, 14))
        self.btn_max.setToolTip("最大化 / 还原")
        self.btn_max.setObjectName("titleWinBtn")
        self.btn_max.clicked.connect(self.maximize_toggle_requested.emit)
        row.addWidget(self.btn_max)

        self.btn_close = QToolButton()
        self.btn_close.setIcon(_make_glyph_icon("close", 14))
        self.btn_close.setIconSize(QSize(14, 14))
        self.btn_close.setToolTip("关闭")
        self.btn_close.setObjectName("titleCloseBtn")
        self.btn_close.clicked.connect(self.close_requested.emit)
        row.addWidget(self.btn_close)

    # ----- actions -----
    def _on_github(self) -> None:
        try:
            webbrowser.open(GITHUB_REPO_URL, new=2)
        except Exception:
            pass

    def _on_donate(self) -> None:
        dlg = DonateDialog(self._parent_window)
        dlg.exec()

    # ----- maximize icon state -----
    def set_maximized(self, is_max: bool) -> None:
        self.btn_max.setIcon(_make_glyph_icon("restore" if is_max else "max", 14))

    # ----- drag to move & double-click to maximize -----
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self._parent_window.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_pos is not None and (e.buttons() & Qt.LeftButton):
            if self._parent_window.isMaximized():
                # Restore first so drag feels natural
                self._parent_window.showNormal()
                self.set_maximized(False)
                self._drag_pos = e.globalPosition().toPoint() - self._parent_window.frameGeometry().topLeft()
            self._parent_window.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._drag_pos = None

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self.maximize_toggle_requested.emit()
