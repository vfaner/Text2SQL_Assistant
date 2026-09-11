"""
SQLAlchemy dialect registration for the domestic databases.

* ``dm+dmpython`` — 达梦 DM8. On the packaged Windows / Linux builds Dameng's
  official ``dmSQLAlchemy`` dialect (which knows DM's catalog views and
  compatibility modes) is present and used directly. Where only the
  ``dmpython`` driver is available (e.g. a minimal source install), a small
  built-in fallback dialect kicks in: DM speaks an Oracle-compatible SQL
  dialect and exposes ALL_TABLES / ALL_TAB_COLUMNS / ALL_CONSTRAINTS style
  catalog views, so the fallback subclasses SQLAlchemy's Oracle dialect and
  only overrides version detection, schema resolution, connect args and the
  DBAPI import.

* ``kingbase+ksycopg2`` — 人大金仓 KingbaseES, driven by the official
  ``ksycopg2`` wheel (self-contained: bundles libkci). ksycopg2 is a psycopg2
  fork with the same API, so the dialect subclasses the PostgreSQL psycopg2
  dialect and swaps only the imported DBAPI. When ksycopg2 is absent (macOS),
  db.py falls back to a plain ``postgresql+psycopg2`` URL.

The native wheels exist for Windows / Linux only (no macOS builds), so
DBAPIs are imported lazily via SQLAlchemy's dialect registry.
"""
from __future__ import annotations

import re
from importlib.util import find_spec

from sqlalchemy.dialects import registry
from sqlalchemy.dialects.oracle.base import OracleDialect
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2


def _module_present(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except (ImportError, ValueError):
        return False


class DmDialect(OracleDialect):
    """Fallback SQLAlchemy dialect for 达梦 (DM) over the dmpython DBAPI.

    Used only when Dameng's official ``dmSQLAlchemy`` package is not
    installed; the packaged Windows / Linux builds ship the official one.
    """

    name = "dm"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls):
        import dmPython  # type: ignore

        return dmPython

    def create_connect_args(self, url):
        # Connections are established via an explicit ``creator`` (see
        # db.create_db_engine); nothing is parsed out of the URL.
        return ([], {})

    def _get_server_version_info(self, connection):
        # DM8's banner looks like "DM Database Server 64 V8". Report 11.2 on
        # purpose: it keeps the Oracle dialect off 12c-only catalog views such
        # as ALL_TAB_IDENTITY_COLS, which DM does not provide.
        try:
            banner = connection.exec_driver_sql(
                "SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1"
            ).scalar()
            m = re.search(r"V?(\d+)", banner or "")
            if m and int(m.group(1)) < 12:
                return (11, 2)
        except Exception:
            pass
        return (11, 2)

    def _get_default_schema_name(self, connection):
        # Oracle dialect asks the live connection for its username; dmPython
        # doesn't expose that reliably, so take it from the URL we already have.
        user = connection.engine.url.username
        if user:
            return user.upper()
        try:
            return connection.connection.username.upper()
        except Exception:
            return None


class KingbaseDialect(PGDialect_psycopg2):
    """SQLAlchemy dialect for 人大金仓 KingbaseES over the ksycopg2 DBAPI."""

    name = "kingbase"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls):
        import ksycopg2  # type: ignore

        return ksycopg2


def register_dialects() -> None:
    # Prefer Dameng's official, DM-aware dialect when it is installed;
    # otherwise fall back to the Oracle-subclass shim defined here.
    if _module_present("dmSQLAlchemy") and _module_present("dmPython"):
        registry.register("dm.dmpython", "dmSQLAlchemy.dmpython", "DMDialect_dmPython")
    else:
        registry.register("dm.dmpython", "app.db_dialects", "DmDialect")
    registry.register("kingbase.ksycopg2", "app.db_dialects", "KingbaseDialect")
