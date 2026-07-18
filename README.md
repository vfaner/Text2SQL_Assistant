# AI Text-to-SQL 智能查询工具

[English](./README.en.md) | 简体中文

一款基于 PySide6 的桌面应用，通过**自然语言描述 → AI 生成 SQL → 在数据库执行并展示结果**。支持主流数据库和信创数据库，兼容多个主流 AI 大模型。

- 项目地址：https://github.com/vfaner/Text2SQL_Assistant
- 如果对你有帮助，欢迎 **Star ⭐**

---

## 界面预览

### Text2SQL 核心页
![Text2SQL 主界面](assets/text2sql.png)

### 数据源配置
![数据源配置](assets/db_config.png)

### AI 配置
![AI 配置](assets/ai_config.png)

---

## 功能亮点

- **Text2SQL**：自然语言输入 → AI 生成 SQL → 手动可编辑 → 一键执行；查询以表格 + 分页展示，非查询显示受影响行数。
- **多数据库支持**：MySQL、PostgreSQL、Oracle、SQL Server、OpenGauss、达梦（DM）、人大金仓（KingbaseES）、南大通用（GBase）、神通（ShenTong），以及自定义。
- **多 AI 厂商**：阿里百炼（Qwen）、豆包（Doubao）、DeepSeek、千问、OpenAI，或自定义（OpenAI 兼容端点）。
- **配置管理**：数据源和 AI 配置持久化到 `config.json`；密码、API Key 使用 base64 编码存储。
- **现代化 UI**：自绘无边框标题栏、右上角 GitHub / 捐赠按钮，Vue element-plus 风格的 Toast 通知，圆角、柔和配色。

---

## 目录结构

```
Text2SQL_Assistant/
├── main.py                        # 应用入口
├── requirements.txt               # 依赖清单
├── config.example.json            # 示例配置
├── README.md                      # 本文件（中文）
├── README.en.md                   # 英文说明
├── LICENSE                        # MIT 协议
├── assets/                        # 图标、二维码、截图
│   ├── github.svg
│   ├── donate.png
│   ├── alipay.png
│   ├── wechat.png
│   ├── qq.png
│   ├── text2sql.png
│   ├── db_config.png
│   └── ai_config.png
└── app/
    ├── __init__.py
    ├── config.py                  # config.json 读写 + DB/AI 列表 + base64 编码
    ├── db.py                      # SQLAlchemy URL 构造 + 各方言分页 + SQL 执行
    ├── ai_providers.py            # AI 适配层（OpenAI 兼容接口）
    ├── workers.py                 # 后台 QThread（AI 生成、DB 测试、SQL 执行）
    ├── highlighter.py             # SQL 语法高亮
    ├── styles.py                  # QSS 样式
    ├── toast.py                   # Vue 风格 Toast 通知
    ├── title_bar.py               # 自定义标题栏（GitHub / 捐赠 / 窗口控制）
    ├── donate_dialog.py           # 打赏二维码弹窗
    ├── pages_text2sql.py          # Text2SQL 页面
    ├── pages_data_source.py       # 数据源配置页面
    ├── pages_ai.py                # AI 配置页面
    ├── pages_about.py             # 软件说明页面
    └── main_window.py             # 主窗口
```

---

## 安装

1. Python 3.9+（本项目开发环境为 Python 3.14）
2. 安装依赖：

```bash
pip install -r requirements.txt
```

信创数据库驱动可能不能直接从 PyPI 安装（如 `dmPython`、部分金仓 / GBase / 神通驱动），需要从各官方渠道下载后手动安装。程序会在连接失败时给出提示。

---

## 运行

```bash
python main.py
```

窗口启动时自动居中于当前屏幕。

---

## 使用步骤

1. 打开 **AI 配置**：选择厂商，填入 API 地址、API Key、模型名称 → 点“测试调用”验证 → 点“保存配置”。
2. 打开 **数据源配置**：点“新建”，选择数据库类型，填写连接信息 → 点“测试连接”验证 → 点“保存当前”。
3. 回到 **Text2SQL**：
   - 顶部选择数据源
   - 在“自然语言描述”中输入需求（例如 “查询销售额大于 1000 的客户名称和订单总额”）
   - 点“生成 SQL” → 中间编辑区出现 SQL，可手动改
   - 点“执行 SQL” → 结果显示在下方；SELECT 结果可分页翻页
4. 详细使用说明也可以在应用内的 **软件说明** 页查看。

“执行 SQL” 按钮在未选择数据源时会置灰。

---

## 配置文件

启动时自动加载工作目录下的 `config.json`（若不存在则使用默认）。示例见 `config.example.json`。密码与 API Key 会以 base64 编码存储（前缀 `b64:`），实用性大于安全性 —— 如需生产强度请自行改用 `cryptography` 加密。

---

## 常见数据库连接字符串示例

- MySQL：`mysql+pymysql://user:pwd@host:3306/db?charset=utf8mb4`
- PostgreSQL / OpenGauss / 人大金仓：`postgresql+psycopg2://user:pwd@host:5432/db`
- Oracle：`oracle+cx_oracle://user:pwd@host:1521/?service_name=ORCL`
- SQL Server：`mssql+pyodbc://user:pwd@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server`
- 达梦：`dm+dmPython://user:pwd@host:5236/DAMENG`
- 自定义：在数据源的“连接参数”中填入 `{"url": "your+dialect://..."}`。

---

## 打包（可选）

```bash
pip install pyinstaller
pyinstaller -F -w -n Text2SQL_Assistant main.py
```

---

## 已知局限

- 达梦、GBase、神通、金仓的官方 Python 驱动分发情况差异较大；本工具仅提供 URL 拼装与提示，不能自动安装驱动。
- 分页对复杂 SQL（含 `ORDER BY / GROUP BY / WITH`）以子查询方式包裹，绝大多数场景可用；极少数极端 SQL 可能需要用户手动加分页。
- 安全性：为便于开发调试，允许所有 SQL 操作。生产环境务必单独做权限控制。
- 多语句一次执行不支持（SQLAlchemy `text()` 底层驱动通常一次只发一条），需要一条一条执行。

---

## 赞助支持

如果这个工具对你有帮助，欢迎在标题栏点击 **捐赠**，通过支付宝 / 微信 / QQ 打赏支持作者继续维护 ☕。

同时也非常欢迎在 [GitHub](https://github.com/vfaner/Text2SQL_Assistant) 上给一个 **Star ⭐** —— 这是对开源作者最实在的鼓励。

---

## 许可证

本项目基于 **MIT License** 开源，版权所有 © 2025 vfaner。详见 [LICENSE](./LICENSE) 文件。
