#!/usr/bin/env python3
"""PS-01 edge node, Day 3: poll the plant, store everything, forward it reliably, alert by email.

Threads:
  sensor   : polls the plant, runs the level alarm and the alert rules, queues each reading
  store    : saves each reading, and puts it in the outbox in the same transaction
  forward  : sends the outbox to the MQTT broker, oldest first, marking each message once confirmed
  mailer   : hands alert emails to the mail server on this Pi
"""
import logging
import queue
import signal
import sqlite3
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

import outbox
from alerts import AlertManager, Mailer
from mqtt_link import BASE, GATEWAY, make_client
from plant import LevelAlarm, ModbusPlant

STATION = "PS-01"
INTERVAL_S = 2
PLANT_HOST, PLANT_PORT = "192.168.4.1", 502      # simulator: "127.0.0.1", 5020
DATA_DIR = Path.home() / "iiot" / "data"
DB_FILE = DATA_DIR / "ps01.db"
RUN_STATE = DATA_DIR / "gateway.state"           # "running" while up, "stopped" after a clean stop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(levelname)s %(message)s")
log = logging.getLogger("gateway")

current_alarm = {"state": None}                  # latest alarm state, republished on every reconnect


def sensor_loop(plant: ModbusPlant, q: queue.Queue, stop: threading.Event, client: mqtt.Client,
                alerts: AlertManager) -> None:
    alarm = LevelAlarm()
    written = None
    while not stop.is_set():
        reading = plant.read()
        state = None
        if reading.status == "COMMS_FAULT":
            written = None
        else:
            state = alarm.update(reading.tank_level_pct)
            wanted = alarm.outputs(state)
            if wanted != written and plant.set_outputs(*wanted):
                log.info("Alarm %s: light %d, horn %s", state, wanted[0], "ON" if wanted[1] else "off")
                written = wanted
                current_alarm["state"] = state
                client.publish(f"{BASE}/alarm", state, qos=1, retain=True)   # state: latest only, retained
        alerts.check(reading, state)
        q.put(("telemetry", asdict(reading)))
        stop.wait(INTERVAL_S)


def store_loop(q: queue.Queue, stop: threading.Event) -> None:
    db = sqlite3.connect(DB_FILE, timeout=10)
    outbox.create_table(db)
    db.execute(
        "CREATE TABLE IF NOT EXISTS plant_readings (ts TEXT, station TEXT, gateway TEXT, "
        "tank_level_pct REAL, room_temp_c REAL, room_humidity_pct REAL, e_stop INTEGER, status TEXT)"
    )
    while not stop.is_set() or not q.empty():
        try:
            kind, item = q.get(timeout=1)
        except queue.Empty:
            continue
        with db:                                            # one transaction: both rows, or neither
            if kind == "telemetry":
                db.execute("INSERT INTO plant_readings VALUES (:ts, :station, :gateway, :tank_level_pct, "
                           ":room_temp_c, :room_humidity_pct, :e_stop, :status)", item)
            outbox.add(db, f"{BASE}/{kind}", item, qos=1)
    db.close()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    q: queue.Queue = queue.Queue()

    previous = RUN_STATE.read_text().strip() if RUN_STATE.exists() else "first start"
    RUN_STATE.write_text("running")

    def on_connect(c: mqtt.Client) -> None:
        c.publish(f"{BASE}/status", "online", qos=1, retain=True)
        if current_alarm["state"]:
            c.publish(f"{BASE}/alarm", current_alarm["state"], qos=1, retain=True)

    client = make_client("gateway", will=(f"{BASE}/status", "offline"), on_connect=on_connect)
    mailer = Mailer(stop)
    alerts = AlertManager(mailer, on_event=lambda e: q.put(("events", e)))

    started = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": "gateway_started",
               "previous_stop": "clean" if previous == "stopped" else previous}
    q.put(("events", started))
    if previous == "running":                       # we never wrote "stopped": the last run crashed
        log.warning("Previous run did not stop cleanly")
        mailer.send(f"[PS-01 {GATEWAY}] Gateway restarted after an unclean stop",
                    f"The gateway on {GATEWAY} started at {started['ts']} (UTC).\n"
                    "Its previous run ended without a clean shutdown: a crash, a kill or a power cut.\n"
                    "Check: journalctl -u gateway -b -1\n")

    threads = [
        threading.Thread(target=sensor_loop, name="sensor",
                         args=(ModbusPlant(PLANT_HOST, PLANT_PORT, STATION), q, stop, client, alerts)),
        threading.Thread(target=store_loop, args=(q, stop), name="store"),
        threading.Thread(target=outbox.forward_loop, args=(DB_FILE, client, stop), name="forward"),
    ]
    for t in threads:
        t.start()
    log.info("Edge node started: plant %s:%d, previous stop: %s", PLANT_HOST, PLANT_PORT, started["previous_stop"])

    try:
        while not stop.is_set():
            stop.wait(1)
    except KeyboardInterrupt:
        stop.set()
    for t in threads:
        t.join()
    try:
        client.publish(f"{BASE}/status", "offline", qos=1, retain=True).wait_for_publish(2)
    except (RuntimeError, ValueError):
        pass
    client.disconnect()
    client.loop_stop()
    RUN_STATE.write_text("stopped")
    log.info("Edge node stopped cleanly")


if __name__ == "__main__":
    main()
