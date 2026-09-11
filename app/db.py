"""
Database connection layer.

Builds SQLAlchemy URLs for each supported DB type and provides helpers to test
connections and execute SQL statements.

The connection URL builders follow common conventions; particular deployments
may require adjustments in the `params` (e.g. driver, charset, service_name).
"""
from __future__ import annotations

import math
import re
from importlib.util import find_spec
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from .db_dialects import register_dialects

# Register dm+dmpython / kingbase+ksycopg2 dialects before any URL is parsed.
register_dialects()


DriverHint = Dict[str, str]

# Every database type offered in the data-source dropdown ships a driver in the
# packaged app, so these hints are normally never shown. They remain as guidance
# for source-code runs on an unsupported platform (the domestic vendors publish
# Windows/Linux wheels only).
DRIVER_HINTS: Dict[str, DriverHint] = {
    "mysql":       {"pkg": "pymysql",    "install": "pip install pymysql"},
    "postgresql":  {"pkg": "psycopg2",   "install": "pip install psycopg2-binary"},
    "oracle":      {"pkg": "oracledb",   "install": "pip install oracledb（纯 Python 瘦模式，无需 Oracle 客户端）"},
    "mssql":       {"pkg": "pymssql",    "install": "pip install pymssql（wheel 已内置 FreeTDS，无需安装 ODBC）"},
    "opengauss":   {"pkg": "psycopg2",   "install": "pip install psycopg2-binary（OpenGauss 兼容 PG 协议）"},
    "dm":          {"pkg": "dmPython",   "install": "Windows/Linux 打包版已内置达梦官方 dmpython（含达梦客户端库）；其他环境请在 Windows/Linux 上 pip install dmpython"},
    "kingbase":    {"pkg": "ksycopg2",   "install": "pip install ksycopg2（人大金仓官方驱动，打包版已内置）或 pip install psycopg2-binary（PG 协议）"},
    "gbase":       {"pkg": "pymysql",    "install": "pip install pymysql（GBase 8a 兼容 MySQL 协议，打包版已内置）"},
    "custom":      {"pkg": "-",          "install": "请在参数中提供 SQLAlchemy 连接字符串 url，并自行安装对应驱动"},
}


