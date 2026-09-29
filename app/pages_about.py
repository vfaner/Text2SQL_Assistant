"""软件说明 / About page — 精简的功能介绍 + 上手步骤 + Star/捐赠 CTA。"""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .donate_dialog import DonateDialog
from .title_bar import GITHUB_REPO_URL


GITEE_REPO_URL = "https://gitee.com/super_rgh/muask"


def _open_url(url: str) -> None:
    if not QDesktopServices.openUrl(QUrl(url)):
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass


class _Card(QFrame):
    """白底圆角卡片，和「关于我们」页保持一致。"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(
            "_Card {"
            "  background:#ffffff;"
            "  border:1px solid #e6ebf2;"
            "  border-radius:10px;"
            "}"
        )


class AboutPage(QWidget):
    """Read-only 软件说明页：功能 / 上手 / 小贴士 / 鼓励。"""

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
        content.setSpacing(14)

        # —— 标题 ——
        title = QLabel("沐问 MuAsk")
        title.setStyleSheet("color:#2c7be5; font-size:22px; font-weight:600;")
        content.addWidget(title)

        subtitle = QLabel(
            "用自然语言描述查询需求 → AI 生成 SQL → 在数据库上执行并展示结果。"
        )
        subtitle.setStyleSheet("color:#6c7a89; font-size:13px;")
        content.addWidget(subtitle)

        # —— 1. 核心功能 ——
        content.addWidget(self._card(
            "✨ 核心功能",
            [
                "<b>真实表结构</b>：自动读取库中表 / 字段 / 注释随问题发给 AI，AI 在你真实的表名里写 SQL，不瞎猜。",
                "<b>多数据库</b>：MySQL / MariaDB / PostgreSQL / Oracle / SQL Server / DB2 / 达梦 / 金仓 / OpenGauss / OceanBase / TiDB 等，<b>驱动全部内置</b>，开箱直连。",
                "<b>多 AI</b>：OpenAI、阿里百炼、火山方舟、豆包、DeepSeek、Kimi、智谱、Ollama 本地等，兼容任意 OpenAI 协议接口。",
                "<b>结果分页</b>：SELECT 表格分页；写操作返回执行状态；失败弹独立错误框附完整报错。",
            ],
        ))

        # —— 2. 快速上手 ——
        content.addWidget(self._card(
            "🚀 三步上手",
            [
                "<b>① AI 配置</b> → 新建 → 选厂商 → 贴 API Key → 测试 → 保存并设为当前。",
                "<b>② 数据源配置</b> → 新建 → 填连接 → 测试连接 → 保存。",
                "<b>③ 沐问页</b> → 选数据源 → 用中文描述需求 → 生成 SQL → 执行。",
            ],
        ))

        # —— 3. 使用小贴士 ——
        content.addWidget(self._card(
            "💡 使用小贴士",
            [
                "生成的 SQL 务必人工核对表名、条件、JOIN 关系再执行。",
                "执行 <b>DROP / TRUNCATE / 大量 DELETE</b> 前请确认所选数据源，工具不阻拦危险操作。",
                "神通 / 崖山 / H2 没有可分发的 Python 驱动，用「其他（自定义）」自行接入。",
                "遇到问题或有好点子，欢迎到「关于我们」页联系我们。",
            ],
        ))

        # —— 4. Star / 捐赠 CTA ——
        cta = self._card(
            "🙌 觉得好用？给作者一个鼓励",
            [
                "如果本工具对你有帮助，欢迎在 GitHub 或 Gitee 上点个 Star ⭐，这是对作者最实在的鼓励。",
            ],
        )
        cta_l = cta.layout()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_star_gh = QPushButton("⭐  GitHub 加 Star")
        self.btn_star_gh.setCursor(Qt.PointingHandCursor)
        self.btn_star_gh.clicked.connect(lambda: _open_url(GITHUB_REPO_URL))
        btn_row.addWidget(self.btn_star_gh)

        self.btn_star_gitee = QPushButton("🌟  Gitee 加 Star")
        self.btn_star_gitee.setProperty("flat", True)
        self.btn_star_gitee.setCursor(Qt.PointingHandCursor)
        self.btn_star_gitee.clicked.connect(lambda: _open_url(GITEE_REPO_URL))
        btn_row.addWidget(self.btn_star_gitee)

        self.btn_donate = QPushButton("💝  赞助作者")
        self.btn_donate.setProperty("flat", True)
        self.btn_donate.setCursor(Qt.PointingHandCursor)
        self.btn_donate.clicked.connect(self._on_donate)
        btn_row.addWidget(self.btn_donate)

        btn_row.addStretch(1)
        cta_l.addSpacing(6)
        cta_l.addLayout(btn_row)

        content.addWidget(cta)
        content.addStretch(1)

        scroll.setWidget(container)

    # ----- 构造工具 -----
    @staticmethod
    def _card(title_text: str, bullets: list[str]) -> _Card:
        card = _Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        title = QLabel(title_text)
        title.setStyleSheet("font-size:15px; font-weight:600; color:#34495e;")
        lay.addWidget(title)

        for b in bullets:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("•")
            dot.setStyleSheet("color:#2c7be5; font-weight:700;")
            dot.setFixedWidth(14)
            row.addWidget(dot)

            body = QLabel(b)
            body.setWordWrap(True)
            body.setTextFormat(Qt.RichText)
            body.setStyleSheet("color:#4a5a6a; font-size:13px;")
            row.addWidget(body, 1)
            lay.addLayout(row)

        return card

    # ----- Actions -----
    def _on_donate(self) -> None:
        DonateDialog(self).exec()
