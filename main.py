"""
Voice assistant orchestrator.

All AI work (STT/LLM/TTS) and tool dispatch lives behind the handlers;
this file's only job is to wire gpiozero events to handler calls and
make sure they don't overlap.
"""

import threading
import time

from src import hardware
from src.handlers import presence, talk
from src.logger import get_logger


log = get_logger("main")
motion_log = get_logger("motion")


_busy = threading.Lock()  # prevent talk + presence from running concurrently


def _on_talk_pressed() -> None:
    if not _busy.acquire(blocking=False):
        return  # something else is running — ignore this press
    try:
        talk.handle()
    finally:
        _busy.release()


def _motion_loop() -> None:
    motion = hardware.motion()
    motion_log.info("watcher started")
    while True:
        motion.wait_for_motion()

        if presence.in_cooldown():
            motion_log.info("motion detected — in cooldown, skipping")
            motion.wait_for_no_motion()
            time.sleep(1.0)
            continue

        if not _busy.acquire(blocking=False):
            motion_log.info("motion detected — busy, skipping")
            motion.wait_for_no_motion()
            time.sleep(1.0)
            continue
        try:
            played = presence.handle()
            if played:
                presence.mark_played()
        finally:
            _busy.release()

        motion.wait_for_no_motion()
        time.sleep(1.0)


def main() -> None:
    talk_btn = hardware.button_talk()
    talk_btn.when_pressed = _on_talk_pressed

    threading.Thread(target=_motion_loop, daemon=True).start()

    log.info("ready")
    log.info("hold TALK (GPIO %d) to record (min %.0fs, max %.0fs)",
             talk_btn.pin.number, talk.MIN_RECORDING_S, talk.MAX_RECORDING_S)
    log.info("welcome on motion (cooldown %.0f min)", presence.COOLDOWN_S / 60)
    log.info("Ctrl-C to exit")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("shutting down")


if __name__ == "__main__":
    main()
