#!/usr/bin/env python3
"""PS-01 pump control with remote commands over MQTT. The local interlock still decides.

Same wiring as Day 1. Subscribes to  ps01/<gateway>/pump/cmd    (START or STOP)
                  publishes        ps01/<gateway>/pump/state  (JSON, retained)
A remote START goes through exactly the same checks as the START jumper.
"""
import json
import logging
import signal
import sys
import threading
from datetime import datetime, timezone

from gpiozero import Button, OutputDevice

from mqtt_link import BASE, make_client

RELAY_ACTIVE_HIGH = True  # use the value you found on Day 1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pump_control")

door = Button(17, pull_up=True, bounce_time=0.05)
start_button = Button(22, pull_up=True, bounce_time=0.05)
stop_button = Button(23, pull_up=True, bounce_time=0.05)
pump = OutputDevice(27, active_high=RELAY_ACTIVE_HIGH, initial_value=False)
lock = threading.Lock()                 # GPIO events and MQTT messages arrive on different threads
client = None


def publish_state(reason: str):
    state = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pump": "ON" if pump.is_active else "OFF",
        "door": "closed" if door.is_pressed else "open",
        "reason": reason,
    }
    if client:
        return client.publish(f"{BASE}/pump/state", json.dumps(state), qos=1, retain=True)
    return None


def start(source: str) -> None:
    with lock:
        if not door.is_pressed:
            reason = f"START from {source} refused: door is open"
        elif stop_button.is_pressed:
            reason = f"START from {source} refused: STOP is held"
        elif pump.is_active:
            reason = "already running"
        else:
            pump.on()
            reason = f"START from {source}"
        log.info("%s -> pump %s", reason, "ON" if pump.is_active else "OFF")
        publish_state(reason)


def stop(reason: str) -> None:
    with lock:
        if pump.is_active:
            pump.off()
        log.info("%s -> pump OFF", reason)
        publish_state(reason)


def door_opened() -> None:
    log.warning("Door OPEN")
    stop("door opened")


def on_command(c, userdata, msg) -> None:
    command = msg.payload.decode(errors="replace").strip().upper()
    if command == "START":
        start("remote")
    elif command == "STOP":
        stop("STOP from remote")
    else:
        log.warning("Ignored unknown command %r on %s", command, msg.topic)


def on_connect(c) -> None:
    c.subscribe(f"{BASE}/pump/cmd", qos=1)
    publish_state("pump control started")


start_button.when_pressed = lambda: start("local jumper")
stop_button.when_pressed = lambda: stop("STOP from local jumper")
door.when_released = door_opened
door.when_pressed = lambda: (log.info("Door closed"), publish_state("door closed"))

client = make_client("pump", will=(f"{BASE}/pump/state", json.dumps({"pump": "UNKNOWN",
                                                                   "reason": "pump control offline"})),
                     on_connect=on_connect)
client.message_callback_add(f"{BASE}/pump/cmd", on_command)

signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

log.info("Pump control ready. Door is %s, pump is OFF", "closed" if door.is_pressed else "OPEN")
try:
    while True:
        threading.Event().wait(1)       # wake every second, so Ctrl+C and SIGTERM are handled promptly
finally:
    pump.off()
    info = publish_state("pump control stopped")
    try:
        info.wait_for_publish(2)
    except (AttributeError, RuntimeError, ValueError):
        pass
    client.disconnect()
    client.loop_stop()
    log.info("Pump control stopped, pump OFF")
