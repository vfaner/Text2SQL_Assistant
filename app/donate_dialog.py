"""Donate dialog - shows Alipay / WeChat / QQ QR codes."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _qr_column(parent: QWidget, title: str, filename: str, size: int = 220) -> QWidget:
    col = QWidget(parent)
    v = QVBoxLayout(col)
    v.setContentsMargins(6, 6, 6, 6)
    v.setSpacing(6)

    lbl_title = QLabel(title)
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_title.setStyleSheet("font-weight:600; color:#34495e;")
    v.addWidget(lbl_title)

    lbl_img = QLabel()
    lbl_img.setFixedSize(size, size)
    lbl_img.setAlignment(Qt.AlignCenter)
    lbl_img.setStyleSheet("background:#ffffff; border:1px solid #e0e6ed; border-radius:8px;")

    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        pix = QPixmap(path)
        if not pix.isNull():
            lbl_img.setPixmap(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_img.setText("图片加载失败")
    else:
        lbl_img.setText(f"缺少 {filename}")
    v.addWidget(lbl_img, 0, Qt.AlignCenter)

    return col


class DonateDialog(QDialog):
    """Displays the three donation QR codes in a compact panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("请作者喝杯咖啡 ☕")
        self.setModal(True)
        self.setMinimumWidth(760)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(10)

        head = QLabel("如果这个小工具对你有帮助，欢迎打赏支持，谢谢！")
        head.setAlignment(Qt.AlignCenter)
        head.setStyleSheet("font-size:14px; font-weight:600; color:#2c3e50;")
        root.addWidget(head)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(_qr_column(self, "支付宝", "alipay.png"))
        row.addWidget(_qr_column(self, "微信", "wechat.png"))
        row.addWidget(_qr_column(self, "QQ", "qq.png"))
        root.addLayout(row)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)