def _has_module(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def build_engine_url(ds: Dict[str, Any]) -> str:
    """Build a SQLAlchemy connection URL from a data-source dict."""
    dtype = (ds.get("type") or "").lower()
    host = ds.get("host") or "localhost"
    port = ds.get("port") or 0
    db = ds.get("database") or ""
    user = quote_plus(ds.get("username") or "")
    pwd = quote_plus(ds.get("password") or "")
    params: Dict[str, Any] = ds.get("params") or {}

    # Merge extra params into a query string
    def qs(extra: Dict[str, Any]) -> str:
        merged = {**params, **extra}
        pairs = [(k, v) for k, v in merged.items() if v not in (None, "")]
        if not pairs:
            return ""
        return "?" + "&".join(f"{k}={v}" for k, v in pairs)

    if dtype == "mysql":
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port or 3306}/{db}{qs({'charset': params.get('charset', 'utf8mb4')})}"
    if dtype == "postgresql":
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 5432}/{db}{qs({})}"
    if dtype == "opengauss":
        # OpenGauss is PG protocol compatible; use psycopg2.
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 5432}/{db}{qs({})}"
    if dtype == "kingbase":
        # Prefer Kingbase's own ksycopg2 (bundled in the packaged app); fall
        # back to plain psycopg2 — KingbaseES also speaks the PostgreSQL wire
        # protocol, so either driver connects.
        if _has_module("ksycopg2"):
            return f"kingbase+ksycopg2://{user}:{pwd}@{host}:{port or 54321}/{db}{qs({})}"
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 54321}/{db}{qs({})}"
    if dtype == "oracle":
        # python-oracledb thin mode is pure Python: no Oracle Instant Client
        # needed. database may be a SID or a service name; caller decides.
        service = params.get("service_name")
        if service:
            return f"oracle+oracledb://{user}:{pwd}@{host}:{port or 1521}/?service_name={service}"
        return f"oracle+oracledb://{user}:{pwd}@{host}:{port or 1521}/{db}"
    if dtype == "mssql":
        # pymssql wheels bundle FreeTDS: no unixODBC / msodbcsql system
        # packages, no "ODBC Driver 17" install required.
        extra = {"charset": params.get("charset")}
        if params.get("tds_version"):
            extra["tds_version"] = params["tds_version"]
        return f"mssql+pymssql://{user}:{pwd}@{host}:{port or 1433}/{db}{qs(extra)}"
    if dtype == "dm":
        # DmDialect is registered in app.db_dialects; the actual login goes
        # through the explicit creator in create_db_engine().
        return f"dm+dmpython://{user}:{pwd}@{host}:{port or 5236}/{db}"
    if dtype == "gbase":
        # GBase 8a speaks the MySQL protocol, so PyMySQL connects directly.
        # Users may still override via 'params.url'.
        if params.get("url"):
            return params["url"]
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port or 5258}/{db}"
    if dtype == "shentong":
        raise ValueError(
            "神通（ShenTong）官方仅提供 JDBC / ODBC 驱动，没有可随程序分发的 "
            "Python 驱动，无法开箱直连。请改用「其他（自定义）」数据源，"
            "自行安装驱动并在参数中填写 SQLAlchemy 连接字符串 url。"
        )
    if dtype == "custom":
        if params.get("url"):
            return params["url"]
        raise ValueError("自定义类型必须在 params 中提供 'url'（SQLAlchemy 连接字符串）。")

    raise ValueError(f"不支持的数据库类型: {dtype}")


def create_db_engine(ds: Dict[str, Any]) -> Engine:
    dtype = (ds.get("type") or "").lower()
    url = build_engine_url(ds)
    engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True, "future": True}

    if dtype == "dm" and not _has_module("dmSQLAlchemy"):
        # Dameng's official dmSQLAlchemy dialect parses the URL itself when
        # installed. With only the fallback shim, log in through an explicit
        # creator (its create_connect_args is a no-op). dmPython is imported
        # lazily so merely selecting a DM data source without the
        # Windows/Linux-only wheel never raises at engine-construction time.
        host = ds.get("host") or "localhost"
        port = int(ds.get("port") or 5236)
        username = ds.get("username") or ""
        password = ds.get("password") or ""

        def dm_creator() -> Any:
            import dmPython  # type: ignore

            return dmPython.connect(
                user=username, password=password, server=host, port=port,
            )

        engine_kwargs["creator"] = dm_creator

    return create_engine(url, **engine_kwargs)


def test_connection(ds: Dict[str, Any]) -> Tuple[bool, str]:
    """Try connecting; returns (ok, message)."""
    dtype = (ds.get("type") or "").lower()
    try:
        engine = create_db_engine(ds)
    except ModuleNotFoundError as e:
        hint = DRIVER_HINTS.get(dtype, {})
        return False, f"缺少驱动: {e}\n请安装: {hint.get('install', '')}"
    except ValueError as e:
        # Deliberate, already-user-facing guidance (e.g. ShenTong).
        return False, str(e)
    except Exception as e:
        return False, f"URL 构造失败: {e}"

    try:
        # Oracle (pre-23c) and DM require a FROM clause; DUAL exists on both.
        ping = "SELECT 1 FROM DUAL" if dtype in ("oracle", "dm") else "SELECT 1"
        with engine.connect() as conn:
            conn.execute(text(ping))
        return True, "连接成功！"
    except ModuleNotFoundError as e:
        hint = DRIVER_HINTS.get((ds.get("type") or "").lower(), {})
        return False, f"缺少驱动: {e}\n请安装: {hint.get('install', '')}"
    except Exception as e:
        return False, f"连接失败: {e}"
    finally:
        try:
            engine.dispose()
        except Exception:
            pass


