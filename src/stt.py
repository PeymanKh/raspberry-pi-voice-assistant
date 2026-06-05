"""
Speech-to-text via OpenRouter.

OpenRouter's /api/v1/audio/transcriptions endpoint is NOT OpenAI-SDK
compatible — it expects a JSON body with base64-encoded audio, not a
multipart file upload. So we use `requests` directly.

Docs: https://openrouter.ai/docs/api/api-reference/transcriptions/create-audio-transcriptions
"""

import base64
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from .config_loader import settings


load_dotenv()

_URL = "https://openrouter.ai/api/v1/audio/transcriptions"


def transcribe(audio_path: str | Path, language: str = "en") -> str:
    """Transcribe a WAV file and return the text."""
    audio_path = Path(audio_path)
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = settings()["models"]["stt"]

    with open(audio_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    resp = requests.post(
        _URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "language": language,
            "input_audio": {"data": b64, "format": "wav"},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["text"]
