#!/usr/bin/env python3
"""A simulated PS-01 plant: the same Modbus register map as the ESP32, on your own Pi.

Run it, then point your programs at --host 127.0.0.1 --port 5020.
It listens on port 5020 instead of 502, because ports below 1024 need root.

It is a small, complete Modbus TCP server written with the standard library only, so you can read
exactly what a field device does with each request.
"""
import argparse
import asyncio
import logging
import math
import random
import struct
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("plant_sim")

# The four Modbus tables, exactly as on the ESP32
coils = [False]                          # C0 alarm horn
discrete = [False, False]                # DI0 e-stop, DI1 sensor fault
holding = [1, 0]                         # HR0 stack light (green), HR1 valve % (shut)
inputs = [0, 0, 0, 0]                    # IR0 level x10, IR1 temp x10, IR2 humidity x10, IR3 uptime s

ILLEGAL_FUNCTION, ILLEGAL_ADDRESS, ILLEGAL_VALUE = 1, 2, 3


def pack_bits(bits: list[bool]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        if b:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def handle(pdu: bytes) -> bytes:
    """Answer one Modbus request (the PDU: function code + data). Returns the response PDU."""
    fc = pdu[0]

    def error(code: int) -> bytes:
        return bytes([fc | 0x80, code])

    if fc in (1, 2, 3, 4):                                   # read coils / discrete / holding / input
        addr, count = struct.unpack(">HH", pdu[1:5])
        table = {1: coils, 2: discrete, 3: holding, 4: inputs}[fc]
        if count < 1 or addr + count > len(table):
            return error(ILLEGAL_ADDRESS)
        values = table[addr:addr + count]
        if fc in (1, 2):
            data = pack_bits(values)
        else:
            data = struct.pack(f">{count}H", *values)
        return bytes([fc, len(data)]) + data

    if fc == 5:                                              # write single coil
        addr, value = struct.unpack(">HH", pdu[1:5])
        if addr >= len(coils):
            return error(ILLEGAL_ADDRESS)
        if value not in (0x0000, 0xFF00):
            return error(ILLEGAL_VALUE)
        coils[addr] = value == 0xFF00
        return pdu[:5]                                       # the response echoes the request

    if fc == 6:                                              # write single holding register
        addr, value = struct.unpack(">HH", pdu[1:5])
        if addr >= len(holding):
            return error(ILLEGAL_ADDRESS)
        holding[addr] = min(value, 3 if addr == 0 else 100)  # clamp like the real plant
        return pdu[:5]

    return error(ILLEGAL_FUNCTION)


async def serve_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")[0]
    log.info("Client connected: %s", peer)
    try:
        while True:
            header = await reader.readexactly(7)             # MBAP header
            tid, pid, length, unit = struct.unpack(">HHHB", header)
            pdu = await reader.readexactly(length - 1)
            reply = handle(pdu)
            writer.write(struct.pack(">HHHB", tid, pid, len(reply) + 1, unit) + reply)
            await writer.drain()
    except (asyncio.IncompleteReadError, ConnectionResetError):
        pass
    finally:
        log.info("Client disconnected: %s", peer)
        writer.close()


async def run_plant() -> None:
    """Move the simulated sensors once a second."""
    start = time.monotonic()
    while True:
        t = time.monotonic() - start
        level = 60 + 30 * math.sin(t / 40) + random.uniform(-1, 1)    # the tank fills and empties
        temp = 28.0 + 1.5 * math.sin(t / 90) + random.uniform(-0.2, 0.2)
        inputs[:] = [round(max(0, min(100, level)) * 10), round(temp * 10),
                     round((65 + random.uniform(-1, 1)) * 10), int(t) & 0xFFFF]
        discrete[1] = random.random() < 0.02                            # the odd failed reading
        log.info("level %5.1f %%  temp %4.1f C  | light %d  valve %3d %%  horn %s",
                 inputs[0] / 10, inputs[1] / 10, holding[0], holding[1], "ON" if coils[0] else "off")
        await asyncio.sleep(1)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5020)
    args = parser.parse_args()
    server = await asyncio.start_server(serve_client, "0.0.0.0", args.port)
    log.info("Simulated PS-01 plant listening on port %d", args.port)
    async with server:
        await asyncio.gather(server.serve_forever(), run_plant())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
