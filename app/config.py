"""Configuration management - load/save config.json with light password obfuscation."""
import base64
import json
import os
from typing import Any, Dict, List, Optional

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")


# Supported database types shown in dropdown -> (display name, type code, default port)
DB_TYPES = [
    ("MySQL", "mysql", 3306),
    ("PostgreSQL", "postgresql", 5432),
    ("Oracle", "oracle", 1521),
    ("SQL Server", "mssql", 1433),
    ("OpenGauss", "opengauss", 5432),
    ("达梦（DM）", "dm", 5236),
    ("人大金仓（KingbaseES）", "kingbase", 54321),
    ("南大通用（GBase）", "gbase", 5258),
    ("神通（ShenTong）", "shentong", 2003),
    ("其他（自定义）", "custom", 0),
]

# Supported AI providers  (display name, code, default base url, default model)
AI_PROVIDERS = [
    ("阿里百炼（Qwen）", "bailian", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-max"),
    ("豆包（Doubao）", "doubao", "https://ark.cn-beijing.volces.com/api/v3", "doubao-pro-32k"),
    ("DeepSeek", "deepseek", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("千问（Qwen）", "qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    ("OpenAI", "openai", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("其他（自定义）", "custom", "", ""),
]


def _obfuscate(text: str) -> str:
    """Very light obfuscation (base64) so plaintext isn't sitting in config.json."""
    if not text:
        return ""
    try:
        return "b64:" + base64.b64encode(text.encode("utf-8")).decode("ascii")
    except Exception:
        return ""


def _deobfuscate(text: str) -> str:
    if not text:
        return ""
    if text.startswith("b64:"):
        try:
            return base64.b64decode(text[4:].encode("ascii")).decode("utf-8")
        except Exception:
            return ""
    # Backward compat: plaintext
    return text


DEFAULT_CONFIG: Dict[str, Any] = {
    "data_sources": [],
    "ai_config": {
        "provider": "openai",
        "api_base": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
    },
    "current_data_source": "",
    "ui_settings": {
        "page_size": 20,
    },
}


class ConfigManager:
    """Load/save configuration from config.json."""

    def __init__(self, path: str = CONFIG_FILE):
        self.path = path
        self.data: Dict[str, Any] = json.loads(json.dumps(DEFAULT_CONFIG))
        self.load()

    # ----- I/O -----
    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return

        # Merge with defaults so missing keys don't break things
        merged = json.loads(json.dumps(DEFAULT_CONFIG))
        merged.update(raw or {})
        # Ensure nested dicts merged
        for k in ("ai_config", "ui_settings"):
            base = DEFAULT_CONFIG[k].copy()
            base.update(merged.get(k, {}) or {})
            merged[k] = base

        # Decrypt sensitive fields
        for ds in merged.get("data_sources", []):
            ds["password"] = _deobfuscate(ds.get("password", ""))
        merged["ai_config"]["api_key"] = _deobfuscate(merged["ai_config"].get("api_key", ""))

        self.data = merged

    def save(self) -> None:
        # Deep-copy and obfuscate secrets before writing
        out = json.loads(json.dumps(self.data))
        for ds in out.get("data_sources", []):
            ds["password"] = _obfuscate(ds.get("password", ""))
        out["ai_config"]["api_key"] = _obfuscate(out["ai_config"].get("api_key", ""))

        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存配置失败: {e}")

    # ----- Data source helpers -----
    def get_data_sources(self) -> List[Dict[str, Any]]:
        return self.data.setdefault("data_sources", [])

    def find_data_source(self, name: str) -> Optional[Dict[str, Any]]:
        for ds in self.get_data_sources():
            if ds.get("name") == name:
                return ds
        return None

    def upsert_data_source(self, ds: Dict[str, Any]) -> None:
        for i, existing in enumerate(self.get_data_sources()):
            if existing.get("name") == ds.get("name"):
                self.get_data_sources()[i] = ds
                return
        self.get_data_sources().append(ds)

    def remove_data_source(self, name: str) -> None:
        self.data["data_sources"] = [d for d in self.get_data_sources() if d.get("name") != name]
        if self.data.get("current_data_source") == name:
            self.data["current_data_source"] = ""

    # ----- AI config -----
    def get_ai_config(self) -> Dict[str, Any]:
        return self.data.setdefault("ai_config", DEFAULT_CONFIG["ai_config"].copy())

    def set_ai_config(self, cfg: Dict[str, Any]) -> None:
        self.data["ai_config"] = cfg

    # ----- current selection -----
    def get_current_data_source(self) -> str:
        return self.data.get("current_data_source", "") or ""

    def set_current_data_source(self, name: str) -> None:
        self.data["current_data_source"] = name

    # ----- UI settings -----
    def get_page_size(self) -> int:
        return int(self.data.get("ui_settings", {}).get("page_size", 20) or 20)

    def set_page_size(self, n: int) -> None:
        self.data.setdefault("ui_settings", {})["page_size"] = int(n)
