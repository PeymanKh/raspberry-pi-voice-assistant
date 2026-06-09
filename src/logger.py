"""
Centralised logging.

One format, one place. Modules do:

    from .logger import get_logger
    log = get_logger("talk")
    log.info("button pressed")

Output:

    12:34:56  talk      button pressed
    12:34:57  stt       transcribing
    12:34:59  stt       transcript: what is the temperature
    12:34:59  llm       chat sent (history=4)
    12:35:00  tool      get_temperature() -> {"temperature_c": 22.4}
    12:35:01  llm       reply: it is about 22 degrees in here
    12:35:01  tts       playing
"""

import logging
import sys


_FORMAT = "%(asctime)s  %(name)-8s  %(message)s"
_DATEFMT = "%H:%M:%S"

# ANSI escapes — only used when stderr is an interactive terminal.
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
        # Dim just the timestamp so the eye lands on the source + message.
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
    # Quiet noisy 3rd-party libraries — we only want to hear about errors.
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name)
