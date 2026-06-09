"""
LLM tool: play_tune — play a short rhythmic pattern on the active buzzer.

Active buzzer can only do on/off, no pitch — so each "tune" is a rhythm.
The agent picks a style based on the user's vibe.
"""

import time

from .. import hardware


# Each tune is a list of (on_seconds, off_seconds) tuples.
_TUNES = {
    "happy":     [(0.08, 0.06), (0.08, 0.06), (0.08, 0.06), (0.30, 0.0)],
    "victory":   [(0.07, 0.05)] * 5 + [(0.40, 0.0)],
    "alert":     [(0.20, 0.15), (0.20, 0.15), (0.20, 0.15)],
    "sad":       [(0.40, 0.30), (0.40, 0.0)],
    "shave":     [  # "shave and a haircut, two bits"
        (0.10, 0.07), (0.10, 0.07), (0.10, 0.07),
        (0.20, 0.10), (0.10, 0.30),
        (0.10, 0.07), (0.20, 0.0),
    ],
}


SPEC = {
    "type": "function",
    "function": {
        "name": "play_tune",
        "description": (
            "Play a short rhythmic tune on the buzzer. Use this when the user asks "
            "for a song, a beat, a beep, a jingle, music, a sound effect, or wants "
            "you to celebrate / alert / signal something."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": list(_TUNES.keys()),
                    "description": (
                        "happy = chirpy default; victory = celebration; alert = warning; "
                        "sad = slow descending; shave = 'shave and a haircut, two bits'."
                    ),
                }
            },
            "required": ["style"],
        },
    },
}


def run(style: str = "happy") -> dict:
    pattern = _TUNES.get(style, _TUNES["happy"])
    buz = hardware.buzzer()
    for on_s, off_s in pattern:
        if on_s > 0:
            buz.on()
            time.sleep(on_s)
            buz.off()
        if off_s > 0:
            time.sleep(off_s)
    return {"ok": True, "style": style}
