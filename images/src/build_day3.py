#!/usr/bin/env python3
"""Draw the Day 3 isometric figures into images/. Run: python3 images/src/build_day3.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso import (P, Scene, caption, door_switch, gap_point, laptop, origin, plate, raspberry_pi,  # noqa: E402
                 server, shade, tank)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GW, IT, GREY = '#fff1c9', '#dfe9fb', '#eef1f5'


def save(sc, name):
    sc.render(os.path.join(OUT, name))
    print('wrote', name)


# ---------- Figure 15.1: where alert emails go, today and in production ----------
def fig_15_1():
    sc = Scene()
    plate(sc, 0, GW); plate(sc, 1, GREY); plate(sc, 2, IT)
    x0, y0 = origin(0)
    raspberry_pi(sc, x0 + 32, y0 + 47)
    x1, y1 = origin(1)
    server(sc, x1 + 58, y1 + 53)
    x2, y2 = origin(2)
    laptop(sc, x2 + 40, y2 + 50)
    sc.wire([(x0 + 110, y0 + 60, 20), gap_point(0, 45), (x1 + 60, y1 + 70, 40)], '#9aa0a6', 3, dash='7 6',
            under=False, arrow='end')
    sc.wire([(x1 + 95, y1 + 90, 30), gap_point(1, 45), (x2 + 60, y2 + 60, 30)], '#9aa0a6', 3, dash='7 6',
            under=False, arrow='end')
    sc.tag(*gap_point(0, 80), 'production only: relayhost', '#5f6368')
    sc.tag(*gap_point(1, 80), 'email', '#5f6368')
    caption(sc, 0, ['Your Pi: gateway.py → Postfix', 'today, mail stays here:', '/var/mail/pelatih, read with mail'],
            GW)
    caption(sc, 1, ["Organisation's mail server", 'production only'], GREY)
    caption(sc, 2, ["Operator's inbox", 'production only: PC or phone'], IT)
    save(sc, 'day3-fig-15-1-mail-path.svg')


# ---------- Op SENTINEL: three outposts, one trainer Pi, every station polls ----------
def fig_sentinel():
    sc = Scene()
    OT, W, R = '#ffe8d6', 120, 150
    outposts = ['ALPHA · unit 1', 'BRAVO · unit 2', 'CHARLIE · unit 3']
    px, py = 290 + R, -290 + R                         # pi00 plate, level with the middle outpost
    for r, name in enumerate(outposts):
        x, y = r * R, r * R
        sc.box(x, y, -3, W, W, 3, OT, depth=-1e6 + x + y, outline=False)
        tank(sc, x + 30, y + 75)
        server(sc, x + 55, y + 20)                     # the generator shed
        door_switch(sc, x + 95, y + 70)                # the perimeter gate
        sc.wire([(x + 90, y + 40, 40), (px + 40, py + 70, 20)], '#e8710a', 2.2, dash='6 6', under=False)
        tx, ty = P(x, y + W, 0)
        sc.overlay.append(f'<text x="{tx - 12:.1f}" y="{ty + 4:.1f}" font-size="14" font-weight="700" '
                          f'fill="{shade(OT, 0.42)}" text-anchor="end">{name}</text>')
        sc.pts += [(tx - 170, ty - 14)]
    sc.box(px, py, -3, W + 10, W + 10, 3, GW, depth=-1e6 + px + py, outline=False)
    raspberry_pi(sc, px + 22, py + 40)
    qx, qy = px + 2 * 165, py - 2 * 165 + 165
    for i, name in enumerate(['pi01', 'pi02']):
        sx, sy = qx + i * 165, qy + i * 165 - 165
        sc.box(sx, sy, -3, W, W, 3, '#dfe9fb', depth=-1e6 + sx + sy, outline=False)
        raspberry_pi(sc, sx + 18, sy + 34)
        sc.wire([(sx + 20, sy + 60, 26), (px + 110, py + 70, 26)], '#188038', 2.4, under=False, arrow='end')
        tx, ty = P(sx + W, sy + W, 0)
        sc.overlay.append(f'<text x="{tx:.1f}" y="{ty + 22:.1f}" font-size="14" font-weight="700" fill="#3c4043" '
                          f'text-anchor="middle">{name}: your SENTINEL node</text>')
        sc.pts += [(tx - 110, ty), (tx + 110, ty + 30)]
    cx, cy = P(px + W + 10, py + W + 10, 0)
    sc.overlay.append(f'<text x="{cx:.1f}" y="{cy + 24:.1f}" font-size="14" font-weight="700" '
                      f'fill="{shade(GW, 0.42)}" text-anchor="middle">pi00 (trainer) · 192.168.4.10:5020</text>'
                      f'<text x="{cx:.1f}" y="{cy + 42:.1f}" font-size="12.5" fill="#3c4043" '
                      f'text-anchor="middle">simulates all three outposts, one Modbus unit each</text>')
    sc.pts += [(cx - 180, cy), (cx + 180, cy + 50)]
    sc.tag(px + 230, py - 60, 40, 'Modbus TCP, every 5 s', '#188038')
    save(sc, 'sentinel-fig-1-outposts.svg')


if __name__ == '__main__':
    fig_15_1()
    fig_sentinel()
