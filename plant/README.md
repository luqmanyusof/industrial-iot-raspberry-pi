# PS-01 plant firmware (ESP32)

The shared field device for the course. It runs the plant Wi-Fi network `plant-wifi` (192.168.4.1) and a
Modbus TCP server on port 502 with two sets of registers:

- **PS-01 pump station** (registers 0–3), driven by the real kit parts: Days 2 and 3.
- **Op SENTINEL outposts** ALPHA, BRAVO and CHARLIE (registers 10–33), simulated: the Day 3 afternoon project.
  See `src/sentinel.h`, and `code/sentinel/README.md` for creating events from the serial monitor.

Flash it once onto the ROBO ESP32 from the ESP32 kit, before Day 1.

## Hardware

| Kit part | Plant role | Where it plugs in |
|---|---|---|
| Rotary angle sensor | Tank level | Grove Port 5 (signal D32) |
| Crowtail DHT11 | Pump room temperature and humidity | Grove Port 3 (signal D25) |
| Onboard button D34 | E-STOP (latches) | onboard |
| Onboard button D35 | RESET (clears the e-stop) | onboard |
| Onboard NeoPixels | Pump lamps: LED 0 = pump 1, LED 1 = pump 2 (blue = running, red = stopped) | onboard |
| Onboard buzzer | Alarm horn (HIGH tank level, or E-STOP) | onboard (mute switch silences it) |
| TS90A servo | Outlet valve | servo header 1 (D4) |
| OLED SSD1315 | Local display | Grove Port 2 (I2C, D21/D22) |

Pins, the Wi-Fi name (`plant-wifi`) and password (`Plant0101`) live in `src/config.h`. The Day 1 notes print the same name and password: change both together.

## Build and flash

1. Install [PlatformIO](https://platformio.org/install) (VS Code extension or `pip install platformio`).
2. Connect the ROBO ESP32 by USB, then from this folder: `pio run -t upload`
3. Watch it start: `pio device monitor`. You should see `Plant Wi-Fi plant-wifi up at 192.168.4.1`.

## Check it before class

- Join `plant-wifi` from a laptop, then read the registers with `code/day2/modbus_read.py --host 192.168.4.1`.
- Turn the knob: `tank_level` follows. Breathe on the DHT11: `room_temp` rises.
- `code/day2/modbus_write.py --pump1 on`: LED 0 turns blue. `--pump1 off`: red again. Same for `--pump2`.
- Press D34: the valve shuts, the horn sounds and the OLED shows `E-STOP`. Press D35 to reset.
- Connect all three Pis at once and run `modbus_read.py` on each, to confirm the access point passes traffic
  between Wi-Fi clients and serves several Modbus clients together.
- Run `code/sentinel/outpost_read.py`: all three outposts show `link OK`. Type `silence bravo` in the serial
  monitor: BRAVO shows `link LOST` and its data age grows. Type `restore bravo`.

## Register map

PS-01: the table at the top of `src/main.cpp` (Day 2, Topic 7 explains it).
Op SENTINEL: the table at the top of `src/sentinel.h` (also in `sentinel.md`).