# --- Schema introspection (for schema-aware text-to-SQL) ---

# Hard caps so a database with thousands of tables can't blow the prompt. When
# the schema is larger than this, tables are ranked against the user's question
# and only the most relevant ones are sent (see build_schema_section).
MAX_SCHEMA_TABLES = 200
MAX_SCHEMA_CHARS = 20000


def introspect_schema(engine: Engine) -> List[Dict[str, Any]]:
    """Return a dialect-neutral description of tables/views in the default schema.

    Uses SQLAlchemy's Inspector rather than per-dialect ``information_schema``
    SQL, so MySQL / PostgreSQL / Oracle / SQL Server / the PG-compatible
    domestic databases all go through the same code path. Anything a given
    dialect can't provide (column comments are not introspected on PostgreSQL,
    for instance) simply degrades to empty instead of failing.
    """
    insp = inspect(engine)

    names: List[Tuple[str, str]] = [(n, "table") for n in insp.get_table_names()]
    get_views = getattr(insp, "get_view_names", None)
    if callable(get_views):
        try:
            names += [(n, "view") for n in get_views()]
        except Exception:
            pass

    tables: List[Dict[str, Any]] = []
    for name, kind in names:
        try:
            raw_cols = insp.get_columns(name)
        except Exception:
            raw_cols = []
        columns = [
            {
                "name": c.get("name", ""),
                "type": str(c["type"]) if c.get("type") is not None else "",
                "nullable": c.get("nullable", True),
                # Only some dialects (notably MySQL) report column comments.
                "comment": c.get("comment") or "",
            }
            for c in raw_cols
        ]

        try:
            pk = list(insp.get_pk_constraint(name).get("constrained_columns") or [])
        except Exception:
            pk = []
        try:
            raw_fks = insp.get_foreign_keys(name)
        except Exception:
            raw_fks = []
        fks = [
            {
                "cols": list(fk.get("constrained_columns") or []),
                "ref_table": fk.get("referred_table") or "",
                "ref_cols": list(fk.get("referred_columns") or []),
            }
            for fk in raw_fks
            if fk.get("referred_table")
        ]

        comment = ""
        try:
            comment = (insp.get_table_comment(name) or {}).get("text") or ""
        except Exception:
            pass

        tables.append(
            {"name": name, "kind": kind, "comment": comment, "pk": pk,
             "columns": columns, "fks": fks}
        )
    return tables


def render_table(t: Dict[str, Any]) -> str:
    """Render one table/view as CREATE TABLE-style DDL for the model's context.

    This is LLM context, not something we ever execute, so comments are attached
    as trailing ``--`` lines rather than dialect-specific ``COMMENT ON`` syntax.
    Views are written to look like tables because the model only needs to know
    they can be SELECTed with these columns.
    """
    is_view = t.get("kind") == "view"
    head = f"-- 视图（可直接 SELECT）: {t['name']}" if is_view else f"-- 表: {t['name']}"
    if t.get("comment"):
        head += f"  {t['comment']}"

    pk = set(t.get("pk") or [])
    lines = []
    for c in t.get("columns", []):
        line = f"  {c['name']} {c.get('type') or 'TEXT'}"
        if c.get("nullable") is False:
            line += " NOT NULL"
        if c["name"] in pk:
            line += " PRIMARY KEY"
        if c.get("comment"):
            line += f"  -- {c['comment']}"
        lines.append(line)
    for fk in t.get("fks") or []:
        cols = ", ".join(fk["cols"])
        ref_cols = ", ".join(fk["ref_cols"]) or "id"
        lines.append(
            f"  FOREIGN KEY ({cols}) REFERENCES {fk['ref_table']}({ref_cols})"
        )

    keyword = "VIEW" if is_view else "TABLE"
    return f"{head}\nCREATE {keyword} {t['name']} (\n" + ",\n".join(lines) + "\n);"


