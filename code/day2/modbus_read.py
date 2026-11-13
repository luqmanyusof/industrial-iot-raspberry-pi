#!/usr/bin/env python3
"""Read every PS-01 register once and print it, raw and scaled."""
import argparse
import sys

from pymodbus.client import ModbusTcpClient

LIGHTS = {0: "off", 1: "green", 2: "amber", 3: "red"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.4.1")
    parser.add_argument("--port", type=int, default=502)
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=2)
    if not client.connect():
        sys.exit(f"Cannot connect to {args.host}:{args.port}")

    ir = client.read_input_registers(0, count=4)       # FC 04
    di = client.read_discrete_inputs(0, count=2)       # FC 02
    co = client.read_coils(0, count=1)                 # FC 01
    hr = client.read_holding_registers(0, count=2)     # FC 03
    client.close()

    for name, resp in (("input registers", ir), ("discrete inputs", di), ("coils", co), ("holding registers", hr)):
        if resp.isError():
            sys.exit(f"Reading {name} failed: {resp}")

    level, temp, hum, uptime = ir.registers
    print(f"{'Register':<6} {'Name':<14} {'Raw':>6}  Value")
    print(f"{'IR0':<6} {'tank_level':<14} {level:>6}  {level / 10:.1f} %")
    print(f"{'IR1':<6} {'room_temp':<14} {temp:>6}  {temp / 10:.1f} °C")
    print(f"{'IR2':<6} {'room_humidity':<14} {hum:>6}  {hum / 10:.1f} %")
    print(f"{'IR3':<6} {'uptime':<14} {uptime:>6}  {uptime} s")
    print(f"{'DI0':<6} {'e_stop':<14} {int(di.bits[0]):>6}  {'ACTIVE' if di.bits[0] else 'clear'}")
    print(f"{'DI1':<6} {'sensor_fault':<14} {int(di.bits[1]):>6}  {'FAULT' if di.bits[1] else 'ok'}")
    print(f"{'C0':<6} {'alarm_horn':<14} {int(co.bits[0]):>6}  {'ON' if co.bits[0] else 'off'}")
    print(f"{'HR0':<6} {'stack_light':<14} {hr.registers[0]:>6}  {LIGHTS.get(hr.registers[0], '?')}")
    print(f"{'HR1':<6} {'valve':<14} {hr.registers[1]:>6}  {hr.registers[1]} % open")


if __name__ == "__main__":
    main()
