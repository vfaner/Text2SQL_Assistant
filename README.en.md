# AI Text-to-SQL Assistant

English | [简体中文](./README.md)

A desktop application built with **PySide6** that turns **natural-language questions into SQL**, executes it on your configured database, and shows the result. Supports mainstream RDBMSes and Chinese "信创" (domestic) databases, and works with multiple LLM vendors out of the box.

- Repo: https://github.com/vfaner/Text2SQL_Assistant
- If this project is useful to you, please consider giving it a **Star ⭐**.

---

## 📦 Grab a pre-built binary (no Python required)

Don't feel like setting up a Python environment? Head over to the **[Releases page](https://github.com/vfaner/Text2SQL_Assistant/releases)** and grab the build for your platform. No Python, no dependencies, no `pip install`. None of the three builds are code-signed, so Windows and macOS both need a one-time manual approval on first launch (once each, never again afterwards) — steps below.

| Platform | Download | How to run |
|----------|----------|------------|
| **Windows x64** | `Text2SQL_Assistant-windows-x86_64.zip` | Unzip → double-click `Text2SQL_Assistant.exe`. SmartScreen blocks it once, see below. |
| **macOS (Apple Silicon)** | `Text2SQL_Assistant-macos-arm64.dmg` | Mount → drag to Applications → double-click. Needs a one-time approval, see below. |
| **Linux x64** | `Text2SQL_Assistant-linux-x86_64.tar.gz` | `tar -xzvf ...tar.gz` → `chmod +x Text2SQL_Assistant && ./Text2SQL_Assistant` |

> 👉 **Latest release**: https://github.com/vfaner/Text2SQL_Assistant/releases/latest
>
> The "run from source" instructions below are only needed if you want to modify the code, contribute, or run on a target we don't yet ship binaries for (e.g. Intel Macs).

### 🪟 First launch on Windows needs a one-time approval

The executable is **not code-signed** (an EV code-signing certificate costs several hundred dollars a year). A zip downloaded through a browser is tagged with the Mark-of-the-Web, the extracted exe inherits that tag, and Microsoft Defender SmartScreen blocks it once:

1. Double-click the exe → **"Windows protected your PC"** appears
2. That dialog only shows a "Don't run" button by default — click **More info** in the lower left
3. A **Run anyway** button appears — click it
4. The app launches. Every launch after this is a plain double-click, with no prompt.

> Alternatively, before unzipping: right-click the zip → Properties → tick **Unblock** at the bottom. The extracted exe then carries no tag and won't be blocked at all.
>
> First launch unpacks roughly 46 MB into a temp directory, so expect a few seconds with no window. That's normal.

### 🍎 First launch on macOS needs a one-time approval

The app is **not notarized by Apple** (notarization requires a $99/year Apple Developer membership), so macOS blocks it the first time. To approve it:

1. Open the DMG and drag `Text2SQL_Assistant.app` into Applications
2. Double-click the app → you'll get *"Apple could not verify…"* → click **Done** (**not** "Move to Trash")
3. Open **System Settings → Privacy & Security**, scroll to the Security section, and click **Open Anyway** next to the app's name
4. A second confirmation dialog appears — click **Open** in it; macOS may ask for Touch ID or your login password
5. The app launches. **Every launch after this one is a plain double-click, with no prompt at all.**

> The dialog in step 2 only offers "Done" and "Move to Trash" — **that is expected**. Any
> unnotarized app behaves this way; the approval lives in System Settings (step 3), not in
> that dialog.

> ⚠️ The widely-cited **right-click → Open** trick was **removed by Apple in macOS 15 (Sequoia)**.
> The System Settings path above is currently the only way to approve an unnotarized app.

If you'd rather do it in one command, strip the quarantine flag and then double-click normally:

```bash
xattr -dr com.apple.quarantine /Applications/Text2SQL_Assistant.app
```

### 🐧 Running on Linux

