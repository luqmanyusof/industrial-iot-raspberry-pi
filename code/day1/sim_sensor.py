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
