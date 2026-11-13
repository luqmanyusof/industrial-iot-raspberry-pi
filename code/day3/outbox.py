#!/usr/bin/env python3
"""Store-and-forward: every message waits in an SQLite outbox until the broker has confirmed it."""
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

from mqtt_link import GATEWAY

log = logging.getLogger("outbox")

BATCH = 20                 # messages read from the outbox at a time
RATE_PER_S = 20            # catch up after an outage, but do not flood the broker
KEEP_SENT = timedelta(hours=24)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_table(db: sqlite3.Connection) -> None:
    db.execute("PRAGMA journal_mode=WAL")          # readers and one writer can work at the same time
    db.execute(
        "CREATE TABLE IF NOT EXISTS outbox ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, topic TEXT, payload TEXT, "
        "qos INTEGER, retain INTEGER, sent_at TEXT)"
    )


def add(db: sqlite3.Connection, topic: str, payload: dict, qos: int = 1, retain: bool = False) -> None:
    """Queue a message. Call it inside the caller's transaction, then commit once."""
    db.execute("INSERT INTO outbox (created, topic, payload, qos, retain) VALUES (?, ?, ?, ?, ?)",
               (now_utc(), topic, json.dumps(payload), qos, int(retain)))


def pending(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COUNT(*) FROM outbox WHERE sent_at IS NULL").fetchone()[0]


def forward_loop(db_file: Path, client: mqtt.Client, stop: threading.Event) -> None:
    """Send waiting messages, oldest first. Mark each one sent only after the broker has acknowledged it."""
    db = sqlite3.connect(db_file, timeout=10)
    create_table(db)
    last_cleanup = 0.0                                          # run housekeeping on the first quiet moment
    while not stop.is_set():
        if not client.is_connected():
            stop.wait(1)
            continue

        rows = db.execute("SELECT id, topic, payload, qos, retain FROM outbox WHERE sent_at IS NULL "
                          "ORDER BY id LIMIT ?", (BATCH,)).fetchall()
        if not rows:                                            # nothing waiting
            stop.wait(0.5)
            if time.monotonic() - last_cleanup > 3600:          # once an hour, keep the SD card tidy
                cutoff = (datetime.now(timezone.utc) - KEEP_SENT).isoformat(timespec="seconds")
                deleted = db.execute("DELETE FROM outbox WHERE sent_at IS NOT NULL AND sent_at < ?",
                                     (cutoff,)).rowcount
                db.commit()
                last_cleanup = time.monotonic()
                if deleted:
                    log.info("Housekeeping: removed %d sent messages older than 24 h", deleted)
            continue

        for row_id, topic, payload, qos, retain in rows:
            message = json.loads(payload)
            message["msg_id"] = f"{GATEWAY}-{row_id}"            # lets receivers spot duplicates
            info = client.publish(topic, json.dumps(message), qos=qos, retain=bool(retain))
            try:
                info.wait_for_publish(5)
            except (RuntimeError, ValueError):
                break                                           # not connected any more: try again later
            if not info.is_published():
                break
            db.execute("UPDATE outbox SET sent_at = ? WHERE id = ?", (now_utc(), row_id))
            db.commit()
            stop.wait(1 / RATE_PER_S)

        backlog = pending(db)
        if backlog > BATCH:
            log.info("Catching up: %d messages still waiting", backlog)
    db.close()
