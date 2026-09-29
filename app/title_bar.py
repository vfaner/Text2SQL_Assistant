"""Custom title bar with GitHub / donate / minimize / maximize / close icons."""
from __future__ import annotations

import os
import webbrowser
from typing import Optional

from PySide6.QtCore import QByteArray, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from . import __version__
from .donate_dialog import DonateDialog
from .paths import resource_path
from .update_dialog import UpdateAvailableDialog
from .updater import UpdateCheckWorker


GITHUB_REPO_URL = "https://github.com/vfaner/muask"

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
        self._start_update_check()

    # ----- update check -----
    def _start_update_check(self) -> None:
        """Fire the version probe in the background; UI updates when it lands."""
        self._updater = UpdateCheckWorker(self)
        self._updater.update_available.connect(self._on_update_available)
        self._updater.up_to_date.connect(self._on_up_to_date)
        self._updater.check_failed.connect(self._on_check_failed)
        # Defer a tick so the window can finish painting first.
        QTimer.singleShot(600, self._updater.start)

    def _on_update_available(self, latest: str, url: str, notes: str) -> None:
        self._update_url = url
        self._update_latest = latest
        self._update_notes = notes
        self.update_dot.show()
        self._reposition_update_dot()
        self._set_pill_style("orange", "有新版本")
        self.version_pill.setToolTip(f"发现新版本 v{latest}，点击查看更新说明并下载")
        # 弹一次提示，让用户立刻看到（但不要抢焦点）
        QTimer.singleShot(300, self._maybe_show_update_dialog)

    def _on_up_to_date(self, latest: str) -> None:
        self._set_pill_style("green", "已是最新")
        self.version_pill.setToolTip(f"已是最新版本 v{latest}，点击打开项目主页")

    def _on_check_failed(self, _reason: str) -> None:
        self._set_pill_style("gray", f"v{__version__}")
        self.version_pill.setToolTip(
            "检查更新失败（GitHub / Gitee 都无法访问），点击打开项目主页"
        )

    def _maybe_show_update_dialog(self) -> None:
        if self._update_latest:
            dlg = UpdateAvailableDialog(
                self._update_latest, self._update_notes,
                self._update_url or GITHUB_REPO_URL,
                self._parent_window,
            )
            dlg.exec()
            # 用户看完后红点可以消掉，避免一直挂着
            self.update_dot.hide()

    def _on_pill_clicked(self) -> None:
        if self._update_latest:
            self._maybe_show_update_dialog()
        else:
            # 已是最新 / 检查失败 → 打开项目主页
            try:
                webbrowser.open(GITHUB_REPO_URL, new=2)
            except Exception:
                pass

    def _set_pill_style(self, color: str, text: str) -> None:
        """
        color:
          gray   — 请求中 / 网络失败
          green  — 已是最新
          orange — 有新版本

        胶囊样式：透明底、彩色边框 + 同色文字 + 同色 tag 图标（边框、文字、图标同色，中间空）。
        """
        palettes = {
            "gray":   "rgba(255,255,255,0.85)",
            "green":  "#2ea860",
            "orange": "#e8891a",
        }
        fg = palettes[color]
        self._pill_color = color
        self.version_pill.setIcon(_render_svg_icon(os.path.join(ASSETS_DIR, "tag.svg"), size=13, color=fg))
        self.version_pill.setIconSize(QSize(13, 13))
        self.version_pill.setText(f"  {text}")
        self.version_pill.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {fg};
                border: 1.5px solid {fg};
                border-radius: 10px;
                padding: 3px 8px 3px 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QToolButton:hover {{
                background: rgba(255,255,255,0.12);
            }}
        """)

    def _reposition_update_dot(self) -> None:
        if not self.update_dot.isVisible():
            return
        margin = -2
        self.update_dot.move(
            self.version_pill.width() - self.update_dot.width() + margin,
            margin,
        )

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._reposition_update_dot()

    def _build_ui(self, title: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 4, 6, 4)
        row.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("color:#ffffff; font-weight:600; font-size:13px;")
        row.addWidget(self.title_label)

        # Version suffix in the title bar, e.g. "沐问 MuAsk · …  v1.4.0"
        self.version_label = QLabel(f"  v{__version__}")
        self.version_label.setStyleSheet(
            "color:rgba(255,255,255,0.75); font-size:12px; font-weight:400;"
        )
        row.addWidget(self.version_label)

        row.addStretch(1)

        # --- 版本状态胶囊（替代原"项目地址"按钮）---
        # 状态：请求中(灰) / 已是最新(绿) / 有新版本(橙+红点) / 失败(灰)
        self.version_pill = QToolButton()
        self.version_pill.setCursor(Qt.PointingHandCursor)
        self.version_pill.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.version_pill.setToolTip("正在检查更新…")
        self._pill_color = "gray"
        self._set_pill_style("gray", f"v{__version__}")
        self.version_pill.clicked.connect(self._on_pill_clicked)
        row.addWidget(self.version_pill)

        # 红点：作为胶囊的子控件，贴在右上角
        self.update_dot = QLabel(self.version_pill)
        self.update_dot.setFixedSize(10, 10)
        self.update_dot.setStyleSheet(
            "background:#ff4d4f; border:2px solid #ffffff; border-radius:5px;"
        )
        self.update_dot.hide()

        # 状态数据
        self._update_url: Optional[str] = None
        self._update_latest: Optional[str] = None
        self._update_notes: str = ""

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
