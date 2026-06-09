"""
OpenRouter speech-to-text client.

OpenRouter's /api/v1/audio/transcriptions endpoint isn't OpenAI-SDK
compatible — it wants a JSON body with base64-encoded audio rather than
a multipart upload. So we hit it directly with `requests`.

Docs: https://openrouter.ai/docs/api/api-reference/transcriptions/create-audio-transcriptions
"""

import base64
import json
from pathlib import Path
from typing import Optional

import requests

from .base import STTClient


_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
_REFERER = "https://github.com/PeymanKh/raspberry-pi-voice-assistant"
_TITLE = "Raspberry Pi Voice Assistant"


class OpenRouterSTT(STTClient):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def transcribe(self, audio_path: str | Path, language: Optional[str] = None) -> str:
        audio_path = Path(audio_path)
        with open(audio_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        body: dict = {
            "model": self.model,
            "input_audio": {"data": b64, "format": "wav"},
        }
        if language:
            body["language"] = language

        resp = requests.post(
            _URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": _REFERER,
                "X-OpenRouter-Title": _TITLE,
            },
            data=json.dumps(body),
            timeout=60,
        )
        if not resp.ok:
            raise RuntimeError(f"OpenRouter STT {resp.status_code}: {resp.text}")
        return resp.json()["text"]