Linux has no signature gate, but you do need to add the executable bit after unpacking (and most file managers won't let you double-click a bare binary anyway):

```bash
tar -xzvf Text2SQL_Assistant-linux-x86_64.tar.gz
chmod +x Text2SQL_Assistant
./Text2SQL_Assistant
```

If you hit `could not load the Qt platform plugin "xcb"`, your system is missing the X11 libraries Qt needs (Debian / Ubuntu):

```bash
sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 \
  libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libdbus-1-3
```

---

## Screenshots

### Text2SQL – main workspace
![Text2SQL main workspace](assets/text2sql.png)

### Data source configuration
![Data source configuration](assets/db_config.png)

### AI configuration
![AI configuration](assets/ai_config.png)

---

## Features

- **Natural language → SQL**: describe your query in plain language, let the AI generate SQL in the target dialect, **let the app pre-check the output** (empty / prose / unbalanced quotes / missing SQL keyword), edit if needed, execute in one click.
- **Multi-database**: MySQL, PostgreSQL, Oracle, SQL Server, OpenGauss, DM (Dameng), KingbaseES, GBase, ShenTong — plus a "custom" option for any SQLAlchemy URL.
- **Multiple AI configs, switch on the fly**: manage several AI configs like data sources (new / edit / delete / test / mark current), switch the active one from a dropdown on the main page.
- **Two protocols, many vendors**:
  - **OpenAI-compatible `/chat/completions`** — OpenAI, Aliyun Bailian, Qwen, Volcengine ARK, Doubao, DeepSeek, Baidu Qianfan (ERNIE), Zhipu GLM, Kimi (Moonshot), Shengsuanyun, GitHub Copilot / Models, custom.
  - **Anthropic-compatible `/messages`** — Anthropic Claude, Volcengine ARK Anthropic endpoint, custom.
- **Clean error UX**: SQL execution errors surface in a dedicated dialog with a **Close button** and scrollable detail; stale results are cleared automatically; a one-line error summary is shown in the result panel.
- **SELECT / DML / DDL**: SELECTs render as a paginated table; INSERT/UPDATE/DELETE/DDL report the affected row count and command status.
- **Persistent config**: data sources and AI settings are stored in `config.json`; passwords and API keys are base64-encoded (obfuscation, not real encryption); older configs auto-migrate.
- **Modern UI**: custom frameless title bar with GitHub / Donate buttons, Vue element-plus style toast notifications, rounded cards, soft palette, window auto-centers on the current screen.
- **Cross-platform**: runs on Windows 10/11, macOS 12+, and Ubuntu 20.04+.

---

## Project layout

```
Text2SQL_Assistant/
├── main.py                        # Entry point
├── requirements.txt               # Python dependencies
├── config.example.json            # Example configuration
├── README.md                      # Chinese README
├── README.en.md                   # This file
├── LICENSE                        # MIT License
├── Text2SQL_Assistant.spec        # PyInstaller config (.app on macOS, one-file elsewhere)
├── scripts/
│   ├── build_macos.sh             # macOS build + ad-hoc sign + DMG
│   └── make_icons.py              # Generates .icns / .ico from the master art
├── assets/                        # Icons, QR codes, screenshots
│   ├── app_icon.png               # 1024x1024 master icon (also the Qt window icon)
│   ├── app_icon.icns              # macOS bundle icon (generated)
│   ├── app_icon.ico               # Windows executable icon (generated)
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
    ├── paths.py                   # Resource / config path resolution (source vs frozen)
    ├── config.py                  # config.json I/O, DB / AI catalogs
    ├── db.py                      # SQLAlchemy URL builders, pagination, execution, pre-check
    ├── ai_providers.py            # OpenAI + Anthropic dual-protocol adapter
    ├── workers.py                 # QThread workers (AI gen, DB test, SQL exec)
    ├── highlighter.py             # SQL syntax highlighter
    ├── styles.py                  # QSS
    ├── toast.py                   # Vue-style toast notifications
    ├── error_dialog.py            # Scrollable error dialog with Close button
    ├── title_bar.py               # Custom title bar (GitHub / Donate / window controls)
    ├── donate_dialog.py           # QR-code donation dialog
    ├── pages_text2sql.py          # Text2SQL page
    ├── pages_data_source.py       # Data source page
    ├── pages_ai.py                # AI config page (multi-entry management)
    ├── pages_about.py             # Help / About page
    └── main_window.py             # Main window
```

---

## Installation

Requires **Python 3.9+** (developed and tested on Python 3.14).

```bash
pip install -r requirements.txt
```

The Chinese "信创" database drivers (`dmPython`, KingbaseES-specific driver, GBase, ShenTong) are typically not on PyPI. Install them from each vendor's download page. The app will show a friendly error with the exact install hint on connection failure.

---

## Running

```bash
python main.py
```

The window auto-centers on the current screen at startup.

---

## Quick start

1. Open **AI 配置 (AI config)** — you can save multiple entries and switch between them at will:
   - Click **新建 (New)** → pick a vendor (protocol + API base URL + default model auto-fill) → paste API Key → **测试调用 (Test)** → **保存当前 (Save)**.
   - Repeat for as many configs as you want (production vs. staging, different vendors to compare, etc.).
   - Select any entry in the list → **设为当前使用 (Set as current)**, or switch it from the AI dropdown on the Text2SQL page.
2. Open **数据源配置 (Data source config)**: click **新建 (New)**, choose a database type, fill connection info → **测试连接 (Test connection)** → **保存当前 (Save)**.
3. Back to **Text2SQL**:
   - Pick the data source and AI config from the toolbar dropdowns.
   - Type your question in the "自然语言描述" (Natural-language description) area, e.g. *"Find customers whose sales exceed 1000 and their total order amount"*.
   - Click **生成 SQL (Generate SQL)** — the app pre-checks the model's output first; if it passes, SQL appears in the middle editor and can be edited.
   - Click **执行 SQL (Execute SQL)** — the result appears below; SELECTs are paginated.
   - If execution fails, a dedicated error dialog pops up (with a Close button and scrollable detail); the previous result is cleared automatically.
4. The in-app **软件说明 (Help)** tab has the full usage guide.

The **Execute SQL** button stays disabled until a data source is selected.

---

## Supported AI providers

Grouped by wire protocol:

### OpenAI-compatible `/chat/completions`

| Vendor | Default base URL | Default model |
|--------|------------------|---------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Aliyun Bailian (Qwen) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max` |
| Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Volcengine ARK · OpenAI | `https://ark.cn-beijing.volces.com/api/plan/v3` | `ark-code-latest` |
| Doubao | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro-32k` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Baidu Qianfan (ERNIE) | `https://qianfan.baidubce.com/v2` | `ernie-4.0-turbo-8k` |
| Zhipu GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-plus` |
| Kimi (Moonshot) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Shengsuanyun | `https://router.shengsuanyun.com/api/v1` | `deepseek-chat` |
| GitHub Copilot / Models | `https://models.inference.ai.azure.com` | `gpt-4o-mini` |
| OpenAI-compatible (custom) | (user-provided) | (user-provided) |

### Anthropic-compatible `/messages`

| Vendor | Default base URL | Default model |
|--------|------------------|---------------|
| Anthropic Claude | `https://api.anthropic.com/v1` | `claude-3-5-sonnet-latest` |
| Volcengine ARK · Anthropic | `https://ark.cn-beijing.volces.com/api/plan` | `ark-code-latest` |
| Anthropic-compatible (custom) | (user-provided) | (user-provided) |

> Selecting a vendor auto-fills **Protocol**, **Base URL** and **Default model**. You can also manually flip the Protocol dropdown between OpenAI and Anthropic — useful for third-party compatibility gateways (LiteLLM, OpenRouter, etc.) that aren't in the preset list.

---

## Configuration

Where `config.json` lives depends on how you run the app:

| How you run it | `config.json` location |
|----------------|------------------------|
| From source | Project root (see `config.example.json` for a template) |
| macOS build | `~/Library/Application Support/Text2SQL_Assistant/` |
| Windows build | `%APPDATA%\Text2SQL_Assistant\` |
| Linux build | `$XDG_CONFIG_HOME/text2sql-assistant/` (defaults to `~/.config/…`) |

Packaged builds **cannot** keep config next to the executable: writing inside a macOS `.app` invalidates its code signature and the bundle stops launching, and a one-file build's runtime directory is a temp dir that's deleted on exit. That's exactly why older builds lost your settings on every restart — config from the old location is now migrated automatically, so there's nothing to move by hand.

Passwords and API keys are stored with a `b64:` prefix — this is obfuscation, **not** real encryption. For production-grade secrets management, swap it out for `cryptography` or your system keyring.

---

## Sample connection URLs

| Database                | SQLAlchemy URL example                                                       |
|-------------------------|------------------------------------------------------------------------------|
| MySQL                   | `mysql+pymysql://user:pwd@host:3306/db?charset=utf8mb4`                      |
| PostgreSQL / OpenGauss / KingbaseES | `postgresql+psycopg2://user:pwd@host:5432/db`                     |
| Oracle                  | `oracle+cx_oracle://user:pwd@host:1521/?service_name=ORCL`                   |
| SQL Server              | `mssql+pyodbc://user:pwd@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server`  |
| Dameng                  | `dm+dmPython://user:pwd@host:5236/DAMENG`                                    |
| Custom                  | Put `{"url": "your+dialect://..."}` in the data source's connection params.  |

---

## What "Execute SQL" can do

- **SELECT / WITH / SHOW / DESC / EXPLAIN** → paginated table view with total-row count.
- **INSERT / UPDATE / DELETE** → runs inside a transaction, shows affected rows.
- **CREATE / ALTER / DROP / TRUNCATE / GRANT / REVOKE** → DDL executes; rowcount is not meaningful, so you'll see "命令执行成功 (Command executed)".
- **Stored procedure calls** — single `CALL/EXEC` works. Multiple statements chained with `;` are **not** supported: SQLAlchemy `text()` normally sends one statement per call.

---

## Packaging (optional)

Packaging is driven by `Text2SQL_Assistant.spec`, which produces a different artifact per platform. Don't use a bare `pyinstaller -F main.py` — it drops the bundled assets and the macOS bundle structure.

**Windows / Linux** — single-file executable:

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm Text2SQL_Assistant.spec
# → dist/Text2SQL_Assistant[.exe]
```

**macOS** — `.app` bundle wrapped in a DMG; the script also ad-hoc signs it:

```bash
pip install pyinstaller
./scripts/build_macos.sh
# → dist/Text2SQL_Assistant.app
#   dist/Text2SQL_Assistant-macos-arm64.dmg
```

Shipping a `.app` on macOS isn't cosmetic: Gatekeeper offers **no** approval path for an unsigned bare Unix executable — its warning dialog only has "Move to Trash", so users simply cannot run it.

If you have an Apple Developer membership ($99/year), follow the two `TODO(notarize)` comments in `scripts/build_macos.sh` to sign with a real Developer ID and add the `notarytool` / `stapler` steps. Users then get **no prompt at all**.

**Changing the icon**: replace `assets/app_icon.png` (1024x1024, transparent rounded corners), then run `python scripts/make_icons.py` to regenerate the `.icns` and `.ico`. The script shells out to macOS's built-in `sips` / `iconutil`, so it needs no third-party libraries.

---

## Known limitations

- **The prebuilt binaries on Releases only bundle the MySQL and PostgreSQL drivers** (`PyMySQL` / `psycopg2`) — those two work out of the box. SQL Server, Oracle, Dameng and friends need a system-level library or a vendor download that can't be embedded in a single executable, so for those you'll need to run from source and install the driver yourself (see the comments in `requirements.txt`).
- Driver availability for Chinese domestic databases (DM / GBase / ShenTong / KingbaseES) varies — the app only builds the URL and surfaces install hints; it does not download drivers for you.
- Pagination wraps user SQL in a `SELECT * FROM (...) __t` subquery, which works for the vast majority of statements but may need manual pagination for very unusual SQL.
- No safety guardrails — `DROP TABLE users;` will drop it. This is by design for dev/test workflows; add role-based access control at the database level for shared environments.
- The macOS build is not notarized by Apple, so it needs a one-time manual approval on first launch (see above). Notarization requires a $99/year Apple Developer membership.

---

## Support the project

If this tool saves you time, consider one of the following — all appreciated 🙌:

- Give the repo a **Star ⭐** on [GitHub](https://github.com/vfaner/Text2SQL_Assistant).
- Click the **捐赠 (Donate)** button in the app's title bar for the Alipay / WeChat / QQ QR codes.

---

## License

Released under the **MIT License**. Copyright © 2025 vfaner. See [LICENSE](./LICENSE) for full text.
