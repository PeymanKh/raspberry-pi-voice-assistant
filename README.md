# Raspberry Pi Voice Assistant

A voice-driven AI assistant running on a Raspberry Pi 3. Hold the **talk** button, speak, and the assistant transcribes (Whisper via OpenRouter), runs the LLM (Gemini 3.1 Flash Lite via OpenRouter), and speaks back (Gemini TTS via OpenRouter). The LLM can control physical hardware (the red LED) through tool calling. A PIR motion sensor greets people who approach.

## Features

1. **Conversational AI** — hold a button to talk, speak, get a spoken answer
2. **Tool use** — the AI can turn the red LED on/off via function calling
3. **Chat history** — persisted in SQLite across runs
4. **Greeting on approach** — PIR motion sensor triggers a welcome message (rate-limited to once every 5 minutes)

## Hardware

| Component         | GPIO | Notes              |
|-------------------|------|--------------------|
| Red LED           | 18   | AI-controlled (tool) |
| Talk button       | 25   | Hold-to-talk       |
| PIR motion sensor | 24   | Greeting trigger   |
| USB microphone    | —    | Plug into any USB port |
| Speaker (3.5mm)   | —    | Plug into headphone jack |

See `configs/settings.yaml` for the full pin map and audio device names, and `docs/WIRING.md` for the physical pin diagram.

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

Drop a `welcome.wav` (16-bit PCM mono, any reasonable rate) into `assets/`; it's what plays on motion. If missing, the assistant falls back to a TTS greeting.

## Verify the hardware

One command exercises every component and prints a pass/fail summary:

```bash
python tests/test_hardware.py
```

You'll be prompted to press the talk button and wave at the PIR; the speaker will play back a 3-second recording from the mic at the end.

## Run the assistant

```bash
python main.py
```

Hold the talk button, speak for at least 5 seconds, release. Recordings shorter than 5 seconds are treated as noise and discarded.

## Project structure

```
raspberry-pi-voice-assistant/
├── README.md
├── requirements.txt
├── .env / .env.example          # OPENROUTER_API_KEY
├── main.py                      # orchestrator
│
├── configs/
│   └── settings.yaml            # GPIO pins, audio device names, model IDs
│
├── prompts/
│   └── system/assistant.md      # system prompt
│
├── src/
│   ├── audio.py                 # arecord/aplay wrappers + hold-to-talk recorder
│   ├── config_loader.py         # cached settings() loader
│   ├── hardware.py              # shared GPIO singletons
│   ├── stt.py                   # speech-to-text via OpenRouter
│   ├── llm.py                   # chat + set_led tool calling
│   ├── tts.py                   # text-to-speech via OpenRouter
│   └── db.py                    # SQLite chat history
│
├── assets/                      # welcome.wav goes here
├── data/                        # chat.db (auto-created, gitignored)
└── tests/
    ├── test_hardware.py         # smoke-test every component
    ├── smoke_stt.py             # STT round trip
    ├── smoke_tts.py             # TTS round trip
    ├── smoke_llm.py             # LLM + tool calling
    └── smoke_db.py              # DB CRUD
```
