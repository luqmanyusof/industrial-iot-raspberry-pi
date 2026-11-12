# Day 1 — Raspberry Pi and Python

> **Today the Pi becomes a gateway you can trust:** you set it up without a screen, learn to drive it from the command line, and finish with a Python program that keeps running on its own, through crashes and reboots.

## Before you start

- [ ] Raspberry Pi, power supply and microSD card on your desk
- [ ] Raspberry Pi Imager 2.0 or later installed on your laptop
- [ ] VS Code installed, with the **Remote - SSH** extension
- [ ] The lab Wi-Fi name and password (on the whiteboard)
- [ ] Your Pi number from the trainer: `pi01` or `pi02`

**Our running use case:** *Stesen Pam PS-01*, a small water pump station. It has a storage tank (level in %), a pump motor (temperature in °C) and, from Day 2, a door switch and a pump relay. Your Pi is the station's edge gateway.

---

## Topic 1 — Single-Board Computers and IoT Architecture (concept)

**Goal:** know where a Raspberry Pi fits in an industrial system, so every lab after this has a place on the map.

### 1.1 — What is a Raspberry Pi?

A Raspberry Pi is a **single-board computer (SBC)**: a full computer on one board, with a processor, memory, networking, USB and a row of **GPIO** (General-Purpose Input/Output) pins. It runs a full **operating system (OS)**, Raspberry Pi OS, which is based on Debian Linux.

### 1.2 — Microcontroller or single-board computer?

| | Microcontroller (ESP32, Arduino) | Single-board computer (Raspberry Pi) |
|---|---|---|
| Operating system | None, or a tiny real-time OS | Full Linux |
| Boot time | Milliseconds | 20–40 seconds |
| Timing | Precise, predictable (real-time) | Good, but Linux can pause your program briefly |
| Power | Very low, can run on battery | Needs a steady power supply |
| Software | One program in C/C++ | Many programs, any language, databases, web servers |
| Typical job | Read sensors, control a motor, react in microseconds | Collect, store, secure and forward data; run dashboards and AI |

> **The rule of thumb:** a microcontroller is close to the machine and reacts fast. A single-board computer sits above several machines and thinks: it collects, decides and communicates. In this course the ESP32 plays the field device and the Pi plays the gateway.

### 1.3 — IoT architecture: device → edge → server

An **IoT** (Internet of Things) system moves data in three layers:

```
[ Devices ]  →  [ Edge gateway ]  →  [ Server / cloud ]
 sensors,        collects, filters,     stores history,
 switches,       secures and            dashboards, reports,
 actuators       forwards data          analytics
```

The **edge** is where the plant meets the network. Doing work at the edge, instead of sending every raw reading to a server, means the site keeps working when the network link is down, uses less bandwidth, and reacts faster.

### 1.4 — The industrial view: the Purdue model

Industry describes the same layers with the **Purdue model** (also used in the ISA-95 standard):

| Level | Name | Examples |
|---|---|---|
| 4 | Enterprise | ERP (Enterprise Resource Planning), email, business systems |
| 3 | Site operations | Historian database, production reports |
| 2 | Supervisory | **SCADA** (Supervisory Control and Data Acquisition), **HMI** (Human-Machine Interface) screens |
| 1 | Control | **PLC** (Programmable Logic Controller), controllers |
| 0 | Field | Sensors, switches, valves, motors, relays |

An **IIoT** (Industrial IoT) edge gateway usually sits between Level 1 and Level 2: it talks to field devices and controllers below, and to supervisory and site systems above. That is exactly where your Pi will sit.

> **Why the levels matter:** each level is a security boundary. Traffic should only pass between neighbouring levels, through controlled points. On Day 2 you will secure the link above your gateway.

**Try it**
1. On paper, map Stesen Pam PS-01 onto the five levels. Place: tank level sensor, pump motor, door switch, pump relay, your Raspberry Pi, the operator's dashboard, and the water utility's billing system.
2. Draw an arrow for each data flow and label it *read* or *command*.
3. Compare with your neighbour. Where did you disagree, and why?

