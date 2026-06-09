"""
Audio recording and playback.

Thin wrappers around `arecord` / `aplay`. Device IDs come from
configs/settings.yaml using ALSA card *names* (e.g. `UACDemoV10`,
`Headphones`) rather than card numbers — names are stable across
reboots and HDMI plug/unplug, numbers are not.

`play()` is interruptible — `stop_playback()` kills the currently
running aplay so the touch sensor can stop the TTS mid-sentence.
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
    """Play an audio file. Blocks until done, but can be cut short by stop_playback()."""
    global _current_play_proc
    a = settings()["audio"]

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

    with _play_lock:
        # If something else was playing, leave it — the caller decides ordering.
        _current_play_proc = proc

    try:
        proc.wait()
    finally:
        with _play_lock:
            if _current_play_proc is proc:
                _current_play_proc = None


def stop_playback() -> bool:
    """Kill the currently playing aplay process, if any. Returns True if it stopped something."""
    with _play_lock:
        proc = _current_play_proc
    if proc is None or proc.poll() is not None:
        return False
    proc.terminate()
    try:
        proc.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return True
