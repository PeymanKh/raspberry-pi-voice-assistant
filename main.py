"""
Voice assistant orchestrator.

All AI work (STT/LLM/TTS) and tool dispatch lives behind the handlers;
this file's only job is to wire gpiozero events to handler calls and
make sure they don't overlap.
"""

import threading
import time

from src import audio, hardware
from src.handlers import presence, talk
from src.logger import SENSOR, SYSTEM


_busy = threading.Lock()  # prevent talk + presence from running concurrently


def _on_talk_pressed() -> None:
    if not _busy.acquire(blocking=False):
        return
    try:
        talk.handle()
    finally:
        _busy.release()


def _on_touch() -> None:
    stopped = audio.stop_playback()
    SENSOR.info("touch — playback stopped" if stopped else "touch — nothing playing")


def _motion_loop() -> None:
    motion = hardware.motion()
    SENSOR.info("motion watcher ready")
    while True:
        motion.wait_for_motion()
        SENSOR.info("motion detected")

        if presence.in_cooldown() or not _busy.acquire(blocking=False):
            motion.wait_for_no_motion()
            time.sleep(1.0)
            continue
        try:
            if presence.handle():
                presence.mark_played()
        finally:
            _busy.release()

        motion.wait_for_no_motion()
        time.sleep(1.0)


def main() -> None:
    talk_btn = hardware.button_talk()
    talk_btn.when_pressed = _on_talk_pressed

    touch_pad = hardware.touch()
    touch_pad.when_pressed = _on_touch

    # Eagerly create the ultrasonic on the main thread. Its internal
    # sampling thread inherits this context, which makes runtime reads
    # reliable. Lazy-creating from the LLM tool thread is flaky.
    hardware.distance_sensor()

    threading.Thread(target=_motion_loop, daemon=True).start()

    SYSTEM.info("ready")
    SYSTEM.info(
        "hold TALK (GPIO %d) to record (min %.0fs, max %.0fs)",
        talk_btn.pin.number, talk.MIN_RECORDING_S, talk.MAX_RECORDING_S,
    )
    SYSTEM.info("touch (GPIO %d) stops playback", touch_pad.pin.number)
    SYSTEM.info("welcome on motion (cooldown %.0f min)", presence.COOLDOWN_S / 60)
    SYSTEM.info("Ctrl-C to exit")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        SYSTEM.info("shutting down")


if __name__ == "__main__":
    main()