**Checkpoint ✅** You can point to your Pi on the map and explain in one sentence what it does at that level.

---

## Topic 2 — Setting up the Raspberry Pi

**Goal:** a Pi that boots without a screen or keyboard, joins the lab Wi-Fi, and that you can control from your laptop over SSH and VS Code.

**Open:** Raspberry Pi Imager on your laptop.

### 2.1 — Write the OS to the microSD card

1. Insert the microSD card into your laptop (use the adapter if needed).
2. Open **Raspberry Pi Imager**.
3. **Device:** choose your Raspberry Pi model.
4. **OS:** choose **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**. Lite has no desktop; a gateway does not need one.
5. **Storage:** choose your microSD card. Double-check: everything on it will be erased.
6. Go through the customisation steps the wizard shows:

| Setting | Value |
|---|---|
| Hostname | Your Pi number, e.g. `pi01` |
| Localisation | Time zone `Asia/Kuala_Lumpur`, keyboard `us` |
| Username | `pelatih` |
| Password | Your own, at least 8 characters. Write it down. |
| Wi-Fi | The lab network name and password |
| Remote access | **Enable SSH**, with password authentication |

7. Write the card and wait for **verification** to finish.
8. Eject the card, put it into the Pi, then connect power. Wait about 90 seconds; the first boot takes longer than normal.

> **Why "headless"?** Equipment in the field rarely has a monitor attached. Setting up everything before the first boot is how gateways are deployed for real.

### 2.2 — Connect over SSH

**SSH** (Secure Shell) gives you an encrypted terminal on a remote machine.

1. On your laptop, open a terminal (Windows: **PowerShell**).
2. Connect, using your hostname:
   ```bash
   ssh pelatih@pi01.local
   ```
3. The first time, type `yes` to accept the Pi's fingerprint, then your password.
4. Your prompt changes to `pelatih@pi01:~ $`. You are now typing on the Pi.

> **Error: "Could not resolve hostname"?** Your network does not pass `.local` names. Ask the trainer for your Pi's IP address from the router, then `ssh pelatih@<ip-address>`.

> **Error: "REMOTE HOST IDENTIFICATION HAS CHANGED"?** You reflashed the card, so the Pi has a new identity. Remove the old one with `ssh-keygen -R pi01.local` and connect again.

### 2.3 — Connect VS Code

1. In VS Code, press **F1** and choose **Remote-SSH: Connect to Host…**
2. Type `pelatih@pi01.local` and press **Enter**. Choose **Linux** if asked, then enter your password.
3. Wait while VS Code installs its helper on the Pi (first time only, 1–2 minutes).
4. Open a terminal inside VS Code: **Terminal → New Terminal**. This terminal runs on the Pi.

From now on, you edit files in VS Code on your laptop, and they are saved on the Pi.

### 2.4 — Linux essentials

Run each command in the terminal and look at the result.

| Command | What it does |
|---|---|
| `pwd` | Print where you are (working directory) |
| `ls -l` | List files with details (owner, permissions, size) |
| `cd ~/iiot` | Change directory; `~` is your home folder |
| `mkdir -p ~/iiot/data` | Make folders, including any missing parents |
| `nano notes.txt` | Simple text editor (**Ctrl+O** save, **Ctrl+X** exit) |
| `cat notes.txt` | Print a file |
| `tail -f file` | Follow a file as new lines are added (**Ctrl+C** to stop) |
| `cp`, `mv`, `rm` | Copy, move/rename, remove (no recycle bin!) |
| `chmod +x script.py` | Make a file executable |
| `sudo <command>` | Run one command as administrator (root) |

1. Update the system (this takes a few minutes):
   ```bash
   sudo apt update
   sudo apt full-upgrade -y
   ```
2. Create the course folder you will use all week:
   ```bash
   mkdir -p ~/iiot/data
   cd ~/iiot
   ```

> **`sudo` is a loaded gun.** Use it only when a command needs system rights (installing software, editing system files, managing services). Never run your own Python programs with `sudo`.

### 2.5 — Services and logs

A **service** is a program that Linux starts and supervises in the background. **systemd** is the part of Linux that manages services.

