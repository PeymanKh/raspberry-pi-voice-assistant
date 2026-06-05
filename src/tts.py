"""
Text-to-speech via OpenRouter (Google Gemini TTS).

OpenRouter's /api/v1/audio/speech IS OpenAI-SDK compatible, so we use
the same `openai` client we already configured for the LLM.

Gemini 3.1 Flash TTS emits raw PCM at 24 kHz / 16-bit mono. We request
`pcm`, wrap the bytes in a WAV header via the stdlib `wave` module, and
play through the existing aplay-based `src.audio.play()`. No mpg123 or
ffmpeg required.
"""

import os
import tempfile
import time
import wave
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .audio import play
from .config_loader import settings


load_dotenv()

_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)


def synthesize(text: str, output_path: str | Path | None = None) -> Path:
    """Generate speech audio for `text` and return the WAV file path."""
    tts_cfg = settings()["tts"]
    model = settings()["models"]["tts"]
    voice = tts_cfg["voice"]
    rate = int(tts_cfg["sample_rate"])

    if output_path is None:
        output_path = Path(tempfile.gettempdir()) / f"tts_{int(time.time() * 1000)}.wav"
    output_path = Path(output_path)

    with _client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        response_format="pcm",
    ) as resp:
        pcm_bytes = resp.read()

    with wave.open(str(output_path), "wb") as w:
        w.setnchannels(1)       # mono
        w.setsampwidth(2)       # 16-bit
        w.setframerate(rate)    # 24000 Hz
        w.writeframes(pcm_bytes)

    return output_path


def speak(text: str) -> None:
    """Synthesize `text` and play it through the speaker."""
    path = synthesize(text)
    play(path)
