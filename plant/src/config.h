#pragma once
// ---------- Plant Wi-Fi (the plant network, PS01-PLANT) ----------
#define PLANT_SSID      "PS01-PLANT"
#define PLANT_PASSWORD  "CHANGE-ME-12345"   // at least 8 characters; write it on the whiteboard
#define PLANT_CHANNEL   6
#define PLANT_MAX_STA   8                   // Wi-Fi clients: 3 Pis plus spares

// ---------- Pins on the ROBO ESP32 (check against your wiring) ----------
#define PIN_KNOB        32   // Grove ADC1 port (D32/D33). If the level never moves, try 33.
#define PIN_DHT         26   // Grove Port 3 (D26/D25). If temperature stays a fault, try 25.
#define PIN_ESTOP_BTN   34   // onboard button, input-only pin, pressed = LOW
#define PIN_RESET_BTN   35   // onboard button, input-only pin, pressed = LOW
#define PIN_NEOPIXEL    15   // onboard RGB LED (the stack light)
#define PIN_BUZZER      23   // onboard piezo (the alarm horn); the mute switch silences it
#define PIN_SERVO       4    // servo header 1 (the outlet valve)
#define NEOPIXEL_COUNT  2    // ROBO ESP32 has 2 onboard NeoPixels
