# assets/

Drop your welcome sound here as **`welcome.wav`**. It plays when the PIR motion sensor detects someone, rate-limited to once every 5 minutes (the cooldown resets when the RESET button is pressed).

Format: any WAV `aplay` can play. 16-bit PCM mono at 16 kHz or 24 kHz is a safe choice. Keep it short (a few seconds) since it blocks other handlers while playing.

If `welcome.wav` is missing, the assistant falls back to a TTS greeting.
