"""
Client singletons.

Importers get ready-to-use `stt`, `tts`, `llm` instances. To swap a
provider, change which class is instantiated below — the rest of the
codebase never touches a concrete provider class.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from ..config_loader import settings
from .openrouter_llm import OpenRouterLLM
from .openrouter_stt import OpenRouterSTT
from .openrouter_tts import OpenRouterTTS


load_dotenv()

_API_KEY = os.environ["OPENROUTER_API_KEY"]
_MODELS = settings()["models"]
_TTS_CFG = settings()["tts"]
_SYSTEM_PROMPT = (
    Path(__file__).resolve().parents[2] / "prompts" / "system" / "assistant.md"
)

stt = OpenRouterSTT(api_key=_API_KEY, model=_MODELS["stt"])

tts = OpenRouterTTS(
    api_key=_API_KEY,
    model=_MODELS["tts"],
    voice=_TTS_CFG["voice"],
    sample_rate=int(_TTS_CFG["sample_rate"]),
)

llm = OpenRouterLLM(
    api_key=_API_KEY,
    model=_MODELS["llm"],
    system_prompt_path=_SYSTEM_PROMPT,
)
