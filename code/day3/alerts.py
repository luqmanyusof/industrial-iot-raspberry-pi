#!/usr/bin/env python3
"""Email alerts through the mail server on this Pi (Postfix on localhost:25)."""
import logging
import queue
import smtplib
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Callable

from mqtt_link import GATEWAY

log = logging.getLogger("alerts")

MAIL_TO = "pelatih"                         # a user on this Pi; Postfix delivers to /var/mail/pelatih
MAIL_FROM = f"ps01-{GATEWAY}@localhost"
REPEAT_GAP_S = 600                          # an alert that clears and returns within 10 min is not emailed again


@dataclass
class Rule:
    key: str
    title: str
    test: Callable                          # (reading, alarm_state) -> bool
    raise_after_s: float                    # must stay true this long before we alert
    detail: Callable                        # (reading) -> str


RULES = [
    Rule("HIGH_LEVEL", "High tank level", lambda r, a: a == "HIGH", 0,
         lambda r: f"Tank level {r.tank_level_pct:.1f} %. Red light and horn are on."),
    Rule("E_STOP", "Emergency stop active", lambda r, a: r.e_stop is True, 0,
         lambda r: "The plant's E-STOP is pressed: valve forced shut."),
    Rule("PLANT_LOST", "Plant not answering", lambda r, a: r.status == "COMMS_FAULT", 60,
         lambda r: "No Modbus answer from the plant for over a minute."),
    Rule("SENSOR_FAULT", "Temperature sensor fault", lambda r, a: r.status == "SENSOR_FAULT", 300,
         lambda r: "The DHT11 has not answered for 5 minutes."),
]


class Mailer:
    """Sends email from its own thread, so a slow or missing mail server never delays polling."""

    def __init__(self, stop: threading.Event):
        self.q: queue.Queue = queue.Queue()
        self.stop = stop
        self.thread = threading.Thread(target=self._run, name="mailer", daemon=True)
        self.thread.start()

    def send(self, subject: str, body: str) -> None:
        self.q.put((subject, body))

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                subject, body = self.q.get(timeout=1)
            except queue.Empty:
                continue
            msg = EmailMessage()
            msg["From"], msg["To"], msg["Subject"] = MAIL_FROM, MAIL_TO, subject
            msg.set_content(body)
            while not self.stop.is_set():
                try:
                    with smtplib.SMTP("localhost", 25, timeout=10) as smtp:
                        smtp.send_message(msg)
                    log.info("Email sent: %s", subject)
                    break
                except (OSError, smtplib.SMTPException) as err:
                    log.warning("Mail server not accepting (%s); retrying in 30 s", err)
                    self.stop.wait(30)


class AlertManager:
    """Raises an alert when a rule has been true long enough, and says when it clears."""

    def __init__(self, mailer: Mailer, on_event: Callable[[dict], None]):
        self.mailer = mailer
        self.on_event = on_event            # also record every alert as an event for the outbox
        self.true_since: dict[str, float] = {}
        self.raised: set[str] = set()
        self.last_email: dict[str, float] = {}
        self.emailed: set[str] = set()     # raised alerts whose RAISED email went out

    def check(self, reading, alarm_state: str) -> None:
        now = time.monotonic()
        for rule in RULES:
            active = bool(rule.test(reading, alarm_state))
            if active:
                self.true_since.setdefault(rule.key, now)
                if rule.key not in self.raised and now - self.true_since[rule.key] >= rule.raise_after_s:
                    self.raised.add(rule.key)
                    self._notify(rule, "RAISED", rule.detail(reading), reading.ts, now)
            else:
                self.true_since.pop(rule.key, None)
                if rule.key in self.raised:
                    self.raised.discard(rule.key)
                    self._notify(rule, "CLEARED", "Back to normal.", reading.ts, now)

    def _notify(self, rule: Rule, change: str, detail: str, ts: str, now: float) -> None:
        self.on_event({"ts": ts, "event": "alert", "alert": rule.key, "change": change, "detail": detail})
        if change == "RAISED":
            if now - self.last_email.get(rule.key, -1e9) < REPEAT_GAP_S:
                log.info("Alert %s raised again within 10 min: not emailed", rule.key)
                return
            self.last_email[rule.key] = now
            self.emailed.add(rule.key)
        elif rule.key in self.emailed:
            self.emailed.discard(rule.key)
        else:
            return                          # its RAISED was not emailed, so neither is its CLEARED
        self.mailer.send(f"[PS-01 {GATEWAY}] {change}: {rule.title}",
                         f"{rule.title}: {change}\n{detail}\n\nGateway: {GATEWAY}\nTime (UTC): {ts}\n")
