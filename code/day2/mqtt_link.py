#!/usr/bin/env python3
"""One place for MQTT settings. Every program connects the same way, from ~/iiot/mqtt.json.

Adding logins to the broker (Topic 11) changes only that file, never the programs.
"""
import json
import logging
import socket
from pathlib import Path
from typing import Callable

import paho.mqtt.client as mqtt

CONFIG_FILE = Path.home() / "iiot" / "mqtt.json"
GATEWAY = socket.gethostname()
BASE = f"ps01/{GATEWAY}"                 # every topic this Pi publishes starts here

log = logging.getLogger("mqtt")


def make_client(role: str, will: tuple[str, str] | None = None,
                on_connect: Callable[[mqtt.Client], None] | None = None) -> mqtt.Client:
    """Create, configure and start an MQTT client for one program (role = gateway, pump, ...)."""
    cfg = json.loads(CONFIG_FILE.read_text())
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{GATEWAY}-{role}")

    login = cfg.get("logins", {}).get(role)
    if login:
        client.username_pw_set(login["username"], login["password"])
    if will:
        client.will_set(will[0], will[1], qos=1, retain=True)

    def _on_connect(c, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.warning("MQTT broker refused us: %s", reason_code)
            return
        log.info("MQTT connected to %s:%s as %s", cfg["host"], cfg["port"], login["username"] if login else "anonymous")
        if on_connect:
            on_connect(c)

    def _on_disconnect(c, userdata, flags, reason_code, properties):
        log.warning("MQTT disconnected: %s", reason_code)

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    client.connect_async(cfg["host"], cfg["port"], keepalive=10)
    client.loop_start()                                        # network traffic runs in its own thread
    return client
