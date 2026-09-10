"""
AI providers: adapters that turn natural-language descriptions into SQL.

Two request/response protocols are supported:

    - `openai`     : POST {base}/chat/completions with the OpenAI schema.
                      Covers most vendors: OpenAI, DeepSeek, Qwen/Bailian,
                      Doubao/Volcengine, GLM, Kimi, Baidu Qianfan v2,
                      GitHub Models, and any 3rd-party gateway that claims
                      "OpenAI-compatible".

    - `anthropic`  : POST {base}/v1/messages with the Anthropic Messages API
                      schema (or {base}/messages when base already ends in
                      /v1). Covers Anthropic Claude and any gateway that
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


# Used when no data source is connected: the model has no schema to work from,
# so it is explicitly allowed to invent placeholder table names.
SYSTEM_PROMPT = (
    "你是一个专业的 SQL 生成助手。用户会用自然语言描述查询需求，"
    "你必须生成对应的 SQL 语句，不要输出任何多余说明。"
    "要求：\n"
    "1. 仅输出可执行的 SQL，不要使用 markdown 代码围栏之外的解释性文字；\n"
    "2. 若无法确定表名/字段，使用合理的占位符（如 users, orders）并以注释说明；\n"
    "3. 目标数据库方言为 {dialect}，请使用该方言语法；\n"
    "4. 默认不加末尾分号也允许，风格清晰即可。"
)

# Used when a data source is connected: the prompt carries the database's real
# structure, so the model is told to stay inside it instead of inventing names.
SYSTEM_PROMPT_SCHEMA = (
    "你是一个专业的 SQL 生成助手。下面给出了目标数据库的真实表结构，"
    "请严格依据它把用户的自然语言需求翻译成可执行 SQL。\n"
    "规则：\n"
    "1. 只能使用下面结构中真实存在的表名和列名，禁止臆造表或字段；\n"
    "2. 需要多表关联时，依据结构中的外键（FOREIGN KEY ... REFERENCES）编写 JOIN 条件；\n"
    "3. 把中文业务词对照列名、列注释和表注释映射到真实列。例如“三年级”应结合 grade "
    "之类的年级列（注意其存的是数字 3 还是文本“三年级”），“数学”对应课程名称列，"
    "“60 分以上”对应分数列并用数值比较；\n"
    "4. 涉及歧义列名时用 表名.列名 限定；查询“学生信息”默认返回学生相关列而非 SELECT *；\n"
    "5. 目标数据库方言为 {dialect}，请使用该方言语法；\n"
    "6. 仅输出可执行的 SQL，不要输出 markdown 代码围栏之外的任何解释。\n\n"
    "数据库真实表结构：\n{schema}"
)


def build_system_prompt(dialect: str, schema: str = "") -> str:
    """Pick the schema-aware prompt when structure is available, else the generic one."""
    if schema and schema.strip():
        return SYSTEM_PROMPT_SCHEMA.format(dialect=dialect, schema=schema.strip())
    return SYSTEM_PROMPT.format(dialect=dialect)


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

    def generate_sql(self, description: str, dialect: str = "MySQL", schema: str = "") -> str:
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

    def generate_sql(self, description: str, dialect: str = "MySQL", schema: str = "") -> str:
        system = build_system_prompt(dialect, schema)
        return _extract_sql(self._chat(system, description))

    def test_call(self) -> Tuple[bool, str]:
        try:
            reply = self._chat("You are a helpful assistant.", "Please reply with the single word: OK")
            return True, f"测试成功 - 模型回复: {reply.strip()[:80]}"
        except Exception as e:
            return False, f"测试失败: {e}"


# ---------- Anthropic-compatible ----------

class AnthropicStyleProvider(BaseProvider):
    """Anthropic Messages API.

    URL assembly follows the official Anthropic SDK convention: a bare base
    (`https://api.anthropic.com`, or Volcengine's `.../api/coding`) gets
    `/v1/messages` appended; a base that already ends with the API version
    (`.../v1`) only gets `/messages`. A fully-qualified `.../messages` URL is
    used as-is.

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
        if base.endswith("/v1"):
            return f"{base}/messages"
        # Bare base (e.g. https://.../api/coding): the Anthropic SDK itself
        # appends /v1/messages, so mirror that instead of hitting /messages.
        return f"{base}/v1/messages"

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

    def generate_sql(self, description: str, dialect: str = "MySQL", schema: str = "") -> str:
        system = build_system_prompt(dialect, schema)
        return _extract_sql(self._chat(system, description))

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
