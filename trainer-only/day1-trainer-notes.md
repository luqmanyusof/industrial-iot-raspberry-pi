# Day 1 — Trainer notes

## Timing (about 5.5 hours of contact time)

| Block | Topics | Time |
|---|---|---|
| Morning 1 | 1 — SBCs and IoT architecture · 2 — Pi setup | 1 h 15 min |
| Morning 2 | 3 — Python for IoT · 4 — Hardening | 1 h 30 min |
| Afternoon 1 | 5 — Classes, threads, SQLite, HTTP (pair lab) | 1 h 15 min |
| Afternoon 2 | 6 — GPIO, relay and interlock | 1 h 30 min |

Topics 1–3 run fast with a group that already codes (1.5–2 h in total). If Topic 6 runs short on time, the test sheet lines 1–4 and the `-9` kill test are the essentials; line 5 and the extras can go.

## Before the day

- [ ] Own lab router up, with a known SSID and password. Venue Wi-Fi often blocks device-to-device traffic, which breaks `.local` names and Day 2 pairing.
- [ ] Reserve DHCP addresses for `pi01`, `pi02` and the ESP32 plant, and print the IP list in case `.local` fails on participants' laptops.
- [ ] Test-flash one card with the current Imager and OS so the wizard screens match the notes.
- [ ] Spare pre-flashed card per participant (hostname, user `pelatih`, lab Wi-Fi, SSH on). If a flash fails or a card is bad, swap it rather than lose 20 minutes.
- [ ] Check venue internet: `apt full-upgrade` and `pip install` need it. If it is slow, pre-run the upgrade on the spare cards.
- [ ] ESP32 plant flashed and powered for the Topic 1 demo.
- [ ] **Test every relay module on a Pi before class:** note whether it is active-high or active-low, and check it fully switches off from a 3.3 V GPIO pin. Swap out any 5 V active-low module that stays on. Label each module with its trigger type.
- [ ] Count jumpers: 6 female-to-female per participant, plus spares.

## Topic 1 — delivery cues

- Open with the ESP32 plant running: turn the knob, show the stack light change. "By Day 3, your Pi is the thing watching this."
- Mapping activity: keep the scenario generic (PS-01). This audience works on defence systems; do not ask them to map their own systems.
- Expected answer: tank sensor, door switch, relay, pump = Level 0; ESP32 plant = Level 1; Pi = between 1 and 2; dashboard = Level 2; billing = Level 4. Disagreement about the Pi's level is fine; use it to discuss the boundary.

## Topic 2 — common problems

| Symptom | Fix |
|---|---|
| `.local` name does not resolve on Windows | Use the IP from the router list |
| Pi never joins Wi-Fi | Wi-Fi password typo in Imager, or 5 GHz-only network on an older Pi. Reflash or use a spare card |
| Host key warning after reflash | `ssh-keygen -R pi01.local` |
| VS Code Remote-SSH hangs on "Setting up SSH host" | Slow venue internet (it downloads its server). Wait, or retry once the download completes |

## Topic 3 — teaching moments

- The `externally-managed-environment` error: let one participant hit it on purpose before introducing the venv.
- The damaged-line exercise is the Day 1 "aha": the same `try`/`except` idea appears in Modbus timeouts on Day 2 and network loss on Day 3.
- The reboot test usually gets a reaction when readings resume with nobody logged in. Point back to the course rule: the edge must fail safe.

## Topic 4 — hardening

- The lockout warning is real: if someone disables password login before their key works, recover by reflashing (keep the spare cards ready).
- The `ufw allow 5353/udp` step is easy to skip. A participant who skips it loses `pi0x.local` from the laptop: a good live demo of "the firewall broke name lookup", fixed with one rule.

## Topic 5 — pair lab

- With 2 participants, `pi01` and `pi02` forward to each other. If one participant falls behind, run the receiver on your laptop and point their `FORWARD_URL` at it.
- Try-it 2 (closing the port) is the moment threads make sense: the queue number climbs while sensor readings keep their 2-second rhythm.

## Topic 6 — GPIO

- Watch every wiring change: the most likely mistake is a jumper to pin 2 or 4 (5 V) instead of a GND pin.
- The `-9` kill result depends on the relay module. Most modules drop out because the pin is released and the module's own resistor pulls the input to its off state, but do not promise it — let participants observe and discuss. That is the point: safety cannot depend on the program's clean-up code.
- Day 2 reuses `pump_control.py`: the MQTT remote command must pass through the same `start()` checks.

## Open decision

- Installing Mosquitto and Node-RED at the end of Day 1 (saves time on Day 2, needs venue internet) — not yet in the participant notes. Day 1 is now full, so this probably belongs in pre-flashed images or at the start of Day 2.
