"""
Talk handler — runs one button-press turn end-to-end.

  hold button → record → STT → LLM → TTS → save to DB

Recordings shorter than MIN_RECORDING_S are treated as accidental presses;
the agent plays a pre-recorded "too short" clip from assets/ if present,
or a TTS fallback. Any backend error logs at ERROR level.
"""

import wave
from pathlib import Path

from .. import db, hardware
from ..audio import play, record_until_released
from ..clients import llm, stt, tts
from ..logger import get_logger


log = get_logger("talk")


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOO_SHORT_AUDIO = _PROJECT_ROOT / "assets" / "too_short.wav"
TMP_TALK_WAV = Path("/tmp/talk.wav")

MIN_RECORDING_S = 5.0
MAX_RECORDING_S = 10.0
HISTORY_LIMIT = 20


def _wav_duration_s(path: Path) -> float:
    try:
        with wave.open(str(path)) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def handle() -> None:
    """Run one talk turn. Safe to call from a gpiozero callback thread."""
    talk_btn = hardware.button_talk()

    log.info("button pressed — recording (max %.0fs)", MAX_RECORDING_S)
    record_until_released(talk_btn, MAX_RECORDING_S, TMP_TALK_WAV)

    duration = _wav_duration_s(TMP_TALK_WAV)
    if duration < MIN_RECORDING_S:
        log.info("discarded — %.1fs < %.0fs (noise)", duration, MIN_RECORDING_S)
        if TOO_SHORT_AUDIO.exists():
            play(TOO_SHORT_AUDIO)
        else:
            tts.speak(f"Please hold the button for at least {int(MIN_RECORDING_S)} seconds.")
        return

    log.info("recorded %.1fs — processing", duration)
    try:
        user_text = stt.transcribe(TMP_TALK_WAV)
        log.info("user: %s", user_text)

        history = db.get_history(limit=HISTORY_LIMIT)
        prev_len = len(history)
        reply, new_history = llm.chat(user_text, history)
        db.add_messages(new_history[prev_len:])
        log.info("assistant: %s", reply)

        tts.speak(reply)
        log.info("done")
    except Exception as e:  # noqa: BLE001
        log.error("pipeline error: %s", e)
