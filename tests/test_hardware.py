"""Hardware integration test.

Exercises every component (LEDs, buzzer, both buttons, PIR motion
sensor, USB mic, speaker) and prints a coloured pass/fail summary.

Run from the project root, with venv active:

    python tests/test_hardware.py
"""

import subprocess
import sys
from pathlib import Path
from time import sleep

import yaml
from gpiozero import LED, Button, Buzzer, MotionSensor


# Make src importable when running from project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

cfg = yaml.safe_load(open("configs/settings.yaml"))
g, a = cfg["gpio"], cfg["audio"]

GREEN, RED, DIM, END = "\033[92m", "\033[91m", "\033[2m", "\033[0m"
PASS = f"{GREEN}✓ PASS{END}"
FAIL = f"{RED}✗ FAIL{END}"

results: list[tuple[str, bool]] = []


def header(text: str) -> None:
    print(f"\n{'=' * 60}\n  {text}\n{'=' * 60}")


def step(name: str, fn) -> None:
    print(f"\n▶ {name}")
    try:
        ok = fn()
    except Exception as e:  # noqa: BLE001 - surface any exception
        ok = False
        print(f"  {DIM}error: {type(e).__name__}: {e}{END}")
    results.append((name, ok))
    print(f"  {PASS if ok else FAIL}")


# ── Tests ──────────────────────────────────────────────────────


def test_leds() -> bool:
    yellow, green, red = (
        LED(g["led_yellow"]),
        LED(g["led_green"]),
        LED(g["led_red"]),
    )
    print("  yellow → green → red, then all blink 2x")
    for led in (yellow, green, red):
        led.on(); sleep(0.5); led.off()
    for _ in range(2):
        yellow.on(); green.on(); red.on(); sleep(0.3)
        yellow.off(); green.off(); red.off(); sleep(0.3)
    return True


def test_buzzer() -> bool:
    buzzer = Buzzer(g["buzzer"])
    print("  3 short beeps")
    for _ in range(3):
        buzzer.on(); sleep(0.15); buzzer.off(); sleep(0.15)
    return True


def test_button(label: str, pin: int) -> bool:
    btn = Button(pin)
    print(f"  press the {label.upper()} button within 8s...")
    for _ in range(80):
        if btn.is_pressed:
            print("  detected")
            return True
        sleep(0.1)
    return False


def test_motion() -> bool:
    pir = MotionSensor(g["motion"])
    print("  wave at the PIR within 8s...")
    for _ in range(80):
        if pir.motion_detected:
            print("  detected")
            return True
        sleep(0.1)
    return False


def test_audio() -> bool:
    out = "/tmp/test_hardware.wav"
    print("  recording 3s — say something...")
    subprocess.run(
        [
            "arecord",
            "-D", f"plughw:CARD={a['mic_name']},DEV={a['mic_device']}",
            "-f", "S16_LE",
            "-r", str(a["sample_rate"]),
            "-c", str(a["channels"]),
            "-d", "3", out,
        ],
        check=True, capture_output=True,
    )
    print("  playing back...")
    subprocess.run(
        [
            "aplay",
            "-D", f"plughw:CARD={a['speaker_name']},DEV={a['speaker_device']}",
            out,
        ],
        check=True, capture_output=True,
    )
    return True


def main() -> int:
    header("Voice Assistant — Hardware Test")

    step("LEDs (yellow + green + red)", test_leds)
    step("Buzzer",                       test_buzzer)
    step("Talk button",                  lambda: test_button("talk",  g["button_talk"]))
    step("Reset button",                 lambda: test_button("reset", g["button_reset"]))
    step("PIR motion sensor",            test_motion)
    step("Microphone + speaker",         test_audio)

    header("Summary")
    for name, ok in results:
        print(f"  {PASS if ok else FAIL}  {name}")

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n  {passed}/{total} components OK\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  aborted by user")
        sys.exit(2)
