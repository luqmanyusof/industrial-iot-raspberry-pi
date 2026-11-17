#pragma once
// ---------- Plant Wi-Fi (the plant network, plant-wifi) ----------
#define PLANT_SSID      "plant-wifi"
#define PLANT_PASSWORD  "Plant0101"         // at least 8 characters; day1.md Topic 2.4 prints it, change both together
#define PLANT_CHANNEL   6
#define PLANT_MAX_STA   8                   // Wi-Fi clients: 3 Pis plus spares

// ---------- Pins on the ROBO ESP32 (check against your wiring) ----------
#define PIN_KNOB        32   // Grove Port 5 (D33/D32): the knob's signal is on D32 (ADC1, works with Wi-Fi on)
#define PIN_DHT         25   // Grove Port 3 (D26/D25): the DHT11's signal is on D25
#define PIN_ESTOP_BTN   34   // onboard button, input-only pin, pressed = LOW
#define PIN_RESET_BTN   35   // onboard button, input-only pin, pressed = LOW
#define PIN_NEOPIXEL    15   // onboard RGB LEDs: LED 0 = pump 1, LED 1 = pump 2
#define PIN_BUZZER      23   // onboard piezo (the alarm horn); the mute switch silences it
#define PIN_SERVO       4    // servo header 1 (the outlet valve)
#define NEOPIXEL_COUNT  2    // ROBO ESP32 has 2 onboard NeoPixels
#define NEOPIXEL_BRIGHTNESS 5   // 0..255; 5 = 2 % of full brightness
