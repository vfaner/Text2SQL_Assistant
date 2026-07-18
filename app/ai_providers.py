"""
AI providers: adapters that turn natural-language descriptions into SQL.

Most Chinese vendor endpoints are OpenAI-compatible (they accept the /chat/completions
schema), so we use a single OpenAIStyleProvider for all of them. `provider` code
only changes the default base URL / default model.
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
    # ```sql ... ```
    m = re.search(r"```(?:sql)?\s*(.+?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


class OpenAIStyleProvider:
    """Any OpenAI /chat/completions - compatible provider (OpenAI, Qwen/Bailian, DeepSeek, Doubao)."""

    def __init__(self, api_base: str, api_key: str, model: str, temperature: float = 0.2, timeout: int = 60):
        self.api_base = (api_base or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or ""
        self.temperature = float(temperature or 0.2)
        self.timeout = timeout

    def _endpoint(self) -> str:
        # Users may or may not include /v1 in api_base - allow both
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

    # ---- Public methods ----
    def generate_sql(self, description: str, dialect: str = "MySQL") -> str:
        content = self._chat(SYSTEM_PROMPT.format(dialect=dialect), description)
        return _extract_sql(content)

    def test_call(self) -> Tuple[bool, str]:
        try:
            reply = self._chat("You are a helpful assistant.", "Please reply with the single word: OK")
            return True, f"测试成功 - 模型回复: {reply.strip()[:80]}"
        except Exception as e:
            return False, f"测试失败: {e}"


def make_provider(cfg: Dict[str, Any]) -> OpenAIStyleProvider:
    """Build a provider instance from an ai_config dict."""
    return OpenAIStyleProvider(
        api_base=cfg.get("api_base") or "",
        api_key=cfg.get("api_key") or "",
        model=cfg.get("model") or "",
        temperature=cfg.get("temperature", 0.2),
    )
