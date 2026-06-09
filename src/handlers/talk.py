"""
Talk handler — runs one button-press turn end-to-end.

  hold button → record → STT → LLM → TTS → save to DB

Recordings shorter than MIN_RECORDING_S are treated as accidental presses;
the agent plays a pre-recorded "too short" clip from assets/ if present,
or a TTS fallback.
"""

from pathlib import Path

from .. import db, hardware
from ..audio import play, record_until_released
from ..clients import llm, stt, tts
from ..config_loader import settings
from ..logger import AI, HUMAN, SENSOR


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOO_SHORT_AUDIO = _PROJECT_ROOT / "assets" / "too_short.wav"
TMP_TALK_WAV = Path("/tmp/talk.wav")

MIN_RECORDING_S = 2.0
MAX_RECORDING_S = 10.0
HISTORY_LIMIT = 20


def _wav_duration_s(path: Path) -> float:
    try:
        a = settings()["audio"]
        bytes_per_sec = a["sample_rate"] * 2 * a["channels"]
        return max(0.0, (path.stat().st_size - 44) / bytes_per_sec)
    except Exception:
        return 0.0


def handle() -> None:
    talk_btn = hardware.button_talk()
    SENSOR.info("button pressed")
    record_until_released(talk_btn, MAX_RECORDING_S, TMP_TALK_WAV)

    duration = _wav_duration_s(TMP_TALK_WAV)
    if duration < MIN_RECORDING_S:
        SENSOR.info("recording too short — ignored")
        if TOO_SHORT_AUDIO.exists():
            play(TOO_SHORT_AUDIO)
        else:
            tts.speak(f"Please hold the button for at least {int(MIN_RECORDING_S)} seconds.")
        return

    try:
        user_text = stt.transcribe(TMP_TALK_WAV)
        HUMAN.info(user_text)

        history = db.get_history(limit=HISTORY_LIMIT)
        prev_len = len(history)
        reply, new_history = llm.chat(user_text, history)
        db.add_messages(new_history[prev_len:])
        AI.info(reply)

        tts.speak(reply)
    except Exception as e:  # noqa: BLE001
        SENSOR.error("pipeline failed: %s", e)
