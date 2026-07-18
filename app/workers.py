"""Background QThread workers so UI stays responsive."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from PySide6.QtCore import QThread, Signal

from .ai_providers import OpenAIStyleProvider, make_provider
from .db import (
    build_paginated_sql,
    build_count_sql,
    create_db_engine,
    is_select,
    run_non_select,
    run_scalar,
    run_select,
    test_connection,
)


class AIGenerateWorker(QThread):
    """Runs AI SQL generation in the background."""
    finished_ok = Signal(str)  # sql text
    failed = Signal(str)

    def __init__(self, ai_cfg: Dict[str, Any], description: str, dialect: str):
        super().__init__()
        self.ai_cfg = ai_cfg
        self.description = description
        self.dialect = dialect

    def run(self):
        try:
            provider = make_provider(self.ai_cfg)
            sql = provider.generate_sql(self.description, self.dialect)
            self.finished_ok.emit(sql)
        except Exception as e:
            self.failed.emit(str(e))


class AITestWorker(QThread):
    finished_result = Signal(bool, str)

    def __init__(self, ai_cfg: Dict[str, Any]):
        super().__init__()
        self.ai_cfg = ai_cfg

    def run(self):
        try:
            provider = make_provider(self.ai_cfg)
            ok, msg = provider.test_call()
            self.finished_result.emit(ok, msg)
        except Exception as e:
            self.finished_result.emit(False, str(e))


class DBTestWorker(QThread):
    finished_result = Signal(bool, str)

    def __init__(self, ds: Dict[str, Any]):
        super().__init__()
        self.ds = ds

    def run(self):
        ok, msg = test_connection(self.ds)
        self.finished_result.emit(ok, msg)


class SQLExecuteWorker(QThread):
    """Executes a SQL statement (SELECT with pagination, or non-SELECT)."""
    select_ok = Signal(list, list, int)   # cols, rows, total_count
    non_select_ok = Signal(int)           # affected rows
    failed = Signal(str)

    def __init__(self, ds: Dict[str, Any], sql: str, page: int, page_size: int):
        super().__init__()
        self.ds = ds
        self.sql = sql
        self.page = max(1, int(page))
        self.page_size = max(1, int(page_size))

    def run(self):
        try:
            engine = create_db_engine(self.ds)
        except Exception as e:
            self.failed.emit(f"创建数据库连接失败: {e}")
            return

        try:
            if is_select(self.sql):
                # Count total
                try:
                    total = int(run_scalar(engine, build_count_sql(self.sql)) or 0)
                except Exception:
                    total = -1  # some queries don't support wrapping; still show page
                offset = (self.page - 1) * self.page_size
                paged = build_paginated_sql(self.sql, self.ds.get("type", ""), offset, self.page_size)
                cols, rows = run_select(engine, paged)
                self.select_ok.emit(cols, rows, total)
            else:
                affected = run_non_select(engine, self.sql)
                self.non_select_ok.emit(affected)
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            try:
                engine.dispose()
            except Exception:
                pass
