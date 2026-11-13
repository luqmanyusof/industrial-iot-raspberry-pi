# Op SENTINEL — running the outposts

The three outposts for the Day 3 afternoon project ([sentinel.md](../../sentinel.md)) are served by the **ESP32 plant**,
next to the PS-01 registers, on `192.168.4.1` port `502`. Nothing extra needs to run: they start with the firmware
(`plant/`), so every Pi already reaches them over the plant Wi-Fi.

| Outpost | Registers |
|---|---|
| ALPHA | IR10–IR13, DI10–DI12 |
| BRAVO | IR20–IR23, DI20–DI22 |
| CHARLIE | IR30–IR33, DI30–DI32 |

Check from any station: `python outpost_read.py`.

## Creating events

Keep the ESP32 connected to your laptop by USB and open its serial monitor at **115200 baud**, for example from the
`plant/` folder: `pio device monitor`. Type a command and press **Enter**. Outposts are `alpha`, `bravo`, `charlie`.
The ESP32 answers `INJECT …` to confirm.

| Command | Effect | What participants should see |
|---|---|---|
| `status` | Prints all three outposts | — |
| `leak <outpost>` | Fuel falls about 15 % a minute | Fuel gauge dropping, then *Fuel low* |
| `refuel <outpost>` | Fuel back to 95 %, leak fixed, generator on | *CLEARED* |
| `genfail <outpost>` | Generator stops; shelter warms up | *Generator stopped*; a few minutes later the shelter passes 35 °C |
| `genstart <outpost>` | Generator restarts (if it has fuel) | *CLEARED* |
| `gate <outpost>` | Opens or shuts the perimeter gate | *Gate left open* after 2 minutes |
| `resupply <outpost>` | Water back to 95 % | — |
| `silence <outpost>` | Link lost: values freeze, link bit 0, data age grows | Link `lost`, *Outpost link lost* after 60 s |
| `restore <outpost>` | Link back | Link `up`, *CLEARED* |

Without any events, fuel falls about 0.6 % a minute while a generator runs, so CHARLIE (starting at 34 %) reaches
20 % after roughly 25 minutes, and patrols open a gate for 20 seconds now and then. Restarting the ESP32 resets
all three outposts.

## A suggested afternoon

| When | Event |
|---|---|
| After everyone's dashboard shows all three outposts | `silence bravo` for two minutes, then `restore bravo` |
| Later | `leak alpha`, wait for the emails, then `refuel alpha` |
| Later | `genfail charlie`; leave it until the shelter passes 35 °C, then `genstart charlie` |
| Before the debrief | `gate bravo`, wait three minutes, `gate bravo` again |

## Practising without the ESP32

`sentinel_sim.py` is a copy of the outposts with the same registers, written in Python. Run it on any Pi, point
programs at `127.0.0.1` port `5020`, and type the same commands into it.
