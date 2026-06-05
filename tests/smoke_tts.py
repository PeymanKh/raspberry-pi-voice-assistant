"""
Smoke test for TTS.

Speaks a short English sentence through the speaker.

Run from project root:
    python -m tests.smoke_tts
"""

from src.tts import speak


def main() -> None:
    text = "Hello! This is your Raspberry Pi voice assistant. Glad to be alive."
    print(f"Speaking: {text!r}")
    speak(text)
    print("Done.")


if __name__ == "__main__":
    main()
