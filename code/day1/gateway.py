#!/usr/bin/env python3
"""PS-01 edge gateway: read, store and forward, each in its own thread.

- sensor thread  : takes a reading every INTERVAL_S seconds and puts it on a queue
- store thread   : saves every reading to SQLite, then forwards it over HTTP
A slow or dead network never delays the sensor readings.
"""
import logging
import queue
import random
import signal
import socket
import sqlite3
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

STATION = "PS-01"
INTERVAL_S = 2
DB_FILE = Path.home() / "iiot" / "data" / "ps01.db"
FORWARD_URL = "http://192.168.4.12:8080/readings"  # your neighbour's Pi, plant side

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(threadName)s %(levelname)s %(message)s")
log = logging.getLogger("gateway")


@dataclass
class Reading:
    ts: str
    station: str
    gateway: str
    tank_level_pct: float
    pump_temp_c: float | None
    status: str


class PumpStationSimulator:
    """Simulated sensors. On Day 2 a Modbus class with the same read() replaces it."""

    def __init__(self, station: str, start_level: float = 60.0):
        self.station = station
        self.level = start_level
        self.gateway = socket.gethostname()

    def _read_pump_temp(self) -> float:
        if random.random() < 0.02:
            raise IOError("pump temperature sensor not responding")
        return round(random.gauss(45.0, 1.5), 1)

    def read(self) -> Reading:
        self.level = max(0.0, min(100.0, self.level + random.uniform(-1.5, 1.5)))
        try:
            temp, status = self._read_pump_temp(), "OK"
        except IOError as err:
            temp, status = None, "SENSOR_FAULT"
            log.warning("Read failed: %s", err)
        return Reading(
            ts=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            station=self.station,
            gateway=self.gateway,
            tank_level_pct=round(self.level, 1),
            pump_temp_c=temp,
            status=status,
        )


def sensor_loop(sim: PumpStationSimulator, q: queue.Queue, stop: threading.Event) -> None:
    while not stop.is_set():
        q.put(sim.read())
        stop.wait(INTERVAL_S)


def store_and_forward_loop(q: queue.Queue, stop: threading.Event) -> None:
    db = sqlite3.connect(DB_FILE)  # a connection belongs to the thread that made it
    db.execute(
        "CREATE TABLE IF NOT EXISTS readings ("
        "ts TEXT, station TEXT, gateway TEXT, tank_level_pct REAL, pump_temp_c REAL, status TEXT)"
    )
    session = requests.Session()

    while not stop.is_set():
        try:
            reading = q.get(timeout=1)
        except queue.Empty:
            continue

        db.execute(
            "INSERT INTO readings VALUES (:ts, :station, :gateway, :tank_level_pct, :pump_temp_c, :status)",
            asdict(reading),
        )
        db.commit()

        try:
            response = session.post(FORWARD_URL, json=asdict(reading), timeout=2)
            response.raise_for_status()
            log.info("Stored and forwarded %s (queue: %d)", reading.ts, q.qsize())
        except requests.RequestException as err:
            log.warning("Stored locally, forward failed (queue: %d): %s", q.qsize(), type(err).__name__)

    db.close()


def main() -> None:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    q: queue.Queue = queue.Queue()
    threads = [
        threading.Thread(target=sensor_loop, args=(PumpStationSimulator(STATION), q, stop), name="sensor"),
        threading.Thread(target=store_and_forward_loop, args=(q, stop), name="store"),
    ]
    for t in threads:
        t.start()
    log.info("Gateway started, forwarding to %s", FORWARD_URL)

    try:
        while not stop.is_set():
            stop.wait(1)
    except KeyboardInterrupt:
        stop.set()

    for t in threads:
        t.join()
    log.info("Gateway stopped cleanly")


if __name__ == "__main__":
    main()
