"""
Audio recording and playback.

Thin wrappers around `arecord` / `aplay`. Device IDs come from
configs/settings.yaml using ALSA card *names* (e.g. `UACDemoV10`,
`Headphones`) rather than card numbers — names are stable across
reboots and HDMI plug/unplug, numbers are not.
"""

import subprocess
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


def play(audio_path: str | Path) -> None:
    """Play an audio file through the configured speaker."""
    a = settings()["audio"]
    subprocess.run(
        [
            "aplay",
            "-D", f"plughw:CARD={a['speaker_name']},DEV={a['speaker_device']}",
            str(audio_path),
        ],
        check=True,
    )
