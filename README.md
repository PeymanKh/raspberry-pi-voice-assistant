# Raspberry Pi Voice Assistant

A voice-driven AI assistant running on a Raspberry Pi 3. Press the **talk** button → speak → the assistant transcribes (Whisper via OpenRouter), runs the LLM (Gemini 3 Flash via OpenRouter), speaks back (TTS via OpenRouter), and can control physical hardware (LEDs) as a tool.

## Features

1. **Conversational AI** — press a button to talk, speak, get an answer
2. **Tool use** — the AI can turn the red LED on/off via function calling
3. **Chat history** — stored in SQLite, reset with a second button
4. **Greeting on approach** — PIR motion sensor triggers a welcome message
5. **Error buzzer** — sounds when a backend call fails

## Hardware

| Component | GPIO | Notes |
|---|---|---|
| Yellow LED | 17 | Recording indicator |
| Green LED | 27 | AI processing indicator |
| Red LED | 18 | AI-controlled (tool) |
| Talk button | 25 | Press-to-talk |
| Reset button | 22 | Clear chat history |
| Active buzzer | 23 | Error indicator |
| PIR motion sensor | 24 | Greeting trigger |
| USB microphone | — | Plug into any USB port |
| Speaker (3.5mm) | — | Plug into headphone jack |

See `configs/settings.yaml` for the full pin map and audio device names.

## Setup

```bash
git clone git@github.com:PeymanKh/raspberry-pi-voice-assistant.git
cd raspberry-pi-voice-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Paste your OpenRouter API key into .env
```

## Verify the hardware

Single command exercises every component and prints a pass/fail summary:

```bash
python tests/test_hardware.py
```

You'll be prompted to press each button and wave at the PIR; the speaker will play back a 3-second recording from the mic at the end.

## Run the assistant

```bash
python main.py
```

## Project structure

```
raspberry-pi-voice-assistant/
├── README.md
├── requirements.txt
├── .env / .env.example          # OPENROUTER_API_KEY
│
├── configs/
│   └── settings.yaml            # GPIO pins + audio device names + model IDs
│
├── src/
│   ├── audio.py                 # record() / play() wrappers around arecord/aplay
│   ├── config_loader.py         # cached settings() loader
│   └── ...                      # more modules added as features land
│
└── tests/
    └── test_hardware.py         # smoke-test every component
```
