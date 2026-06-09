"""
SQLite chat history.

Stores every message in full — user prompts, assistant replies, assistant
messages with `tool_calls`, AND the matching `tool` results. We need all of
them: if we replay an assistant message that carries `tool_calls` without
its corresponding `tool` results immediately after, OpenRouter / OpenAI
errors with "tool_call_id ... has no matching tool_calls".

Schema:
    messages(id, role, payload, created_at)
where `payload` is the full JSON message dict (role, content, tool_calls,
tool_call_id, etc.). Storing the raw dict keeps us forward-compatible with
any new fields the API adds (e.g. reasoning_details).

The DB lives at <project_root>/data/chat.db. Directory and table are
created on first use.

NOTE: schema changed from an earlier version. If you have an old
data/chat.db lying around, delete it.
"""

import json
import time
import sqlite3
from pathlib import Path


_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "chat.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    created_at REAL    NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def add_message(msg: dict) -> None:
    """Append a full message dict (role + content + optional tool_calls / tool_call_id)."""
    role = msg.get("role")
    if not role:
        raise ValueError("message missing 'role'")
    payload = json.dumps(msg)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (role, payload, created_at) VALUES (?, ?, ?)",
            (role, payload, time.time()),
        )


def add_messages(msgs: list[dict]) -> None:
    """Bulk insert. Used after chat() to persist a turn's new messages in order."""
    rows = [(m["role"], json.dumps(m), time.time()) for m in msgs]
    with _connect() as conn:
        conn.executemany(
            "INSERT INTO messages (role, payload, created_at) VALUES (?, ?, ?)",
            rows,
        )


def get_history(limit: int = 20) -> list[dict]:
    """
    Return up to the last `limit` messages, oldest first.

    Trims leading orphan messages (anything before the first 'user' role) so
    we never replay an `assistant`+`tool_calls` or a `tool` message whose
    paired counterpart was cut off by the limit. This may return fewer than
    `limit` messages.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT payload FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    msgs = [json.loads(p) for (p,) in reversed(rows)]
    while msgs and msgs[0].get("role") != "user":
        msgs.pop(0)
    return msgs


def clear() -> None:
    """Delete all chat history."""
    with _connect() as conn:
        conn.execute("DELETE FROM messages")


def count_messages() -> int:
    """Count user turns (i.e. how many times the user has spoken). Used for TTS announcements."""
    with _connect() as conn:
        (n,) = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE role = 'user'"
        ).fetchone()
    return n
