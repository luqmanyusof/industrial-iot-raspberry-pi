# Op SENTINEL — Forward Operating Base Utilities Watch

> **Day 3 afternoon project.** Use everything from the course to build one edge node that watches three remote outposts, keeps a full record, and warns the duty officer when an outpost needs attention.

## Situation

A forward operating base supports three remote outposts: **ALPHA**, **BRAVO** and **CHARLIE**. Each outpost runs on:

| Utility | What can go wrong |
|---|---|
| A **generator**, and its fuel tank | Fuel runs low or leaks; the generator stops |
| A **water tank** | Water runs low before the next resupply |
| A **shelter** cooled by air-conditioning, powered by the generator | Without the generator, the shelter heats up |
| A **perimeter gate** | It opens for patrols; left open, it is a security risk |

Each outpost's controller reports by radio to a **data concentrator** at the base, which serves all three over **Modbus TCP**, each outpost in its own block of registers. In this exercise the ESP32 plant you already know plays the concentrator: it simulates the three outposts next to the PS-01 registers, on the same address and port.

**Figure 1 — The exercise**

![Three outposts, ALPHA, BRAVO and CHARLIE, each with a water tank, a generator and a perimeter gate, served by the ESP32 plant at 192.168.4.1 port 502 in register blocks starting at 10, 20 and 30; pi01 and pi02 each poll the ESP32 over Modbus TCP on Wi-Fi every 5 seconds](images/sentinel-fig-1-outposts.svg)

## Mission

Build **SENTINEL** on your Pi: an edge node that

1. polls all three outposts every 5 seconds,
2. keeps every reading and forwards it over MQTT without losing any,
3. gives the duty officer a **common operating picture** on a Node-RED dashboard, and
4. emails the duty officer when an outpost needs attention.

There are no trick questions and no scores. The aim is to apply what you built over the three days, and to be able to explain your choices.

## The outposts

| Setting | Value |
|---|---|
| Address | `192.168.4.1`, port `502`: the ESP32 plant, as on Day 2 |
| Register blocks | ALPHA from `10`, BRAVO from `20`, CHARLIE from `30` |
| Access | Read only |

Each outpost uses the same layout, starting at its block's first address (`b` = 10, 20 or 30):

| Address | Table | Name | Scaling | Meaning |
|---|---|---|---|---|
| IR b | Input register | `fuel` | ÷ 10 → % | Generator fuel, 0.0–100.0 % |
| IR b+1 | Input register | `water` | ÷ 10 → % | Water tank, 0.0–100.0 % |
| IR b+2 | Input register | `shelter_temp` | ÷ 10 → °C | Shelter temperature |
| IR b+3 | Input register | `data_age` | seconds | How old the outpost's values are; grows while its link is down |
| DI b | Discrete input | `generator` | — | 1 = running |
| DI b+1 | Discrete input | `gate` | — | 1 = open |
| DI b+2 | Discrete input | `link_ok` | — | 1 = fresh data from the outpost; 0 = link lost, values frozen |

So BRAVO's fuel is input register 20, and CHARLIE's link bit is discrete input 32. One Modbus connection reads all three outposts, and the PS-01 registers 0–3 are still there, unchanged.

> **When the link bit is 0,** the concentrator still answers, but the outpost's values are the last ones it heard, `data_age` seconds ago. Never show them as current: an old fuel reading presented as live is worse than no reading.

## Tasks

Work through them in order. Each one says which earlier work to build on.

### 1 — Reconnaissance

Get the course files, then read the outposts by hand:

```bash
cd ~/course && git pull
cp ~/course/code/sentinel/outpost_read.py ~/iiot/
cd ~/iiot && source .venv/bin/activate
python outpost_read.py
python outpost_read.py --unit 2
```

Note each outpost's fuel and water now. Which one will need attention first?

> **Practising alone?** `cp ~/course/code/sentinel/sentinel_sim.py ~/iiot/ && python sentinel_sim.py` runs a copy of the outposts on your own Pi. Point your programs at `127.0.0.1`, port `5020`, and type events into it yourself (`help` lists them).

### 2 — Plan

