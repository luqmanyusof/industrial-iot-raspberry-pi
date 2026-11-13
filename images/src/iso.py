"""Tiny isometric SVG toolkit: world (x, y, z) -> screen, shaded boxes, and device icons.

+x runs right-down, +y runs left-down, +z runs up. Visible box faces: top, +x side (right), +y side (left).
"""
import math

C30, S30 = math.cos(math.radians(30)), 0.5
FONT = 'Segoe UI, Helvetica, Arial, sans-serif'


def P(x, y, z=0.0):
    return ((x - y) * C30, (x + y) * S30 - z)


def shade(hex_colour, f):
    h = hex_colour.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f >= 1:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    else:
        r, g, b = (int(c * f) for c in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}'


def poly(pts, fill, stroke=None, sw=0.8, extra=''):
    d = ' '.join(f'{px:.1f},{py:.1f}' for px, py in pts)
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ''
    return f'<polygon points="{d}" fill="{fill}"{st} {extra}/>'


class Scene:
    def __init__(self):
        self.items = []      # (depth, svg)
        self.overlay = []    # drawn last (labels, lines on top)
        self.pts = []

    def add(self, depth, svg, pts=()):
        self.items.append((depth, svg))
        self.pts.extend(pts)

    # ---------- primitives ----------
    def box(self, x, y, z, w, d, h, col, depth=None, outline=True):
        c = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
        fx = [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)]
        fy = [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)]
        sk = shade(col, 0.55) if outline else None
        svg = (poly(fy, shade(col, 0.82), sk, 0.6) + poly(fx, shade(col, 0.64), sk, 0.6)
               + poly(c, shade(col, 1.12), sk, 0.6))
        self.add(depth if depth is not None else x + y + z * 0.01, svg, c + fx + fy)

    def top_rect(self, x, y, z, w, d, col, depth):
        pts = [P(x, y, z), P(x + w, y, z), P(x + w, y + d, z), P(x, y + d, z)]
        self.add(depth, poly(pts, col), pts)

    def face_y(self, x, y, z, w, h, col, depth):
        """Rectangle on a plane facing +y (left-down), e.g. a screen."""
        pts = [P(x, y, z), P(x + w, y, z), P(x + w, y, z + h), P(x, y, z + h)]
        self.add(depth, poly(pts, col), pts)

    def face_x(self, x, y, z, d, h, col, depth):
        pts = [P(x, y, z), P(x, y + d, z), P(x, y + d, z + h), P(x, y, z + h)]
        self.add(depth, poly(pts, col), pts)

    def cylinder(self, x, y, z, r, h, col, depth):
        cx, cy = P(x, y, z)
        rx, ry = r * C30 * 1.41, r * S30 * 1.41
        body = (f'<path d="M{cx - rx:.1f},{cy:.1f} L{cx - rx:.1f},{cy - h:.1f} '
                f'A{rx:.1f},{ry:.1f} 0 0 0 {cx + rx:.1f},{cy - h:.1f} L{cx + rx:.1f},{cy:.1f} '
                f'A{rx:.1f},{ry:.1f} 0 0 1 {cx - rx:.1f},{cy:.1f} Z" fill="{shade(col, 0.78)}" '
                f'stroke="{shade(col, 0.55)}" stroke-width="0.6"/>')
        top = (f'<ellipse cx="{cx:.1f}" cy="{cy - h:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
               f'fill="{shade(col, 1.15)}" stroke="{shade(col, 0.55)}" stroke-width="0.6"/>')
        self.add(depth, body + top, [(cx - rx, cy + ry), (cx + rx, cy - h - ry)])

    # ---------- overlay ----------
    def label(self, x, y, z, lines, dy=0, size=13, bold_first=True, colour='#202124'):
        px, py = P(x, y, z)
        out = []
        for i, t in enumerate(lines):
            w = '700' if (i == 0 and bold_first) else '400'
            c = colour if i == 0 else '#5f6368'
            s = size if i == 0 else size - 1.5
            out.append(f'<text x="{px:.1f}" y="{py + dy + i * (size + 3):.1f}" font-size="{s}" font-weight="{w}" '
                       f'fill="{c}" text-anchor="middle" stroke="#ffffff" stroke-width="4" '
                       f'paint-order="stroke" stroke-linejoin="round">{t}</text>')
        self.overlay.append(''.join(out))
        self.pts += [(px - 70, py + dy - size), (px + 70, py + dy + len(lines) * (size + 3))]

    def wire(self, pts3, colour, width=3.5, dash=None, under=True, depth=-1e9, arrow=None):
        pts = [P(*p) for p in pts3]
        d = 'M' + ' L'.join(f'{a:.1f},{b:.1f}' for a, b in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ''
        svg = (f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}" '
               f'stroke-linecap="round" stroke-linejoin="round"{da}/>')
        for (a, b) in ([(pts[-2], pts[-1])] if arrow in ('end', 'both') else []) + \
                      ([(pts[1], pts[0])] if arrow in ('start', 'both') else []):
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1
            ux, uy = dx / n, dy / n
            L, W = 6 + width * 2.2, 4 + width * 1.2
            tip = (b[0] + ux * 2, b[1] + uy * 2)
            base = (tip[0] - ux * L, tip[1] - uy * L)
            svg += poly([tip, (base[0] - uy * W, base[1] + ux * W), (base[0] + uy * W, base[1] - ux * W)], colour)
        if under:
            self.add(depth, svg, pts)
        else:
            self.overlay.append(svg)
            self.pts += pts

    def tag(self, x, y, z, text, colour):
        """Small pill label on a wire."""
        px, py = P(x, y, z)
        w = 7.2 * len(text) + 14
        self.overlay.append(
            f'<rect x="{px - w / 2:.1f}" y="{py - 11:.1f}" width="{w:.1f}" height="22" rx="11" fill="#ffffff" '
            f'stroke="{colour}" stroke-width="1.5"/><text x="{px:.1f}" y="{py + 4.5:.1f}" font-size="12" '
            f'font-weight="600" fill="{colour}" text-anchor="middle">{text}</text>')
        self.pts += [(px - w / 2, py - 13), (px + w / 2, py + 13)]

    def waves(self, x, y, z, colour='#1a73e8', n=3, size=7):
        px, py = P(x, y, z)
        out = [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{colour}"/>']
        for i in range(1, n + 1):
            r = size * i
            out.append(f'<path d="M{px - r * 0.8:.1f},{py - r * 0.6:.1f} A{r},{r} 0 0 1 {px + r * 0.8:.1f},'
                       f'{py - r * 0.6:.1f}" fill="none" stroke="{colour}" stroke-width="2.4" '
                       f'stroke-linecap="round" opacity="{1 - i * 0.18:.2f}"/>')
        self.overlay.append(''.join(out))

    def callout(self, x, y, z, tx, ty, lines, colour='#202124', anchor='start'):
        """Leader line from a world point to text at a screen offset (tx, ty)."""
        px, py = P(x, y, z)
        ex, ey = px + tx, py + ty
        out = [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{colour}"/>',
               f'<path d="M{px:.1f},{py:.1f} L{ex:.1f},{ey:.1f}" stroke="{colour}" stroke-width="1.3" fill="none"/>']
        off = 6 if anchor == 'start' else -6
        for i, t in enumerate(lines):
            w, s, c = ('700', 13, colour) if i == 0 else ('400', 12, '#5f6368')
            out.append(f'<text x="{ex + off:.1f}" y="{ey + 4 + i * 16:.1f}" font-size="{s}" font-weight="{w}" '
                       f'fill="{c}" text-anchor="{anchor}" stroke="#ffffff" stroke-width="4" '
                       f'paint-order="stroke" stroke-linejoin="round">{t}</text>')
        self.overlay.append(''.join(out))
        wmax = max(len(t) for t in lines) * 7.2
        x1 = ex + off + (wmax if anchor == 'start' else -wmax)
        self.pts += [(px, py), (min(ex, x1), ey - 14), (max(ex, x1), ey + len(lines) * 16)]

    def render(self, path, title=None, pad=24, zoom=1.0):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        x0, y0 = min(xs) - pad, min(ys) - pad - (34 if title else 0)
        w, h = max(xs) - x0 + pad, max(ys) - y0 + pad
        body = ''.join(s for _, s in sorted(self.items, key=lambda t: t[0])) + ''.join(self.overlay)
        t = (f'<text x="{x0 + pad:.1f}" y="{y0 + pad + 8:.1f}" font-size="17" font-weight="700" '
             f'fill="#202124">{title}</text>') if title else ''
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}" '
               f'width="{w * zoom:.0f}" height="{h * zoom:.0f}" font-family="{FONT}">'
               f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" rx="14" fill="#ffffff"/>'
               f'{t}{body}</svg>\n')
        open(path, 'w').write(svg)


