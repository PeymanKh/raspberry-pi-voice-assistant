"""Hardware integration test.

Exercises every component (LED + LDR combo, DHT11, talk button, PIR
motion sensor, USB mic, speaker) and prints a coloured pass/fail
summary. Run this before a demo to catch a loose wire fast.

Run from the project root, with venv active:

    python tests/test_hardware.py
"""

import subprocess
import sys
from pathlib import Path
from time import sleep

import yaml
from gpiozero import LED, Button, DigitalInputDevice, MotionSensor


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


def test_led_and_ldr() -> bool:
    """Combined test: toggle LED and verify the LDR (placed next to it) follows.

    Polarity baked in from tuning:
      LDR = 1 → DARK
      LDR = 0 → LIGHT (LED shining on it)
    """
    led = LED(g["led"])
    ldr = DigitalInputDevice(g["ldr"])

    print("  step 1: LED off → expect LDR=1 (DARK)")
    led.off()
    sleep(2)
    off1 = ldr.value
    print(f"    LDR={off1}")

    print("  step 2: LED on → expect LDR=0 (LIGHT)")
    led.on()
    sleep(2)
    on = ldr.value
    print(f"    LDR={on}")

    print("  step 3: LED off → expect LDR=1 (DARK) again")
    led.off()
    sleep(2)
    off2 = ldr.value
    print(f"    LDR={off2}")

    return off1 == 1 and on == 0 and off2 == 1


def test_dht11() -> bool:
    """Read temperature and humidity from the DHT11. Retries a few times — DHT11 is flaky on first reads."""
    import adafruit_dht
    import board

    pin_attr = f"D{g['dht']}"
    dht = adafruit_dht.DHT11(getattr(board, pin_attr))
    print(f"  reading DHT11 on GPIO {g['dht']} (may need a few retries)...")
    try:
        for i in range(10):
            try:
                t = dht.temperature
                h = dht.humidity
                if t is not None and h is not None:
                    print(f"  temperature={t}°C  humidity={h}%")
                    return True
                print(f"    retry {i+1}: got None")
            except RuntimeError as e:
                print(f"    retry {i+1}: {e}")
            sleep(2)
        return False
    finally:
        try:
            dht.exit()
        except Exception:
            pass


def test_talk_button() -> bool:
    btn = Button(g["button_talk"])
    print("  press the TALK button within 8s...")
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

    step("LED + LDR (combined)",  test_led_and_ldr)
    step("DHT11 (temp/humidity)", test_dht11)
    step("Talk button",           test_talk_button)
    step("PIR motion sensor",     test_motion)
    step("Microphone + speaker",  test_audio)

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
