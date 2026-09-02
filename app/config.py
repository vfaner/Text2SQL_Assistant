"""Configuration management - load/save config.json with light password obfuscation."""
import base64
import json
import os
from typing import Any, Dict, List, Optional

from .paths import legacy_config_paths, user_config_path

# Frozen builds keep this in a per-user directory; see app/paths.py for why the
# bundle itself is not writable.
CONFIG_FILE = user_config_path()


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

# Supported AI providers.
# Tuple: (display name, code, protocol, default base url, default model)
#   protocol: "openai" (OpenAI-compatible /chat/completions) or
#             "anthropic" (Anthropic Messages API /messages)
#
# Note: a single physical vendor can appear more than once when it exposes
# different base URLs per protocol (e.g. Volcengine ARK). The vendor list is
# the source of truth for what the "Vendor" dropdown displays; switching
# vendor auto-fills protocol + base URL + default model.
AI_PROVIDERS = [
    # ── OpenAI-compatible vendors ─────────────────────────────────────
    ("OpenAI", "openai", "openai", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("阿里百炼（Qwen）", "bailian", "openai", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-max"),
    ("千问（Qwen）", "qwen", "openai", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    ("火山引擎（Volcengine ARK · OpenAI 协议）", "volcengine", "openai", "https://ark.cn-beijing.volces.com/api/plan/v3", "ark-code-latest"),
    ("豆包（Doubao）", "doubao", "openai", "https://ark.cn-beijing.volces.com/api/v3", "doubao-pro-32k"),
    ("DeepSeek", "deepseek", "openai", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("百度千帆（ERNIE）", "qianfan", "openai", "https://qianfan.baidubce.com/v2", "ernie-4.0-turbo-8k"),
    ("智谱 GLM", "zhipu", "openai", "https://open.bigmodel.cn/api/paas/v4", "glm-4-plus"),
    ("Kimi（Moonshot）", "kimi", "openai", "https://api.moonshot.cn/v1", "moonshot-v1-8k"),
    ("胜算云", "shengsuanyun", "openai", "https://router.shengsuanyun.com/api/v1", "deepseek-chat"),
    ("GitHub Copilot / Models", "github_models", "openai", "https://models.inference.ai.azure.com", "gpt-4o-mini"),
    ("兼容 OpenAI 协议（自定义）", "openai_custom", "openai", "", ""),

    # ── Anthropic-compatible vendors ──────────────────────────────────
    ("Anthropic Claude", "anthropic", "anthropic", "https://api.anthropic.com/v1", "claude-3-5-sonnet-latest"),
    ("火山引擎（Volcengine ARK · Anthropic 协议）", "volcengine_anthropic", "anthropic", "https://ark.cn-beijing.volces.com/api/plan", "ark-code-latest"),
    ("兼容 Anthropic 协议（自定义）", "anthropic_custom", "anthropic", "", ""),
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
    # New multi-config schema. Legacy `ai_config` (single dict) is auto-migrated.
    "ai_configs": [],
    "current_ai_config": "",
    "current_data_source": "",
    "ui_settings": {
        "page_size": 20,
    },
}


def _default_ai_entry(name: str = "默认") -> Dict[str, Any]:
    return {
        "name": name,
        "provider": "openai",
        "protocol": "openai",
        "api_base": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
    }


class ConfigManager:
    """Load/save configuration from config.json."""

    def __init__(self, path: str = CONFIG_FILE):
        self.path = path
        self.data: Dict[str, Any] = json.loads(json.dumps(DEFAULT_CONFIG))
        self.load()

    # ----- I/O -----
    def _read_raw(self) -> tuple[Optional[Dict[str, Any]], bool]:
        """Read the config JSON, falling back to pre-`.app` locations.

        Returns ``(raw, migrated)`` where ``migrated`` is True when the data came
        from a legacy path and should be written back to ``self.path``.
        """
        for path, is_legacy in [(self.path, False)] + [(p, True) for p in legacy_config_paths()]:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f), is_legacy
            except Exception:
                continue
        return None, False

    def load(self) -> None:
        raw, migrated = self._read_raw()
        if raw is None:
            return

        merged = json.loads(json.dumps(DEFAULT_CONFIG))
        merged.update(raw or {})
        # Ensure nested dicts merged
        base = DEFAULT_CONFIG["ui_settings"].copy()
        base.update(merged.get("ui_settings", {}) or {})
        merged["ui_settings"] = base

        # Migrate legacy single-config schema (ai_config: {...}) -> ai_configs: [...]
        legacy = raw.get("ai_config") if isinstance(raw, dict) else None
        if legacy and not merged.get("ai_configs"):
            entry = _default_ai_entry("默认")
            entry.update({k: v for k, v in legacy.items() if k in entry})
            entry["api_key"] = legacy.get("api_key", "")
            merged["ai_configs"] = [entry]
            if not merged.get("current_ai_config"):
                merged["current_ai_config"] = entry["name"]

        # Ensure the list exists
        merged.setdefault("ai_configs", [])

        # Decrypt sensitive fields
        for ds in merged.get("data_sources", []):
            ds["password"] = _deobfuscate(ds.get("password", ""))
        for ai in merged.get("ai_configs", []):
            ai["api_key"] = _deobfuscate(ai.get("api_key", ""))

        self.data = merged

        # Persist into the writable location so the legacy copy is only read once.
        if migrated:
            try:
                self.save()
            except Exception:
                pass

    def save(self) -> None:
        # Deep-copy and obfuscate secrets before writing
        out = json.loads(json.dumps(self.data))
        for ds in out.get("data_sources", []):
            ds["password"] = _obfuscate(ds.get("password", ""))
        for ai in out.get("ai_configs", []):
            ai["api_key"] = _obfuscate(ai.get("api_key", ""))
        # Don't persist the legacy key
        out.pop("ai_config", None)

        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
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

    # ----- AI configs (multi) -----
    def get_ai_configs(self) -> List[Dict[str, Any]]:
        return self.data.setdefault("ai_configs", [])

    def find_ai_config(self, name: str) -> Optional[Dict[str, Any]]:
        for ai in self.get_ai_configs():
            if ai.get("name") == name:
                return ai
        return None

    def upsert_ai_config(self, cfg: Dict[str, Any]) -> None:
        for i, existing in enumerate(self.get_ai_configs()):
            if existing.get("name") == cfg.get("name"):
                self.get_ai_configs()[i] = cfg
                return
        self.get_ai_configs().append(cfg)

    def remove_ai_config(self, name: str) -> None:
        self.data["ai_configs"] = [c for c in self.get_ai_configs() if c.get("name") != name]
        if self.data.get("current_ai_config") == name:
            self.data["current_ai_config"] = ""

    def get_current_ai_config(self) -> Optional[Dict[str, Any]]:
        """Return the AI config marked as current, or the first one if none is marked."""
        name = self.data.get("current_ai_config") or ""
        if name:
            found = self.find_ai_config(name)
            if found:
                return found
        configs = self.get_ai_configs()
        return configs[0] if configs else None

    def set_current_ai_config(self, name: str) -> None:
        self.data["current_ai_config"] = name

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
