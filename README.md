# Industrial IoT Development

*Turn a Raspberry Pi into an industrial edge gateway that reads plant equipment, moves data securely and acts on it. A hands-on 3-day course.*

You will set up a Raspberry Pi as the **edge gateway** of a small water pump station, Stesen Pam PS-01. Day by day it is hardened, learns GPIO inputs and outputs, talks to a real field device over Modbus and switches its two pumps, publishes data over MQTT to an operator dashboard, and finally runs as a self-contained edge node that never loses a reading and emails alerts.

**The flow:** Raspberry Pi + Python → hardened gateway → GPIO switch and relay → Modbus field device with two pumps → MQTT + Node-RED → edge node with store-and-forward and email alerts

**Acronyms used throughout:** **IoT** = Internet of Things · **IIoT** = Industrial IoT · **SBC** = Single-Board Computer · **MCU** = Microcontroller Unit · **OS** = Operating System · **SSH** = Secure Shell · **SQL** = Structured Query Language · **HTTP** = Hypertext Transfer Protocol · **GPIO** = General-Purpose Input/Output · **PLC** = Programmable Logic Controller · **SCADA** = Supervisory Control and Data Acquisition · **HMI** = Human-Machine Interface · **MTA** = Mail Transfer Agent · **SMTP** = Simple Mail Transfer Protocol · **MQTT** = Message Queuing Telemetry Transport · **JSON** = JavaScript Object Notation · **TLS** = Transport Layer Security · **IT / OT** = Information / Operational Technology · **ADC** = Analog-to-Digital Converter · **FC** = (Modbus) Function Code · **QoS** = Quality of Service

## The 3 days

- **[Day 1 — Raspberry Pi and Python](day1.md)**: where the Pi sits in an industrial system, setting it up headless and hardening it, a threaded gateway that reads, stores and forwards, and GPIO basics: a switch in, a relay out.
- **[Day 2 — Interfacing with the Physical World](day2.md)**: how field devices connect, polling the PS-01 plant over Modbus, a level alarm, MQTT, and a Node-RED operator dashboard that switches the plant's two pumps.
- **[Day 3 — Building a Smart Project](day3.md)**: design for failure, store-and-forward, email alerts through a mail server on the Pi, production readiness and a troubleshooting drill.
  - **Afternoon project: [Op SENTINEL — Forward Operating Base Utilities Watch](sentinel.md)**: watch three simulated outposts, keep a complete record, and alert the duty officer.

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
- Single-channel relay module and 4 female-to-female jumper wires (from Day 1, Topic 6)
- Windows 10 or 11 laptop with internet, and administrator rights to share it (the notes assume Windows; macOS and Linux steps are given where they differ)
- LAN cable, plus a USB-to-Ethernet adapter if your laptop has no LAN port

**Software on your laptop**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) 2.0 or later
- [Visual Studio Code](https://code.visualstudio.com/) with the **Remote - SSH** extension

**Shared, provided by the trainer**
- The ESP32 "plant" field device. It also runs the plant's own Wi-Fi network, `plant-wifi`, which every Pi joins from Day 1

## Repository structure

```
industrial-iot-raspberry-pi/
├── README.md
├── day1.md
├── day2.md
├── day3.md
├── sentinel.md                  # Day 3 afternoon project brief
├── plant/                       # ESP32 firmware: PS-01 plant and SENTINEL outposts (flash once, before Day 1)
├── images/
│   ├── day*-fig-*.svg / .png    # figures used in the day files
│   └── src/                     # Python that draws the isometric figures:
│                                #   python3 images/src/build_day1.py (also day2, day3)
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
│   │   └── switch_relay.py      # input drives output (Topic 6)
│   ├── day2/
│   │   ├── plant_sim.py         # simulated plant, same Modbus map (Topic 8)
│   │   ├── modbus_read.py       # read every register (Topic 8)
│   │   ├── modbus_write.py      # write pumps, valve, horn (Topic 8)
│   │   ├── plant.py             # ModbusPlant and LevelAlarm (Topic 9)
│   │   ├── gateway.py           # Day 2 gateway with HTTP (Topic 9)
│   │   ├── gateway_mqtt.py      # gateway publishing over MQTT, taking pump commands (Topic 10)
│   │   ├── ps01-dashboard-starter.json  # Node-RED flow to import: readings, no pumps (Topic 11)
│   │   └── ps01-dashboard-flow.json     # the finished flow, with the pump controls (Topic 11)
│   ├── day3/
│   │   ├── outbox.py            # store-and-forward outbox (Topic 13)
│   │   ├── alerts.py            # alert rules and mailer (Topic 14)
│   │   └── gateway.py           # Day 3 edge node (Topics 13-14)
│   └── sentinel/
│       ├── sentinel_sim.py      # practice copy of the outposts (the real ones run on the ESP32)
│       ├── outpost_read.py      # read the outposts by unit ID
│       └── README.md            # outpost registers and how to create events
```
