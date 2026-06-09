"""
Voice assistant orchestrator.

State machine:

  IDLE
   ├─ TALK button held → record while held (max 10s)
   │                     if ≥ 5s of audio: STT → LLM → TTS → save to DB
   │                     else: discard (too short, treat as noise)
   └─ MOTION detected → play welcome sound, rate-limited to once every 5 min

The red LED is controlled by the LLM via the `set_led` tool.

Run from project root:
    python main.py
"""

import threading
import time
import wave
from pathlib import Path

from src import db, hardware
from src.audio import play, record_until_released
from src.llm import chat
from src.stt import transcribe
from src.tts import speak


# === Tunables ===
PROJECT_ROOT = Path(__file__).resolve().parent
WELCOME_SOUND = PROJECT_ROOT / "assets" / "welcome.wav"
TMP_TALK_WAV = Path("/tmp/talk.wav")

MIN_RECORDING_S = 5.0      # below this is "noise", discarded
MAX_RECORDING_S = 10.0     # hard cap on a single recording
MOTION_COOLDOWN_S = 300.0  # 5 minutes between welcome plays
HISTORY_LIMIT = 20         # turns of context sent to the LLM


# === Shared state ===
# Held while any high-level handler is running so handlers can't overlap
# (e.g. motion welcome won't crash into the middle of a talk).
_busy = threading.Lock()

# Cooldown state for the motion welcome.
_welcome_lock = threading.Lock()
_last_welcome_ts = 0.0  # monotonic seconds; 0 means "never"


# === Helpers ===

def _wav_duration_s(path: Path) -> float:
    """Return WAV duration in seconds, or 0.0 if the file is missing/corrupt."""
    try:
        with wave.open(str(path)) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


# === Handlers ===

def _handle_talk() -> None:
    if not _busy.acquire(blocking=False):
        return  # already processing something — drop this press
    try:
        talk_btn = hardware.button_talk()

        # Record while held (max 10s).
        record_until_released(talk_btn, MAX_RECORDING_S, TMP_TALK_WAV)

        duration = _wav_duration_s(TMP_TALK_WAV)
        if duration < MIN_RECORDING_S:
            print(f"[talk] discarded — {duration:.1f}s < {MIN_RECORDING_S}s (noise).")
            return

        print(f"[talk] {duration:.1f}s of audio. Processing...")
        try:
            user_text = transcribe(TMP_TALK_WAV)
            print(f"[user] {user_text}")

            history = db.get_history(limit=HISTORY_LIMIT)
            prev_len = len(history)
            reply, new_history = chat(user_text, history)
            # Persist only the newly-added messages (user + assistant + any tool turns).
            db.add_messages(new_history[prev_len:])
            print(f"[assistant] {reply}")

            speak(reply)
        except Exception as e:
            print(f"[talk] pipeline error: {e}")
    finally:
        _busy.release()


def _motion_loop() -> None:
    """Background thread. Plays welcome on motion, rate-limited to once / 5 min."""
    global _last_welcome_ts
    motion = hardware.motion()
    print("[motion] thread started.")

    while True:
        motion.wait_for_motion()

        # Cooldown check. Read-only — only mark cooldown AFTER a successful
        # play, so a motion event that races with a talk doesn't consume the slot.
        with _welcome_lock:
            in_cooldown = (time.monotonic() - _last_welcome_ts) < MOTION_COOLDOWN_S
        if in_cooldown:
            motion.wait_for_no_motion()
            time.sleep(1.0)
            continue

        # Don't crash into an in-progress talk.
        if not _busy.acquire(blocking=False):
            motion.wait_for_no_motion()
            time.sleep(1.0)
            continue
        try:
            played = False
            try:
                if WELCOME_SOUND.exists():
                    print(f"[motion] playing {WELCOME_SOUND.name}")
                    play(WELCOME_SOUND)
                else:
                    print("[motion] welcome.wav missing — falling back to TTS.")
                    speak("Hello! Press the talk button to chat with me.")
                played = True
            except Exception as e:
                print(f"[motion] welcome failed: {e}")
            # Only consume the 5-min cooldown if we actually played.
            if played:
                with _welcome_lock:
                    _last_welcome_ts = time.monotonic()
        finally:
            _busy.release()

        motion.wait_for_no_motion()
        time.sleep(1.0)


# === Entrypoint ===

def main() -> None:
    talk_btn = hardware.button_talk()
    talk_btn.when_pressed = _handle_talk

    threading.Thread(target=_motion_loop, daemon=True).start()

    print("Voice assistant ready.")
    print(f"  Hold TALK (GPIO {talk_btn.pin.number}) to record (min {MIN_RECORDING_S:.0f}s, max {MAX_RECORDING_S:.0f}s).")
    print(f"  Welcome on motion, cooldown {MOTION_COOLDOWN_S/60:.0f} min.")
    print("Press Ctrl-C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
