#!/usr/bin/env python3
"""Command the PS-01 plant: pump 1, pump 2, outlet valve, alarm horn.

Examples:
  python modbus_write.py --pump1 on
  python modbus_write.py --pump2 off
  python modbus_write.py --valve 40
  python modbus_write.py --horn on
"""
import argparse
import sys

from pymodbus.client import ModbusTcpClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="192.168.4.1")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--pump1", choices=["on", "off"])
    parser.add_argument("--pump2", choices=["on", "off"])
    parser.add_argument("--valve", type=int, metavar="0-100")
    parser.add_argument("--horn", choices=["on", "off"])
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=2)
    if not client.connect():
        sys.exit(f"Cannot connect to {args.host}:{args.port}")

    results = []
    if args.pump1:
        results.append(("pump 1", client.write_coil(1, args.pump1 == "on")))             # FC 05, C1
    if args.pump2:
        results.append(("pump 2", client.write_coil(2, args.pump2 == "on")))             # FC 05, C2
    if args.valve is not None:
        results.append(("valve", client.write_register(1, args.valve)))                  # FC 06, HR1
    if args.horn:
        results.append(("horn", client.write_coil(0, args.horn == "on")))                # FC 05, C0
    client.close()

    for name, resp in results:
        print(f"{name}: {'FAILED ' + str(resp) if resp.isError() else 'written'}")


if __name__ == "__main__":
    main()
