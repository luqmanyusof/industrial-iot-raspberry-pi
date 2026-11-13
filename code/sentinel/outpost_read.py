#!/usr/bin/env python3
"""Op SENTINEL: read the outposts from the ESP32 plant, raw and scaled.

  python outpost_read.py                     all three outposts
  python outpost_read.py --outpost bravo     BRAVO only
  python outpost_read.py --host 127.0.0.1 --port 5020   your practice copy (sentinel_sim.py)
"""
import argparse
import sys

from pymodbus.client import ModbusTcpClient

BASES = {"alpha": 10, "bravo": 20, "charlie": 30}       # each outpost's first register


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="192.168.4.1")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument("--outpost", choices=BASES, help="default: all three")
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=2)
    if not client.connect():
        sys.exit(f"Cannot connect to {args.host}:{args.port}")
    for name in ([args.outpost] if args.outpost else BASES):
        base = BASES[name]
        ir = client.read_input_registers(base, count=4)       # fuel, water, shelter temp, data age
        di = client.read_discrete_inputs(base, count=3)       # generator, gate, link OK
        if ir.isError() or di.isError():
            print(f"{name.upper():<8} read failed: {ir if ir.isError() else di}")
            continue
        fuel, water, temp, age = ir.registers
        generator, gate, link = di.bits[0], di.bits[1], di.bits[2]
        print(f"{name.upper():<8} link {'OK  ' if link else 'LOST'}  fuel {fuel / 10:5.1f} %  water {water / 10:5.1f} %  "
              f"shelter {temp / 10:4.1f} °C  generator {'running' if generator else 'STOPPED'}  "
              f"gate {'OPEN' if gate else 'shut'}  data age {age} s")
    client.close()


if __name__ == "__main__":
    main()