On paper, before any code (Day 3, Topic 13):
- Your **topic names**. Suggested: `sentinel/<outpost>/telemetry`, `sentinel/<outpost>/link` (`up` or `lost`, retained), `sentinel/<outpost>/events`.
- Your **alert rules**: what, for which outpost, after how long.
- What your node does when **one** outpost stops answering, and when the **broker** stops.

### 3 — Poll and store

Write `~/iiot/sentinel_node.py`:
- Poll the three outposts every 5 seconds with **one** Modbus connection: 4 input registers and 3 discrete inputs from each block. *Built on:* `ModbusPlant.read()` in `plant.py` (Day 2, Topic 9), with the block's first address instead of 0.
- Give every reading a status: `OK`; `LINK_LOST` when the outpost's link bit is 0 (keep `data_age`, but not the frozen values); `NO_ANSWER` when the ESP32 itself does not answer. Never crash, and always read the other outposts.
- Store every reading in SQLite, for example `~/iiot/data/sentinel.db`. *Built on:* the store thread in Day 3's `gateway.py`.

### 4 — Publish without losing anything

- Put every reading in an outbox and forward it. *Built on:* `outbox.py` (Day 3, Topic 14): reuse it as it is.
- Publish each outpost's link state (`up` / `lost`) straight to the broker, **retained**. It is state, not history.
- Allow your new topics in the broker's ACL (Day 2, Topic 11), then `sudo systemctl restart mosquitto`:
  ```conf
  # in /etc/mosquitto/acl, under user gateway:
  topic write sentinel/#
  # under user dashboard:
  topic read sentinel/#
  ```
- Check with `mosquitto_sub -h localhost -t 'sentinel/#' -v -u dashboard -P '<password>'`.

### 5 — Alert the duty officer

Email through Postfix on your Pi (Day 3, Topic 15). *Built on:* `alerts.py`: reuse the `Mailer` as it is, and adapt the rule checking so each rule runs **per outpost**. At least:

| Alert | Raised when | Suggested wait |
|---|---|---|
| Outpost link lost | Status `LINK_LOST` or `NO_ANSWER` | 60 s |
| Fuel low | Fuel below 20 % | 30 s |
| Generator stopped | Generator not running | 30 s |
| Gate left open | Gate open | 2 min (patrols open it briefly) |

Put the outpost's name in every subject line, for example `[SENTINEL CHARLIE] RAISED: Fuel low`.

### 6 — The common operating picture

In Node-RED (Day 2, Topic 12), build a page `/sentinel` with **one group per outpost**, each showing fuel and water gauges, shelter temperature, generator, gate and link. *Built on:* the PS-01 flow: an `mqtt in` on `sentinel/+/telemetry`, then a function or a switch node that sends each outpost's values to its own widgets (`msg.topic.split('/')[1]` is the outpost's name).

Make the link state impossible to miss: an outpost showing old values without saying it is `lost` would be lying to the duty officer.

### 7 — Leave it running

Run `sentinel_node.py` as a systemd service, like the gateway (Day 1, Topic 3), so it survives a crash and a reboot.

## Optional extras

- An alert for a shelter above 35 °C.
- Estimate each outpost's **hours of fuel left** from how fast the level is falling, and show it on the dashboard.
- An hourly **SITREP** (situation report) email: one line per outpost.
- An alarm list on the dashboard: every alert raised and cleared, newest first.

## During the exercise

The trainer will create events at the outposts so you can watch your node react: fuel leaks, generator failures, gates left open, an outpost whose link goes down. Keep a short log:

| Time | Outpost | What happened | How you noticed (dashboard, email, both) |
|---|---|---|---|
| | | | |

## Debrief

Each participant, about five minutes:
1. Show your common operating picture.
2. Show one alert email and the event that caused it.
3. Explain one design decision, and one thing you would change before deploying SENTINEL for real.

## Done when

- [ ] All three outposts appear on your dashboard and update every 5 seconds
- [ ] An outpost with a lost link shows as `lost` and the other two keep updating
- [ ] Stopping your broker for a minute loses no readings
- [ ] You received at least one alert email and its matching *CLEARED*
- [ ] `sentinel_node.py` runs as a service and comes back after `sudo reboot`
