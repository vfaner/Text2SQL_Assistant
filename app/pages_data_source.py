"""Data source configuration page."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from .config import ConfigManager, DB_TYPES
from . import toast
from .workers import DBTestWorker


class DataSourcePage(QWidget):
    """Manages a list of data sources with add/edit/delete/test/save."""

    data_sources_changed = Signal()

    def __init__(self, cfg: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cfg = cfg
        self._current_name: Optional[str] = None
        self._test_worker: Optional[DBTestWorker] = None

        self._build_ui()
        self._refresh_list()

    # ----- UI -----
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("数据源配置")
        title.setProperty("title", True)
        root.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # Left: list
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(QLabel("已配置的数据源"))

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_select)
        left_l.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("新建")
        self.btn_new.setProperty("flat", True)
        self.btn_new.clicked.connect(self._on_new)
        btn_row.addWidget(self.btn_new)

        self.btn_delete = QPushButton("删除")
        self.btn_delete.setProperty("danger", True)
        self.btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(self.btn_delete)
        left_l.addLayout(btn_row)

        splitter.addWidget(left)

        # Right: form
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)

        form_group = QGroupBox("详细配置")
        form = QFormLayout(form_group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setContentsMargins(12, 20, 12, 12)

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        for label, code, _port in DB_TYPES:
            self.type_combo.addItem(label, code)
        self.type_combo.currentIndexChanged.connect(self._on_type_change)

        self.host_edit = QLineEdit("127.0.0.1")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(0, 65535)
        self.port_spin.setValue(3306)

        self.db_edit = QLineEdit()
        self.user_edit = QLineEdit()
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)

        self.params_edit = QPlainTextEdit()
        self.params_edit.setPlaceholderText('可选。JSON 格式，如 {"charset": "utf8mb4", "service_name": "ORCL"}')
        self.params_edit.setFixedHeight(80)

        form.addRow("数据源名称", self.name_edit)
        form.addRow("数据库类型", self.type_combo)
        form.addRow("主机地址", self.host_edit)
        form.addRow("端口", self.port_spin)
        form.addRow("数据库名", self.db_edit)
        form.addRow("用户名", self.user_edit)
        form.addRow("密码", self.pwd_edit)
        form.addRow("连接参数", self.params_edit)

        right_l.addWidget(form_group)

        # Actions
        actions = QHBoxLayout()
        self.btn_test = QPushButton("测试连接")
        self.btn_test.clicked.connect(self._on_test)
        actions.addWidget(self.btn_test)

        self.btn_apply = QPushButton("保存当前")
        self.btn_apply.clicked.connect(self._on_apply)
        actions.addWidget(self.btn_apply)

        actions.addStretch(1)

        self.btn_save_all = QPushButton("保存所有到配置文件")
        self.btn_save_all.setProperty("flat", True)
        self.btn_save_all.clicked.connect(self._on_save_all)
        actions.addWidget(self.btn_save_all)

        right_l.addLayout(actions)
        right_l.addStretch(1)

        splitter.addWidget(right)
        splitter.setSizes([250, 650])

    # ----- Data flow -----
    def _refresh_list(self) -> None:
        self.list_widget.clear()
        for ds in self.cfg.get_data_sources():
            item = QListWidgetItem(f"{ds.get('name', '(未命名)')}   [{ds.get('type', '?')}]")
            item.setData(Qt.UserRole, ds.get("name"))
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self) -> None:
        self._current_name = None
        self.name_edit.setText("")
        self.type_combo.setCurrentIndex(0)
        self.host_edit.setText("127.0.0.1")
        self.port_spin.setValue(3306)
        self.db_edit.setText("")
        self.user_edit.setText("")
        self.pwd_edit.setText("")
        self.params_edit.setPlainText("")

    def _fill_form(self, ds: Dict[str, Any]) -> None:
        self._current_name = ds.get("name")
        self.name_edit.setText(ds.get("name", ""))
        idx = 0
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == ds.get("type"):
                idx = i
                break
        self.type_combo.setCurrentIndex(idx)
        self.host_edit.setText(ds.get("host", ""))
        self.port_spin.setValue(int(ds.get("port") or 0))
        self.db_edit.setText(ds.get("database", ""))
        self.user_edit.setText(ds.get("username", ""))
        self.pwd_edit.setText(ds.get("password", ""))
        params = ds.get("params") or {}
        self.params_edit.setPlainText(json.dumps(params, ensure_ascii=False, indent=2) if params else "")

    def _read_form(self) -> Optional[Dict[str, Any]]:
        name = self.name_edit.text().strip()
        if not name:
            toast.warning(self, "数据源名称不能为空")
            return None
        params_txt = self.params_edit.toPlainText().strip()
        params: Dict[str, Any] = {}
        if params_txt:
            try:
                params = json.loads(params_txt)
                if not isinstance(params, dict):
                    raise ValueError("连接参数必须是 JSON 对象")
            except Exception as e:
                toast.warning(self, f"连接参数不是有效 JSON: {e}")
                return None

        return {
            "name": name,
            "type": self.type_combo.currentData(),
            "host": self.host_edit.text().strip(),
            "port": self.port_spin.value(),
            "database": self.db_edit.text().strip(),
            "username": self.user_edit.text().strip(),
            "password": self.pwd_edit.text(),
            "params": params,
        }

    # ----- Events -----
    def _on_select(self, current: QListWidgetItem, _prev: QListWidgetItem) -> None:
        if not current:
            self._clear_form()
            return
        name = current.data(Qt.UserRole)
        ds = self.cfg.find_data_source(name)
        if ds:
            self._fill_form(ds)

    def _on_type_change(self, _idx: int) -> None:
        code = self.type_combo.currentData()
        for _label, c, port in DB_TYPES:
            if c == code:
                # Only change port if the current one is a known default of some other type
                if self.port_spin.value() in [3306, 5432, 1521, 1433, 5236, 54321, 5258, 2003, 0]:
                    self.port_spin.setValue(port)
                break

    def _on_new(self) -> None:
        self.list_widget.setCurrentItem(None)
        self._clear_form()
        self.name_edit.setFocus()

    def _on_delete(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        # Keep the confirmation modal - deleting is destructive
        if QMessageBox.question(self, "确认删除", f"确定删除数据源 “{name}”?") != QMessageBox.Yes:
            return
        self.cfg.remove_data_source(name)
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
        self._refresh_list()
        self.data_sources_changed.emit()
        toast.success(self, f"已删除数据源 “{name}”")

    def _on_apply(self) -> None:
        ds = self._read_form()
        if not ds:
            return
        # If renaming, delete old first
        if self._current_name and self._current_name != ds["name"]:
            self.cfg.remove_data_source(self._current_name)
        self.cfg.upsert_data_source(ds)
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
            return
        self._current_name = ds["name"]
        self._refresh_list()
        # Reselect the saved one
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.UserRole) == ds["name"]:
                self.list_widget.setCurrentRow(i)
                break
        self.data_sources_changed.emit()
        toast.success(self, f"数据源 “{ds['name']}” 已保存")

    def _on_save_all(self) -> None:
        try:
            self.cfg.save()
            toast.success(self, "所有数据源配置已写入 config.json")
        except Exception as e:
            toast.error(self, f"保存失败: {e}")

    def _on_test(self) -> None:
        ds = self._read_form()
        if not ds:
            return
        self.btn_test.setEnabled(False)
        self.btn_test.setText("测试中…")

        self._test_worker = DBTestWorker(ds)

        def done(ok: bool, msg: str) -> None:
            self.btn_test.setEnabled(True)
            self.btn_test.setText("测试连接")
            if ok:
                toast.success(self, msg or "连接成功")
            else:
                toast.error(self, msg or "连接失败")

        self._test_worker.finished_result.connect(done)
        self._test_worker.start()
