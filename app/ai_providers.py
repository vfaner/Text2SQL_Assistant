"""
AI providers: adapters that turn natural-language descriptions into SQL.

Two request/response protocols are supported:

    - `openai`     : POST {base}/chat/completions with the OpenAI schema.
                      Covers most vendors: OpenAI, DeepSeek, Qwen/Bailian,
                      Doubao/Volcengine, GLM, Kimi, Baidu Qianfan v2,
                      GitHub Models, and any 3rd-party gateway that claims
                      "OpenAI-compatible".

    - `anthropic`  : POST {base}/messages with the Anthropic Messages API
                      schema. Covers Anthropic Claude and any gateway that
                      claims "Anthropic-compatible" (e.g. LiteLLM,
                      OpenRouter's Anthropic mode).

`make_provider(cfg)` picks one based on `cfg["protocol"]`, falling back to
`openai` for older config files.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

import requests


SYSTEM_PROMPT = (
    "你是一个专业的 SQL 生成助手。用户会用自然语言描述查询需求，"
    "你必须生成对应的 SQL 语句，不要输出任何多余说明。"
    "要求：\n"
    "1. 仅输出可执行的 SQL，不要使用 markdown 代码围栏之外的解释性文字；\n"
    "2. 若无法确定表名/字段，使用合理的占位符（如 users, orders）并以注释说明；\n"
    "3. 目标数据库方言为 {dialect}，请使用该方言语法；\n"
    "4. 默认不加末尾分号也允许，风格清晰即可。"
)


def _extract_sql(text: str) -> str:
    """Remove markdown fences / stray commentary if any."""
    if not text:
        return ""
    m = re.search(r"```(?:sql)?\s*(.+?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


# ---------- Base ----------

class BaseProvider:
    """Common shape for provider adapters."""

    def generate_sql(self, description: str, dialect: str = "MySQL") -> str:
        raise NotImplementedError

    def test_call(self) -> Tuple[bool, str]:
        raise NotImplementedError


# ---------- OpenAI-compatible ----------

class OpenAIStyleProvider(BaseProvider):
    """/chat/completions with the OpenAI schema.

    Works for: OpenAI, DeepSeek, Qwen/Bailian, Doubao/Volcengine, GLM,
    Kimi/Moonshot, Baidu Qianfan v2, GitHub Models, custom gateways.
    """

    def __init__(self, api_base: str, api_key: str, model: str, temperature: float = 0.2, timeout: int = 60):
        self.api_base = (api_base or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or ""
        self.temperature = float(temperature or 0.2)
        self.timeout = timeout

    def _endpoint(self) -> str:
        base = self.api_base
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = requests.post(self._endpoint(), headers=headers, data=json.dumps(payload), timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f"AI 接口返回 HTTP {resp.status_code}: {resp.text[:500]}")
        try:
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"AI 响应不是合法 JSON: {e} | body={resp.text[:300]}")

    def _chat(self, system: str, user: str) -> str:
        data = self._post({
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        })
        try:
            return data["choices"][0]["message"]["content"] or ""
        except Exception:
            raise RuntimeError(f"AI 响应格式不符合预期: {json.dumps(data, ensure_ascii=False)[:500]}")

    def generate_sql(self, description: str, dialect: str = "MySQL") -> str:
        return _extract_sql(self._chat(SYSTEM_PROMPT.format(dialect=dialect), description))

    def test_call(self) -> Tuple[bool, str]:
        try:
            reply = self._chat("You are a helpful assistant.", "Please reply with the single word: OK")
            return True, f"测试成功 - 模型回复: {reply.strip()[:80]}"
        except Exception as e:
            return False, f"测试失败: {e}"


# ---------- Anthropic-compatible ----------

class AnthropicStyleProvider(BaseProvider):
    """Anthropic Messages API (`POST {base}/messages`).

    Auth via `x-api-key`, plus `anthropic-version` header.
    System prompt is a top-level field, not a message.
    """

    DEFAULT_VERSION = "2023-06-01"
    DEFAULT_MAX_TOKENS = 2048

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        timeout: int = 60,
        anthropic_version: str = DEFAULT_VERSION,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.api_base = (api_base or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or ""
        self.temperature = float(temperature or 0.2)
        self.timeout = timeout
        self.version = anthropic_version
        self.max_tokens = int(max_tokens)

    def _endpoint(self) -> str:
        base = self.api_base
        if base.endswith("/messages"):
            return base
        return f"{base}/messages"

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.version,
        }
        resp = requests.post(self._endpoint(), headers=headers, data=json.dumps(payload), timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f"AI 接口返回 HTTP {resp.status_code}: {resp.text[:500]}")
        try:
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"AI 响应不是合法 JSON: {e} | body={resp.text[:300]}")

    def _chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        data = self._post(payload)
        # Anthropic response: { content: [{type:"text", text:"..."}], ...}
        try:
            content = data.get("content", [])
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block.get("text", "") or ""
            # Fallback if the API returns unexpected shape
            if content and isinstance(content, list) and isinstance(content[0], dict):
                return content[0].get("text", "") or ""
        except Exception:
            pass
        raise RuntimeError(f"AI 响应格式不符合预期: {json.dumps(data, ensure_ascii=False)[:500]}")

    def generate_sql(self, description: str, dialect: str = "MySQL") -> str:
        return _extract_sql(self._chat(SYSTEM_PROMPT.format(dialect=dialect), description))

    def test_call(self) -> Tuple[bool, str]:
        try:
            reply = self._chat("You are a helpful assistant.", "Please reply with the single word: OK")
            return True, f"测试成功 - 模型回复: {reply.strip()[:80]}"
        except Exception as e:
            return False, f"测试失败: {e}"


# ---------- Factory ----------

def make_provider(cfg: Dict[str, Any]) -> BaseProvider:
    """Build a provider adapter from an ai_config dict.

    Dispatches on `cfg["protocol"]`. Defaults to `openai` for older configs
    that were saved before the field was introduced.
    """
    protocol = (cfg.get("protocol") or "openai").lower()
    if protocol == "anthropic":
        return AnthropicStyleProvider(
            api_base=cfg.get("api_base") or "",
            api_key=cfg.get("api_key") or "",
            model=cfg.get("model") or "",
            temperature=cfg.get("temperature", 0.2),
        )
    # Default: OpenAI-compatible
    return OpenAIStyleProvider(
        api_base=cfg.get("api_base") or "",
        api_key=cfg.get("api_key") or "",
        model=cfg.get("model") or "",
        temperature=cfg.get("temperature", 0.2),
    )
