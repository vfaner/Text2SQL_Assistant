"""AI configuration page - manages multiple AI provider configs."""
from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

from .config import AI_PROVIDERS, ConfigManager
from . import toast
from .workers import AITestWorker


PROVIDER_LABEL_BY_CODE = {code: label for label, code, _, _, _ in AI_PROVIDERS}
PROVIDER_META_BY_CODE = {code: (protocol, url, model) for _label, code, protocol, url, model in AI_PROVIDERS}


class AIConfigPage(QWidget):
    """Manages a list of AI configs with add/edit/delete/test/save (mirrors DataSourcePage)."""

    ai_changed = Signal()

    def __init__(self, cfg: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cfg = cfg
        self._current_name: Optional[str] = None
        self._test_worker: Optional[AITestWorker] = None

        self._build_ui()
        self._refresh_list()

    # ----- UI -----
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("AI 配置")
        title.setProperty("title", True)
        root.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # Left: list
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(QLabel("已配置的 AI 引擎"))

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

        # Set as current
        self.btn_use = QPushButton("设为当前使用")
        self.btn_use.clicked.connect(self._on_use)
        left_l.addWidget(self.btn_use)

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
        self.name_edit.setMinimumWidth(360)
        self.name_edit.setPlaceholderText("给这份配置起个名字，例如 “生产-DeepSeek”")

        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(360)
        for label, code, _protocol, _url, _model in AI_PROVIDERS:
            self.provider_combo.addItem(label, code)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_change)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("OpenAI 兼容协议 (/chat/completions)", "openai")
        self.protocol_combo.addItem("Anthropic 兼容协议 (/messages)", "anthropic")

        self.api_base_edit = QLineEdit()
        self.api_base_edit.setMinimumWidth(560)
        self.api_base_edit.setPlaceholderText("例如 https://dashscope.aliyuncs.com/compatible-mode/v1")

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setMinimumWidth(560)
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请粘贴完整的 API Key（保存时会以 base64 编码存入 config.json）")

        self.model_edit = QLineEdit()
        self.model_edit.setMinimumWidth(560)
        self.model_edit.setPlaceholderText("例如 gpt-4o-mini / qwen-max / deepseek-chat / doubao-1-5-pro-32k-250115 / claude-3-5-sonnet-latest")

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.2)

        form.addRow("配置名称", self.name_edit)
        form.addRow("厂商", self.provider_combo)
        form.addRow("协议", self.protocol_combo)
        form.addRow("API 地址", self.api_base_edit)
        form.addRow("API Key", self.api_key_edit)
        form.addRow("模型名称", self.model_edit)
        form.addRow("Temperature", self.temp_spin)

        right_l.addWidget(form_group)

        # Actions
        actions = QHBoxLayout()
        self.btn_test = QPushButton("测试调用")
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

        tip = QLabel(
            "支持两类协议：\n"
            "  • OpenAI 兼容 /chat/completions：OpenAI / DeepSeek / 阿里百炼 / 千问 / 火山 / 豆包 / 智谱 GLM / Kimi / 百度千帆 / 胜算云 / GitHub Models 等\n"
            "  • Anthropic 兼容 /messages：Anthropic Claude 及兼容网关\n"
            "选择上方“厂商”会自动填充默认 API 地址、协议和模型；也可以选“自定义”手动填写。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#6c7a89; padding:8px 4px;")
        right_l.addWidget(tip)

        right_l.addStretch(1)
        splitter.addWidget(right)
        splitter.setSizes([250, 750])

    # ----- Data flow -----
    def _refresh_list(self) -> None:
        current_used = self.cfg.data.get("current_ai_config", "") or ""
        self.list_widget.clear()
        for cfg in self.cfg.get_ai_configs():
            name = cfg.get("name", "(未命名)")
            provider_label = PROVIDER_LABEL_BY_CODE.get(cfg.get("provider", ""), cfg.get("provider", ""))
            marker = " ✓ 当前" if name == current_used else ""
            item = QListWidgetItem(f"{name}   [{provider_label}]{marker}")
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self) -> None:
        self._current_name = None
        self.name_edit.setText("")
        self.provider_combo.setCurrentIndex(0)
        # Pre-fill from newly chosen provider's defaults
        code = self.provider_combo.currentData()
        for _lbl, c, protocol, url, model in AI_PROVIDERS:
            if c == code:
                self._set_protocol(protocol)
                self.api_base_edit.setText(url)
                self.model_edit.setText(model)
                break
        self.api_key_edit.setText("")
        self.temp_spin.setValue(0.2)

    def _fill_form(self, cfg: Dict[str, Any]) -> None:
        self._current_name = cfg.get("name")
        self.name_edit.setText(cfg.get("name", ""))
        idx = 0
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == cfg.get("provider"):
                idx = i
                break
        self.provider_combo.blockSignals(True)
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)

        # Restore protocol from the saved config; fall back to the vendor's default,
        # and finally to "openai" for legacy configs that didn't record it.
        protocol = cfg.get("protocol") or PROVIDER_META_BY_CODE.get(cfg.get("provider", ""), ("openai",))[0]
        self._set_protocol(protocol)

        self.api_base_edit.setText(cfg.get("api_base", ""))
        self.api_key_edit.setText(cfg.get("api_key", ""))
        self.model_edit.setText(cfg.get("model", ""))
        self.temp_spin.setValue(float(cfg.get("temperature", 0.2) or 0.2))

    def _read_form(self) -> Optional[Dict[str, Any]]:
        name = self.name_edit.text().strip()
        if not name:
            toast.warning(self, "配置名称不能为空")
            return None
        api_base = self.api_base_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        model = self.model_edit.text().strip()
        if not api_base or not api_key or not model:
            toast.warning(self, "API 地址 / API Key / 模型名称 不能为空")
            return None
        return {
            "name": name,
            "provider": self.provider_combo.currentData(),
            "protocol": self.protocol_combo.currentData() or "openai",
            "api_base": api_base,
            "api_key": api_key,
            "model": model,
            "temperature": float(self.temp_spin.value()),
        }

    def _set_protocol(self, protocol: str) -> None:
        target = 0 if (protocol or "openai") == "openai" else 1
        self.protocol_combo.blockSignals(True)
        self.protocol_combo.setCurrentIndex(target)
        self.protocol_combo.blockSignals(False)

    # ----- Events -----
    def _on_select(self, current: QListWidgetItem, _prev: QListWidgetItem) -> None:
        if not current:
            self._clear_form()
            return
        name = current.data(Qt.UserRole)
        cfg = self.cfg.find_ai_config(name)
        if cfg:
            self._fill_form(cfg)

    def _on_provider_change(self, _idx: int) -> None:
        code = self.provider_combo.currentData()
        for _lbl, c, protocol, url, model in AI_PROVIDERS:
            if c == code:
                # Overwrite the protocol / api_base / model whenever the vendor
                # changes - matches the behavior of the DB type dropdown pre-filling defaults.
                self._set_protocol(protocol)
                if url:
                    self.api_base_edit.setText(url)
                if model:
                    self.model_edit.setText(model)
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
        if QMessageBox.question(self, "确认删除", f"确定删除 AI 配置 “{name}”？") != QMessageBox.Yes:
            return
        self.cfg.remove_ai_config(name)
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
        self._refresh_list()
        self.ai_changed.emit()

    def _on_apply(self) -> None:
        cfg = self._read_form()
        if not cfg:
            return
        # If renaming, delete old first
        if self._current_name and self._current_name != cfg["name"]:
            self.cfg.remove_ai_config(self._current_name)
        self.cfg.upsert_ai_config(cfg)
        # If nothing was current, use this one
        if not self.cfg.data.get("current_ai_config"):
            self.cfg.set_current_ai_config(cfg["name"])
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
            return
        self._current_name = cfg["name"]
        self._refresh_list()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.UserRole) == cfg["name"]:
                self.list_widget.setCurrentRow(i)
                break
        self.ai_changed.emit()
        toast.success(self, f"配置 “{cfg['name']}” 已保存")

    def _on_use(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            toast.warning(self, "请先选择一份配置")
            return
        name = item.data(Qt.UserRole)
        self.cfg.set_current_ai_config(name)
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
            return
        self._refresh_list()
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.UserRole) == name:
                self.list_widget.setCurrentRow(i)
                break
        self.ai_changed.emit()
        toast.success(self, f"已切换到 “{name}”")

    def _on_save_all(self) -> None:
        try:
            self.cfg.save()
            toast.success(self, "所有 AI 配置已保存到 config.json")
        except Exception as e:
            toast.error(self, f"保存失败: {e}")

    def _on_test(self) -> None:
        cfg = self._read_form()
        if not cfg:
            return
        self.btn_test.setEnabled(False)
        self.btn_test.setText("测试中…")

        self._test_worker = AITestWorker(cfg)

        def done(ok: bool, msg: str) -> None:
            self.btn_test.setEnabled(True)
            self.btn_test.setText("测试调用")
            if ok:
                toast.success(self, msg)
            else:
                toast.error(self, f"AI 测试失败: {msg}")

        self._test_worker.finished_result.connect(done)
        self._test_worker.start()
