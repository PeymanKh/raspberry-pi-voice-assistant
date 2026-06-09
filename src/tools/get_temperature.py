"""
LLM tool: get_temperature — current room temperature in °C from the DHT11.
"""

from .. import hardware


SPEC = {
    "type": "function",
    "function": {
        "name": "get_temperature",
        "description": "Read the current room temperature in degrees Celsius from the DHT11 sensor.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def run() -> dict:
    t, _ = hardware.read_dht11()
    if t is None:
        return {"error": "DHT11 read failed after retries"}
    return {"temperature_c": round(t, 1)}
