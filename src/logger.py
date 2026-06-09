"""
Centralised logging.

Five categories, in CAPS down the left column:

    SYSTEM  — startup / shutdown messages from main.py
    SENSOR  — physical world events: motion, recording-too-short
    HUMAN   — what the user said (after transcription)
    AI      — what the assistant replied
    TOOL    — every tool call the agent makes, with args and result

Errors are red regardless of category.

Output:

    15:24:03  SYSTEM  ready
    15:24:18  SENSOR  motion — playing welcome
    15:25:16  HUMAN   how is the temperature in the room
    15:25:18  TOOL    get_temperature() -> {"temperature_c": 25.0}
    15:25:18  AI      It's about 25 degrees and a bit warm.
"""

import logging
import sys


_FORMAT = "%(asctime)s  %(name)-6s  %(message)s"
_DATEFMT = "%H:%M:%S"

_DIM = "\033[2m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_END = "\033[0m"


class _ColourFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if record.levelno >= logging.ERROR:
            return f"{_RED}{msg}{_END}"
        if record.levelno >= logging.WARNING:
            return f"{_YELLOW}{msg}{_END}"
        ts, _, rest = msg.partition("  ")
        return f"{_DIM}{ts}{_END}  {rest}"


_configured = False


def _configure_once() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stderr)
    fmt_cls = _ColourFormatter if sys.stderr.isatty() else logging.Formatter
    handler.setFormatter(fmt_cls(_FORMAT, _DATEFMT))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name)


# Pre-made loggers for the five categories. Modules just import these.
SYSTEM = get_logger("SYSTEM")
SENSOR = get_logger("SENSOR")
HUMAN = get_logger("HUMAN")
AI = get_logger("AI")
TOOL = get_logger("TOOL")
