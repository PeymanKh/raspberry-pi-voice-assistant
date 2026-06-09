"""
Event handlers — what happens when the user presses TALK or the PIR
fires. Each module exposes a small public surface (`handle()` plus any
cooldown helpers) that `main.py` wires to gpiozero events.
"""

from . import presence, talk


__all__ = ["presence", "talk"]
