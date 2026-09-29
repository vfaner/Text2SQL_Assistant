"""新版可用提示框：显示最新版本号、更新说明、下载按钮。"""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from . import __version__


def _open_url(url: str) -> None:
    if not QDesktopServices.openUrl(QUrl(url)):
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass


class UpdateAvailableDialog(QDialog):
    """弹给用户看的「发现新版本」对话框。"""

    def __init__(self, latest: str, notes: str, release_url: str, parent=None):
        super().__init__(parent)
        self._release_url = release_url
        self.setWindowTitle(f"发现新版本 v{latest}")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(380)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        # 标题
        title = QLabel(f"🎉 发现新版本 <b>v{latest}</b>")
        title.setStyleSheet("font-size:16px; color:#2c3e50;")
        lay.addWidget(title)

        # 当前版本
        sub = QLabel(f"当前版本：v{__version__}　→　最新版本：v{latest}")
        sub.setStyleSheet("color:#6c7a89; font-size:13px;")
        lay.addWidget(sub)

        # 更新说明（可滚动）
        notes_label = QLabel(notes or "（暂无更新说明）")
        notes_label.setWordWrap(True)
        notes_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        notes_label.setStyleSheet(
            "background:#f8fafc; border:1px solid #e6ebf2; border-radius:8px;"
            " padding:12px; color:#34495e; font-size:13px;"
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(notes_label)
        lay.addWidget(scroll, 1)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        btn_close = QPushButton("稍后再说")
        btn_close.setProperty("flat", True)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        btn_download = QPushButton(f"前往下载 v{latest}")
        btn_download.setMinimumWidth(160)
        btn_download.clicked.connect(self._on_download)
        btn_row.addWidget(btn_download)

        lay.addLayout(btn_row)

    def _on_download(self) -> None:
        _open_url(self._release_url)
        self.accept()
