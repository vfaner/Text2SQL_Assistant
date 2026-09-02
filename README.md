# AI Text-to-SQL 智能查询工具

[English](./README.en.md) | 简体中文

一款基于 PySide6 的桌面应用，通过**自然语言描述 → AI 生成 SQL → 在数据库执行并展示结果**。支持主流数据库和信创数据库，兼容多个主流 AI 大模型。

- 项目地址：https://github.com/vfaner/Text2SQL_Assistant
- 如果对你有帮助，欢迎 **Star ⭐**

---

## 📦 直接下载可执行文件（无需 Python 环境）

不想折腾环境？直接到 **[Releases 页面](https://github.com/vfaner/Text2SQL_Assistant/releases)** 下载对应平台的打包程序，不依赖 Python、不依赖任何库。三个平台的包都**没有代码签名**，所以 Windows 和 macOS 首次运行都要手动放行一次（各一次，之后再无提示），步骤见下。

| 平台 | 下载文件 | 使用方式 |
|------|---------|----------|
| **Windows x64** | `Text2SQL_Assistant-windows-x86_64.zip` | 解压 → 双击 `Text2SQL_Assistant.exe`。首次会被 SmartScreen 拦一次，见下方说明 |
| **macOS (Apple Silicon)** | `Text2SQL_Assistant-macos-arm64.dmg` | 挂载 → 拖到「应用程序」→ 双击。首次需放行一次，见下方说明 |
| **Linux x64** | `Text2SQL_Assistant-linux-x86_64.tar.gz` | `tar -xzvf ...tar.gz` → `chmod +x Text2SQL_Assistant && ./Text2SQL_Assistant` |

> 👉 **最新版本**：https://github.com/vfaner/Text2SQL_Assistant/releases/latest
>
> 只有想改代码、二次开发或跑不同架构（如 Intel Mac）时才需要下面的“从源码运行”步骤。

### 🪟 Windows 首次运行需放行一次

程序**没有代码签名**（EV 代码签名证书一年数千元），从浏览器下载的 zip 会被打上 Mark-of-the-Web 标记，解压出来的 exe 继承该标记，于是 Microsoft Defender SmartScreen 会拦一次：

1. 双击 exe，弹出「**Windows 已保护你的电脑**」
2. 这个弹窗默认只显示「不运行」按钮 —— 点左下角的「**更多信息**」
3. 展开后出现「**仍要运行**」，点它
4. 程序启动，此后双击直接打开，不再提示

> 也可以在解压前右键 zip → 属性 → 勾选底部的「**解除锁定**」，这样解压出来的 exe 不带标记，不会触发拦截。
>
> 首次启动需要把约 46 MB 的内容解包到临时目录，会有几秒钟没有窗口出现，属正常现象。

### 🍎 macOS 首次运行需放行一次

应用**未经 Apple 公证**（公证需要 $99/年的 Apple Developer 会员），所以从网上下载后 macOS 会拦一次。放行步骤：

1. 双击 DMG，把 `Text2SQL_Assistant.app` 拖到「应用程序」
2. 双击应用 → 弹出「Apple 无法验证…是否包含恶意软件」→ 点**完成**（不要点「移到废纸篓」）
3. 打开**系统设置 → 隐私与安全性**，向下滚动到「安全性」，点应用名旁的**仍要打开**
4. 会再弹一个确认框，点里面的**打开**；系统可能要求 Touch ID 或登录密码
5. 应用启动。**之后每次双击都直接打开，不再有任何提示。**

> 第 2 步那个弹窗只有「完成」和「移到废纸篓」两个按钮，**这是正常的** —— 未公证应用必然如此，
> 放行入口在第 3 步的系统设置里，不在这个弹窗上。

> ⚠️ 网上流传的「右键 → 打开」这个老办法**在 macOS 15 (Sequoia) 及更新版本上已被 Apple 移除**，
> 上面的「系统设置」路径是目前唯一的放行入口。

嫌麻烦也可以用一行命令直接清除隔离标记，然后正常双击：

```bash
xattr -dr com.apple.quarantine /Applications/Text2SQL_Assistant.app
```

### 🐧 Linux 运行说明

Linux 没有类似的签名拦截，但 tar 解包后需要手动加执行权限（多数文件管理器也不会让你直接双击一个裸二进制）：

```bash
tar -xzvf Text2SQL_Assistant-linux-x86_64.tar.gz
chmod +x Text2SQL_Assistant
./Text2SQL_Assistant
```

若报 `could not load the Qt platform plugin "xcb"`，说明系统缺 Qt 需要的 X11 库，补上即可（Debian / Ubuntu）：

```bash
sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libdbus-1-3
```

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

- **Text2SQL**：自然语言输入 → AI 生成 SQL → **自动预检**（防止 AI 返回散文 / 括号不匹配等）→ 手动可编辑 → 一键执行；查询以表格 + 分页展示，非查询显示受影响行数。
- **多数据库支持**：MySQL、PostgreSQL、Oracle、SQL Server、OpenGauss、达梦（DM）、人大金仓（KingbaseES）、南大通用（GBase）、神通（ShenTong），以及自定义 SQLAlchemy URL。
- **多 AI 配置 · 一键切换**：像数据源一样可以配置多份 AI（新建 / 编辑 / 删除 / 测试调用 / 设为当前），主界面顶部下拉切换。
- **双协议 · 多厂商**：
  - **OpenAI 兼容 `/chat/completions`**：OpenAI、阿里百炼、千问、火山引擎 ARK、豆包、DeepSeek、百度千帆（ERNIE）、智谱 GLM、Kimi（Moonshot）、胜算云、GitHub Copilot/Models，以及自定义。
  - **Anthropic 兼容 `/messages`**：Anthropic Claude、火山引擎 ARK Anthropic 协议入口，以及自定义。
- **友好错误处理**：SQL 执行失败弹独立错误对话框（可关闭 / 可滚动），旧结果不会残留；错误摘要提取一行显示。
- **配置管理**：数据源和 AI 配置持久化到 `config.json`；密码、API Key 使用 base64 编码存储；老配置自动迁移。
- **现代化 UI**：自绘无边框标题栏、右上角 GitHub / 捐赠按钮，Vue element-plus 风格的 Toast 通知，圆角、柔和配色，启动窗口自动居中。

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
├── Text2SQL_Assistant.spec        # PyInstaller 配置（macOS 出 .app，Win/Linux 出单文件）
├── scripts/
│   ├── build_macos.sh             # macOS 构建 + ad-hoc 签名 + 打 DMG
│   └── make_icons.py              # 由母图生成 .icns / .ico
├── assets/                        # 图标、二维码、截图
│   ├── app_icon.png               # 1024x1024 应用图标母图（也用作 Qt 窗口图标）
│   ├── app_icon.icns              # macOS bundle 图标（由母图生成）
│   ├── app_icon.ico               # Windows 可执行文件图标（由母图生成）
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
    ├── paths.py                   # 资源/配置路径解析（源码 vs 打包、可写用户目录）
    ├── config.py                  # config.json 读写 + DB/AI 列表 + base64 编码
    ├── db.py                      # SQLAlchemy URL 构造 + 各方言分页 + SQL 执行 + 预检
    ├── ai_providers.py            # AI 适配层（OpenAI + Anthropic 双协议）
    ├── workers.py                 # 后台 QThread（AI 生成、DB 测试、SQL 执行）
    ├── highlighter.py             # SQL 语法高亮
    ├── styles.py                  # QSS 样式
    ├── toast.py                   # Vue 风格 Toast 通知
    ├── error_dialog.py            # 错误弹窗（可关闭 / 可滚动）
    ├── title_bar.py               # 自定义标题栏（GitHub / 捐赠 / 窗口控制）
    ├── donate_dialog.py           # 打赏二维码弹窗
    ├── pages_text2sql.py          # Text2SQL 页面
    ├── pages_data_source.py       # 数据源配置页面
    ├── pages_ai.py                # AI 配置页面（多份配置管理）
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

1. 打开 **AI 配置**（可保存多份，随时切换）：
   - 点 **新建** → 选厂商（会自动填协议、API 地址、默认模型）→ 补 API Key → **测试调用** 验证 → **保存当前**
   - 需要多套配置（比如生产 / 测试、不同厂商对比）就重复上一步
   - 在列表中选中某份 → 点 **设为当前使用** 即可切换（也可以在 Text2SQL 页顶部下拉直接切）
2. 打开 **数据源配置**：点 **新建**，选数据库类型，填写连接信息 → **测试连接** → **保存当前**
3. 回到 **Text2SQL**：
   - 顶部选择数据源和要使用的 AI 配置
   - 在“自然语言描述”中输入需求（例如 “查询销售额大于 1000 的客户名称和订单总额”）
   - 点 **生成 SQL** → 系统对返回内容做一次预检 → 通过后填入中间编辑区，可手动改
   - 点 **执行 SQL** → 结果显示在下方；SELECT 支持分页翻页
   - 若 SQL 执行失败，会弹出独立错误弹窗（有关闭按钮，可滚动查看完整报错），旧结果自动清空
4. 详细使用说明也可以在应用内的 **软件说明** 页查看。

“执行 SQL” 按钮在未选择数据源时会置灰。

---

## 支持的 AI 厂商

按接口协议分类：

### OpenAI 兼容 `/chat/completions`

| 厂商 | 默认 Base URL | 默认模型 |
|------|--------------|---------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 阿里百炼（Qwen） | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max` |
| 千问（Qwen） | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 火山引擎 ARK · OpenAI 协议 | `https://ark.cn-beijing.volces.com/api/plan/v3` | `ark-code-latest` |
| 豆包（Doubao） | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro-32k` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 百度千帆（ERNIE） | `https://qianfan.baidubce.com/v2` | `ernie-4.0-turbo-8k` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-plus` |
| Kimi（Moonshot） | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 胜算云 | `https://router.shengsuanyun.com/api/v1` | `deepseek-chat` |
| GitHub Copilot / Models | `https://models.inference.ai.azure.com` | `gpt-4o-mini` |
| 兼容 OpenAI 协议（自定义） | 用户填写 | 用户填写 |

### Anthropic 兼容 `/messages`

| 厂商 | 默认 Base URL | 默认模型 |
|------|--------------|---------|
| Anthropic Claude | `https://api.anthropic.com/v1` | `claude-3-5-sonnet-latest` |
| 火山引擎 ARK · Anthropic 协议 | `https://ark.cn-beijing.volces.com/api/plan` | `ark-code-latest` |
| 兼容 Anthropic 协议（自定义） | 用户填写 | 用户填写 |

> 选择厂商后，**协议**、**Base URL**、**默认模型** 会自动填充；也可以手动在“协议”下拉里在两种协议之间切换，用于对接不在预置列表中的第三方兼容网关（LiteLLM / OpenRouter 等）。

---

## 配置文件

配置文件位置取决于运行方式：

| 运行方式 | `config.json` 位置 |
|---------|-------------------|
| 从源码运行 | 项目根目录（示例见 `config.example.json`） |
| macOS 打包版 | `~/Library/Application Support/Text2SQL_Assistant/` |
| Windows 打包版 | `%APPDATA%\Text2SQL_Assistant\` |
| Linux 打包版 | `$XDG_CONFIG_HOME/text2sql-assistant/`（默认 `~/.config/…`） |

打包版**不能**把配置写在程序目录里：macOS 的 `.app` 一旦被写入就会破坏代码签名导致无法启动，而单文件版的运行目录是临时目录、退出即删。旧版本正是因此每次重启都丢配置 —— 现在会自动把旧配置迁移到上表位置，无需手动搬。

密码与 API Key 以 base64 编码存储（前缀 `b64:`），实用性大于安全性 —— 如需生产强度请自行改用 `cryptography` 加密。

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

打包配置集中在 `Text2SQL_Assistant.spec`，按平台产出不同形态（不要用裸 `pyinstaller -F main.py`，会丢掉 assets 和 macOS 的 bundle 结构）：

**Windows / Linux** —— 单文件可执行：

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm Text2SQL_Assistant.spec
# 产物：dist/Text2SQL_Assistant[.exe]
```

**macOS** —— `.app` bundle + DMG，脚本会顺带做 ad-hoc 签名：

```bash
pip install pyinstaller
./scripts/build_macos.sh
# 产物：dist/Text2SQL_Assistant.app
#       dist/Text2SQL_Assistant-macos-arm64.dmg
```

macOS 必须打成 `.app` 而不是裸可执行文件：Gatekeeper **不给**未签名的裸 Unix 可执行文件任何放行入口，弹窗只有「移到废纸篓」一个选项，用户根本没法运行。

若你有 Apple Developer 会员（$99/年），把 `scripts/build_macos.sh` 里两处 `TODO(notarize)` 按注释改成真实 Developer ID 并加上 `notarytool` / `stapler` 两步，用户即可**零提示**直接双击运行。

**换图标**：只需替换 `assets/app_icon.png`（1024x1024、带透明圆角），然后跑 `python scripts/make_icons.py` 重新生成 `.icns` 和 `.ico`（该脚本依赖 macOS 自带的 `sips` / `iconutil`，无需第三方库）。

---

## 已知局限

- **Releases 里的打包版只内置 MySQL 与 PostgreSQL 驱动**（`PyMySQL` / `psycopg2`），这两类开箱可连。SQL Server、Oracle、达梦等需要系统级库或厂商下载的驱动无法塞进单个可执行文件 —— 要连这些请改用「从源码运行」，按 `requirements.txt` 里的注释装对应驱动。
- 达梦、GBase、神通、金仓的官方 Python 驱动分发情况差异较大；本工具仅提供 URL 拼装与提示，不能自动安装驱动。
- 分页对复杂 SQL（含 `ORDER BY / GROUP BY / WITH`）以子查询方式包裹，绝大多数场景可用；极少数极端 SQL 可能需要用户手动加分页。
- 安全性：为便于开发调试，允许所有 SQL 操作。生产环境务必单独做权限控制。
- 多语句一次执行不支持（SQLAlchemy `text()` 底层驱动通常一次只发一条），需要一条一条执行。
- macOS 版未经 Apple 公证，首次运行需手动放行一次（见上文）。公证需要 $99/年的 Apple Developer 会员。

---

## 赞助支持

如果这个工具对你有帮助，欢迎在标题栏点击 **捐赠**，通过支付宝 / 微信 / QQ 打赏支持作者继续维护 ☕。

同时也非常欢迎在 [GitHub](https://github.com/vfaner/Text2SQL_Assistant) 上给一个 **Star ⭐** —— 这是对开源作者最实在的鼓励。

---

## 许可证

本项目基于 **MIT License** 开源，版权所有 © 2025 vfaner。详见 [LICENSE](./LICENSE) 文件。
