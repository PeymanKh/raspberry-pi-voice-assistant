"""
Smoke test for the chat-history DB.

Verifies: full message persistence (including tool_calls and tool results),
ordering, user-turn counting, limit-based slicing without orphaning a
tool sequence, and clear().

Run from project root:
    python -m tests.smoke_db
"""

from src import db


def main() -> None:
    db.clear()
    assert db.count_messages() == 0

    # A full tool-calling turn, as llm.py would return it.
    db.add_messages(
        [
            {"role": "user", "content": "Turn on the red light."},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "set_led",
                            "arguments": '{"state": "on"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_abc123",
                "content": '{"ok": true, "state": "on"}',
            },
            {"role": "assistant", "content": "Done, the red light is on."},
        ]
    )

    # A plain text turn.
    db.add_messages(
        [
            {"role": "user", "content": "Where is the Eiffel Tower?"},
            {"role": "assistant", "content": "Paris, France."},
        ]
    )

    assert db.count_messages() == 2, f"expected 2 user turns, got {db.count_messages()}"

    history = db.get_history(limit=20)
    assert len(history) == 6, f"expected 6 messages, got {len(history)}"
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert "tool_calls" in history[1]
    assert history[2]["role"] == "tool"
    assert history[2]["tool_call_id"] == "call_abc123"
    assert history[-1]["content"] == "Paris, France."

    # Slicing test: ask for the last 3 messages.
    # Raw last 3 = [tool, assistant, user, assistant][-3:] = [assistant, user, assistant]
    # -> starts with 'assistant', so trim until 'user' -> [user, assistant]
    trimmed = db.get_history(limit=3)
    assert trimmed[0]["role"] == "user", f"trimmed should start at user, got {trimmed[0]['role']}"
    print(f"limit=3 trimmed to {len(trimmed)} messages starting at 'user' (safe).")

    print(f"\nTotal user turns: {db.count_messages()}")
    print(f"Full history ({len(history)} messages):")
    for m in history:
        snippet = m.get("content") or f"<tool_calls: {[tc['function']['name'] for tc in m.get('tool_calls', [])]}>"
        print(f"  [{m['role']}] {snippet}")

    db.clear()
    assert db.count_messages() == 0
    print("\nCleared. OK.")


if __name__ == "__main__":
    main()
