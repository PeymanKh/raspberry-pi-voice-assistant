"""
Shared GPIO singletons.

Both `main.py` (yellow/green LEDs, buttons, buzzer, PIR) and `src/llm.py`
(red LED via the set_led tool) need GPIO. If both modules instantiate
their own gpiozero objects on the same pin, the second one fails with
'GPIO busy'. This module owns one instance per pin and lazily creates
them on first use.
"""

from functools import lru_cache

from gpiozero import LED, Button, Buzzer, MotionSensor

from .config_loader import settings


def _pin(name: str) -> int:
    return settings()["gpio"][name]


@lru_cache(maxsize=1)
def led_yellow() -> LED:
    return LED(_pin("led_yellow"))


@lru_cache(maxsize=1)
def led_green() -> LED:
    return LED(_pin("led_green"))


@lru_cache(maxsize=1)
def led_red() -> LED:
    return LED(_pin("led_red"))


@lru_cache(maxsize=1)
def button_talk() -> Button:
    return Button(_pin("button_talk"), pull_up=True, bounce_time=0.05)


@lru_cache(maxsize=1)
def button_reset() -> Button:
    return Button(_pin("button_reset"), pull_up=True, bounce_time=0.05)


@lru_cache(maxsize=1)
def buzzer() -> Buzzer:
    return Buzzer(_pin("buzzer"))


@lru_cache(maxsize=1)
def motion() -> MotionSensor:
    return MotionSensor(_pin("motion"))


def set_red_led(on: bool) -> None:
    """Turn the AI-controlled red LED on or off."""
    led = led_red()
    if on:
        led.on()
    else:
        led.off()