# ======================= icons (anchor = world x, y on the floor) =======================

def floor(sc, x, y, w, d, col, title, sub=None):
    sc.box(x, y, -3, w, d, 3, col, depth=-1e6 + x + y, outline=False)
    px, py = P(x + 8, y, 0)          # back edge, runs right-down at 30 degrees
    tc = shade(col, 0.42)
    s = (f'<text x="{px:.1f}" y="{py - 8:.1f}" font-size="14" font-weight="700" fill="{tc}" '
         f'transform="rotate(30 {px:.1f} {py - 8:.1f})">{title}</text>')
    if sub:
        s += (f'<text x="{px - 8:.1f}" y="{py - 25:.1f}" font-size="12" fill="{tc}" '
              f'transform="rotate(30 {px - 8:.1f} {py - 25:.1f})">{sub}</text>')
    sc.overlay.insert(0, s)
    sc.pts += [(px - 20, py - 40)]


def raspberry_pi(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 85, 56, 3, '#2f9e55', dep)                       # PCB
    sc.box(x + 8, y + 2, 3, 64, 6, 7, '#26282b', dep + 0.1)          # GPIO header
    for i in range(16):
        sc.top_rect(x + 10 + i * 3.8, y + 3.5, 10.05, 1.6, 1.6, '#d4af37', dep + 0.11)
        sc.top_rect(x + 10 + i * 3.8, y + 5.5, 10.05, 1.6, 1.6, '#d4af37', dep + 0.11)
    sc.box(x + 28, y + 20, 3, 16, 16, 2.5, '#c3c7cc', dep + 0.2)    # SoC lid
    sc.box(x + 66, y + 4, 3, 22, 15, 13, '#c9ccd1', dep + 0.3)       # LAN
    sc.box(x + 66, y + 22, 3, 21, 13, 15, '#c9ccd1', dep + 0.31)     # USB
    sc.box(x + 66, y + 38, 3, 21, 13, 15, '#c9ccd1', dep + 0.32)     # USB
    sc.top_rect(x + 69, y + 24.5, 18.05, 15, 8, '#1a73e8', dep + 0.33)
    sc.top_rect(x + 69, y + 40.5, 18.05, 15, 8, '#1a73e8', dep + 0.34)


