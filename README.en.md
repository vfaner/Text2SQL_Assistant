# AI Text-to-SQL Assistant

English | [简体中文](./README.md)

A desktop application built with **PySide6** that turns **natural-language questions into SQL**, executes it on your configured database, and shows the result. Supports mainstream RDBMSes and Chinese "信创" (domestic) databases, and works with multiple LLM vendors out of the box.

- Repo: https://github.com/vfaner/Text2SQL_Assistant
- If this project is useful to you, please consider giving it a **Star ⭐**.

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

- **Natural language → SQL**: describe your query in plain language, let the AI generate SQL in the target dialect, edit it if needed, and execute in one click.
- **Multi-database**: MySQL, PostgreSQL, Oracle, SQL Server, OpenGauss, DM (Dameng), KingbaseES, GBase, ShenTong — plus a "custom" option for anything with a SQLAlchemy URL.
- **Multi-vendor AI**: Aliyun Bailian (Qwen), Doubao, DeepSeek, Qwen, OpenAI — or any OpenAI-compatible endpoint.
- **SELECT / DML / DDL**: SELECTs render as a paginated table; INSERT/UPDATE/DELETE/DDL report the affected row count and command status.
- **Persistent config**: data sources and AI settings are stored in `config.json`; passwords and API keys are base64-encoded (not encryption — see caveats below).
- **Modern UI**: custom frameless title bar with GitHub / Donate buttons, Vue element-plus style toast notifications, rounded cards, soft palette.
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
├── assets/                        # Icons, QR codes, screenshots
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
    ├── config.py                  # config.json I/O, DB / AI catalogs
    ├── db.py                      # SQLAlchemy URL builders, pagination, execution
    ├── ai_providers.py            # OpenAI-compatible adapter
    ├── workers.py                 # QThread workers (AI gen, DB test, SQL exec)
    ├── highlighter.py             # SQL syntax highlighter
    ├── styles.py                  # QSS
    ├── toast.py                   # Vue-style toast notifications
    ├── title_bar.py               # Custom title bar (GitHub / Donate / window controls)
    ├── donate_dialog.py           # QR-code donation dialog
    ├── pages_text2sql.py          # Text2SQL page
    ├── pages_data_source.py       # Data source page
    ├── pages_ai.py                # AI config page
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

1. Open **AI 配置 (AI config)**: pick a vendor, fill in API Base / API Key / model → click **测试调用 (Test)** → **保存配置 (Save)**.
2. Open **数据源配置 (Data source config)**: click **新建 (New)**, choose a database type, fill connection info → **测试连接 (Test connection)** → **保存当前 (Save)**.
3. Back to **Text2SQL**:
   - Pick the data source from the toolbar dropdown.
   - Type your question in the "自然语言描述" (Natural-language description) area, e.g. *"Find customers whose sales exceed 1000 and their total order amount"*.
   - Click **生成 SQL (Generate SQL)** — the generated SQL appears in the middle editor and can be edited.
   - Click **执行 SQL (Execute SQL)** — the result appears below; SELECTs are paginated.
4. The in-app **软件说明 (Help)** tab has the full usage guide.

The **Execute SQL** button stays disabled until a data source is selected.

---

## Configuration

`config.json` is auto-loaded from the working directory on startup (see `config.example.json` for a template). Passwords and API keys are stored with a `b64:` prefix — this is obfuscation, **not** real encryption. For production-grade secrets management, swap it out for `cryptography` or your system keyring.

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

```bash
pip install pyinstaller
pyinstaller -F -w -n Text2SQL_Assistant main.py
```

The `-w` flag hides the console window on Windows / macOS.

---

## Known limitations

- Driver availability for Chinese domestic databases (DM / GBase / ShenTong / KingbaseES) varies — the app only builds the URL and surfaces install hints; it does not download drivers for you.
- Pagination wraps user SQL in a `SELECT * FROM (...) __t` subquery, which works for the vast majority of statements but may need manual pagination for very unusual SQL.
- No safety guardrails — `DROP TABLE users;` will drop it. This is by design for dev/test workflows; add role-based access control at the database level for shared environments.

---

## Support the project

If this tool saves you time, consider one of the following — all appreciated 🙌:

- Give the repo a **Star ⭐** on [GitHub](https://github.com/vfaner/Text2SQL_Assistant).
- Click the **捐赠 (Donate)** button in the app's title bar for the Alipay / WeChat / QQ QR codes.

---

## License

Released under the **MIT License**. Copyright © 2025 vfaner. See [LICENSE](./LICENSE) for full text.
