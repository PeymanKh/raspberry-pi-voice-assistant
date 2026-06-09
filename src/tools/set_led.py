"""
LLM tool: set_led — turn the LED on or off.

Only call after checking the current state with `get_led_state`. The
system prompt enforces this so we don't act when the LED is already in
the requested state.
"""

from .. import hardware


SPEC = {
    "type": "function",
    "function": {
        "name": "set_led",
        "description": (
            "Turn the physical LED on or off. Only call this AFTER checking the "
            "current state with get_led_state — do not call if the LED is already "
            "in the requested state."
        ),
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


def run(state: str) -> dict:
    hardware.set_led(state == "on")
    return {"ok": True, "state": state}