def esp32(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 64, 30, 3, '#24324f', dep)
    for i in range(14):
        sc.top_rect(x + 4 + i * 4, y + 1.5, 3.05, 1.8, 1.8, '#d4af37', dep + 0.05)
        sc.top_rect(x + 4 + i * 4, y + 26.7, 3.05, 1.8, 1.8, '#d4af37', dep + 0.05)
    sc.box(x + 30, y + 6, 3, 24, 18, 4, '#d5d8dc', dep + 0.1)        # metal shield
    sc.top_rect(x + 54, y + 7, 3.05, 8, 16, '#3c4a6b', dep + 0.08)   # antenna area
    sc.wire([(x + 55, y + 9, 3.1), (x + 60, y + 9, 3.1), (x + 60, y + 13, 3.1), (x + 56, y + 13, 3.1),
             (x + 56, y + 17, 3.1), (x + 60, y + 17, 3.1), (x + 60, y + 21, 3.1)], '#e8b04a', 1.4, depth=dep + 0.09)
    sc.box(x + 8, y + 9, 3, 9, 12, 3, '#d5d8dc', dep + 0.12)         # USB


def laptop(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 70, 48, 4, '#b9c0c9', dep)
    sc.top_rect(x + 6, y + 6, 4.05, 58, 24, '#8d96a3', dep + 0.1)    # keyboard
    sc.top_rect(x + 24, y + 34, 4.05, 22, 10, '#a7b0bb', dep + 0.1)  # trackpad
    sc.box(x, y - 3, 4, 70, 3, 46, '#3c4043', dep - 2)               # lid
    sc.face_y(x + 4, y, 8, 62, 38, '#5aa9e6', dep - 1.9)             # screen
    sc.face_y(x + 4, y, 30, 62, 16, '#7fbdee', dep - 1.85)


