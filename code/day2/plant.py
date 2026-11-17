#!/usr/bin/env python3
"""The PS-01 plant over Modbus TCP: one class that reads and commands it, one that decides the alarm."""
import logging
import socket
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

log = logging.getLogger("plant")

ALARM_CODES = {"NORMAL": 0, "WARN": 1, "HIGH": 2}   # HR0: shown on the plant's OLED


@dataclass
class Reading:
    ts: str
    station: str
    gateway: str
    tank_level_pct: float | None
    room_temp_c: float | None
    room_humidity_pct: float | None
    e_stop: bool | None
    pump1_on: bool | None
    pump2_on: bool | None
    status: str                 # OK, SENSOR_FAULT or COMMS_FAULT


class ModbusPlant:
    """Reads the plant's registers and writes its outputs. Same read() as Day 1's simulator.

    One Modbus connection, used by two threads (polling, and pump commands from MQTT): a lock
    makes sure only one of them talks to the plant at a time.
    """

    def __init__(self, host: str, port: int = 502, station: str = "PS-01"):
        self.station = station
        self.gateway = socket.gethostname()
        self.client = ModbusTcpClient(host, port=port, timeout=1, retries=1)
        self.lock = threading.Lock()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def read(self) -> Reading:
        try:
            with self.lock:
                if not self.client.connected:
                    self.client.connect()
                ir = self.client.read_input_registers(0, count=4)  # level, temp, humidity, uptime
                di = self.client.read_discrete_inputs(0, count=2)  # e-stop, sensor fault
                co = self.client.read_coils(0, count=3)            # horn, pump 1, pump 2
            for resp in (ir, di, co):
                if resp.isError():
                    raise ModbusException(f"plant answered with an error: {resp}")
        except (ModbusException, OSError) as err:
            log.warning("Plant not answering: %s", err)
            self.client.close()                                    # start clean next time
            return Reading(self._now(), self.station, self.gateway, None, None, None, None, None, None,
                           "COMMS_FAULT")

        level, temp, hum, _uptime = ir.registers
        e_stop, sensor_fault = di.bits[0], di.bits[1]
        return Reading(
            ts=self._now(),
            station=self.station,
            gateway=self.gateway,
            tank_level_pct=level / 10,
            room_temp_c=None if sensor_fault else temp / 10,
            room_humidity_pct=None if sensor_fault else hum / 10,
            e_stop=e_stop,
            pump1_on=co.bits[1],
            pump2_on=co.bits[2],
            status="SENSOR_FAULT" if sensor_fault else "OK",
        )

    def set_outputs(self, alarm_code: int, horn: bool) -> bool:
        """Write the alarm state and the horn. Returns False if the plant did not accept it."""
        try:
            with self.lock:
                r1 = self.client.write_register(0, alarm_code)     # HR0
                r2 = self.client.write_coil(0, horn)               # C0
            return not (r1.isError() or r2.isError())
        except (ModbusException, OSError) as err:
            log.warning("Could not write outputs: %s", err)
            return False

    def set_pump(self, pump: int, on: bool) -> bool:
        """Start (on=True) or stop pump 1 or 2. Returns False if the plant did not accept it."""
        try:
            with self.lock:
                if not self.client.connected:
                    self.client.connect()
                resp = self.client.write_coil(pump, on)            # C1 = pump 1, C2 = pump 2
            return not resp.isError()
        except (ModbusException, OSError) as err:
            log.warning("Could not switch pump %d: %s", pump, err)
            return False


class LevelAlarm:
    """High-level alarm with hysteresis, so the light does not flicker at the limit."""

    HIGH_ON, HIGH_OFF = 90.0, 85.0
    WARN_ON, WARN_OFF = 80.0, 75.0

    def __init__(self):
        self.state = "NORMAL"

    def update(self, level: float) -> str:
        if level >= self.HIGH_ON or (self.state == "HIGH" and level >= self.HIGH_OFF):
            self.state = "HIGH"
        elif level >= self.WARN_ON or (self.state in ("HIGH", "WARN") and level >= self.WARN_OFF):
            self.state = "WARN"
        else:
            self.state = "NORMAL"
        return self.state

    @staticmethod
    def outputs(state: str) -> tuple[int, bool]:
        """(alarm code for HR0, horn) for each alarm state. Only HIGH sounds the horn."""
        return ALARM_CODES[state], state == "HIGH"