1. Check the SSH service you are using right now:
   ```bash
   systemctl status ssh
   ```
   Look for `active (running)` and `enabled`. Press **q** to leave.
2. Read its log:
   ```bash
   journalctl -u ssh -n 20
   ```
   You should see your own login.

| Command | What it does |
|---|---|
| `systemctl status <name>` | Is it running? Recent log lines |
| `sudo systemctl start/stop/restart <name>` | Control it now |
| `sudo systemctl enable/disable <name>` | Start it on boot, or not |
| `journalctl -u <name> -f` | Follow its log live |

### 2.6 — Network checks

```bash
hostname -I          # your Pi's IP address(es)
ip a                 # all network interfaces and addresses
ping -c 3 8.8.8.8    # can we reach the internet?
ss -tulpn            # which programs are listening on which ports
```

In the `ss` output, find port **22**. That is SSH, waiting for connections.

**Try it**
1. Ping your neighbour's Pi by name: `ping -c 3 pi02.local`.
2. **Break it on purpose.** Stop SSH while you are connected through it: `sudo systemctl stop ssh`. Your current session stays open, but try a *new* connection from a second laptop terminal. It is refused. A stopped service means a closed door.
3. **Put everything back:** `sudo systemctl start ssh`, and confirm a new connection works.

**Checkpoint ✅** You can open VS Code on your Pi, `~/iiot/data` exists, the system is updated, and you can find your Pi's IP address and listening ports.

---

## Topic 3 — Python for IoT

**Goal:** write a Python program that produces readings from the pump station, stores them safely, and runs as a service that survives crashes and reboots. Day 2 replaces the simulated readings with real equipment.

**Open:** VS Code connected to your Pi, folder `~/iiot`.

### 3.1 — Why Python at the edge?

- Comes with Raspberry Pi OS, and runs the same on your laptop and on the Pi.
- Has libraries for nearly every industrial protocol (Modbus, MQTT, OPC UA) and for data and AI.
- Readable: the person who maintains your gateway in five years can follow it.

### 3.2 — A virtual environment for your project

Raspberry Pi OS protects its own Python. A plain `pip install` fails with `error: externally-managed-environment`. Instead, each project gets its own **virtual environment (venv)**: a private folder of Python packages.

1. Create and activate it:
   ```bash
   cd ~/iiot
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   Your prompt now starts with `(.venv)`.
2. Install the packages the course uses on Day 2, and record them:
   ```bash
   pip install pymodbus paho-mqtt
   pip freeze > requirements.txt
   ```
3. In VS Code, press **F1** → **Python: Select Interpreter** → choose `./.venv/bin/python`.

> **Every new terminal:** run `source ~/iiot/.venv/bin/activate` again. If `(.venv)` is missing from your prompt, you are using the system Python.

### 3.3 — Python in twenty minutes

Type these into the interactive interpreter (`python3`, leave with `exit()`), one block at a time.

```python
# Variables and types
station = "PS-01"            # str
tank_level = 62.5            # float
pump_running = True          # bool
print(f"{station}: tank {tank_level}%, pump running: {pump_running}")

# A dict: named values, the shape of every reading this week
reading = {"station": station, "tank_level_pct": tank_level, "pump_temp_c": 45.2}
print(reading["pump_temp_c"])

# A list and a loop
levels = [62.5, 63.1, 61.8, 95.2, 60.4]
for level in levels:
    if level > 90:
        print(f"HIGH LEVEL ALARM: {level}%")

# A function
def is_alarm(level, limit=90):
    return level > limit

print(is_alarm(95.2), is_alarm(50))
```

### 3.4 — The pump station simulator

1. In VS Code, create `~/iiot/sim_sensor.py` and type in the program below, or copy it from `code/day1/sim_sensor.py` in this repo.

```python
#!/usr/bin/env python3
"""Simulated sensors for Stesen Pam PS-01 (water pump station).

Writes one JSON reading per line to ~/iiot/data/ps01.jsonl every INTERVAL_S seconds.
"""
import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path

STATION = "PS-01"
INTERVAL_S = 2
DATA_FILE = Path.home() / "iiot" / "data" / "ps01.jsonl"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sim_sensor")


