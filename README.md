# Industrial IoT Development

*Turn a Raspberry Pi into an industrial edge gateway that reads plant equipment, moves data securely and acts on it. A hands-on 3-day course.*

You will set up a Raspberry Pi as the **edge gateway** of a small water pump station, Stesen Pam PS-01. Day by day it learns to read equipment, switch outputs safely, talk to a real field device over Modbus, publish data over MQTT, and finally run as a self-contained edge node with local anomaly detection.

**The flow:** Raspberry Pi + Python → digital I/O and relay → Modbus field device → MQTT + Node-RED → edge node with local AI

**Acronyms used throughout:** **IoT** = Internet of Things · **IIoT** = Industrial IoT · **SBC** = Single-Board Computer · **MCU** = Microcontroller Unit · **OS** = Operating System · **SSH** = Secure Shell · **GPIO** = General-Purpose Input/Output · **PLC** = Programmable Logic Controller · **SCADA** = Supervisory Control and Data Acquisition · **HMI** = Human-Machine Interface · **MQTT** = Message Queuing Telemetry Transport · **JSON** = JavaScript Object Notation · **TLS** = Transport Layer Security

## The 3 days

- **[Day 1 — Raspberry Pi and Python](day1.md)**: where the Pi sits in an industrial system, setting it up headless, and running a Python program as a proper service.
- **Day 2 — Interfacing with the Physical World** *(draft pending)*: digital input and relay output with interlocks, polling a Modbus field device, and secure MQTT with Node-RED.
- **Day 3 — Building a Smart Project** *(draft pending)*: an edge node that polls equipment, detects anomalies locally, survives network loss and shows everything on a dashboard.

## How to read this

Every topic has a **Goal**, numbered **steps**, a **Try it** section where you change and break things on purpose, and a **Checkpoint ✅** you must reach before moving on. Topics go in order: each one builds on the files from the one before.

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
- Raspberry Pi with power supply and a microSD card (16 GB or more)
- Single-channel relay module and jumper cables (used from Day 2)
- Laptop (Windows, macOS or Linux) on the same network as the Pi

**Software on your laptop**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) 2.0 or later
- [Visual Studio Code](https://code.visualstudio.com/) with the **Remote - SSH** extension

**Shared, provided by the trainer**
- The ESP32 "plant" field device (from Day 2)
- Lab Wi-Fi router

## Repository structure

```
industrial-iot-raspberry-pi/
├── README.md
├── day1.md
├── code/
│   └── day1/
│       ├── sim_sensor.py        # simulated pump station sensors
│       ├── summarise.py         # reads the data log and reports
│       └── sim-sensor.service   # systemd unit for the simulator
```

> **Trainer material** (delivery notes, timing, common problems) lives on the `trainer` branch, not here. `git checkout trainer` to see it.
