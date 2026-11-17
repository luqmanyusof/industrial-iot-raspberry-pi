#!/usr/bin/env python3
"""PS-01 edge gateway, Day 2 with MQTT: reads the plant over Modbus, runs the alarm, publishes over MQTT,
and switches pump 1 and pump 2 on the plant when a command arrives.

- sensor thread  : polls the plant every INTERVAL_S seconds, updates the alarm, puts the reading on a queue
- store thread   : saves every reading to SQLite, then publishes it to the MQTT broker
- MQTT thread     : (paho's own) runs pump_command() when ps01/<gateway>/pump/<n>/cmd arrives
Since Topic 9 only the forwarding changed: HTTP POST became MQTT publish.
"""
import json
import logging
import queue
import signal
import sqlite3
import threading
from dataclasses import asdict
from pathlib import Path

import paho.mqtt.client as mqtt

from mqtt_link import BASE, make_client
from plant import LevelAlarm, ModbusPlant

STATION = "PS-01"
INTERVAL_S = 2
PLANT_HOST, PLANT_PORT = "192.168.4.1", 502      # simulator: "127.0.0.1", 5020
DB_FILE = Path.home() / "iiot" / "data" / "ps01.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(levelname)s %(message)s")
log = logging.getLogger("gateway")


def pump_command(plant: ModbusPlant, msg: mqtt.MQTTMessage) -> None:
    """ps01/<gateway>/pump/<1 or 2>/cmd, payload ON or OFF: switch that pump on the plant."""
    pump = msg.topic.split("/")[3]
    command = msg.payload.decode(errors="replace").strip().upper()
    if pump not in ("1", "2") or command not in ("ON", "OFF"):
        log.warning("Ignored %r on %s", command, msg.topic)
        return
    ok = plant.set_pump(int(pump), command == "ON")
    log.info("Pump %s %s from remote: %s", pump, command, "done" if ok else "FAILED, plant not answering")


def sensor_loop(plant: ModbusPlant, q: queue.Queue, stop: threading.Event, client: mqtt.Client) -> None:
    alarm = LevelAlarm()
    written = None                          # outputs last accepted by the plant; None = unknown
    while not stop.is_set():
        reading = plant.read()
        if reading.status == "COMMS_FAULT":
            written = None                  # rewrite the outputs once the plant is back
        else:
            state = alarm.update(reading.tank_level_pct)
            wanted = alarm.outputs(state)
            if wanted != written:
                if plant.set_outputs(*wanted):
                    log.info("Alarm %s: horn %s", state, "ON" if wanted[1] else "off")
                    client.publish(f"{BASE}/alarm", state, qos=1, retain=True)
                    written = wanted
        q.put(reading)
        stop.wait(INTERVAL_S)


def store_and_forward_loop(q: queue.Queue, stop: threading.Event, client: mqtt.Client) -> None:
    db = sqlite3.connect(DB_FILE)  # a connection belongs to the thread that made it
    db.execute(
        "CREATE TABLE IF NOT EXISTS plant_readings (ts TEXT, station TEXT, gateway TEXT, "
        "tank_level_pct REAL, room_temp_c REAL, room_humidity_pct REAL, e_stop INTEGER, "
        "pump1_on INTEGER, pump2_on INTEGER, status TEXT)"
    )
    while not stop.is_set():
        try:
            reading = q.get(timeout=1)
        except queue.Empty:
            continue

        db.execute(
            "INSERT INTO plant_readings VALUES (:ts, :station, :gateway, :tank_level_pct, :room_temp_c, "
            ":room_humidity_pct, :e_stop, :pump1_on, :pump2_on, :status)",
            asdict(reading),
        )
        db.commit()

        if client.is_connected():
            client.publish(f"{BASE}/telemetry", json.dumps(asdict(reading)), qos=0)
            log.info("Stored and published %s %s (queue: %d)", reading.ts, reading.status, q.qsize())
        else:
            log.warning("Stored locally, broker not connected (queue: %d)", q.qsize())

    db.close()


def main() -> None:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    plant = ModbusPlant(PLANT_HOST, PLANT_PORT, STATION)

    def on_connect(c: mqtt.Client) -> None:
        c.publish(f"{BASE}/status", "online", qos=1, retain=True)
        for n in (1, 2):
            c.subscribe(f"{BASE}/pump/{n}/cmd", qos=1)

    client = make_client("gateway", will=(f"{BASE}/status", "offline"), on_connect=on_connect)
    client.message_callback_add(f"{BASE}/pump/+/cmd", lambda c, userdata, msg: pump_command(plant, msg))

    q: queue.Queue = queue.Queue()
    threads = [
        threading.Thread(target=sensor_loop, args=(plant, q, stop, client), name="sensor"),
        threading.Thread(target=store_and_forward_loop, args=(q, stop, client), name="store"),
    ]
    for t in threads:
        t.start()
    log.info("Gateway started: plant %s:%d, publishing to %s/#", PLANT_HOST, PLANT_PORT, BASE)

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
        pass                                # broker not reachable: the last will says "offline" for us
    client.disconnect()                     # a clean goodbye: the broker does not send the last will
    client.loop_stop()
    log.info("Gateway stopped cleanly")


if __name__ == "__main__":
    main()
