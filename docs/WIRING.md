# Wiring Reference

Components (in wiring order): **talk button → BME280 → BH1750 → PIR → red LED.**

## Strategy: one rail = GND, central columns for everything else

A typical breadboard has two side rails (`+` and `−`). We use **only one**, as the **GND (`−`) rail**, because every single component needs GND. For the few things that need to be shared but aren't GND (3.3V to both I²C sensors, SDA/SCL to both I²C sensors), we use regular breadboard **center columns** as small branching points — one Pi jumper drops into a column, two sensor jumpers tap the same column. Same idea as a rail, just shorter.

## Before you start

1. Enable I²C on the Pi (one-time):

   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable → reboot
   ```

2. Pick a side rail and dedicate it to GND. Mark it with a piece of tape if you want.

3. Have on hand: 220 Ω resistor (red LED), male-to-male and male-to-female jumpers, 1× tactile button.

## Setup the GND rail (do this first)

A single wire turns the rail into GND. Every black/ground wire then taps the rail.

| Pi pin | Pi label | Goes to        |
| -----: | -------- | -------------- |
|      6 | GND      | `−` rail (any hole) |

## At a glance

| # | Component        | Wire         | Pi side / Rail / Column                |
| - | ---------------- | ------------ | -------------------------------------- |
| 1 | Talk button A    | signal       | GPIO 25 — **pin 22**                   |
| 1 | Talk button B    | GND          | `−` rail                               |
| 2 | BME280 VCC       | 3.3 V        | shared column **V33** (← from pin 1)   |
| 2 | BME280 GND       | GND          | `−` rail                               |
| 2 | BME280 SDA       | I²C data     | shared column **SDA** (← from pin 3)    |
| 2 | BME280 SCL       | I²C clock    | shared column **SCL** (← from pin 5)    |
| 3 | BH1750 VCC       | 3.3 V        | shared column **V33** (same as BME280)  |
| 3 | BH1750 GND       | GND          | `−` rail                               |
| 3 | BH1750 SDA       | I²C data     | shared column **SDA**                  |
| 3 | BH1750 SCL       | I²C clock    | shared column **SCL**                  |
| 4 | PIR VCC          | 5 V          | **pin 2** — direct jumper (no rail!)   |
| 4 | PIR GND          | GND          | `−` rail                               |
| 4 | PIR OUT          | signal       | GPIO 24 — **pin 18**                   |
| 5 | Red LED + (long) | signal       | 220 Ω → GPIO 18 — **pin 12**           |
| 5 | Red LED − (short)| GND          | `−` rail                               |

**Three "shared columns"** on the breadboard (any 3 unused center columns will do):

| Column label | Pi feeder jumper        | Then BME280 + BH1750 each plug their matching pin into this column |
| ------------ | ----------------------- | ------------------------------------------------------------------ |
| **V33**      | Pi pin 1  (3.3V) → col  | BME280 `VCC`, BH1750 `VCC`                                          |
| **SDA**      | Pi pin 3  (GPIO 2) → col| BME280 `SDA`, BH1750 `SDA`                                          |
| **SCL**      | Pi pin 5  (GPIO 3) → col| BME280 `SCL`, BH1750 `SCL`                                          |

That's the trick: one wire from Pi → column → both sensors tap the column.

## Total Pi jumpers (count check — should be 8)

| # | Pi pin | Purpose                       |
| - | -----: | ----------------------------- |
| 1 |      1 | 3.3 V → V33 column            |
| 2 |      2 | 5 V → PIR VCC (direct)        |
| 3 |      3 | SDA (GPIO 2) → SDA column     |
| 4 |      5 | SCL (GPIO 3) → SCL column     |
| 5 |      6 | GND → `−` rail                |
| 6 |     12 | GPIO 18 → LED (via 220 Ω)     |
| 7 |     18 | GPIO 24 → PIR OUT             |
| 8 |     22 | GPIO 25 → talk button signal  |

## 40-pin header map (only what we use is highlighted)

```
                          ┌─────────┐
       3V3 → V33 col ────┤ 1     2 ├── 5V          → PIR VCC (direct)
                  GPIO2 ──┤ 3     4 ├── 5V          ← SDA → SDA col
                  GPIO3 ──┤ 5     6 ├── GND         ← SCL → SCL col | GND → − rail
                  GPIO4 ──┤ 7     8 ├── GPIO14
                    GND ──┤ 9    10 ├── GPIO15
                 GPIO17 ──┤11    12 ├── GPIO18      → Red LED (via 220Ω)
                 GPIO27 ──┤13    14 ├── GND
                 GPIO22 ──┤15    16 ├── GPIO23
                    3V3 ──┤17    18 ├── GPIO24      ← PIR OUT
                 GPIO10 ──┤19    20 ├── GND
                  GPIO9 ──┤21    22 ├── GPIO25      ← Talk button signal
                 GPIO11 ──┤23    24 ├── GPIO8
                    GND ──┤25    26 ├── GPIO7
                  GPIO0 ──┤27    28 ├── GPIO1
                  GPIO5 ──┤29    30 ├── GND
                  GPIO6 ──┤31    32 ├── GPIO12
                 GPIO13 ──┤33    34 ├── GND
                 GPIO19 ──┤35    36 ├── GPIO16
                 GPIO26 ──┤37    38 ├── GPIO20
                    GND ──┤39    40 ├── GPIO21
                          └─────────┘
