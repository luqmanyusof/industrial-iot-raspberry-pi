#!/usr/bin/env python3
"""Read the PS-01 door switch: jumper GPIO17 (pin 11) to GND (pin 9) = door closed."""
from signal import pause

from gpiozero import Button

door = Button(17, pull_up=True, bounce_time=0.05)
door.when_pressed = lambda: print("Door CLOSED")
door.when_released = lambda: print("Door OPEN")

print("Door is", "CLOSED" if door.is_pressed else "OPEN", "- Ctrl+C to stop")
pause()
