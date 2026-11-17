#!/usr/bin/env python3
"""Click the relay on GPIO27 (pin 13) three times."""
from time import sleep

from gpiozero import OutputDevice

RELAY_ACTIVE_HIGH = True  # set to False if the relay is ON while this says OFF

relay = OutputDevice(27, active_high=RELAY_ACTIVE_HIGH, initial_value=False)
print("Relay should be OFF now. Starting in 3 seconds...")
sleep(3)

for _ in range(3):
    relay.on()
    print("ON")
    sleep(1)
    relay.off()
    print("OFF")
    sleep(1)
