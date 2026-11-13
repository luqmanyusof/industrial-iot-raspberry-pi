#!/usr/bin/env python3
"""Draw the Day 1 isometric figures into images/. Run: python3 images/src/build_day1.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso import (P, Scene, building, caption, cloud, door_switch, esp32, gap_point, laptop,  # noqa: E402
                 monitor, origin, plate, plc, raspberry_pi, relay_module, sd_card, server, tank)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
IT, GW, OT = '#dfe9fb', '#fff1c9', '#ffe8d6'
CABLE, WIFI, DATA = '#3c4043', '#1a73e8', '#188038'


def save(sc, name):
    sc.render(os.path.join(OUT, name))
    print('wrote', name)




def at(k, dx, dy, dz=0.0):
    x, y = origin(k)
    return (x + dx, y + dy, dz)


def put(sc, icon, k, dx, dy):
    x, y = origin(k)
    icon(sc, x + dx, y + dy)


# ---------- Figure 1.1: the system you build this week ----------
def fig_1_1():
    sc = Scene()
    plate(sc, 0, OT); plate(sc, 1, GW); plate(sc, 2, IT)
    put(sc, esp32, 0, 15, 15)
    put(sc, door_switch, 0, 20, 80)
    put(sc, relay_module, 0, 60, 100)
    put(sc, raspberry_pi, 1, 32, 47)
    put(sc, monitor, 2, 10, 20)
    put(sc, server, 2, 90, 70)
    sc.wire([at(0, 70, 30, 14), gap_point(0, 60), at(1, 60, 50, 30)], WIFI, 2.5, dash='7 6', under=False, arrow='end')
    sc.wire([at(0, 120, 125, 3), gap_point(0, 3, 40), at(1, 60, 100, 3)], '#8e24aa', 3.5, depth=-10, arrow='end')
    sc.wire([at(1, 110, 70, 12), gap_point(1, 30), at(2, 50, 60, 30)], CABLE, 3.5, under=False, arrow='end')
    sc.tag(*gap_point(0, 95), 'Modbus TCP (Day 2)', WIFI)
    sc.tag(*gap_point(0, 3, 40), 'GPIO (Day 1)', '#8e24aa')
    sc.tag(*gap_point(1, 70), 'HTTP today, MQTT on Day 2', CABLE)
    caption(sc, 0, ['Stesen Pam PS-01 (the plant)', 'ESP32 field device: tank level, e-stop,', 'stack light, alarm',
                    'door switch and pump relay'], OT)
    caption(sc, 1, ['Gateway', 'Raspberry Pi edge gateway'], GW)
    caption(sc, 2, ['Operators and servers', 'dashboards and history;', 'commands come back down'], IT)
    save(sc, 'day1-fig-1-1-system.svg')


# ---------- device -> edge -> server ----------
def fig_layers():
    sc = Scene()
    plate(sc, 0, OT); plate(sc, 1, GW); plate(sc, 2, IT)
    put(sc, esp32, 0, 15, 15)
    put(sc, door_switch, 0, 20, 80)
    put(sc, relay_module, 0, 60, 100)
    put(sc, raspberry_pi, 1, 32, 47)
    put(sc, server, 2, 40, 70)
    cloud(sc, *at(2, 100, 40)[:2], 50)
    ends = {0: at(1, 45, 50, 16), 1: at(2, 45, 75, 66)}
    for k in (0, 1):
        sc.wire([at(k, 120, 40, 40), gap_point(k, 55), ends[k]], DATA, 3, under=False, arrow='end')
        sc.wire([at(k + 1, 70, 120, 6), gap_point(k, 6, 40), at(k, 140, 110, 6)], '#e8710a', 2.5, dash='6 5',
                under=False, arrow='end')
    sc.tag(*gap_point(0, 90), 'raw signals', DATA)
    sc.tag(*gap_point(1, 90), 'clean, secured data', DATA)
    sc.tag(*gap_point(0, 6, 40), 'commands', '#e8710a')
    sc.tag(*gap_point(1, 6, 40), 'commands', '#e8710a')
    caption(sc, 0, ['Devices', 'sensors, switches, actuators'], OT)
    caption(sc, 1, ['Edge gateway', 'collects, filters,', 'secures, forwards'], GW)
    caption(sc, 2, ['Server / cloud', 'history, dashboards,', 'reports, analytics'], IT)
    save(sc, 'day1-fig-1-3-layers.svg')


# ---------- Figure 1.2: Purdue levels as stacked floors ----------
def fig_1_2():
    sc = Scene()
    levels = [
        (5, 'Level 4 — Enterprise', 'ERP, email, business systems', '#eceff1', building),
        (4, 'Level 3 — Site operations', 'historian, production reports', '#e3f2fd', server),
        (3, 'Level 2 — Supervisory', 'SCADA, HMI screens', '#e8f5e9', monitor),
        (2, 'IIoT edge gateway', 'your Raspberry Pi', '#fff1c9', raspberry_pi),
        (1, 'Level 1 — Control', 'PLCs, controllers', '#ede7f6', plc),
        (0, 'Level 0 — Field', 'sensors, switches, valves, motors, relays', '#ffe8d6', None),
    ]
    step, w, d = 150, 150, 110
    spots = {building: (50, 30), server: (58, 33), monitor: (42, 35), raspberry_pi: (32, 27), plc: (60, 25)}
    for k, name, sub, col, icon in levels:
        z = k * step
        sc.box(0, 0, z - 3, w, d, 3, col, depth=k * 1000 - 500, outline=False)
        tmp = Scene()
        if icon:
            icon(tmp, *spots[icon])
        else:
            door_switch(tmp, 15, 40)
            tank(tmp, 60, 50)
            relay_module(tmp, 75, 15)
        for dep, svg in tmp.items:
            sc.add(k * 1000 + dep, f'<g transform="translate(0,{-z})">{svg}</g>')
        sc.pts += [(px, py - z) for px, py in tmp.pts]
        sc.callout(w, d / 2, z, 60, 0, [name, sub], colour='#b8860b' if k == 2 else '#202124')
    for k in range(5):
        sc.wire([(8, d, k * step + 6), (8, d, (k + 1) * step - 10)], '#9aa0a6', 2, dash='4 5',
                under=False, arrow='both')
    save(sc, 'day1-fig-1-2-purdue.svg')


# ---------- Figure 2.1: two networks ----------
def fig_2_1():
    sc = Scene()
    plate(sc, 0, IT); plate(sc, 1, GW); plate(sc, 2, OT)
    cloud(sc, *at(0, 35, 35)[:2], 55)
    put(sc, laptop, 0, 55, 70)
    put(sc, raspberry_pi, 1, 32, 47)
    put(sc, esp32, 2, 15, 25)
    put(sc, raspberry_pi, 2, 50, 85)
    sc.wire([at(0, 60, 40, 30), at(0, 70, 60, 8)], '#9aa0a6', 2.5, dash='2 6', under=False)
    sc.wire([at(0, 125, 110, 1), gap_point(0, 1, 30), at(1, 40, 110, 1), at(1, 60, 103, 2)], CABLE, 4, depth=-10)
    sc.wire([at(1, 90, 60, 30), gap_point(1, 40), at(2, 70, 40, 18)], WIFI, 2.5, dash='7 6', under=False)
    sc.wire([at(2, 72, 40, 18), at(2, 100, 100, 24)], WIFI, 2.5, dash='7 6', under=False)
    sc.waves(*at(2, 70, 40, 14))
    sc.waves(*at(1, 90, 60, 30))
    sc.tag(*gap_point(0, 1, 30), 'LAN cable · eth0', CABLE)
    sc.tag(*gap_point(1, 75), 'Wi-Fi · wlan0', WIFI)
    caption(sc, 0, ['Office side (IT)', 'internet + your laptop,', 'which shares its internet'], IT)
    caption(sc, 1, ['Gateway', 'your Pi (pi01) · 192.168.4.11', 'the only link between the two'], GW)
    caption(sc, 2, ['Plant side (OT) · PS01-PLANT', 'ESP32 access point · 192.168.4.1',
                    "neighbour's Pi · 192.168.4.12"], OT)
    save(sc, 'day1-fig-2-1-two-networks.svg')


# ---------- Figure 2.2: headless setup ----------
def fig_2_2():
    sc = Scene()
    G = '#eef1f5'
    plate(sc, 0, G); plate(sc, 1, G); plate(sc, 2, GW)
    put(sc, laptop, 0, 40, 50)
    put(sc, sd_card, 1, 55, 55)
    put(sc, raspberry_pi, 2, 32, 47)
    sc.wire([at(0, 110, 60, 25), gap_point(0, 40), at(1, 55, 60, 10)], DATA, 3, under=False, arrow='end')
    sc.wire([at(1, 90, 70, 6), gap_point(1, 30), at(2, 40, 60, 12)], DATA, 3, under=False, arrow='end')
    sc.tag(*gap_point(0, 85), 'writes OS + your settings', DATA)
    sc.tag(*gap_point(1, 75), 'insert, cable in, power on', DATA)
    caption(sc, 0, ['1. Raspberry Pi Imager', 'on your laptop'], G)
    caption(sc, 1, ['2. microSD card', 'hostname, user, SSH on'], G)
    caption(sc, 2, ['3. First boot (about 90 s)', 'gets an address from your laptop,', 'reachable as pi01.local'], GW)
    save(sc, 'day1-fig-2-2-headless.svg')


# ---------- Figure 2.3: laptop as router ----------
def fig_2_3():
    sc = Scene()
    plate(sc, 0, '#eef1f5'); plate(sc, 1, IT); plate(sc, 2, GW)
    cloud(sc, *at(0, 75, 75)[:2], 35)
    put(sc, laptop, 1, 40, 50)
    put(sc, raspberry_pi, 2, 32, 47)
    sc.wire([at(0, 120, 60, 30), gap_point(0, 40), at(1, 40, 60, 30)], WIFI, 2.5, dash='7 6', under=False, arrow='end')
    sc.wire([at(1, 115, 100, 1), gap_point(1, 1, 30), at(2, 40, 110, 1), at(2, 60, 103, 2)], CABLE, 4, depth=-10)
    sc.tag(*gap_point(0, 80), "laptop's Wi-Fi", WIFI)
    sc.tag(*gap_point(1, 1, 30), 'LAN cable', CABLE)
    caption(sc, 0, ['Internet'], '#9aa0a6')
    caption(sc, 1, ['Your laptop', 'shares its connection,', 'hands out an address'], IT)
    caption(sc, 2, ['Raspberry Pi · eth0', 'gets an address automatically'], GW)
    save(sc, 'day1-fig-2-3-laptop-router.svg')


# ---------- Figure 2.4: two ways in ----------
def fig_2_4():
    sc = Scene()
    plate(sc, 0, IT); plate(sc, 1, GW)
    put(sc, laptop, 0, 40, 50)
    put(sc, raspberry_pi, 1, 32, 47)
    sc.wire([at(0, 115, 100, 1), gap_point(0, 1, 30), at(1, 40, 110, 1), at(1, 60, 103, 2)], CABLE, 6, depth=-10)
    sc.tag(*gap_point(0, 1, 30), 'SSH · encrypted · port 22', CABLE)
    caption(sc, 0, ['Your laptop', 'Terminal / PowerShell,', 'VS Code + Remote-SSH'], IT)
    caption(sc, 1, ['Raspberry Pi (pi01)'], GW)
    sc.callout(*at(1, 60, 60, 10), 130, -70, ['SSH server, port 22', 'checks who you are'])
    sc.callout(*at(1, 40, 75, 6), 160, -20, ['Shell as pelatih', 'and the VS Code Server'])
    sc.callout(*at(1, 55, 95, 3), 160, 30, ['Your files', '~/iiot'])
    save(sc, 'day1-fig-2-4-two-ways-in.svg')


# ---------- Figure 5.1: pair lab ----------
def fig_5_1():
    sc = Scene()
    plate(sc, 0, OT); plate(sc, 1, OT); plate(sc, 2, OT)
    put(sc, raspberry_pi, 0, 32, 47)
    put(sc, esp32, 1, 43, 60)
    put(sc, raspberry_pi, 2, 32, 47)
    sc.waves(*at(1, 100, 75, 12))
    sc.wire([at(0, 110, 60, 50), at(2, 40, 60, 50)], DATA, 3.5, under=False, arrow='end')
    sc.wire([at(2, 40, 90, 30), at(0, 110, 90, 30)], '#e8710a', 3.5, under=False, arrow='end')
    sc.tag(*at(1, 75, 75, 95), 'pi01 → pi02 · POST /readings', DATA)
    sc.tag(*at(1, 120, 120, 0), 'pi02 → pi01 · POST /readings', '#e8710a')
    caption(sc, 0, ['pi01 · 192.168.4.11', 'gateway.py and receiver.py'], OT)
    caption(sc, 1, ['ESP32 access point', 'Wi-Fi PS01-PLANT,', 'relays the traffic'], OT)
    caption(sc, 2, ['pi02 · 192.168.4.12', 'gateway.py and receiver.py'], OT)
    save(sc, 'day1-fig-5-1-pair-lab.svg')


# ---------- Figure 6.4: inside the relay module ----------
def fig_6_4():
    sc = Scene()
    plate(sc, 0, GW); plate(sc, 1, '#e8f0fe')
    put(sc, raspberry_pi, 0, 32, 47)
    rx, ry = at(1, 45, 60)[:2]
    relay_module(sc, rx, ry)
    for i, col in enumerate(('#8e24aa', '#d93025', '#26282b')):     # IN, VCC, GND jumpers
        sc.wire([at(0, 62 + i * 4, 50, 10), at(0, 62 + i * 4, 50, 34), (rx + 58, ry + 7 + i * 6, 34),
                 (rx + 58, ry + 7 + i * 6, 16)], col, 2.5, under=False)
    sc.callout(rx + 58, ry + 7, 16, 110, -95, ['IN ← GPIO27 (pin 13)', '3.3 V signal from the Pi'], colour='#8e24aa')
    sc.callout(rx + 58, ry + 13, 16, 125, -55, ['VCC ← 5 V (pin 2)', 'powers the coil'], colour='#d93025')
    sc.callout(rx + 58, ry + 19, 16, 140, -15, ['GND ← GND (pin 6)'], colour='#26282b')
    sc.callout(rx + 17, ry + 13, 22, -40, -75, ['Relay coil', 'an electromagnet in the blue box'], anchor='end')
    sc.callout(rx + 41, ry + 14, 13, 90, 70, ['Contacts COM · NO · NC', 'nothing connected today'])
    sc.callout(rx + 49, ry + 22, 5, -10, 80, ['Module LED', 'lights when the relay is on'], colour='#e53935',
               anchor='end')
    caption(sc, 0, ['Raspberry Pi', 'GPIO header'], GW)
    save(sc, 'day1-fig-6-4-relay-module.svg')


if __name__ == '__main__':
    for f in (fig_1_1, fig_layers, fig_1_2, fig_2_1, fig_2_2, fig_2_3, fig_2_4, fig_5_1, fig_6_4):
        f()
