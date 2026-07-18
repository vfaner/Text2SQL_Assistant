"""AI configuration page."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .config import AI_PROVIDERS, ConfigManager
from . import toast
from .workers import AITestWorker


class AIConfigPage(QWidget):
    ai_changed = Signal()

    def __init__(self, cfg: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cfg = cfg
        self._test_worker: Optional[AITestWorker] = None
        self._build_ui()
        self._load_current()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("AI 配置")
        title.setProperty("title", True)
        root.addWidget(title)

        group = QGroupBox("AI 引擎")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setContentsMargins(12, 20, 12, 12)

        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(360)
        for label, code, _url, _model in AI_PROVIDERS:
            self.provider_combo.addItem(label, code)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_change)

        self.api_base_edit = QLineEdit()
        self.api_base_edit.setMinimumWidth(560)
        self.api_base_edit.setPlaceholderText("例如 https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setMinimumWidth(560)
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请粘贴完整的 API Key（保存时会以 base64 编码存入 config.json）")
        self.model_edit = QLineEdit()
        self.model_edit.setMinimumWidth(560)
        self.model_edit.setPlaceholderText("例如 gpt-4o-mini / qwen-max / deepseek-chat")

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.2)

        form.addRow("厂商", self.provider_combo)
        form.addRow("API 地址", self.api_base_edit)
        form.addRow("API Key", self.api_key_edit)
        form.addRow("模型名称", self.model_edit)
        form.addRow("Temperature", self.temp_spin)

        root.addWidget(group)

        actions = QHBoxLayout()
        self.btn_test = QPushButton("测试调用")
        self.btn_test.clicked.connect(self._on_test)
        actions.addWidget(self.btn_test)

        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self._on_save)
        actions.addWidget(self.btn_save)
        actions.addStretch(1)
        root.addLayout(actions)

        tip = QLabel(
            "提示：以上厂商均使用 OpenAI 兼容 /chat/completions 接口。\n"
            "阿里百炼 / 千问：使用 DashScope 的 compatible-mode/v1 端点。\n"
            "豆包（火山方舟）：需要 ARK API Key，接口路径为 /api/v3/chat/completions。\n"
            "DeepSeek：https://api.deepseek.com/v1/chat/completions。\n"
            "自定义厂商可手动填写 API 地址。"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#6c7a89; padding:8px 4px;")
        root.addWidget(tip)

        root.addStretch(1)

    # ----- data flow -----
    def _load_current(self) -> None:
        cfg = self.cfg.get_ai_config()
        code = cfg.get("provider", "openai")
        idx = 0
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == code:
                idx = i
                break
        self.provider_combo.blockSignals(True)
        self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)

        self.api_base_edit.setText(cfg.get("api_base", ""))
        self.api_key_edit.setText(cfg.get("api_key", ""))
        self.model_edit.setText(cfg.get("model", ""))
        self.temp_spin.setValue(float(cfg.get("temperature", 0.2) or 0.2))

    def _on_provider_change(self, _idx: int) -> None:
        code = self.provider_combo.currentData()
        for _lbl, c, url, model in AI_PROVIDERS:
            if c == code:
                # Only overwrite if fields look default-empty
                if not self.api_base_edit.text().strip():
                    self.api_base_edit.setText(url)
                else:
                    # Detect if user just switched to a different vendor - offer replace
                    self.api_base_edit.setText(url or self.api_base_edit.text())
                if not self.model_edit.text().strip():
                    self.model_edit.setText(model)
                else:
                    self.model_edit.setText(model or self.model_edit.text())
                break

    def _read_form(self) -> dict:
        return {
            "provider": self.provider_combo.currentData(),
            "api_base": self.api_base_edit.text().strip(),
            "api_key": self.api_key_edit.text().strip(),
            "model": self.model_edit.text().strip(),
            "temperature": float(self.temp_spin.value()),
        }

    # ----- events -----
    def _on_save(self) -> None:
        cfg = self._read_form()
        if not cfg["api_base"] or not cfg["api_key"] or not cfg["model"]:
            toast.warning(self, "API 地址 / API Key / 模型名称 不能为空")
            return
        self.cfg.set_ai_config(cfg)
        try:
            self.cfg.save()
        except Exception as e:
            toast.error(self, f"保存失败: {e}")
            return
        self.ai_changed.emit()
        toast.success(self, "AI 配置已保存")

    def _on_test(self) -> None:
        cfg = self._read_form()
        if not cfg["api_base"] or not cfg["api_key"] or not cfg["model"]:
            toast.warning(self, "API 地址 / API Key / 模型名称 不能为空")
            return
        self.btn_test.setEnabled(False)
        self.btn_test.setText("测试中…")

        self._test_worker = AITestWorker(cfg)

        def done(ok: bool, msg: str) -> None:
            self.btn_test.setEnabled(True)
            self.btn_test.setText("测试调用")
            if ok:
                toast.success(self, msg or "AI 测试成功")
            else:
                toast.error(self, msg or "AI 测试失败")

        self._test_worker.finished_result.connect(done)
        self._test_worker.start()
