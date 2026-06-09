"""
Audio recording and playback.

Thin wrappers around `arecord` / `aplay`. Device IDs come from
configs/settings.yaml using ALSA card *names* (e.g. `UACDemoV10`,
`Headphones`) rather than card numbers — names are stable across
reboots and HDMI plug/unplug, numbers are not.

`play()` is interruptible — `request_stop()` kills the currently
running aplay so the touch sensor can stop the TTS mid-sentence.
If `request_stop()` is called while we're between turns (e.g. mid
TTS synthesis), a one-shot "stop requested" flag is latched so the
imminent `play()` call returns immediately. This makes the touch
interrupt feel reliable even when the user touches the pad before
the audio has actually started.
"""

import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from .config_loader import settings


# Module-level handle to the currently-playing aplay process so a
# concurrent caller (the touch handler) can terminate it.
_play_lock = threading.Lock()
_current_play_proc: Optional[subprocess.Popen] = None
# Latched when stop is requested but nothing is playing yet.
# The next `play()` call sees it, clears it, and returns without
# touching aplay. Cleared on every successful start of a new play.
_stop_pending: bool = False


def record(seconds: int, output_path: str | Path) -> Path:
    """Record `seconds` of audio from the USB mic to a WAV file."""
    a = settings()["audio"]
    output_path = Path(output_path)

    subprocess.run(
        [
            "arecord",
            "-D", f"plughw:CARD={a['mic_name']},DEV={a['mic_device']}",
            "-f", "S16_LE",
            "-r", str(a["sample_rate"]),
            "-c", str(a["channels"]),
            "-d", str(seconds),
            str(output_path),
        ],
        check=True,
    )
    return output_path


def record_until_released(button, max_seconds: float, output_path: str | Path) -> Path:
    """Record from the mic while `button.is_pressed` is True, up to `max_seconds`."""
    a = settings()["audio"]
    output_path = Path(output_path)

    proc = subprocess.Popen(
        [
            "arecord",
            "-D", f"plughw:CARD={a['mic_name']},DEV={a['mic_device']}",
            "-f", "S16_LE",
            "-r", str(a["sample_rate"]),
            "-c", str(a["channels"]),
            "-d", str(int(max_seconds) + 1),
            "-q",
            str(output_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    start = time.monotonic()
    try:
        while button.is_pressed and (time.monotonic() - start) < max_seconds:
            time.sleep(0.05)
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    return output_path


def play(audio_path: str | Path) -> None:
    """Play an audio file. Blocks until done, but can be cut short by request_stop()."""
    global _current_play_proc, _stop_pending
    a = settings()["audio"]

    # If the user already asked to stop (e.g. touched the pad during TTS
    # synthesis), consume the request and skip this clip entirely.
    with _play_lock:
        if _stop_pending:
            _stop_pending = False
            return

    proc = subprocess.Popen(
        [
            "aplay",
            "-q",
            "-D", f"plughw:CARD={a['speaker_name']},DEV={a['speaker_device']}",
            str(audio_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Publish the proc handle, but also re-check the stop flag: a touch
    # could have raced in between the flag check above and Popen returning.
    with _play_lock:
        if _stop_pending:
            _stop_pending = False
            kill_now = True
        else:
            _current_play_proc = proc
            kill_now = False

    if kill_now:
        proc.terminate()
        try:
            proc.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return

    try:
        proc.wait()
    finally:
        with _play_lock:
            if _current_play_proc is proc:
                _current_play_proc = None


def request_stop() -> bool:
    """Stop the current playback, or latch a stop for the next one.

    Returns True if an aplay process was actually terminated; False if
    nothing was playing (in which case the stop is *latched* so the next
    `play()` call returns immediately — this covers touches that land
    during TTS synthesis, before aplay has started).
    """
    global _stop_pending
    with _play_lock:
        proc = _current_play_proc
        if proc is None or proc.poll() is not None:
            _stop_pending = True
            return False
    # Outside the lock: terminating can take ~tens of ms; we don't want
    # to hold the lock while play()'s finally clause is also trying to
    # touch the shared state.
    proc.terminate()
    try:
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return True


# Back-compat alias — older callers (and tests) import stop_playback.
stop_playback = request_stop
