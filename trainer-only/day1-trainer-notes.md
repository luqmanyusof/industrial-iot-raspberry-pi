# Day 1 — Trainer notes

## Timing (about 5.5 hours of contact time)

| Block | Topic | Time |
|---|---|---|
| Morning 1 | Topic 1 — SBCs and IoT architecture, plus mapping activity | 1 h |
| Morning 2 | Topic 2 — Imager, SSH, VS Code, Linux essentials | 2 h |
| Afternoon | Topic 3 — venv, Python basics, simulator, shift report, systemd | 2.5 h |

If the group already writes Python comfortably, cut 3.3 to a five-minute read-through and give the time to Day 2.

## Before the day

- [ ] Own lab router up, with a known SSID and password. Venue Wi-Fi often blocks device-to-device traffic, which breaks `.local` names and Day 2 pairing.
- [ ] Reserve DHCP addresses for `pi01`, `pi02` and the ESP32 plant, and print the IP list in case `.local` fails on participants' laptops.
- [ ] Test-flash one card with the current Imager and OS so the wizard screens match the notes.
- [ ] Spare pre-flashed card per participant (hostname, user `pelatih`, lab Wi-Fi, SSH on). If a flash fails or a card is bad, swap it rather than lose 20 minutes.
- [ ] Check venue internet: `apt full-upgrade` and `pip install` need it. If it is slow, pre-run the upgrade on the spare cards.
- [ ] ESP32 plant flashed and powered for the Topic 1 demo.

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

## Open decision

- Installing Mosquitto and Node-RED at the end of Day 1 (saves time on Day 2, needs venue internet) — not yet in the participant notes.
