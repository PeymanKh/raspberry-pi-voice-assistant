"""
Shared GPIO + DHT singletons.

Anything that talks to physical hardware goes through this module so we
keep exactly one instance per device and avoid 'GPIO busy' errors when
multiple modules touch the same pin.
"""

import time
from functools import lru_cache

from gpiozero import LED, Button, Buzzer, DigitalInputDevice, MotionSensor, OutputDevice

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
def _hcsr04_trig() -> OutputDevice:
    return OutputDevice(_pin("hcsr04_trig"))


@lru_cache(maxsize=1)
def _hcsr04_echo() -> DigitalInputDevice:
    return DigitalInputDevice(_pin("hcsr04_echo"))


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


def read_distance_cm(timeout: float = 0.04, retries: int = 4) -> float | None:
    """Manual HC-SR04 read. Returns cm, or None if no valid echo after retries.

    We bypass gpiozero's DistanceSensor — its internal sampling thread is
    flaky from non-main threads (the first read often fails with
    'no echo received'). A direct trigger+echo poll with retries is more
    reliable for our use case.
    """
    trig = _hcsr04_trig()
    echo = _hcsr04_echo()

    for _ in range(retries):
        # 10us trigger pulse
        trig.on()
        time.sleep(0.00001)
        trig.off()

        # Wait for echo rising edge
        deadline = time.monotonic() + timeout
        while not echo.value:
            if time.monotonic() > deadline:
                break
        else:
            start = time.monotonic()
            # Wait for echo falling edge
            deadline = start + timeout
            while echo.value:
                if time.monotonic() > deadline:
                    break
            else:
                end = time.monotonic()
                # speed of sound 34300 cm/s, divide by 2 for round trip
                cm = (end - start) * 17150
                if 1.0 <= cm <= 400.0:
                    return round(cm, 1)
        # Otherwise: timed out or read out of range — short pause then retry
        time.sleep(0.05)

    return None


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
