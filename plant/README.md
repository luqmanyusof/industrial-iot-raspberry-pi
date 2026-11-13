# PS-01 plant firmware (ESP32)

The shared field device for the course. It runs the plant Wi-Fi network `PS01-PLANT` (192.168.4.1) and a
Modbus TCP server on port 502. Flash it once onto the ROBO ESP32 from the ESP32 kit, before Day 1.

## Hardware

| Kit part | Plant role | Where it plugs in |
|---|---|---|
| Rotary angle sensor | Tank level | Grove ADC1 port (D32/D33) |
| Crowtail DHT11 | Pump room temperature and humidity | Grove Port 3 (D26/D25) |
| Onboard button D34 | E-STOP (latches) | onboard |
| Onboard button D35 | RESET (clears the e-stop) | onboard |
| Onboard NeoPixels | Stack light | onboard |
| Onboard buzzer | Alarm horn | onboard (mute switch silences it) |
| TS90A servo | Outlet valve | servo header 1 (D4) |
| OLED SSD1315 | Local display | Grove Port 2 (I2C, D21/D22) |

Pins live in `src/config.h`. Set your own Wi-Fi password there before flashing.

## Build and flash

1. Install [PlatformIO](https://platformio.org/install) (VS Code extension or `pip install platformio`).
2. Edit `PLANT_PASSWORD` in `src/config.h`.
3. Connect the ROBO ESP32 by USB, then from this folder: `pio run -t upload`
4. Watch it start: `pio device monitor`. You should see `Plant Wi-Fi PS01-PLANT up at 192.168.4.1`.

## Check it before class

- Join `PS01-PLANT` from a laptop, then read the registers with `code/day2/modbus_read.py --host 192.168.4.1`.
- Turn the knob: `tank_level` follows. Breathe on the DHT11: `room_temp` rises.
- Press D34: the light flashes red and the horn sounds. Press D35 to reset.
- Connect all three Pis at once and run `modbus_read.py` on each, to confirm the access point passes traffic
  between Wi-Fi clients and serves several Modbus clients together.

## Register map

See the table at the top of `src/main.cpp`; Day 2, Topic 7 explains it.