def cloud(sc, x, y, z=34):
    px, py = P(x, y, z)
    c = '#cfe0f5'
    s = (f'<g transform="translate({px:.1f},{py:.1f})">'
         f'<ellipse cx="0" cy="16" rx="52" ry="12" fill="#e8eef6"/>'
         f'<circle cx="-26" cy="0" r="18" fill="{c}"/><circle cx="2" cy="-12" r="24" fill="#dbe8f8"/>'
         f'<circle cx="28" cy="0" r="17" fill="{c}"/><rect x="-44" y="0" width="88" height="16" rx="8" fill="{c}"/>'
         f'<path d="M-44,8 Q-44,16 -36,16 L36,16 Q44,16 44,8" fill="#b4cbe8"/></g>')
    sc.add(x + y + 100, s, [(px - 56, py - 40), (px + 56, py + 30)])


def relay_module(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 64, 28, 3, '#1f5fbf', dep)
    sc.box(x + 5, y + 4, 3, 24, 19, 19, '#2a7be4', dep + 0.1)        # relay cube
    sc.top_rect(x + 9, y + 8, 22.05, 16, 11, '#5aa0f2', dep + 0.11)
    sc.box(x + 32, y + 4, 3, 13, 20, 10, '#2f9e55', dep + 0.2)       # screw terminal COM/NO/NC
    for i in range(3):
        sc.top_rect(x + 35, y + 6 + i * 6.3, 13.05, 6, 4, '#c9ccd1', dep + 0.21)
    sc.box(x + 48, y + 21, 3, 3, 3, 2, '#e53935', dep + 0.3)         # LED
    for i in range(3):                                               # header pins IN/VCC/GND
        sc.box(x + 56, y + 5 + i * 6, 3, 4, 4, 3, '#26282b', dep + 0.4 + i * 0.01)
        sc.box(x + 57.2, y + 6.2 + i * 6, 6, 1.6, 1.6, 9, '#d4af37', dep + 0.42 + i * 0.01)


def server(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 34, 44, 64, '#5f6b7a', dep)
    for i in range(5):
        sc.face_x(x + 34.05, y + 5, 8 + i * 11, 34, 6, '#465060', dep + 0.1)
        sc.face_x(x + 34.1, y + 34, 9.5 + i * 11, 3, 3, '#34c759', dep + 0.2)


def monitor(sc, x, y):
    dep = x + y
    sc.box(x + 22, y + 10, 0, 22, 18, 3, '#9aa0a6', dep)             # foot
    sc.box(x + 30, y + 14, 3, 6, 5, 18, '#9aa0a6', dep + 0.1)        # stand
    sc.box(x, y + 10, 18, 66, 4, 42, '#3c4043', dep + 0.2)           # panel
    sc.face_y(x + 4, y + 14.05, 22, 58, 34, '#0f9d58', dep + 0.3)    # screen (dashboard)
    sc.face_y(x + 10, y + 14.1, 26, 12, 22, '#7ee2a8', dep + 0.31)
    sc.face_y(x + 26, y + 14.1, 26, 12, 14, '#7ee2a8', dep + 0.31)
    sc.face_y(x + 42, y + 14.1, 26, 12, 26, '#7ee2a8', dep + 0.31)


