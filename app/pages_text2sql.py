"""Text2SQL core page: natural language -> SQL -> execute -> results."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import sqlparse
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit,
    QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from .config import DB_TYPES, ConfigManager
from .db import precheck_sql
from .error_dialog import show_error
from .highlighter import SQLHighlighter
from . import toast
from .workers import AIGenerateWorker, SQLExecuteWorker


DB_LABEL_BY_CODE = {code: label for label, code, _ in DB_TYPES}


class Text2SQLPage(QWidget):
    status_message = Signal(str)

    def __init__(self, cfg: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cfg = cfg
        self._ai_worker: Optional[AIGenerateWorker] = None
        self._sql_worker: Optional[SQLExecuteWorker] = None

        # Pagination state
        self._current_page = 1
        self._page_size = cfg.get_page_size()
        self._total_rows = 0
        self._last_sql = ""

        self._build_ui()
        self.refresh_data_sources()
        self.refresh_ai_configs()

    # ----- UI -----
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Toolbar row
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("当前数据源:"))
        self.ds_combo = QComboBox()
        self.ds_combo.setMinimumWidth(200)
        self.ds_combo.currentIndexChanged.connect(self._on_ds_change)
        toolbar.addWidget(self.ds_combo)

        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("AI:"))
        self.ai_combo = QComboBox()
        self.ai_combo.setMinimumWidth(180)
        self.ai_combo.currentIndexChanged.connect(self._on_ai_change)
        toolbar.addWidget(self.ai_combo)

        toolbar.addSpacing(20)
        toolbar.addStretch(1)

        self.btn_generate = QPushButton("生成 SQL")
        self.btn_generate.clicked.connect(self._on_generate)
        toolbar.addWidget(self.btn_generate)

        self.btn_execute = QPushButton("执行 SQL")
        self.btn_execute.clicked.connect(self._on_execute)
        toolbar.addWidget(self.btn_execute)

        self.btn_format = QPushButton("格式化")
        self.btn_format.setProperty("flat", True)
        self.btn_format.clicked.connect(self._on_format_sql)
        toolbar.addWidget(self.btn_format)

        root.addLayout(toolbar)

        # Splitter for three regions: NL input | SQL editor | Results
        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter, 1)

        # 1. natural language
        nl_wrap = QWidget()
        nl_l = QVBoxLayout(nl_wrap)
        nl_l.setContentsMargins(0, 0, 0, 0)
        nl_title = QLabel("自然语言描述")
        nl_title.setProperty("title", True)
        nl_l.addWidget(nl_title)
        self.nl_edit = QTextEdit()
        self.nl_edit.setPlaceholderText("请输入查询需求，例如：\n查询销售额大于1000的客户名称和订单总额。")
        nl_l.addWidget(self.nl_edit, 1)
        splitter.addWidget(nl_wrap)

        # 2. SQL editor
        sql_wrap = QWidget()
        sql_l = QVBoxLayout(sql_wrap)
        sql_l.setContentsMargins(0, 0, 0, 0)
        sql_title = QLabel("SQL 语句 (可编辑)")
        sql_title.setProperty("title", True)
        sql_l.addWidget(sql_title)
        self.sql_edit = QPlainTextEdit()
        self.sql_edit.setObjectName("sqlEditor")
        self.sql_edit.setPlaceholderText("生成的 SQL 会显示在此，可手动修改后再执行。")
        self.sql_edit.setFont(QFont("Menlo, Consolas, monospace"))
        self._highlighter = SQLHighlighter(self.sql_edit.document())
        sql_l.addWidget(self.sql_edit, 1)
        splitter.addWidget(sql_wrap)

        # 3. Results
        result_wrap = QWidget()
        result_l = QVBoxLayout(result_wrap)
        result_l.setContentsMargins(0, 0, 0, 0)

        result_header = QHBoxLayout()
        result_title = QLabel("执行结果")
        result_title.setProperty("title", True)
        result_header.addWidget(result_title)
        result_header.addStretch(1)
        result_header.addWidget(QLabel("每页:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(5, 1000)
        self.page_size_spin.setValue(self._page_size)
        self.page_size_spin.valueChanged.connect(self._on_page_size_change)
        result_header.addWidget(self.page_size_spin)

        self.btn_prev = QPushButton("上一页")
        self.btn_prev.setProperty("flat", True)
        self.btn_prev.clicked.connect(self._on_prev_page)
        result_header.addWidget(self.btn_prev)

        self.page_label = QLabel("第 0 / 0 页")
        result_header.addWidget(self.page_label)

        self.btn_next = QPushButton("下一页")
        self.btn_next.setProperty("flat", True)
        self.btn_next.clicked.connect(self._on_next_page)
        result_header.addWidget(self.btn_next)

        result_l.addLayout(result_header)

        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        result_l.addWidget(self.result_table, 1)

        self.result_message = QLabel("")
        self.result_message.setStyleSheet("padding: 6px; color:#34495e;")
        self.result_message.setWordWrap(True)
        result_l.addWidget(self.result_message)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        result_l.addWidget(self.progress)

        splitter.addWidget(result_wrap)
        splitter.setSizes([160, 220, 380])

        self._update_pagination_ui()
        self._update_execute_enabled()

    # ----- Public: hooks from main window -----
    def refresh_data_sources(self) -> None:
        prev_current = self.cfg.get_current_data_source()
        self.ds_combo.blockSignals(True)
        self.ds_combo.clear()
        self.ds_combo.addItem("（未选择数据源）", "")
        for ds in self.cfg.get_data_sources():
            self.ds_combo.addItem(f"{ds['name']}  [{DB_LABEL_BY_CODE.get(ds.get('type',''), ds.get('type',''))}]",
                                  ds["name"])

        # Restore selection
        idx = 0
        for i in range(self.ds_combo.count()):
            if self.ds_combo.itemData(i) == prev_current:
                idx = i
                break
        self.ds_combo.setCurrentIndex(idx)
        self.ds_combo.blockSignals(False)
        self._update_execute_enabled()

    def refresh_page_size(self) -> None:
        self._page_size = self.cfg.get_page_size()
        self.page_size_spin.blockSignals(True)
        self.page_size_spin.setValue(self._page_size)
        self.page_size_spin.blockSignals(False)

    def refresh_ai_configs(self) -> None:
        """Reload the AI-config dropdown from ConfigManager."""
        current = self.cfg.data.get("current_ai_config", "") or ""
        self.ai_combo.blockSignals(True)
        self.ai_combo.clear()
        self.ai_combo.addItem("（未选择 AI）", "")
        for ai in self.cfg.get_ai_configs():
            label = f"{ai.get('name','?')}  [{ai.get('provider','?')}]"
            self.ai_combo.addItem(label, ai["name"])
        idx = 0
        for i in range(self.ai_combo.count()):
            if self.ai_combo.itemData(i) == current:
                idx = i
                break
        self.ai_combo.setCurrentIndex(idx)
        self.ai_combo.blockSignals(False)

    # ----- helpers -----
    def _current_ai_cfg(self) -> Optional[Dict[str, Any]]:
        name = self.ai_combo.currentData()
        if not name:
            return None
        return self.cfg.find_ai_config(name)
    def _current_ds(self) -> Optional[Dict[str, Any]]:
        name = self.ds_combo.currentData()
        if not name:
            return None
        return self.cfg.find_data_source(name)

    def _update_execute_enabled(self) -> None:
        has_ds = self._current_ds() is not None
        self.btn_execute.setEnabled(has_ds)
        if not has_ds:
            self.btn_execute.setToolTip("请先在“数据源配置”中配置并选择数据源")
        else:
            self.btn_execute.setToolTip("")

    def _update_pagination_ui(self) -> None:
        page_size = max(1, self._page_size)
        total = max(0, self._total_rows)
        pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0
        self.page_label.setText(f"第 {self._current_page if pages else 0} / {pages} 页  (共 {total if total >=0 else '?'} 条)")
        self.btn_prev.setEnabled(self._current_page > 1 and total > 0)
        self.btn_next.setEnabled(self._current_page < pages)

    # ----- Events -----
    def _on_ds_change(self, _idx: int) -> None:
        name = self.ds_combo.currentData() or ""
        self.cfg.set_current_data_source(name)
        try:
            self.cfg.save()
        except Exception:
            pass
        self._update_execute_enabled()
        if name:
            self.status_message.emit(f"已切换到数据源: {name}")

    def _on_ai_change(self, _idx: int) -> None:
        name = self.ai_combo.currentData() or ""
        self.cfg.set_current_ai_config(name)
        try:
            self.cfg.save()
        except Exception:
            pass
        if name:
            self.status_message.emit(f"已切换到 AI: {name}")

    def _on_page_size_change(self, val: int) -> None:
        self._page_size = int(val)
        self.cfg.set_page_size(self._page_size)
        try:
            self.cfg.save()
        except Exception:
            pass
        self._current_page = 1
        self._update_pagination_ui()

    def _on_format_sql(self) -> None:
        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            return
        try:
            formatted = sqlparse.format(sql, reindent=True, keyword_case="upper")
            self.sql_edit.setPlainText(formatted)
        except Exception as e:
            toast.error(self, f"格式化失败: {e}")

    def _on_generate(self) -> None:
        desc = self.nl_edit.toPlainText().strip()
        if not desc:
            toast.warning(self, "请先输入自然语言描述")
            return
        ai_cfg = self._current_ai_cfg() or self.cfg.get_current_ai_config()
        if not ai_cfg or not ai_cfg.get("api_key") or not ai_cfg.get("api_base") or not ai_cfg.get("model"):
            toast.warning(self, "请先在“AI 配置”中新建并选中一份可用的配置")
            return

        ds = self._current_ds()
        dialect = DB_LABEL_BY_CODE.get(ds.get("type", ""), "MySQL") if ds else "MySQL"

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("生成中…")
        self.progress.setVisible(True)

        self._ai_worker = AIGenerateWorker(ai_cfg, desc, dialect)

        def ok(sql: str) -> None:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("生成 SQL")
            self.progress.setVisible(False)

            # Pre-check before writing to the editor - catches AI returning prose,
            # unbalanced quotes, or empty output.
            ok_check, reason = precheck_sql(sql)
            if not ok_check:
                show_error(
                    self,
                    summary="AI 生成的 SQL 预检未通过",
                    detail=f"原因：{reason}\n\n模型返回内容：\n{sql[:2000]}",
                    title="预检失败",
                )
                self.status_message.emit(f"AI 生成的 SQL 预检未通过：{reason}")
                return

            self.sql_edit.setPlainText(sql)
            self.status_message.emit("SQL 已生成并通过预检，可执行或编辑")
            toast.success(self, "AI 已生成 SQL（预检通过）")

        def fail(msg: str) -> None:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setText("生成 SQL")
            self.progress.setVisible(False)
            show_error(
                self,
                summary="AI 调用失败",
                detail=msg,
                title="AI 生成失败",
            )
            self.status_message.emit("AI 生成失败")

        self._ai_worker.finished_ok.connect(ok)
        self._ai_worker.failed.connect(fail)
        self._ai_worker.start()

    def _on_execute(self) -> None:
        ds = self._current_ds()
        if not ds:
            toast.warning(self, "请先配置并选择数据源")
            return
        sql = self.sql_edit.toPlainText().strip()
        if not sql:
            toast.warning(self, "SQL 语句不能为空")
            return

        # Only reset pagination if the SQL changed
        if sql != self._last_sql:
            self._current_page = 1
            self._total_rows = 0
        self._last_sql = sql

        self._run_sql(ds, sql, self._current_page, self._page_size)

    def _on_prev_page(self) -> None:
        if self._current_page <= 1:
            return
        ds = self._current_ds()
        if not ds or not self._last_sql:
            return
        self._current_page -= 1
        self._run_sql(ds, self._last_sql, self._current_page, self._page_size)

    def _on_next_page(self) -> None:
        page_size = max(1, self._page_size)
        pages = max(1, (self._total_rows + page_size - 1) // page_size) if self._total_rows > 0 else 1
        if self._current_page >= pages:
            return
        ds = self._current_ds()
        if not ds or not self._last_sql:
            return
        self._current_page += 1
        self._run_sql(ds, self._last_sql, self._current_page, self._page_size)

    # ----- SQL execution -----
    def _run_sql(self, ds: Dict[str, Any], sql: str, page: int, page_size: int) -> None:
        self.btn_execute.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self.progress.setVisible(True)
        # Clear any stale content so the previous result never lingers
        # underneath an error message.
        self._clear_result_view("正在执行…")

        self._sql_worker = SQLExecuteWorker(ds, sql, page, page_size)

        def sel_ok(cols: List[str], rows: List[Any], total: int) -> None:
            self._finish_exec()
            self._total_rows = total if isinstance(total, int) else 0
            self._show_table(cols, rows)
            self._update_pagination_ui()
            msg = f"查询成功，本页 {len(rows)} 条"
            if total >= 0:
                msg += f"，共 {total} 条"
            self.result_message.setText(msg)
            self.status_message.emit(msg)
            toast.success(self, msg)

        def ns_ok(affected: int) -> None:
            self._finish_exec()
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self._total_rows = 0
            self._update_pagination_ui()
            if affected >= 0:
                msg = f"命令执行成功，受影响行数: {affected}"
            else:
                msg = "命令执行成功"
            self.result_message.setText(msg)
            self.status_message.emit(msg)
            toast.success(self, msg)

        def fail(msg: str) -> None:
            self._finish_exec()
            # Wipe the result view so nothing from a previous successful run
            # is left behind under the failure state.
            self._clear_result_view("")
            # Show a proper dialog with a Close button and scrollable detail.
            summary = self._short_error(msg)
            show_error(self, summary=summary, detail=msg, title="SQL 执行失败")
            self.result_message.setText(f"执行失败：{summary}")
            self.status_message.emit("SQL 执行失败")

        self._sql_worker.select_ok.connect(sel_ok)
        self._sql_worker.non_select_ok.connect(ns_ok)
        self._sql_worker.failed.connect(fail)
        self._sql_worker.start()

    def _clear_result_view(self, message: str) -> None:
        """Drop the table's contents and reset pagination state."""
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self._total_rows = 0
        self._update_pagination_ui()
        self.result_message.setText(message)

    @staticmethod
    def _short_error(msg: str) -> str:
        """Extract a concise one-liner from a long SQLAlchemy traceback-style message."""
        if not msg:
            return "未知错误"
        # SQLAlchemy typically formats as "(engine.error.SomeError) driver-message\n[SQL: ...]"
        # We want just the driver message.
        text = msg.strip()
        # Trim after [SQL: or [parameters:
        for marker in ("\n[SQL:", "\n[parameters:", " [SQL:", " [parameters:"):
            i = text.find(marker)
            if i >= 0:
                text = text[:i]
        # Take the first line
        first_line = text.splitlines()[0].strip()
        # Drop leading "(some.Error)" prefix if present
        if first_line.startswith("(") and ")" in first_line:
            close = first_line.find(")")
            first_line = first_line[close + 1:].strip()
        # Cap length
        if len(first_line) > 180:
            first_line = first_line[:180] + "…"
        return first_line or "未知错误"

    def _finish_exec(self) -> None:
        self.btn_execute.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.progress.setVisible(False)
        self._update_execute_enabled()

    def _show_table(self, cols: List[str], rows: List[Any]) -> None:
        self.result_table.clear()
        self.result_table.setColumnCount(len(cols))
        self.result_table.setRowCount(len(rows))
        self.result_table.setHorizontalHeaderLabels(cols)

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem("" if val is None else str(val))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(r, c, item)

        self.result_table.resizeColumnsToContents()
        # Cap very wide cols
        for c in range(self.result_table.columnCount()):
            w = self.result_table.columnWidth(c)
            if w > 320:
                self.result_table.setColumnWidth(c, 320)
