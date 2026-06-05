"""
Smoke test for the LLM module.

Sends three turns:
  1. "Turn on the red light." -> should trigger set_led("on"), LED lights up
  2. "Thanks. Now turn it off." -> should trigger set_led("off"), LED dark
  3. "Where is the Eiffel Tower?" -> plain text answer, no tool call

Run from project root:
    python -m tests.smoke_llm
"""

import time

from src.llm import chat


def step(message: str, history: list) -> list:
    print(f"\n>>> {message}")
    reply, history = chat(message, history)
    print(f"<<< {reply}")
    return history


def main() -> None:
    history: list = []
    history = step("Turn on the red light.", history)
    time.sleep(1.5)
    history = step("Thanks. Now turn it off.", history)
    time.sleep(0.5)
    history = step("Where is the Eiffel Tower?", history)
    print(f"\nFinal history has {len(history)} messages.")


if __name__ == "__main__":
    main()
