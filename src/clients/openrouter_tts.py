"""
OpenRouter text-to-speech client (Google Gemini TTS).

OpenRouter's /api/v1/audio/speech IS OpenAI-SDK compatible, so we use
the same `openai` client we already use for the LLM. Gemini emits raw
24 kHz / 16-bit / mono PCM — we wrap it in a WAV header (stdlib `wave`)
so the existing aplay-based player can read it.
"""

import tempfile
import time
import wave
from pathlib import Path
from typing import Optional

from openai import OpenAI

from .base import TTSClient


class OpenRouterTTS(TTSClient):
    def __init__(self, api_key: str, model: str, voice: str, sample_rate: int = 24000):
        self.model = model
        self.voice = voice
        self.sample_rate = sample_rate
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def synthesize(self, text: str, output_path: Optional[str | Path] = None) -> Path:
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"tts_{int(time.time() * 1000)}.wav"
        output_path = Path(output_path)

        with self._client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="pcm",
        ) as resp:
            pcm_bytes = resp.read()

        with wave.open(str(output_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(pcm_bytes)

        return output_path
