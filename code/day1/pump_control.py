#!/usr/bin/env python3
"""PS-01 pump control: START/STOP with a door interlock, fail-safe by design.

Wiring (jumpers go to GND only):
  door switch  GPIO17 (pin 11)  -> GND (pin 9)   jumper in place = door closed
  START        GPIO22 (pin 15)  -> GND (pin 14)  touch briefly
  STOP         GPIO23 (pin 16)  -> GND (pin 20)  touch briefly
  relay IN     GPIO27 (pin 13); relay VCC -> 5V (pin 2); relay GND -> GND (pin 6)
"""
import logging
import signal
import sys
from signal import pause

from gpiozero import Button, OutputDevice

RELAY_ACTIVE_HIGH = True  # set to False if your relay switches ON when the program starts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pump_control")

door = Button(17, pull_up=True, bounce_time=0.05)
start_button = Button(22, pull_up=True, bounce_time=0.05)
stop_button = Button(23, pull_up=True, bounce_time=0.05)
pump = OutputDevice(27, active_high=RELAY_ACTIVE_HIGH, initial_value=False)


def start() -> None:
    if not door.is_pressed:
        log.warning("START refused: door is open")
        return
    if stop_button.is_pressed:
        log.warning("START refused: STOP is held")
        return
    if not pump.is_active:
        pump.on()
        log.info("Pump ON")


def stop(reason: str) -> None:
    if pump.is_active:
        pump.off()
        log.info("Pump OFF (%s)", reason)


def door_opened() -> None:
    log.warning("Door OPEN")
    stop("door opened")


start_button.when_pressed = start
stop_button.when_pressed = lambda: stop("STOP pressed")
door.when_released = door_opened
door.when_pressed = lambda: log.info("Door closed")

signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

log.info("Pump control ready. Door is %s, pump is OFF", "closed" if door.is_pressed else "OPEN")
try:
    pause()
finally:
    pump.off()
    log.info("Pump control stopped, pump OFF")
