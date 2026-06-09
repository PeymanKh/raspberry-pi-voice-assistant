"""
LLM tool: get_led_state — read the current LED state.

We do this physically, via the LDR sitting next to the LED. LDR
value = 0 means it's seeing light → the LED is on. value = 1 means dark
→ LED is off. Reading the sensor (instead of trusting a software flag)
means the agent sees the actual physical reality.
"""

from .. import hardware


SPEC = {
    "type": "function",
    "function": {
        "name": "get_led_state",
        "description": (
            "Read the current state of the LED by sensing the light it gives off. "
            "Returns 'on' or 'off'. Call this BEFORE set_led so you don't toggle "
            "the LED when it's already in the requested state."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


def run() -> dict:
    state = "off" if hardware.ldr().value == 1 else "on"
    return {"state": state}
