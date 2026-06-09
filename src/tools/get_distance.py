"""
LLM tool: get_distance — distance to the nearest object from the
HC-SR04 ultrasonic sensor, in centimetres.
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
    metres = hardware.distance_sensor().distance  # 0.0 to max_distance (2.0)
    return {"distance_cm": round(metres * 100, 1)}
