"""
LLM tool: get_distance — distance to the nearest object from the
HC-SR04 ultrasonic sensor, in centimetres.

Uses our manual HC-SR04 reader (hardware.read_distance_cm) which
already has built-in retries and a hard timeout, so the agent can
never hang on a bad echo.
"""

from .. import hardware


SPEC = {
    "type": "function",
    "function": {
        "name": "get_distance",
        "description": (
            "Measure how far the nearest object is from the device using the "
            "ultrasonic sensor. Returns the distance in centimetres. Useful when "
            "the user asks 'how close am I?', 'how far is X?', or anything about "
            "physical distance / proximity."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


def run() -> dict:
    cm = hardware.read_distance_cm()
    if cm is None:
        return {"error": "ultrasonic sensor got no echo — view may be blocked"}
    return {"distance_cm": cm}
