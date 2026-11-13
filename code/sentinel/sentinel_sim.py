#!/usr/bin/env python3
"""Op SENTINEL: three simulated forward-operating-base outposts behind one Modbus TCP server.

Runs on the trainer's Pi (pi00). Participants poll 192.168.4.10, port 5020:
  unit 1 = ALPHA, unit 2 = BRAVO, unit 3 = CHARLIE

Per outpost (same map for every unit):
  IR0 generator fuel     % x 10      IR2 shelter temperature  °C x 10
  IR1 water tank         % x 10      IR3 uptime               seconds, wraps at 65535
  DI0 generator running  1 = running
  DI1 perimeter gate     1 = open

Type commands while it runs (help for the list), for example:  leak charlie
"""
import argparse
import asyncio
import logging
import math
import random
import struct
import sys
import time
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sentinel")

ILLEGAL_FUNCTION, ILLEGAL_ADDRESS = 1, 2


@dataclass
class Outpost:
    name: str
    fuel: float
    water: float
    temp: float = 27.0
    generator: bool = True
    gate_open: bool = False
    gate_until: float = 0.0       # when a patrol's gate opening ends by itself
    leak: bool = False
    silent: bool = False          # stops answering Modbus, like a lost radio link
    started: float = 0.0

    def step(self, t: float, dt: float) -> None:
        burn = 0.01 if self.generator else 0.0                  # % per second while the generator runs
        if self.leak:
            burn += 0.25
        self.fuel = max(0.0, self.fuel - burn * dt)
        if self.fuel == 0.0:
            self.generator = False                              # out of fuel
        self.water = max(0.0, self.water - (0.006 + random.uniform(0, 0.004)) * dt)
        ambient = 29 + 3 * math.sin(t / 600) + random.uniform(-0.2, 0.2)
        target = ambient - 5 if self.generator else ambient + 10  # air-conditioning needs the generator
        self.temp += (target - self.temp) * 0.01 * dt
        if not self.gate_open and random.random() < dt / 1200:   # now and then a patrol goes out
            self.gate_open, self.gate_until = True, t + 20
        if self.gate_until and t >= self.gate_until:
            self.gate_open, self.gate_until = False, 0.0

    def inputs(self, now: float) -> list[int]:
        return [round(self.fuel * 10), round(self.water * 10), round(self.temp * 10),
                int(now - self.started) & 0xFFFF]

    def discretes(self) -> list[bool]:
        return [self.generator, self.gate_open]


OUTPOSTS = {1: Outpost("ALPHA", fuel=82, water=74), 2: Outpost("BRAVO", fuel=57, water=41),
            3: Outpost("CHARLIE", fuel=34, water=63)}
BY_NAME = {o.name.lower(): o for o in OUTPOSTS.values()}


def pack_bits(bits: list[bool]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        if b:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def handle(unit: int, pdu: bytes) -> bytes | None:
    """Answer one request for one outpost. None = stay silent (no reply at all)."""
    outpost = OUTPOSTS.get(unit)
    if outpost is None or outpost.silent:
        return None
    fc = pdu[0]
    if fc not in (2, 4):                                 # this scenario is read-only
        return bytes([fc | 0x80, ILLEGAL_FUNCTION])
    addr, count = struct.unpack(">HH", pdu[1:5])
    table = outpost.inputs(time.monotonic()) if fc == 4 else outpost.discretes()
    if count < 1 or addr + count > len(table):
        return bytes([fc | 0x80, ILLEGAL_ADDRESS])
    values = table[addr:addr + count]
    data = struct.pack(f">{count}H", *values) if fc == 4 else pack_bits(values)
    return bytes([fc, len(data)]) + data


async def serve_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")[0]
    log.info("Station connected: %s", peer)
    try:
        while True:
            tid, pid, length, unit = struct.unpack(">HHHB", await reader.readexactly(7))
            reply = handle(unit, await reader.readexactly(length - 1))
            if reply is not None:
                writer.write(struct.pack(">HHHB", tid, pid, len(reply) + 1, unit) + reply)
                await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass
    finally:
        log.info("Station disconnected: %s", peer)
        writer.close()


def show() -> None:
    for unit, o in OUTPOSTS.items():
        flags = [f for f, on in (("LEAK", o.leak), ("SILENT", o.silent)) if on]
        print(f"  unit {unit} {o.name:<8} fuel {o.fuel:5.1f} %  water {o.water:5.1f} %  temp {o.temp:4.1f} C  "
              f"generator {'ON ' if o.generator else 'OFF'}  gate {'OPEN' if o.gate_open else 'shut'}  "
              f"{' '.join(flags)}", flush=True)


HELP = """Commands (outpost = alpha, bravo or charlie):
  status                  show all outposts
  leak <outpost>          fuel starts leaking fast       refuel <outpost>    fuel back to 95 %, leak fixed
  genfail <outpost>       generator stops (shelter heats) genstart <outpost>  generator restarts
  gate <outpost>          open or shut the perimeter gate resupply <outpost>  water back to 95 %
  silence <outpost>       outpost stops answering         restore <outpost>   outpost answers again
  quit"""


def command(line: str) -> bool:
    words = line.lower().split()
    if not words:
        return True
    cmd, target = words[0], BY_NAME.get(words[1]) if len(words) > 1 else None
    if cmd in ("quit", "exit"):
        return False
    if cmd == "status":
        show()
    elif cmd == "help" or target is None:
        print(HELP, flush=True)
    else:
        actions = {
            "leak": lambda o: setattr(o, "leak", True),
            "refuel": lambda o: (setattr(o, "fuel", 95.0), setattr(o, "leak", False),
                                 setattr(o, "generator", True)),
            "genfail": lambda o: setattr(o, "generator", False),
            "genstart": lambda o: setattr(o, "generator", o.fuel > 0),
            "gate": lambda o: (setattr(o, "gate_open", not o.gate_open), setattr(o, "gate_until", 0.0)),
            "resupply": lambda o: setattr(o, "water", 95.0),
            "silence": lambda o: setattr(o, "silent", True),
            "restore": lambda o: setattr(o, "silent", False),
        }
        if cmd not in actions:
            print(HELP, flush=True)
        else:
            actions[cmd](target)
            log.info("INJECT %s %s", cmd.upper(), target.name)
    return True


async def run_outposts() -> None:
    start = last = time.monotonic()
    for o in OUTPOSTS.values():
        o.started = start
    while True:
        await asyncio.sleep(1)
        now = time.monotonic()
        for o in OUTPOSTS.values():
            o.step(now - start, now - last)
        last = now


async def console() -> None:
    loop = asyncio.get_running_loop()
    print(HELP, flush=True)
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if line == "" or not command(line):              # end of input, or quit
            if line == "":
                await asyncio.Event().wait()             # running without a keyboard: keep serving
            raise SystemExit


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=5020)
    args = parser.parse_args()
    server = await asyncio.start_server(serve_client, "0.0.0.0", args.port)
    log.info("Op SENTINEL outposts on port %d: unit 1 ALPHA, 2 BRAVO, 3 CHARLIE", args.port)
    async with server:
        await asyncio.gather(server.serve_forever(), run_outposts(), console())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
