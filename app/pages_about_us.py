"""「关于我们」页面：开源团队介绍、联系方式、其他工具推荐。"""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


# —— 其他工具推荐（按钮点击直接在浏览器打开） ——
FRIEND_TOOLS = [
    {
        "name": "捷同 Jync",
        "desc": "数据库实时同步",
        "url": "https://jync.qqmu.com",
        "emoji": "🔄",
    },
    {
        "name": "百目 Jargus",
        "desc": "Jar 代码评审",
        "url": "https://jargus.qqmu.com",
        "emoji": "🔍",
    },
]


def _open_url(url: str) -> None:
    if not QDesktopServices.openUrl(QUrl(url)):
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass


class _Card(QFrame):
    """一张带浅边框、白底、圆角的卡片。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(
            "_Card {"
            "  background:#ffffff;"
            "  border:1px solid #e6ebf2;"
            "  border-radius:10px;"
            "}"
        )


class AboutUsPage(QWidget):
    """自我介绍 + 联系方式 + 推荐其他开源工具。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        root.addWidget(scroll, 1)

        container = QWidget()
        content = QVBoxLayout(container)
        content.setContentsMargins(28, 22, 28, 22)
        content.setSpacing(16)

        # —— 标题 ——
        title = QLabel("关于我们")
        title.setStyleSheet("color:#2c7be5; font-size:22px; font-weight:600;")
        content.addWidget(title)

        # —— 团队介绍卡片 ——
        intro = _Card()
        intro_l = QVBoxLayout(intro)
        intro_l.setContentsMargins(20, 16, 20, 16)
        intro_l.setSpacing(8)

        intro_title = QLabel("👋 我们是一群开源爱好者")
        intro_title.setStyleSheet("font-size:15px; font-weight:600; color:#34495e;")
        intro_l.addWidget(intro_title)

        intro_body = QLabel(
            "我们致力于分享实用、开箱即用的小工具，希望能帮你在日常工作中少写一点重复代码、"
            "少踩一点坑。<br><br>"
            "如果你有好点子、想提需求，或者在使用中遇到软件上的问题，欢迎随时联系我们："
        )
        intro_body.setWordWrap(True)
        intro_body.setStyleSheet("color:#5a6877; font-size:13px; line-height:150%;")
        intro_l.addWidget(intro_body)

        # 联系方式
        contact_row1 = QHBoxLayout()
        contact_row1.setSpacing(20)
        contact_row1.addWidget(self._contact_label("QQ：", "817094 / 2912167928"))
        contact_row1.addStretch(1)
        intro_l.addLayout(contact_row1)

        contact_row2 = QHBoxLayout()
        contact_row2.setSpacing(20)
        contact_row2.addWidget(self._contact_label("微信：", "hua47609"))
        contact_row2.addStretch(1)
        intro_l.addLayout(contact_row2)

        content.addWidget(intro)

        # —— 其他工具推荐卡片 ——
        rec_card = _Card()
        rec_l = QVBoxLayout(rec_card)
        rec_l.setContentsMargins(20, 16, 20, 16)
        rec_l.setSpacing(12)

        rec_title = QLabel("🧰 其他工具推荐")
        rec_title.setStyleSheet("font-size:15px; font-weight:600; color:#34495e;")
        rec_l.addWidget(rec_title)

        rec_sub = QLabel("都是我们团队出品的开源工具，感兴趣可以点进去看看：")
        rec_sub.setWordWrap(True)
        rec_sub.setStyleSheet("color:#6c7a89; font-size:13px;")
        rec_l.addWidget(rec_sub)

        for tool in FRIEND_TOOLS:
            row = QHBoxLayout()
            row.setSpacing(12)

            label = QLabel(f"<b>{tool['emoji']}  {tool['name']}</b>　{tool['desc']}")
            label.setStyleSheet("color:#2c3e50; font-size:13px;")
            row.addWidget(label, 1)

            btn = QPushButton("前往官网 ↗")
            btn.setProperty("flat", True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, url=tool["url"]: _open_url(url))
            row.addWidget(btn)

            rec_l.addLayout(row)

        content.addWidget(rec_card)
        content.addStretch(1)

        scroll.setWidget(container)

    @staticmethod
    def _contact_label(name: str, value: str) -> QLabel:
        lbl = QLabel(f'<span style="color:#6c7a89;">{name}</span>'
                     f'<span style="color:#2c3e50; font-weight:600;">{value}</span>')
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet("font-size:13px;")
        return lbl
