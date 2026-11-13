#pragma once
/*
 * Op SENTINEL (Day 3 afternoon): three simulated outposts served by the same Modbus server.
 *
 *   Outpost   base   Input registers (x 10)                         Discrete inputs
 *   ALPHA      10    IR10 fuel %, IR11 water %, IR12 shelter C,      DI10 generator running, DI11 gate open,
 *   BRAVO      20    IR13 data age s                                  DI12 link OK
 *   CHARLIE    30    (same layout from 20 and 30)
 *
 * Events are typed into the USB serial monitor (115200 baud), for example:  leak charlie
 */
#include <Arduino.h>
#include <ModbusIP_ESP8266.h>

struct Outpost {
  const char *name;
  uint16_t base;
  float fuel, water, temp;
  bool generator, gateOpen, leak, silent;
  uint32_t gateUntil;      // millis when a patrol's gate opening ends (0 = none)
  uint32_t lastFresh;      // millis of the last fresh data
};

static Outpost outposts[3] = {
  {"alpha", 10, 82, 74, 27, true, false, false, false, 0, 0},
  {"bravo", 20, 57, 41, 27, true, false, false, false, 0, 0},
  {"charlie", 30, 34, 63, 27, true, false, false, false, 0, 0},
};

static String serialLine;

inline void sentinelBegin(ModbusIP &mb) {
  for (auto &o : outposts) {
    mb.addIreg(o.base, 0, 4);
    mb.addIsts(o.base, false, 3);
  }
  Serial.println("SENTINEL outposts ready. Type 'help' for events.");
}

inline void sentinelPublish(ModbusIP &mb, const Outpost &o, uint32_t now) {
  if (!o.silent) {             // a silent outpost's values freeze, as with a lost radio link
    mb.Ireg(o.base + 0, (uint16_t)lroundf(o.fuel * 10));
    mb.Ireg(o.base + 1, (uint16_t)lroundf(o.water * 10));
    mb.Ireg(o.base + 2, (uint16_t)lroundf(o.temp * 10));
    mb.Ists(o.base + 0, o.generator);
    mb.Ists(o.base + 1, o.gateOpen);
  }
  mb.Ireg(o.base + 3, (uint16_t)min<uint32_t>((now - o.lastFresh) / 1000, 65535));
  mb.Ists(o.base + 2, !o.silent);
}

// Called once a second
inline void sentinelStep(ModbusIP &mb, uint32_t now) {
  float t = now / 1000.0f;
  for (auto &o : outposts) {
    float burn = (o.generator ? 0.01f : 0.0f) + (o.leak ? 0.25f : 0.0f);   // % per second
    o.fuel = max(0.0f, o.fuel - burn);
    if (o.fuel <= 0.0f) o.generator = false;                              // out of fuel
    o.water = max(0.0f, o.water - 0.006f - random(0, 40) / 10000.0f);
    float ambient = 29 + 3 * sinf(t / 600) + random(-20, 21) / 100.0f;
    float target = o.generator ? ambient - 5 : ambient + 10;              // A/C needs the generator
    o.temp += (target - o.temp) * 0.01f;
    if (!o.gateOpen && random(0, 1200) == 0) { o.gateOpen = true; o.gateUntil = now + 20000; }  // a patrol
    if (o.gateUntil && now >= o.gateUntil) { o.gateOpen = false; o.gateUntil = 0; }
    if (!o.silent) o.lastFresh = now;
    sentinelPublish(mb, o, now);
  }
}

inline void sentinelHelp() {
  Serial.println("Events (outpost = alpha, bravo, charlie):");
  Serial.println("  status | leak <o> | refuel <o> | genfail <o> | genstart <o> | gate <o>");
  Serial.println("  resupply <o> | silence <o> | restore <o>");
}

inline void sentinelStatus() {
  for (auto &o : outposts)
    Serial.printf("  %-8s fuel %5.1f%%  water %5.1f%%  temp %4.1fC  gen %s  gate %s%s%s\n", o.name, o.fuel, o.water,
                  o.temp, o.generator ? "ON " : "OFF", o.gateOpen ? "OPEN" : "shut", o.leak ? "  LEAK" : "",
                  o.silent ? "  SILENT" : "");
}

inline void sentinelCommand(String line) {
  line.trim();
  line.toLowerCase();
  int space = line.indexOf(' ');
  String cmd = space < 0 ? line : line.substring(0, space);
  String who = space < 0 ? String("") : line.substring(space + 1);
  if (cmd == "status") { sentinelStatus(); return; }
  Outpost *o = nullptr;
  for (auto &x : outposts) if (who == x.name) o = &x;
  if (o == nullptr) { sentinelHelp(); return; }
  if (cmd == "leak") o->leak = true;
  else if (cmd == "refuel") { o->fuel = 95; o->leak = false; o->generator = true; }
  else if (cmd == "genfail") o->generator = false;
  else if (cmd == "genstart") o->generator = o->fuel > 0;
  else if (cmd == "gate") { o->gateOpen = !o->gateOpen; o->gateUntil = 0; }
  else if (cmd == "resupply") o->water = 95;
  else if (cmd == "silence") o->silent = true;
  else if (cmd == "restore") o->silent = false;
  else { sentinelHelp(); return; }
  Serial.printf("INJECT %s %s\n", cmd.c_str(), o->name);
}

// Called every loop: collect typed characters into a line
inline void sentinelSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialLine.length()) sentinelCommand(serialLine);
      serialLine = "";
    } else if (serialLine.length() < 40) {
      serialLine += c;
    }
  }
}
