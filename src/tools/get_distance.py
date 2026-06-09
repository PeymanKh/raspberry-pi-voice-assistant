"""
LLM tool: get_distance — distance to the nearest object from the
HC-SR04 ultrasonic sensor, in centimetres.

The read is wrapped in a short timeout. If the sensor fails to echo
(noisy environment, blocked view, dead sensor) we return an error
instead of hanging the agent.
"""

import threading
import warnings

from .. import hardware


# Silence the gpiozero "no echo received" warnings — we handle the failure
# explicitly through the timeout below, the user doesn't need to see them.
warnings.filterwarnings("ignore", module="gpiozero.input_devices")


_READ_TIMEOUT_S = 2.0


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
    result: list = [None]

    def _read() -> None:
        try:
            metres = hardware.distance_sensor().distance
            result[0] = ("ok", round(metres * 100, 1))
        except Exception as e:  # noqa: BLE001
            result[0] = ("err", str(e))

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=_READ_TIMEOUT_S)

    if result[0] is None:
        return {"error": "ultrasonic sensor timed out — view may be blocked"}

    kind, val = result[0]
    if kind == "err":
        return {"error": f"ultrasonic read failed: {val}"}
    return {"distance_cm": val}