```

Physical pin 1 = corner nearest the SD card slot (labeled 3.3 V on the silkscreen).

## Component-by-component

### 1. Talk button (GPIO 25, pin 22)

```
Pi pin 22 ── one leg of the button
− rail    ── other leg of the button
```

No resistor — `gpiozero.Button(pin, pull_up=True)` enables the internal pull-up. Pick any two legs on opposite sides of a tactile button.

### 2. BME280 — temperature, humidity, air pressure (I²C, address `0x76`)

```
VCC → V33 column
GND → − rail
SDA → SDA column
SCL → SCL column
```

3.3 V module. If yours has an SDO pin, leave it floating for `0x76` (or tie SDO to VCC for `0x77`).

### 3. BH1750 — ambient light in lux (I²C, address `0x23`)

```
VCC → V33 column
GND → − rail
SDA → SDA column
SCL → SCL column
ADDR → leave floating  (= address 0x23, default)
```

Sharing pins with BME280 is fine — different I²C addresses, no conflict.

### 4. PIR motion sensor — HC-SR501 (GPIO 24, pin 18)

```
VCC (red)    → Pi pin 2 (5 V)  ← direct jumper, NOT a rail or column
GND (black)  → − rail
OUT (yellow) → Pi pin 18 (GPIO 24)
```

Keep the 5 V wire *off* the breadboard rails entirely — if 5 V ever touches a 3.3V pin, the BME280 and BH1750 die instantly. A single male-to-female jumper from Pi pin 2 straight to the PIR's VCC is the safest path.

On the back of the HC-SR501: two orange trim pots (sensitivity + delay) at the middle, jumper on **H**. Wait ~30–60 s after power-on before testing.

### 5. Red LED — AI-controlled (GPIO 18, pin 12)

```
Pi pin 12 ── 220 Ω resistor ── LED anode (long leg)
                                LED cathode (short leg) ── − rail
```

220–470 Ω is fine. Long leg = `+`, short leg = `−`.

## Sanity check after wiring

```bash
# Confirm both I²C sensors are visible
sudo i2cdetect -y 1
```

You should see `23` and `76` in the grid — that's BH1750 and BME280. If either is missing, double-check that sensor's VCC and GND first (those are by far the most common mistake), then SDA/SCL.

Then run the per-component test (after we add sensor code to it):

```bash
cd ~/voice-agent
source .venv/bin/activate
python tests/test_hardware.py
```
