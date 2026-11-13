#!/usr/bin/env python3
"""Op SENTINEL: read the outposts on the trainer's Pi, raw and scaled.

  python outpost_read.py              all three outposts
  python outpost_read.py --unit 2     BRAVO only
"""
import argparse

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

NAMES = {1: "ALPHA", 2: "BRAVO", 3: "CHARLIE"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="192.168.4.10")
    parser.add_argument("--port", type=int, default=5020)
    parser.add_argument("--unit", type=int, choices=NAMES, help="1 ALPHA, 2 BRAVO, 3 CHARLIE (default: all)")
    args = parser.parse_args()

    client = ModbusTcpClient(args.host, port=args.port, timeout=2, retries=1)
    client.connect()
    for unit in ([args.unit] if args.unit else NAMES):
        try:
            ir = client.read_input_registers(0, count=4, device_id=unit)      # device_id = the unit ID
            di = client.read_discrete_inputs(0, count=2, device_id=unit)
            if ir.isError() or di.isError():
                raise ModbusException(str(ir if ir.isError() else di))
        except ModbusException as err:
            print(f"{NAMES[unit]:<8} no answer ({err})")
            client.close()
            client.connect()                       # a timed-out request can leave the connection unusable
            continue
        fuel, water, temp, uptime = ir.registers
        generator, gate = di.bits[0], di.bits[1]
        print(f"{NAMES[unit]:<8} fuel {fuel / 10:5.1f} %  water {water / 10:5.1f} %  shelter {temp / 10:4.1f} °C  "
              f"generator {'running' if generator else 'STOPPED'}  gate {'OPEN' if gate else 'shut'}  "
              f"up {uptime} s")
    client.close()


if __name__ == "__main__":
    main()