def read_tank_level(previous: float) -> float:
    """Tank level in percent: drifts a little from the previous value."""
    level = previous + random.uniform(-1.5, 1.5)
    return max(0.0, min(100.0, level))


def read_pump_temp() -> float:
    """Pump motor temperature in °C. Fails now and then, like a real sensor."""
    if random.random() < 0.02:
        raise IOError("pump temperature sensor not responding")
    return round(random.gauss(45.0, 1.5), 1)


def main() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    level = 60.0
    log.info("Simulator started, writing to %s", DATA_FILE)

    while True:
        level = read_tank_level(level)
        reading = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "station": STATION,
            "tank_level_pct": round(level, 1),
        }
        try:
            reading["pump_temp_c"] = read_pump_temp()
            reading["status"] = "OK"
        except IOError as err:
            reading["pump_temp_c"] = None
            reading["status"] = "SENSOR_FAULT"
            log.warning("Read failed: %s", err)

        with DATA_FILE.open("a") as f:
            f.write(json.dumps(reading) + "\n")
        log.info("%s", reading)
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
```

| Piece | What it does |
|---|---|
| `DATA_FILE` | Where readings go: one **JSON** (JavaScript Object Notation) object per line, a format called JSON Lines |
| `read_tank_level()` | Moves the level a little from the last value, kept between 0 and 100 |
| `read_pump_temp()` | Returns a realistic temperature, but raises an error about 2% of the time |
| `try` / `except IOError` | A failed read becomes a `SENSOR_FAULT` record instead of crashing the program |
| `ts` in UTC | Timestamps in UTC (Coordinated Universal Time), so data from different sites lines up |
| `logging` | Timestamped messages with a level (INFO, WARNING), instead of plain `print` |

2. Run it:
   ```bash
   python sim_sensor.py
   ```
   A reading appears every 2 seconds. Leave it for a minute, then stop it with **Ctrl+C**.
3. Look at the data file:
   ```bash
   tail -n 5 data/ps01.jsonl
   ```

> **Why keep running after a failed read?** In a plant, one bad reading is normal: a loose cable, electrical noise, a sensor restarting. A gateway that crashes on the first bad value is worse than useless. Record the fault, and carry on.

### 3.5 — Read the log back: a shift report

1. Create `~/iiot/summarise.py` (or copy `code/day1/summarise.py`):

```python
#!/usr/bin/env python3
"""Read the PS-01 data log and print a short shift report."""
import json
from pathlib import Path

DATA_FILE = Path.home() / "iiot" / "data" / "ps01.jsonl"


def main() -> None:
    levels = []
    faults = 0
    bad_lines = 0

    with DATA_FILE.open() as f:
        for line_no, line in enumerate(f, start=1):
            try:
                reading = json.loads(line)
            except json.JSONDecodeError:
                bad_lines += 1
                print(f"Skipping damaged line {line_no}: {line.strip()[:40]}")
                continue

            levels.append(reading["tank_level_pct"])
            if reading["status"] != "OK":
                faults += 1

    if not levels:
        print("No readings yet.")
        return

    print(f"Readings      : {len(levels)}")
    print(f"Tank level    : min {min(levels):.1f}%  max {max(levels):.1f}%  "
          f"avg {sum(levels) / len(levels):.1f}%")
    print(f"Sensor faults : {faults}")
    print(f"Damaged lines : {bad_lines}")


if __name__ == "__main__":
    main()
