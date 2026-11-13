/*
 * PS-01 plant: a Modbus TCP field device for the Industrial IoT course.
 *
 * Runs the plant Wi-Fi access point (PS01-PLANT, 192.168.4.1) and a Modbus TCP server on port 502.
 *
 *   Input registers (FC 04, read-only, value x 10)
 *     IR0  tank level      0..1000  = 0.0..100.0 %   (rotary knob)
 *     IR1  room temp       e.g. 285 = 28.5 C         (DHT11)
 *     IR2  room humidity   e.g. 650 = 65.0 %         (DHT11)
 *     IR3  uptime          seconds since boot, wraps at 65535
 *   Discrete inputs (FC 02, read-only)
 *     DI0  e-stop active   latched by button 34, cleared by button 35
 *     DI1  sensor fault    DHT11 did not answer
 *   Coils (FC 01 read, FC 05 write)
 *     C0   alarm horn      buzzer beeps while ON
 *   Holding registers (FC 03 read, FC 06 write)
 *     HR0  stack light     0 off, 1 green, 2 amber, 3 red
 *     HR1  outlet valve    0..100 % open (servo 0..180 degrees)
 *
 * Local safety wins: while the e-stop is active the valve is forced shut, the light flashes red and the
 * horn sounds, whatever the gateways write. Their writes are kept and take effect again after RESET.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <ModbusIP_ESP8266.h>
#include <Adafruit_NeoPixel.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <U8g2lib.h>
#include "config.h"

enum { IR_LEVEL = 0, IR_TEMP, IR_HUM, IR_UPTIME };
enum { DI_ESTOP = 0, DI_FAULT };
enum { C_HORN = 0 };
enum { HR_LIGHT = 0, HR_VALVE };

ModbusIP mb;
Adafruit_NeoPixel pixels(NEOPIXEL_COUNT, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
DHT dht(PIN_DHT, DHT11);
Servo valve;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

bool estop = false;
float levelFiltered = 0;
uint32_t tKnob = 0, tDht = 0, tOled = 0, tBlink = 0;
bool blinkOn = false;
int lastServoAngle = -1;

const IPAddress PLANT_IP(192, 168, 4, 1);
const IPAddress PLANT_MASK(255, 255, 255, 0);

void readKnob() {
  // 12-bit ADC: 0..4095 -> 0..1000 (tenths of a percent), lightly filtered so the value does not jitter
  float raw = analogRead(PIN_KNOB) * 1000.0f / 4095.0f;
  levelFiltered = levelFiltered * 0.8f + raw * 0.2f;
  mb.Ireg(IR_LEVEL, (uint16_t)(levelFiltered + 0.5f));
}

void readDht() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  bool fault = isnan(t) || isnan(h);
  mb.Ists(DI_FAULT, fault);
  if (!fault) {
    mb.Ireg(IR_TEMP, (uint16_t)lroundf(t * 10));
    mb.Ireg(IR_HUM, (uint16_t)lroundf(h * 10));
  }
}

void readButtons() {
  if (digitalRead(PIN_ESTOP_BTN) == LOW && !estop) {
    estop = true;
    Serial.println("E-STOP pressed");
  }
  if (digitalRead(PIN_RESET_BTN) == LOW && estop) {
    estop = false;
    Serial.println("E-STOP reset");
  }
  mb.Ists(DI_ESTOP, estop);
}

uint32_t lightColour(uint16_t code) {
  switch (code) {
    case 1: return pixels.Color(0, 120, 0);     // green
    case 2: return pixels.Color(140, 70, 0);    // amber
    case 3: return pixels.Color(160, 0, 0);     // red
    default: return 0;                          // off
  }
}

void driveOutputs() {
  uint16_t light = mb.Hreg(HR_LIGHT);
  uint16_t valvePct = mb.Hreg(HR_VALVE);
  if (light > 3) mb.Hreg(HR_LIGHT, light = 3);           // clamp bad writes, and show the clamped value
  if (valvePct > 100) mb.Hreg(HR_VALVE, valvePct = 100);
  bool horn = mb.Coil(C_HORN);

  if (estop) {                                           // local safety overrides remote commands
    valvePct = 0;
    horn = true;
  }

  int angle = map(valvePct, 0, 100, 0, 180);
  if (angle != lastServoAngle) {
    valve.write(angle);
    lastServoAngle = angle;
  }

  uint32_t colour = estop ? (blinkOn ? lightColour(3) : 0) : lightColour(light);
  for (int i = 0; i < NEOPIXEL_COUNT; i++) pixels.setPixelColor(i, colour);
  pixels.show();

  if (horn && blinkOn) tone(PIN_BUZZER, 2000);
  else noTone(PIN_BUZZER);
}

void drawOled() {
  char line[32];
  oled.clearBuffer();
  oled.setFont(u8g2_font_6x12_tr);
  oled.drawStr(0, 10, estop ? "PS-01  ** E-STOP **" : "PS-01  plant running");
  snprintf(line, sizeof line, "Level  %5.1f %%", mb.Ireg(IR_LEVEL) / 10.0);
  oled.drawStr(0, 24, line);
  if (mb.Ists(DI_FAULT)) snprintf(line, sizeof line, "Temp   SENSOR FAULT");
  else snprintf(line, sizeof line, "Temp   %4.1f C  %2.0f %%", mb.Ireg(IR_TEMP) / 10.0, mb.Ireg(IR_HUM) / 10.0);
  oled.drawStr(0, 36, line);
  static const char *names[] = {"off", "green", "amber", "red"};
  snprintf(line, sizeof line, "Valve  %3u %%  %s", estop ? 0 : mb.Hreg(HR_VALVE), names[min<uint16_t>(mb.Hreg(HR_LIGHT), 3)]);
  oled.drawStr(0, 48, line);
  snprintf(line, sizeof line, "Wi-Fi clients: %d", WiFi.softAPgetStationNum());
  oled.drawStr(0, 62, line);
  oled.sendBuffer();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ESTOP_BTN, INPUT);
  pinMode(PIN_RESET_BTN, INPUT);
  analogReadResolution(12);

  pixels.begin();
  pixels.clear();
  pixels.show();
  dht.begin();
  valve.attach(PIN_SERVO, 500, 2500);
  valve.write(0);
  oled.begin();

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(PLANT_IP, PLANT_IP, PLANT_MASK);
  WiFi.softAP(PLANT_SSID, PLANT_PASSWORD, PLANT_CHANNEL, 0, PLANT_MAX_STA);
  Serial.printf("Plant Wi-Fi %s up at %s\n", PLANT_SSID, WiFi.softAPIP().toString().c_str());

  mb.server();                     // Modbus TCP on port 502
  mb.addIreg(IR_LEVEL, 0, 4);
  mb.addIsts(DI_ESTOP, false, 2);
  mb.addCoil(C_HORN, false, 1);
  mb.addHreg(HR_LIGHT, 1, 2);      // start: light green, valve shut
  mb.Hreg(HR_VALVE, 0);
}

void loop() {
  mb.task();
  uint32_t now = millis();
  readButtons();
  if (now - tKnob >= 200) { tKnob = now; readKnob(); }
  if (now - tDht >= 2000) { tDht = now; readDht(); }   // the DHT11 is slow: never faster than every 2 s
  if (now - tBlink >= 300) { tBlink = now; blinkOn = !blinkOn; }
  mb.Ireg(IR_UPTIME, (uint16_t)((now / 1000) & 0xFFFF));
  driveOutputs();
  if (now - tOled >= 500) { tOled = now; drawOled(); }
}
