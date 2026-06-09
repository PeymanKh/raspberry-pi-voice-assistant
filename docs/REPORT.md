# Raspberry Pi Voice Assistant — Project Report

**Author:** Peyman Khodabandehlouei
**Course:** AI Engineering

## What is this project?

I built a small voice assistant that runs on a Raspberry Pi 3. You press a button, talk to it, and an AI replies through a speaker. The AI can also read sensors and control physical things — for example, it can tell you the temperature of the room or turn a small light on and off. When someone walks past the Pi, a motion sensor wakes it up and it plays a welcome message.

The goal was to take the kind of cloud AI you would use on a phone, and connect it to real hardware so it can actually feel the world and act on it.

## Hardware

I used the following components, all wired directly to the Raspberry Pi's GPIO pins on a small breadboard:

| Component | Pin | What it does |
|---|---|---|
| Push button | GPIO 4 | Press and hold to talk to the AI |
| PIR motion sensor | GPIO 17 | Detects when a person walks near the device |
| DHT11 sensor | GPIO 27 | Reads the room's temperature and humidity |
| LDR module (with comparator) | GPIO 22 | Detects whether the LED is on or off |
| LED | GPIO 18 | A small light the AI can switch on or off |
| USB microphone | USB port | The AI hears you through this |
| 3.5 mm speaker | Audio jack | The AI talks back through this |

The LED and the LDR are placed right next to each other, so the LDR can physically sense whether the LED is shining. This way the AI checks reality through a sensor, instead of trusting its own memory.

## Software architecture

I tried to keep the code organised in layers, so each part has one clear job:

```
src/
├── hardware.py       # Talks to the GPIO pins and sensors
├── audio.py          # Records from the mic and plays through the speaker
├── db.py             # Saves chat history in a small SQLite database
├── clients/          # Connects to the AI providers (STT, TTS, LLM)
│   ├── base.py       # Abstract classes — easy to swap providers later
│   └── openrouter_*  # Current implementations (all use OpenRouter)
├── tools/            # Functions the AI is allowed to call
│   ├── set_led.py
│   ├── get_led_state.py
│   ├── get_temperature.py
│   └── get_humidity.py
├── handlers/         # What happens when a user presses TALK / a person walks by
│   ├── talk.py
│   └── presence.py
└── logger.py         # One clean logging format for the whole program
main.py               # Wires everything together (small entry point)
```

`main.py` does almost nothing — it just connects the button and the motion sensor to the right handler, then keeps the program alive. The actual work happens in the handlers, which call into the clients and the tools.

## How it works (step by step)

1. **You press and hold the button** and start speaking.
2. The Pi records audio through the USB microphone using ALSA's `arecord`.
3. When you release the button, the audio file is sent to **OpenRouter's speech-to-text API** (currently GPT-4o transcribe).
4. The transcript is added to the chat history and sent to a **Google Gemini Flash Lite** model along with the previous turns and the list of available **tools**.
5. The model decides whether to answer directly, or to **call a tool first** — for example, if you asked about the temperature, it calls `get_temperature()` which reads the DHT11. If you asked about the light, it first calls `get_led_state` (which physically looks at the LDR) and only calls `set_led` if a change is actually needed.
6. The final text reply is sent to **Google's Gemini TTS** model, which sends back the audio of the assistant's voice.
7. That audio is played back through the speaker.
8. The full conversation (with tool calls preserved) is saved to a small SQLite database, so the AI remembers the context across turns.

Recordings shorter than 2 seconds are treated as accidental presses, so the AI plays a short "that was too short" clip instead of wasting an API call. The motion sensor plays a welcome message at most once every 5 minutes so it doesn't get annoying.

## Tools the AI can use

The AI does not control the hardware directly. Instead, I gave it **four small Python functions** that it can call as JSON tool calls. The system prompt teaches it when to use each:

- `get_temperature` — reads the DHT11 and returns a number in °C.
- `get_humidity` — same sensor, returns a percentage.
- `get_led_state` — reads the LDR to find out whether the LED is on.
- `set_led` — turns the LED on or off.

This is the same pattern OpenAI uses for function calling. The benefit is that the AI is "blind" to the hardware — it only sees the function names and their descriptions. If I ever change the temperature sensor from DHT11 to something else, the prompt and the model don't need to change at all.

## Why I split clients into a base class

The three AI clients (STT, TTS, LLM) each inherit from a base class in `clients/base.py`. Right now all of them use OpenRouter, but if I ever want to switch to OpenAI, Groq or a local model, I only need to write a new subclass — the rest of the program doesn't change. This is a small piece of work that makes the project easier to extend later.

## Challenges I had to solve

- **GPIO pin conflicts.** When two parts of the code tried to use the same pin, the second one would crash with "GPIO busy". I fixed this with a single `hardware.py` module that owns one instance per pin.
- **The DHT11 is unreliable.** The first read often fails. I added a small retry loop with a one-second delay.
- **The LDR's threshold.** The blue trim pot was extremely sensitive. I wrote a small tuning script that toggles the LED on and off and prints the LDR's reading, so I could turn the pot until "LED on" and "LED off" produced different values reliably.
- **Recording duration was wrong.** When I killed `arecord` on a quick tap, the WAV header still said the full duration. I fixed it by computing the duration from the actual file size instead of the (sometimes stale) header.
- **OpenRouter audio endpoints.** They are not quite OpenAI-SDK compatible for transcription (they want base64 JSON, not a multipart upload). I had to read the API docs carefully and use `requests` directly for STT, while TTS works fine with the OpenAI SDK.

## What I learned

This project taught me how to combine three things I had only studied separately before: cloud AI APIs, embedded hardware, and a clean Python codebase. I learned that the *interface* between layers matters more than any single layer — once I had clean abstractions for clients, tools, and handlers, adding new sensors became almost trivial.

I also learned how important small details are in a hardware project. A loose ground wire, a tiny trim pot half a turn off, or a misread WAV header can all silently break the whole pipeline.

## Future improvements

- Add a small camera so the AI can describe what it sees.
- Add a wake-word so the user does not have to press a button.
- Store sensor readings over time so the AI can answer questions like "was it warmer yesterday morning?"
- Run a smaller LLM directly on the Pi to reduce network dependency.
