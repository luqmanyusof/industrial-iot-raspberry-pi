#!/usr/bin/env python3
"""Draw the Day 2 isometric figures into images/. Run: python3 images/src/build_day2.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso import (P, Scene, caption, dht11, esp32, gap_point, knob, laptop, origin, plate,  # noqa: E402
                 raspberry_pi, shade)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GW, OT = '#fff1c9', '#ffe8d6'
WIFI, DATA = '#1a73e8', '#188038'


def save(sc, name):
    sc.render(os.path.join(OUT, name))
    print('wrote', name)


def at(k, dx, dy, dz=0.0):
    x, y = origin(k)
    return (x + dx, y + dy, dz)


# ---------- Figure 7.1: sensors live inside the field device ----------
def fig_7_1():
    sc = Scene()
    plate(sc, 0, OT, w=190, d=150)
    plate(sc, 1, GW)
    x, y = origin(0)
    knob(sc, x + 15, y + 20)
    dht11(sc, x + 15, y + 95)
    esp32(sc, x + 100, y + 60)
    sc.wire([(x + 41, y + 32, 3), (x + 70, y + 32, 3), (x + 70, y + 70, 3), (x + 100, y + 70, 3)], '#e8710a', 2.5,
            depth=-10)
    sc.wire([(x + 41, y + 105, 3), (x + 70, y + 105, 3), (x + 70, y + 84, 3), (x + 100, y + 84, 3)], '#8e24aa', 2.5,
            depth=-10)
    sc.tag(x + 10, y - 5, 45, 'knob: analog (ADC)', '#e8710a')
    sc.tag(x + 95, y + 160, 0, 'DHT11: single-wire digital', '#8e24aa')
    put_pi = origin(1)
    raspberry_pi(sc, put_pi[0] + 32, put_pi[1] + 47)
    sc.wire([(x + 160, y + 75, 14), gap_point(0, 50, 10), at(1, 50, 50, 22)], WIFI, 2.5, dash='7 6', under=False,
            arrow='end')
    sc.tag(*gap_point(0, 85, 10), 'Modbus TCP over Wi-Fi', WIFI)
    caption(sc, 0, ['Field device (the ESP32 plant)', 'reads its own sensors, each with', 'its own wiring and protocol'],
            OT, w=190, d=150)
    caption(sc, 1, ['Gateway', 'speaks one standard protocol', 'to every field device'], GW)
    save(sc, 'day2-fig-7-1-field-device.svg')


# ---------- Figure 8.1: every Pi polls the one plant ----------
def fig_8_1():
    sc = Scene()
    W, R = 130, 165
    rows = [('pi01', '192.168.4.11'), ('pi02', '192.168.4.12'), ('pi00 (trainer)', '192.168.4.10')]
    ex, ey = 260 + R, -260 + R
    for r, (name, ip) in enumerate(rows):
        qx, qy = r * R, r * R
        sc.box(qx, qy, -3, W, W, 3, GW, depth=-1e6 + qx + qy, outline=False)
        raspberry_pi(sc, qx + 22, qy + 38)
        sc.wire([(qx + 90, qy + 55, 26), (ex + 70, ey + 70, 14)], DATA, 2.4, under=False, arrow='end')
        tx, ty = P(qx, qy + W, 0)
        sc.overlay.append(
            f'<text x="{tx - 14:.1f}" y="{ty - 4:.1f}" font-size="14" font-weight="700" fill="#202124" '
            f'text-anchor="end">{name}</text><text x="{tx - 14:.1f}" y="{ty + 14:.1f}" font-size="12.5" '
            f'fill="#3c4043" text-anchor="end">{ip} · Modbus client</text>')
        sc.pts += [(tx - 220, ty - 20), (tx, ty + 20)]
    sc.tag(*((90 + ex + 70) / 2, (55 + ey + 70) / 2, 45), 'request → ← response, every 2 s', DATA)
    sc.box(ex, ey, -3, W + 20, W + 20, 3, OT, depth=-1e6 + ex + ey, outline=False)
    esp32(sc, ex + 45, ey + 60)
    sc.waves(ex + 103, ey + 75, 14)
    cx, cy = P(ex + W + 20, ey + W + 20, 0)
    sc.overlay.append(f'<text x="{cx:.1f}" y="{cy + 24:.1f}" font-size="14" font-weight="700" '
                      f'fill="{shade(OT, 0.42)}" text-anchor="middle">ESP32 plant · Modbus server</text>'
                      f'<text x="{cx:.1f}" y="{cy + 42:.1f}" font-size="12.5" fill="#3c4043" '
                      f'text-anchor="middle">192.168.4.1, port 502 · answers one request at a time</text>')
    sc.pts += [(cx - 170, cy), (cx + 170, cy + 50)]
    save(sc, 'day2-fig-8-1-polling.svg')


# ---------- Figure 12.1: where everything runs ----------
def fig_12_1():
    sc = Scene()
    IT = '#dfe9fb'
    plate(sc, 0, IT); plate(sc, 1, GW); plate(sc, 2, OT)
    x0, y0 = origin(0)
    laptop(sc, x0 + 40, y0 + 50)
    x1, y1 = origin(1)
    raspberry_pi(sc, x1 + 32, y1 + 47)
    x2, y2 = origin(2)
    esp32(sc, x2 + 43, y2 + 60)
    sc.waves(x2 + 101, y2 + 75, 14)
    sc.wire([(x0 + 115, y0 + 100, 1), gap_point(0, 1, 30), (x1 + 40, y1 + 110, 1), (x1 + 60, y1 + 103, 2)], '#3c4043',
            4, depth=-10)
    sc.wire([(x1 + 110, y1 + 60, 25), gap_point(1, 40), (x2 + 70, y2 + 70, 14)], WIFI, 2.5, dash='7 6', under=False)
    sc.tag(*gap_point(0, 1, 30), 'browser → :1880 (eth0)', '#3c4043')
    sc.tag(*gap_point(1, 75), 'Modbus TCP (wlan0)', WIFI)
    caption(sc, 0, ['Your laptop', 'only a web browser:', 'http://pi01.local:1880/dashboard'], IT)
    caption(sc, 1, ['Your Pi', 'Node-RED · Mosquitto broker (TLS) ·', 'gateway.py · pump_control_mqtt.py'], GW)
    caption(sc, 2, ['ESP32 plant', 'never sees MQTT or the dashboard'], OT)
    save(sc, 'day2-fig-12-1-where-it-runs.svg')


if __name__ == '__main__':
    fig_7_1()
    fig_8_1()
    fig_12_1()
