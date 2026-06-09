"""
Abstract base classes for the three AI clients.

Each provider (OpenRouter, OpenAI direct, Groq, etc.) implements these
three interfaces. The rest of the codebase only ever sees the bases —
swap providers by changing what's instantiated in `clients/__init__.py`.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class STTClient(ABC):
    """Speech-to-text. Takes a WAV path, returns text."""

    @abstractmethod
    def transcribe(self, audio_path: str | Path, language: Optional[str] = None) -> str:
        ...


class TTSClient(ABC):
    """Text-to-speech. Synthesise WAV; `speak()` synthesises and plays."""

    @abstractmethod
    def synthesize(self, text: str, output_path: Optional[str | Path] = None) -> Path:
        ...

    def speak(self, text: str) -> None:
        from ..audio import play
        path = self.synthesize(text)
        play(path)


class LLMClient(ABC):
    """Chat completion with tool calling.

    `chat()` should run any tool calls internally and return only the final
    assistant text plus the updated message history.
    """

    @abstractmethod
    def chat(
        self,
        message: str,
        history: Optional[list[dict]] = None,
    ) -> tuple[str, list[dict]]:
        ...
