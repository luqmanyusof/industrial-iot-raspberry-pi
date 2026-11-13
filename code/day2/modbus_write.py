#!/usr/bin/env python3
"""Command the PS-01 plant: stack light, outlet valve, alarm horn.

Examples:
  python modbus_write.py --light red
  python modbus_write.py --valve 40
  python modbus_write.py --horn on
"""
import argparse
import sys

from pymodbus.client import ModbusTcpClient

LIGHTS = {"off": 0, "green": 1, "amber": 2, "red": 3}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="192.168.4.1")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--light", choices=LIGHTS)
    parser.add_argument("--valve", type=int, metavar="0-100")
    parser.add_argument("--horn", choices=["on", "off"])
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=2)
    if not client.connect():
        sys.exit(f"Cannot connect to {args.host}:{args.port}")

    results = []
    if args.light:
        results.append(("stack light", client.write_register(0, LIGHTS[args.light])))     # FC 06, HR0
    if args.valve is not None:
        results.append(("valve", client.write_register(1, args.valve)))                   # FC 06, HR1
    if args.horn:
        results.append(("horn", client.write_coil(0, args.horn == "on")))                 # FC 05, C0
    client.close()

    for name, resp in results:
        print(f"{name}: {'FAILED ' + str(resp) if resp.isError() else 'written'}")


if __name__ == "__main__":
    main()
