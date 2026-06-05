"""
Smoke test for STT.

Records 5 seconds from the mic, transcribes via OpenRouter, prints result.

Run from project root:
    python -m tests.smoke_stt
"""

from pathlib import Path

from src.audio import record
from src.stt import transcribe


def main() -> None:
    out = Path("/tmp/stt_smoke.wav")
    print("Recording 5 seconds — speak now...")
    record(5, out)
    print(f"Recorded to {out}. Transcribing...")
    text = transcribe(out)
    print(f"\nTranscript: {text!r}")


if __name__ == "__main__":
    main()