_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")
_CJK_RE = re.compile(r"[一-鿿]")


def _tokens(text: str) -> set:
    """Latin/digit words plus CJK character bigrams.

    Chinese has no spaces, so for Chinese table/column comments we compare
    overlapping 2-character sequences — "数学" in the question then matches the
    "数学" bigram in a column comment like "数学成绩".
    """
    low = (text or "").lower()
    toks = set(_TOKEN_RE.findall(low))
    cjk = _CJK_RE.findall(low)
    toks.update(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    return toks


def _table_tokens(t: Dict[str, Any]) -> set:
    parts = [t.get("name", ""), t.get("comment", "")]
    parts += [c["name"] + " " + c.get("comment", "") for c in t.get("columns", [])]
    return _tokens(" ".join(parts))


def _rank_tables(tables: List[Dict[str, Any]], query: str) -> List[float]:
    """Relevance score per table for ``query``.

    Shared tokens are weighted by inverse document frequency across the schema:
    a bigram like "数学" that names one table beats a near-universal one like
    "信息" that happens to appear in several comments.
    """
    q = _tokens(query)
    if not q:
        return [0.0] * len(tables)
    token_sets = [_table_tokens(t) for t in tables]
    doc_freq: Dict[str, int] = {}
    for s in token_sets:
        for tok in s:
            doc_freq[tok] = doc_freq.get(tok, 0) + 1
    n = len(tables)
    scores = []
    for s in token_sets:
        scores.append(
            sum(1.0 + math.log((n + 1) / (doc_freq[tok] + 1)) for tok in q & s)
        )
    return scores


def build_schema_section(
    tables: List[Dict[str, Any]], description: str = "",
    max_chars: int = MAX_SCHEMA_CHARS, max_tables: int = MAX_SCHEMA_TABLES,
) -> Tuple[str, int, int]:
    """Render the schema for the prompt, trimming if it exceeds the budget.

    Returns ``(section, shown, total)``. When every table fits, all are sent.
    Otherwise tables are scored against ``description`` (Latin words + CJK
    bigrams) and the most relevant are kept, with a note about how many were
    omitted.
    """
    all_n = len(tables)
    considered = tables[:max_tables]
    beyond_cap = max(0, all_n - max_tables)
    blocks = [render_table(t) for t in considered]

    if sum(len(b) for b in blocks) <= max_chars:
        chosen = list(range(len(blocks)))
    else:
        scores = _rank_tables(considered, description)
        if any(s > 0 for s in scores):
            order = sorted(range(len(blocks)), key=lambda i: (-scores[i], i))
        else:
            order = list(range(len(blocks)))
        chosen = []
        used = 0
        for i in order:
            extra = len(blocks[i]) + 2
            if used + extra > max_chars and chosen:
                continue
            chosen.append(i)
            used += extra
        chosen.sort()

    body = "\n\n".join(blocks[i] for i in chosen)
    omitted = (len(considered) - len(chosen)) + beyond_cap
    note = ""
    if omitted > 0:
        note = (
            f"\n\n-- 注意：数据库中还有 {omitted} 张表/视图因篇幅未列出，"
            "如确有需要请在问题中点名相关表。"
        )
    return body + note, len(chosen), all_n


def fetch_schema_text(
    ds: Dict[str, Any], description: str = "",
    max_chars: int = MAX_SCHEMA_CHARS, max_tables: int = MAX_SCHEMA_TABLES,
) -> Tuple[str, int, int]:
    """Open the data source, introspect it, and return (section, shown, total).

    Opens and disposes its own engine; callers run this on a worker thread.
    """
    engine = create_db_engine(ds)
    try:
        tables = introspect_schema(engine)
        return build_schema_section(tables, description, max_chars, max_tables)
    finally:
        try:
            engine.dispose()
        except Exception:
            pass


# --- SQL execution ---

_SELECT_RE = re.compile(r"^\s*(SELECT|WITH|SHOW|DESC|DESCRIBE|EXPLAIN)\b", re.IGNORECASE)


def is_select(sql: str) -> bool:
    return bool(_SELECT_RE.match(sql or ""))


# --- SQL pre-check ---


def precheck_sql(sql: str) -> Tuple[bool, str]:
    """Cheap syntactic sanity check on AI-generated SQL.

    Returns (ok, message). This is a fail-fast layer that catches the common
    ways AI output goes wrong (empty output, only comments, unbalanced
    delimiters). It does NOT parse SQL fully — that's the database's job at
    execute time.
    """
    if not sql or not sql.strip():
        return False, "SQL 为空"

    stripped = sql.strip()

    # Comment-only?
    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if lines and all(ln.startswith("--") or ln.startswith("#") for ln in lines):
        return False, "SQL 只包含注释，没有可执行语句"

    # Try to parse with sqlparse - not a full validator, but catches obviously
    # broken input (e.g. AI returned prose).
    try:
        import sqlparse
        parsed = sqlparse.parse(stripped)
        if not parsed or not parsed[0].tokens:
            return False, "SQL 解析为空"
        # Look for at least one recognizable DML/DDL keyword.
        upper = stripped.upper()
        if not re.search(
            r"\b(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|"
            r"TRUNCATE|SHOW|DESC|DESCRIBE|EXPLAIN|GRANT|REVOKE|CALL|MERGE)\b",
            upper,
        ):
            return False, "未检测到 SQL 关键字（SELECT / INSERT / UPDATE / CREATE ...）"
    except Exception:
        # sqlparse is very tolerant, so this really is unusual.
        pass

    # Balanced parentheses & quotes
    if stripped.count("(") != stripped.count(")"):
        return False, "圆括号不匹配"
    # Only count quotes outside comments; simplistic but useful.
    single = stripped.count("'") - stripped.count("\\'")
    if single % 2 != 0:
        return False, "单引号不闭合"

    return True, ""



def _strip_trailing_semi(sql: str) -> str:
    return (sql or "").strip().rstrip(";").strip()


def build_paginated_sql(sql: str, dtype: str, offset: int, limit: int) -> str:
    """Wrap a SELECT with pagination that works across dialects."""
    body = _strip_trailing_semi(sql)
    dtype = (dtype or "").lower()

    if dtype in ("mysql", "postgresql", "opengauss", "kingbase", "gbase"):
        return f"SELECT * FROM ({body}) AS __t LIMIT {limit} OFFSET {offset}"
    if dtype in ("oracle", "mssql"):
        # Standard SQL:2008 syntax - Oracle 12c+ and SQL Server 2012+ support it
        return f"SELECT * FROM ({body}) __t OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
    if dtype in ("dm",):
        return f"SELECT * FROM ({body}) __t LIMIT {limit} OFFSET {offset}"
    if dtype in ("shentong", "custom"):
        # Try the SQL:2008 form
        return f"SELECT * FROM ({body}) __t OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"

    return f"SELECT * FROM ({body}) __t LIMIT {limit} OFFSET {offset}"


def build_count_sql(sql: str) -> str:
    """Build a COUNT(*) that wraps the SELECT."""
    body = _strip_trailing_semi(sql)
    return f"SELECT COUNT(*) AS __cnt FROM ({body}) __t"


def run_select(engine: Engine, sql: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [tuple(r) for r in result.fetchall()]
        return cols, rows


def run_scalar(engine: Engine, sql: str) -> Any:
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def run_non_select(engine: Engine, sql: str) -> int:
    """Execute a non-SELECT statement in a transaction. Returns affected rowcount (-1 if unknown)."""
    with engine.begin() as conn:
        result = conn.execute(text(sql))
        try:
            return int(result.rowcount) if result.rowcount is not None else -1
        except Exception:
            return -1