def door_switch(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 6, 34, 52, '#8d6e63', dep)                       # door frame
    sc.box(x + 6, y + 2, 0, 3, 30, 48, '#bcaaa4', dep + 0.1)         # door leaf
    sc.box(x + 9, y + 24, 22, 3, 4, 4, '#fbc02d', dep + 0.2)         # handle


def sd_card(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 30, 40, 2.5, '#2b2f36', dep)
    sc.top_rect(x + 3, y + 10, 2.55, 24, 27, '#3d7be0', dep + 0.1)
    for i in range(7):
        sc.top_rect(x + 3 + i * 3.6, y + 1.5, 2.55, 2.2, 6, '#d4af37', dep + 0.1)


def plc(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 26, 60, 40, '#cfd3d8', dep)                    # rail-mounted body
    sc.face_x(x + 26.05, y + 4, 30, 52, 6, '#2f9e55', dep + 0.1)    # top terminal strip
    sc.face_x(x + 26.05, y + 4, 4, 52, 6, '#2f9e55', dep + 0.1)     # bottom terminal strip
    sc.face_x(x + 26.05, y + 6, 13, 30, 14, '#37474f', dep + 0.1)   # display
    for i in range(4):
        sc.face_x(x + 26.1, y + 41 + i * 4, 22, 2.5, 2.5, '#34c759', dep + 0.2)


def building(sc, x, y):
    dep = x + y
    sc.box(x, y, 0, 50, 50, 70, '#90a4ae', dep)
    for r in range(4):
        for c in range(3):
            sc.face_x(x + 50.05, y + 6 + c * 15, 10 + r * 15, 9, 9, '#cfe8fc', dep + 0.1)
            sc.face_y(x + 6 + c * 15, y + 50.05, 10 + r * 15, 9, 9, '#b3d4f0', dep + 0.1)


def tank(sc, x, y):
    sc.cylinder(x, y, 0, 18, 46, '#4a90d9', x + y)
    sc.box(x + 14, y - 4, 0, 16, 8, 8, '#78909c', x + y + 0.5)     # outlet pipe stub


# ---------- row layout: platforms in a horizontal line ----------
PLATE, GAP = 150, 220          # plate size; distance between plate origins along x and -y


def origin(k):
    return k * GAP, -k * GAP


def plate(sc, k, col, w=PLATE, d=PLATE):
    x, y = origin(k)
    sc.box(x, y, -3, w, d, 3, col, depth=-1e6 + k, outline=False)
    return x, y


def caption(sc, k, lines, col, w=PLATE, d=PLATE):
    """Caption under a plate's front corner: first line bold in the plate colour."""
    x, y = origin(k)
    px, py = P(x + w, y + d, 0)
    out = []
    for i, t in enumerate(lines):
        c, wt, sz = (shade(col, 0.42), '700', 14) if i == 0 else ('#3c4043', '400', 12.5)
        out.append(f'<text x="{px:.1f}" y="{py + 26 + i * 18:.1f}" font-size="{sz}" font-weight="{wt}" '
                   f'fill="{c}" text-anchor="middle">{t}</text>')
    sc.overlay.append(''.join(out))
    wmax = max(len(t) for t in lines) * 3.8
    sc.pts += [(px - wmax, py), (px + wmax, py + 30 + len(lines) * 18)]


def gap_point(k, z=0.0, shift=0.0):
    """World point in the gap between plate k and k+1 (shift moves it toward the viewer)."""
    x, y = origin(k)
    return (x + PLATE + (GAP - PLATE) / 2 + shift, y + PLATE / 2 - GAP / 2 + shift, z)
