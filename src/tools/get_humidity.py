"""
LLM tool: get_humidity — current room humidity (%) from the DHT11.
"""

from .. import hardware


SPEC = {
    "type": "function",
    "function": {
        "name": "get_humidity",
        "description": "Read the current room relative humidity as a percentage from the DHT11 sensor.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def run() -> dict:
    _, h = hardware.read_dht11()
    if h is None:
        return {"error": "DHT11 read failed after retries"}
    return {"humidity_pct": round(h, 1)}
