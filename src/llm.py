"""
LLM chat with tool calling, via OpenRouter.

Exposes `chat(message, history) -> (reply, updated_history)`. The model
can call `set_led(state)` to toggle the LED. We loop until the model
returns a final text reply (no more tool calls).

History is a list of plain dicts (no system prompt — we prepend it each
call). Safe to JSON-serialize for persistence.

Reasoning is OFF by default to keep voice latency low. Flip
REASONING_ENABLED if you want deeper reasoning at the cost of seconds
per turn.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from . import hardware
from .config_loader import settings


load_dotenv()

REASONING_ENABLED = False

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts" / "system"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "assistant.md"

_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "set_led",
            "description": "Turn the LED on or off.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "Desired LED state.",
                    }
                },
                "required": ["state"],
            },
        },
    }
]


def _tool_set_led(state: str) -> dict:
    hardware.set_led(state == "on")
    return {"ok": True, "state": state}


_TOOL_DISPATCH = {"set_led": _tool_set_led}


def _system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text()


def chat(message: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
    """Send `message`, execute any tool calls, return (final text, new history)."""
    history = list(history or [])
    messages = (
        [{"role": "system", "content": _system_prompt()}]
        + history
        + [{"role": "user", "content": message}]
    )

    model = settings()["models"]["llm"]
    extra: dict = {}
    if REASONING_ENABLED:
        extra["reasoning"] = {"enabled": True}

    while True:
        resp = _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=_TOOLS_SPEC,
            extra_body=extra or None,
        )
        msg = resp.choices[0].message
        # Serialize the assistant message into a plain dict so it round-trips.
        assistant_dict = msg.model_dump(exclude_none=True)
        messages.append(assistant_dict)

        if msg.tool_calls:
            for tc in msg.tool_calls:
                fn = _TOOL_DISPATCH.get(tc.function.name)
                if fn is None:
                    result = {"error": f"unknown tool: {tc.function.name}"}
                else:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                        result = fn(**args)
                    except Exception as e:  # noqa: BLE001
                        result = {"error": str(e)}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        # Final answer — drop the system message before returning history.
        new_history = messages[1:]
        return (msg.content or ""), new_history
