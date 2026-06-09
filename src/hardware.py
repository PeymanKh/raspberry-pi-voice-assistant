"""
Shared GPIO singletons.

Both `main.py` (talk button, PIR) and `src/llm.py` (LED via the set_led
tool) need GPIO. If both modules instantiate their own gpiozero objects
on the same pin, the second one fails with 'GPIO busy'. This module
owns one instance per pin and lazily creates them on first use.
"""

from functools import lru_cache

from gpiozero import LED, Button, DigitalInputDevice, MotionSensor

from .config_loader import settings


def _pin(name: str) -> int:
    return settings()["gpio"][name]


@lru_cache(maxsize=1)
def led() -> LED:
    return LED(_pin("led"))


@lru_cache(maxsize=1)
def button_talk() -> Button:
    return Button(_pin("button_talk"), pull_up=True, bounce_time=0.05)


@lru_cache(maxsize=1)
def motion() -> MotionSensor:
    return MotionSensor(_pin("motion"))


@lru_cache(maxsize=1)
def ldr() -> DigitalInputDevice:
    return DigitalInputDevice(_pin("ldr"))


def set_led(on: bool) -> None:
    """Turn the AI-controlled LED on or off."""
    l = led()
    if on:
        l.on()
    else:
        l.off()
