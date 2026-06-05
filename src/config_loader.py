"""
Load configs/settings.yaml once per process.
"""

from functools import lru_cache
from pathlib import Path

import yaml


_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "configs" / "settings.yaml"


@lru_cache(maxsize=1)
def settings() -> dict:
    """Return the parsed settings.yaml (cached)."""
    with open(_SETTINGS_PATH) as f:
        return yaml.safe_load(f)
