#!/usr/bin/env python3
"""Input drives output: the relay on GPIO27 (pin 13) follows the door switch on GPIO17 (pin 11).

Jumper in place (door closed) = relay ON. Jumper pulled (door open) = relay OFF.
"""
from signal import pause

from gpiozero import Button, OutputDevice

RELAY_ACTIVE_HIGH = True  # use the value you found with relay_test.py

door = Button(17, pull_up=True, bounce_time=0.05)
relay = OutputDevice(27, active_high=RELAY_ACTIVE_HIGH, initial_value=False)


def door_closed() -> None:
    relay.on()
    print("Door CLOSED -> relay ON")


def door_opened() -> None:
    relay.off()
    print("Door OPEN   -> relay OFF")


door.when_pressed = door_closed
door.when_released = door_opened
if door.is_pressed:
    door_closed()

print("The relay follows the door switch - Ctrl+C to stop")
try:
    pause()
finally:
    relay.off()
    print("Stopped, relay OFF")
