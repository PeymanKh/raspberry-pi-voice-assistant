"""
OpenRouter chat LLM client with tool calling.

Loops until the model returns a final text reply (no more tool_calls).
Tool specs and dispatch live in `src/tools/` — this class doesn't know
which tools exist, it just hands the registry to the model.

Reasoning is OFF by default to keep voice latency low.
"""

import json
from pathlib import Path
from typing import Optional

from openai import OpenAI

from ..logger import get_logger
from ..tools import DISPATCH, TOOLS_SPEC
from .base import LLMClient


log = get_logger("llm")
tool_log = get_logger("tool")


def _short(obj, limit: int = 120) -> str:
    s = json.dumps(obj, default=str)
    return s if len(s) <= limit else s[: limit - 1] + "…"


class OpenRouterLLM(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt_path: str | Path,
        reasoning: bool = False,
    ):
        self.model = model
        self.system_prompt_path = Path(system_prompt_path)
        self.reasoning = reasoning
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def _system_prompt(self) -> str:
        return self.system_prompt_path.read_text()

    def chat(
        self,
        message: str,
        history: Optional[list[dict]] = None,
    ) -> tuple[str, list[dict]]:
        history = list(history or [])
        messages = (
            [{"role": "system", "content": self._system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )

        extra = {"reasoning": {"enabled": True}} if self.reasoning else None
        log.info("chat sent (model=%s, history=%d)", self.model, len(history))

        while True:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SPEC,
                extra_body=extra,
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn = DISPATCH.get(tc.function.name)
                    if fn is None:
                        result = {"error": f"unknown tool: {tc.function.name}"}
                    else:
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                            result = fn(**args)
                        except Exception as e:  # noqa: BLE001
                            result = {"error": str(e)}
                    tool_log.info("%s(%s) -> %s", tc.function.name, _short(args), _short(result))
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result),
                        }
                    )
                continue

            log.info("reply: %s", msg.content or "")
            # Drop system prompt before returning the history we persist.
            return (msg.content or ""), messages[1:]
