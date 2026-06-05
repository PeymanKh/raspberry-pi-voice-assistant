"""
Speech-to-text via OpenRouter.

OpenRouter's /api/v1/audio/transcriptions endpoint is NOT OpenAI-SDK
compatible — it expects a JSON body with base64-encoded audio. We use
`requests` directly.

Docs: https://openrouter.ai/docs/api/api-reference/transcriptions/create-audio-transcriptions
"""

import base64
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from .config_loader import settings


load_dotenv()

_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
_REFERER = "https://github.com/PeymanKh/raspberry-pi-voice-assistant"
_TITLE = "Raspberry Pi Voice Assistant"


def transcribe(audio_path: str | Path, language: str | None = None) -> str:
    """Transcribe a WAV file and return the text. Language is auto-detected if None."""
    audio_path = Path(audio_path)
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = settings()["models"]["stt"]

    with open(audio_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    body: dict = {
        "model": model,
        "input_audio": {"data": b64, "format": "wav"},
    }
    if language:
        body["language"] = language

    resp = requests.post(
        _URL,
        headers={
            "Authorization": f"Bearer {api_key}",
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
