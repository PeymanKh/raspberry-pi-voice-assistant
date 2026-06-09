"""
Audio recording and playback.

Thin wrappers around `arecord` / `aplay`. Device IDs come from
configs/settings.yaml using ALSA card *names* (e.g. `UACDemoV10`,
`Headphones`) rather than card numbers — names are stable across
reboots and HDMI plug/unplug, numbers are not.
"""

import signal
import subprocess
import time
from pathlib import Path

from .config_loader import settings


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
    """
    Record from the mic while `button.is_pressed` is True, up to `max_seconds`.

    Starts `arecord` with -d max_seconds, then polls the button. On release
    (or timeout) sends SIGINT so arecord finalises the WAV header cleanly.
    Returns the output path regardless of duration — caller decides whether
    the resulting file is long enough to process.
    """
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
    """Play an audio file through the configured speaker, silently."""
    a = settings()["audio"]
    subprocess.run(
        [
            "aplay",
            "-q",
            "-D", f"plughw:CARD={a['speaker_name']},DEV={a['speaker_device']}",
            str(audio_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
