"""软件说明 / About page - usage help + star request + donate."""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .donate_dialog import DonateDialog
from .title_bar import GITHUB_REPO_URL


_HELP_HTML = """
<h2 style="color:#2c7be5; margin-top:0;">AI Text-to-SQL 智能查询工具</h2>
<p style="color:#6c7a89;">
用自然语言描述查询需求 →  由 AI 生成 SQL →  在配置好的数据库上执行并展示结果。
本工具面向开发 / 测试场景，帮助非纯技术人员也能查数据。
</p>

<h3>核心功能</h3>
<ul>
  <li><b>自然语言转 SQL</b>：用中文描述你想查什么，AI 会生成对应方言的 SQL 语句，可手动编辑后再执行。</li>
  <li><b>多数据库支持</b>：MySQL / PostgreSQL / Oracle / SQL Server / OpenGauss / 达梦 / 人大金仓 / 南大通用 / 神通，以及自定义。</li>
  <li><b>多 AI 厂商</b>：阿里百炼（Qwen）/ 豆包 / DeepSeek / 千问 / OpenAI，或任意 OpenAI 兼容接口。</li>
  <li><b>结果分页与执行反馈</b>：SELECT 以表格形式展示并分页；INSERT/UPDATE/DELETE/DDL 返回执行状态。</li>
  <li><b>配置持久化</b>：数据源和 AI 配置保存到 <code>config.json</code>，密码 / API Key 以 base64 编码存储。</li>
</ul>

<h3>快速上手</h3>
<ol>
  <li>切换到 <b>AI 配置</b>，选择厂商 → 填 API 地址 / API Key / 模型 → 点“测试调用”验证 → 点“保存配置”。</li>
  <li>切换到 <b>数据源配置</b>，点“新建” → 填写连接信息 → 点“测试连接”验证 → 点“保存当前”。</li>
  <li>回到 <b>Text2SQL</b> 页：
    <ul>
      <li>在顶部下拉框选中要使用的数据源</li>
      <li>在“自然语言描述”区输入需求（例如：<i>查询销售额大于 1000 的客户名称和订单总额</i>）</li>
      <li>点“生成 SQL” → SQL 出现在中间可编辑区（可自行修改）</li>
      <li>点“执行 SQL” → 结果显示在下方；SELECT 结果可翻页并调整每页行数</li>
    </ul>
  </li>
</ol>

<h3>使用小贴士</h3>
<ul>
  <li>生成的 SQL <b>不完全等于</b>正确 SQL —— AI 猜表名 / 字段时会用常见占位符，务必人工检查后再执行。</li>
  <li>执行 <b>破坏性操作</b>（DROP / TRUNCATE / 大量 DELETE）前，请确认所选数据源。工具本身<b>不会</b>阻拦危险操作。</li>
  <li>信创数据库（达梦 / GBase / 神通）驱动多为非 PyPI 包，需从官方渠道下载后安装；连接失败时会提示需要的包。</li>
  <li>分页对复杂 SQL（含 ORDER BY / GROUP BY / WITH）以子查询方式包裹，绝大多数情况可用。</li>
</ul>

<h3>快捷操作</h3>
<ul>
  <li>标题栏右上：<b>项目地址</b> —— 打开 GitHub 仓库获取最新版本 / 提交 Issue</li>
  <li>标题栏右上：<b>捐赠</b> —— 请作者喝杯咖啡 ☕（支付宝 / 微信 / QQ 收款码）</li>
</ul>
"""


class AboutPage(QWidget):
    """A read-only help page describing what the app does and how to use it."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable content so smaller windows still work
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        root.addWidget(scroll, 1)

        container = QWidget()
        content = QVBoxLayout(container)
        content.setContentsMargins(28, 20, 28, 20)
        content.setSpacing(12)

        # --- Rich text body ---
        body = QLabel(_HELP_HTML)
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        body.setTextInteractionFlags(Qt.TextBrowserInteraction)
        body.setOpenExternalLinks(True)
        body.setStyleSheet("QLabel { color:#2c3e50; font-size:13px; }")
        content.addWidget(body)

        # --- Divider ---
        divider = QLabel()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background:#e0e6ed;")
        content.addWidget(divider)

        # --- CTA row: project URL + star + donate ---
        cta = QWidget()
        cta_l = QVBoxLayout(cta)
        cta_l.setContentsMargins(0, 8, 0, 0)
        cta_l.setSpacing(10)

        title = QLabel("觉得好用？给作者一个鼓励吧 🙌")
        title.setStyleSheet("font-size:15px; font-weight:600; color:#34495e;")
        cta_l.addWidget(title)

        url_label = QLabel(
            f'项目地址：<a href="{GITHUB_REPO_URL}" '
            f'style="color:#2c7be5; text-decoration:none;">{GITHUB_REPO_URL}</a>'
        )
        url_label.setTextFormat(Qt.RichText)
        url_label.setOpenExternalLinks(True)
        url_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        url_label.setStyleSheet("font-size:13px; color:#34495e;")
        cta_l.addWidget(url_label)

        tip = QLabel(
            "如果本工具对你有帮助，欢迎到 GitHub 上 <b>Star ⭐</b> 支持一下 —— "
            "这是对作者最实在的鼓励。<br>"
            "也欢迎通过右上角“捐赠”按钮请作者喝一杯咖啡，让开源持续。"
        )
        tip.setWordWrap(True)
        tip.setTextFormat(Qt.RichText)
        tip.setStyleSheet("color:#6c7a89; font-size:13px;")
        cta_l.addWidget(tip)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_star = QPushButton("⭐  前往 GitHub 加个 Star")
        self.btn_star.setCursor(Qt.PointingHandCursor)
        self.btn_star.clicked.connect(self._on_star)
        btn_row.addWidget(self.btn_star)

        self.btn_donate = QPushButton("💝  赞助作者")
        self.btn_donate.setProperty("flat", True)
        self.btn_donate.setCursor(Qt.PointingHandCursor)
        self.btn_donate.clicked.connect(self._on_donate)
        btn_row.addWidget(self.btn_donate)

        btn_row.addStretch(1)
        cta_l.addLayout(btn_row)

        content.addWidget(cta)
        content.addStretch(1)

        scroll.setWidget(container)

    # ----- Actions -----
    def _on_star(self) -> None:
        # Prefer Qt's opener (handles sandboxed macOS builds better than webbrowser)
        if not QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL)):
            try:
                webbrowser.open(GITHUB_REPO_URL, new=2)
            except Exception:
                pass

    def _on_donate(self) -> None:
        DonateDialog(self).exec()
