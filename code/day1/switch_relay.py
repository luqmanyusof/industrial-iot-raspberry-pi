#!/usr/bin/env python3
"""Input drives output: the relay on GPIO27 (pin 13) follows the switch on GPIO17 (pin 11).

Jumper GPIO17 to GND (pin 9) = switch closed = relay ON. Pull the jumper = relay OFF.
"""
from signal import pause

from gpiozero import Button, OutputDevice

RELAY_ACTIVE_HIGH = True  # use the value you found with relay_test.py

switch = Button(17, pull_up=True, bounce_time=0.05)
relay = OutputDevice(27, active_high=RELAY_ACTIVE_HIGH, initial_value=False)


def closed() -> None:
    relay.on()
    print("Switch CLOSED -> relay ON")


def opened() -> None:
    relay.off()
    print("Switch OPEN   -> relay OFF")


switch.when_pressed = closed
switch.when_released = opened
if switch.is_pressed:
    closed()

print("Relay follows the switch - Ctrl+C to stop")
try:
    pause()
finally:
    relay.off()
