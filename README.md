# Industrial IoT Development

*Turn a Raspberry Pi into an industrial edge gateway that reads plant equipment, moves data securely and acts on it. A hands-on 3-day course.*

You will set up a Raspberry Pi as the **edge gateway** of a small water pump station, Stesen Pam PS-01. Day by day it is hardened, learns to switch outputs safely, talks to a real field device over Modbus, publishes data over MQTT, and finally runs as a self-contained edge node with local anomaly detection.

**The flow:** Raspberry Pi + Python → hardened gateway → door switch, relay and interlock → Modbus field device → MQTT + Node-RED → edge node with local AI

**Acronyms used throughout:** **IoT** = Internet of Things · **IIoT** = Industrial IoT · **SBC** = Single-Board Computer · **MCU** = Microcontroller Unit · **OS** = Operating System · **SSH** = Secure Shell · **SQL** = Structured Query Language · **HTTP** = Hypertext Transfer Protocol · **GPIO** = General-Purpose Input/Output · **PLC** = Programmable Logic Controller · **SCADA** = Supervisory Control and Data Acquisition · **HMI** = Human-Machine Interface · **MQTT** = Message Queuing Telemetry Transport · **JSON** = JavaScript Object Notation · **TLS** = Transport Layer Security

## The 3 days

- **[Day 1 — Raspberry Pi and Python](day1.md)**: where the Pi sits in an industrial system, setting it up headless and hardening it, a threaded gateway that reads, stores and forwards, and a door switch and pump relay with a fail-safe interlock.
- **[Day 2 — Interfacing with the Physical World](day2.md)** *(Topics 7–9 drafted)*: polling a Modbus field device, secure MQTT, and a Node-RED operator dashboard whose remote commands must obey the local interlock.
- **Day 3 — Building a Smart Project** *(draft pending)*: an edge node that polls equipment, detects anomalies locally, survives network loss and shows everything on a dashboard.

## How to read this

Every topic has a **Goal**, numbered **steps**, numbered **figures** that show the flow and structure, a **Try it** section where you change and break things on purpose, and a **Checkpoint ✅** you must reach before moving on. Topics go in order: each one builds on the files from the one before.

## The one rule of this course

> **The edge must fail safe.** When a program crashes, a cable is pulled or the network drops, the plant must end up in a known, safe state. Every lab tests this.

## Course learning outcomes

By the end of the course you will be able to:
- Explain the architecture and components of an IoT system
- Configure and operate a single-board computer for IoT applications
- Develop basic Python programs for hardware interaction
- Interface inputs and actuators
- Collect and process data from physical devices
- Transmit device data to remote servers or cloud platforms
- Build a simple IoT monitoring system for industrial applications

## What you need

**Per participant**
- Raspberry Pi 4 Model B with power supply and a microSD card (16 GB or more)
- Single-channel relay module and 6 female-to-female jumper wires (from Day 1, Topic 6)
- Laptop (Windows, macOS or Linux) with internet, and administrator rights to share it
- LAN cable, plus a USB-to-Ethernet adapter if your laptop has no LAN port

**Software on your laptop**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) 2.0 or later
- [Visual Studio Code](https://code.visualstudio.com/) with the **Remote - SSH** extension

**Shared, provided by the trainer**
- The ESP32 "plant" field device. It also runs the plant's own Wi-Fi network, `PS01-PLANT`, which every Pi joins from Day 1

## Repository structure

```
industrial-iot-raspberry-pi/
├── README.md
├── day1.md
├── day2.md
├── plant/                       # ESP32 firmware for the shared PS-01 plant (flash once, before Day 1)
├── images/
│   ├── day1-*.svg, day2-*.svg   # figures used in the day files
│   └── src/                     # Python that draws the isometric figures:
│                                #   python3 images/src/build_day1.py (and build_day2.py)
├── code/
│   ├── day1/
│   │   ├── sim_sensor.py        # simulated pump station sensors (Topic 3)
│   │   ├── summarise.py         # reads the data log and reports (Topic 3)
│   │   ├── sim-sensor.service   # systemd unit for the simulator (Topic 3)
│   │   ├── receiver.py          # HTTP receiver for the pair lab (Topic 5)
│   │   ├── gateway.py           # threaded read, store and forward gateway (Topic 5)
│   │   ├── gateway.service      # systemd unit for the gateway (Topic 5)
│   │   ├── door_switch.py       # digital input (Topic 6)
│   │   ├── relay_test.py        # relay output (Topic 6)
│   │   └── pump_control.py      # START/STOP with door interlock (Topic 6)
│   └── day2/
│       ├── plant_sim.py         # simulated plant, same Modbus map (Topic 8)
│       ├── modbus_read.py       # read every register (Topic 8)
│       ├── modbus_write.py      # write light, valve, horn (Topic 8)
│       ├── plant.py             # ModbusPlant and LevelAlarm (Topic 9)
│       └── gateway.py           # Day 2 gateway (Topic 9)
```
