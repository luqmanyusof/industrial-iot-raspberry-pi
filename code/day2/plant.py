#!/usr/bin/env python3
"""The PS-01 plant over Modbus TCP: one class that reads it and one that decides the alarm."""
import logging
import socket
from dataclasses import dataclass
from datetime import datetime, timezone

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

log = logging.getLogger("plant")

LIGHT_OFF, LIGHT_GREEN, LIGHT_AMBER, LIGHT_RED = 0, 1, 2, 3


@dataclass
class Reading:
    ts: str
    station: str
    gateway: str
    tank_level_pct: float | None
    room_temp_c: float | None
    room_humidity_pct: float | None
    e_stop: bool | None
    status: str                 # OK, SENSOR_FAULT or COMMS_FAULT


class ModbusPlant:
    """Reads the plant's registers and writes its outputs. Same read() as Day 1's simulator."""

    def __init__(self, host: str, port: int = 502, station: str = "PS-01"):
        self.station = station
        self.gateway = socket.gethostname()
        self.client = ModbusTcpClient(host, port=port, timeout=1, retries=1)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def read(self) -> Reading:
        try:
            if not self.client.connected:
                self.client.connect()
            ir = self.client.read_input_registers(0, count=4)      # level, temp, humidity, uptime
            di = self.client.read_discrete_inputs(0, count=2)      # e-stop, sensor fault
            if ir.isError() or di.isError():
                raise ModbusException(f"plant answered with an error: {ir if ir.isError() else di}")
        except (ModbusException, OSError) as err:
            log.warning("Plant not answering: %s", err)
            self.client.close()                                    # start clean next time
            return Reading(self._now(), self.station, self.gateway, None, None, None, None, "COMMS_FAULT")

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
            status="SENSOR_FAULT" if sensor_fault else "OK",
        )

    def set_outputs(self, light: int, horn: bool) -> bool:
        """Write the stack light and the horn. Returns False if the plant did not accept it."""
        try:
            r1 = self.client.write_register(0, light)               # HR0
            r2 = self.client.write_coil(0, horn)                    # C0
            return not (r1.isError() or r2.isError())
        except (ModbusException, OSError) as err:
            log.warning("Could not write outputs: %s", err)
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
        """(stack light, horn) for each alarm state."""
        return {"NORMAL": (LIGHT_GREEN, False), "WARN": (LIGHT_AMBER, False), "HIGH": (LIGHT_RED, True)}[state]