```

2. Run it: `python summarise.py`

**Try it**
1. **Break it on purpose.** Simulate a power cut in the middle of a write, which leaves half a line in the file:
   ```bash
   echo '{"ts": "2026-11-20T08:00:00+00:00", "station": "PS-0' >> data/ps01.jsonl
   ```
   Run `summarise.py` again. It reports one damaged line and carries on.
2. Now comment out the `try:` / `except` lines (keep the `json.loads` line, unindented) and run it again. Read the `JSONDecodeError` traceback: Python tells you the line and the exact character where the JSON broke.
3. **Put everything back:** restore the `try` / `except`.

> **Recap:** two kinds of failure, two answers. A failed *sensor read* becomes a recorded fault. A damaged *stored record* is skipped and counted. In both cases the program keeps running.

### 3.6 — Run the simulator as a service

A gateway program must start by itself after a power cut and restart itself after a crash. You do not log in to start it. That is a job for systemd.

1. Create the service file:
   ```bash
   sudo nano /etc/systemd/system/sim-sensor.service
   ```
2. Paste this (also in `code/day1/sim-sensor.service`):
   ```ini
   [Unit]
   Description=PS-01 simulated pump station sensors
   After=network.target

   [Service]
   User=pelatih
   WorkingDirectory=/home/pelatih/iiot
   ExecStart=/home/pelatih/iiot/.venv/bin/python /home/pelatih/iiot/sim_sensor.py
   Restart=always
   RestartSec=3
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

| Line | What it does |
|---|---|
| `User=pelatih` | Runs as your normal user, not as root |
| `ExecStart=` | The venv's Python, so your installed packages are found. Full paths only. |
| `Restart=always` | Restart whenever the program exits, including after a crash |
| `RestartSec=3` | Wait 3 seconds before restarting, so a broken program cannot restart in a tight loop |
| `PYTHONUNBUFFERED=1` | Log lines appear in the journal immediately |
| `WantedBy=multi-user.target` | Start it at boot, once the system is up |

3. Load, enable and start it:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now sim-sensor
   systemctl status sim-sensor
   ```
4. Follow its log live: `journalctl -u sim-sensor -f` (**Ctrl+C** to stop following; the service keeps running).

**Try it**
1. **Crash it.** Kill the program the hard way:
   ```bash
   pkill -f sim_sensor.py
   ```
   Wait 3 seconds, then `systemctl status sim-sensor`. It is running again with a new process ID. In the journal you can see it exit and restart.
2. **Power cut.** `sudo reboot`. Reconnect after a minute (VS Code reconnects for you), then check `systemctl status sim-sensor` and `tail data/ps01.jsonl`. Readings resumed without you logging in.
3. **Break it on purpose.** Edit the service and misspell the path in `ExecStart` (for example `sim_sensr.py`). Run `sudo systemctl daemon-reload && sudo systemctl restart sim-sensor`, then `systemctl status sim-sensor`. Read the error in the journal: it names the file it could not open.
4. **Put everything back:** fix the path, reload, restart, and confirm `active (running)`.

> **Later, in production:** `Restart=always` hides crashes if nobody looks. Real gateways also report "I restarted" upstream, so someone notices a program that crashes every hour. You will add that on Day 3.

**Checkpoint ✅** `systemctl status sim-sensor` shows `active (running)` after a reboot, and `summarise.py` reports readings collected while you were not logged in.

---

## End of Day 1 — what you should have

- A Raspberry Pi named `pi01` / `pi02`, updated, reachable over SSH and from VS Code
- `~/iiot/.venv` with `pymodbus` and `paho-mqtt`, and `requirements.txt`
- `~/iiot/sim_sensor.py` running as the `sim-sensor` service, surviving crashes and reboots
- `~/iiot/data/ps01.jsonl` filling with readings
- `~/iiot/summarise.py` producing a shift report that copes with damaged lines

**Security recap**
- Your Pi password is the only thing between the lab network and a computer that will soon switch a relay. Do not reuse a password from elsewhere.
- Your programs run as `pelatih`, not root. Only use `sudo` for system tasks.

**Extra, if you finish early**
1. Add a high-level alarm to the simulator: when `tank_level_pct` goes above 90, log a `WARNING` and add `"alarm": "HIGH_LEVEL"` to the reading. Change the starting level to 88 to test it.
2. Switch to SSH key login. On your laptop: `ssh-keygen -t ed25519`, then copy the contents of the `.pub` file into `~/.ssh/authorized_keys` on the Pi. Log in again: no password prompt.

**Tomorrow (Day 2):** the Pi meets real equipment. You wire a door switch and a pump relay to the GPIO pins, read the plant's field device over Modbus, and publish everything securely over MQTT.
