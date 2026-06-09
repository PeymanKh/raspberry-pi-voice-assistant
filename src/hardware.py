"""
Shared GPIO + DHT singletons.

Anything that talks to physical hardware goes through this module so we
keep exactly one instance per device and avoid 'GPIO busy' errors when
multiple modules touch the same pin.
"""

import time
from functools import lru_cache

from gpiozero import LED, Button, Buzzer, DigitalInputDevice, DistanceSensor, MotionSensor

from .config_loader import settings


def _pin(name: str) -> int:
    return settings()["gpio"][name]


# GPIO devices

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
    """Digital LDR module. value=0 → LIGHT, value=1 → DARK."""
    return DigitalInputDevice(_pin("ldr"))


@lru_cache(maxsize=1)
def dht11():
    """DHT11 sensor. Imported lazily because adafruit_dht needs the GPIO interface."""
    import adafruit_dht
    import board
    pin_attr = f"D{_pin('dht')}"
    return adafruit_dht.DHT11(getattr(board, pin_attr))


@lru_cache(maxsize=1)
def distance_sensor() -> DistanceSensor:
    """HC-SR04 ultrasonic. distance attr returns metres.

    queue_len=1 disables internal sample smoothing so first reads return
    immediately. With the default queue_len=9 the sensor blocks until 9
    valid samples are buffered — fine in a tight test loop, but if even
    one trigger/echo cycle fails (which happens occasionally with the
    HC-SR04 on a software-PWM Pi) the whole call hangs.
    """
    return DistanceSensor(
        echo=_pin("hcsr04_echo"),
        trigger=_pin("hcsr04_trig"),
        max_distance=2.0,
        queue_len=1,
    )


@lru_cache(maxsize=1)
def touch() -> Button:
    """TTP223 capacitive touch — active high, no pull-up needed."""
    return Button(_pin("touch"), pull_up=False, bounce_time=0.05)


@lru_cache(maxsize=1)
def buzzer() -> Buzzer:
    return Buzzer(_pin("buzzer"))


# High-level helpers

def set_led(on: bool) -> None:
    """Turn the LED on or off."""
    l = led()
    if on:
        l.on()
    else:
        l.off()


def read_dht11(retries: int = 5, delay: float = 1.0) -> tuple[float | None, float | None]:
    """Read (temperature_c, humidity_pct) with retries. Returns (None, None) on persistent failure."""
    dht = dht11()
    for _ in range(retries):
        try:
            t = dht.temperature
            h = dht.humidity
            if t is not None and h is not None:
                return t, h
        except RuntimeError:
            pass
        time.sleep(delay)
    return None, None
