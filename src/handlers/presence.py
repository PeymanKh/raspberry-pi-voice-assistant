"""
Presence handler — plays the welcome clip on PIR motion, rate-limited.

Cooldown state lives in this module. We only consume it AFTER a successful
play, so a motion event that races with an in-progress talk doesn't burn
the 5-minute window.
"""

import threading
import time
from pathlib import Path

from ..audio import play
from ..clients import tts
from ..logger import SENSOR


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
WELCOME_SOUND = _PROJECT_ROOT / "assets" / "welcome.wav"
COOLDOWN_S = 300.0

_lock = threading.Lock()
# -inf so a fresh boot is never considered "in cooldown".
_last_played_ts: float = float("-inf")


def in_cooldown() -> bool:
    with _lock:
        return (time.monotonic() - _last_played_ts) < COOLDOWN_S


def mark_played() -> None:
    global _last_played_ts
    with _lock:
        _last_played_ts = time.monotonic()


def handle() -> bool:
    try:
        if WELCOME_SOUND.exists():
            play(WELCOME_SOUND)
        else:
            SENSOR.warning("welcome.wav missing — using live TTS")
            tts.speak("Hello! Press the talk button to chat with me.")
        SENSOR.info("welcome played")
        return True
    except Exception as e:  # noqa: BLE001
        SENSOR.error("welcome failed: %s", e)
        return False
