#!/usr/bin/env python3
"""Draw the Day 3 isometric figures into images/. Run: python3 images/src/build_day3.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso import caption, gap_point, laptop, origin, plate, raspberry_pi, server, Scene  # noqa: E402

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


if __name__ == '__main__':
    fig_15_1()
