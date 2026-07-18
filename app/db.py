"""
Database connection layer.

Builds SQLAlchemy URLs for each supported DB type and provides helpers to test
connections and execute SQL statements.

The connection URL builders follow common conventions; particular deployments
may require adjustments in the `params` (e.g. driver, charset, service_name).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DriverHint = Dict[str, str]

# Missing-driver hint messages for the user.
DRIVER_HINTS: Dict[str, DriverHint] = {
    "mysql":       {"pkg": "pymysql",         "install": "pip install pymysql"},
    "postgresql":  {"pkg": "psycopg2",        "install": "pip install psycopg2-binary"},
    "oracle":      {"pkg": "cx_Oracle",       "install": "pip install cx_Oracle (需先安装 Oracle Instant Client)"},
    "mssql":       {"pkg": "pyodbc",          "install": "pip install pyodbc (需系统安装 ODBC Driver for SQL Server)"},
    "opengauss":   {"pkg": "psycopg2",        "install": "pip install psycopg2-binary (使用 PG 兼容驱动)"},
    "dm":          {"pkg": "dmPython",        "install": "从达梦官网下载 dmPython 并安装（pip install dmPython 若可获取）"},
    "kingbase":    {"pkg": "psycopg2",        "install": "pip install psycopg2-binary（人大金仓兼容 PG 协议）"},
    "gbase":       {"pkg": "pyodbc / gbase 驱动", "install": "参考南大通用官方文档安装 Python 驱动"},
    "shentong":    {"pkg": "jaydebeapi",      "install": "pip install jaydebeapi 并提供 JDBC 驱动 jar"},
    "custom":      {"pkg": "-",               "install": "请在参数中提供 sqlalchemy url"},
}


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
        if not merged:
            return ""
        return "?" + "&".join(f"{k}={v}" for k, v in merged.items() if v not in (None, ""))

    if dtype == "mysql":
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port or 3306}/{db}{qs({'charset': params.get('charset', 'utf8mb4')})}"
    if dtype == "postgresql":
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 5432}/{db}{qs({})}"
    if dtype == "opengauss":
        # OpenGauss is PG protocol compatible; use psycopg2.
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 5432}/{db}{qs({})}"
    if dtype == "kingbase":
        # KingbaseES is PG-compatible.
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port or 54321}/{db}{qs({})}"
    if dtype == "oracle":
        # database may be SID or service name; caller decides.
        service = params.get("service_name")
        if service:
            return f"oracle+cx_oracle://{user}:{pwd}@{host}:{port or 1521}/?service_name={service}"
        return f"oracle+cx_oracle://{user}:{pwd}@{host}:{port or 1521}/{db}"
    if dtype == "mssql":
        driver = params.get("driver", "ODBC+Driver+17+for+SQL+Server")
        return f"mssql+pyodbc://{user}:{pwd}@{host}:{port or 1433}/{db}?driver={driver}"
    if dtype == "dm":
        # dmPython dialect registered by SQLAlchemy plugin from Dameng
        return f"dm+dmPython://{user}:{pwd}@{host}:{port or 5236}/{db}"
    if dtype == "gbase":
        # Best-effort; users may override via 'params.url'
        if params.get("url"):
            return params["url"]
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port or 5258}/{db}"
    if dtype == "shentong":
        if params.get("url"):
            return params["url"]
        # jdbc via jaydebeapi requires manual dialect; leave user to supply url
        return f"shentong://{user}:{pwd}@{host}:{port}/{db}"
    if dtype == "custom":
        if params.get("url"):
            return params["url"]
        raise ValueError("自定义类型必须在 params 中提供 'url'（SQLAlchemy 连接字符串）。")

    raise ValueError(f"不支持的数据库类型: {dtype}")


def create_db_engine(ds: Dict[str, Any]) -> Engine:
    url = build_engine_url(ds)
    return create_engine(url, pool_pre_ping=True, future=True)


def test_connection(ds: Dict[str, Any]) -> Tuple[bool, str]:
    """Try connecting; returns (ok, message)."""
    try:
        engine = create_db_engine(ds)
    except ModuleNotFoundError as e:
        hint = DRIVER_HINTS.get((ds.get("type") or "").lower(), {})
        return False, f"缺少驱动: {e}\n请安装: {hint.get('install', '')}"
    except Exception as e:
        return False, f"URL 构造失败: {e}"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
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


# --- SQL execution ---

_SELECT_RE = re.compile(r"^\s*(SELECT|WITH|SHOW|DESC|DESCRIBE|EXPLAIN)\b", re.IGNORECASE)


def is_select(sql: str) -> bool:
    return bool(_SELECT_RE.match(sql or ""))


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
