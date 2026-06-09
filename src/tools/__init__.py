"""
LLM tools registry.

Each tool is a tiny module exposing two things:
  - SPEC: an OpenAI-style function spec (name, description, parameters)
  - run(**kwargs) -> dict: what runs when the model calls the tool

To add a new tool: drop a `<name>.py` here, import it below, append to
ALL_TOOLS. The LLM client picks up TOOLS_SPEC and DISPATCH automatically.
"""

from . import (
    get_distance,
    get_humidity,
    get_led_state,
    get_temperature,
    play_tune,
    set_led,
)


ALL_TOOLS = [
    set_led,
    get_led_state,
    get_temperature,
    get_humidity,
    get_distance,
    play_tune,
]


TOOLS_SPEC = [t.SPEC for t in ALL_TOOLS]
DISPATCH = {t.SPEC["function"]["name"]: t.run for t in ALL_TOOLS}
