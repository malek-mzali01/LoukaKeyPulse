# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import math


BG = "#13131c"
BORDER = "#33334a"
PANEL = "#1c1c28"
PANEL2 = "#23232f"
KB = "#2b2b3d"
KT = "#e6e6f0"
DB = "#202029"
DT = "#5b5b70"
SEL = "#f5a623"
SELT = "#1a1a24"
HOV = "#3b3b56"
ACC = "#7c5cff"
GRN = "#33c06b"
RED = "#e0524e"
SUB = "#8a8aa0"
FT = "Segoe UI"

U = 44
KH = 44
G = 6
P = 16
FH = 38


def rr(c, x1, y1, x2, y2, r, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = []

    for cx, cy, a0 in (
        (x2-r, y1+r, -90),
        (x2-r, y2-r, 0),
        (x1+r, y2-r, 90),
        (x1+r, y1+r, 180)
    ):
        for i in range(10):
            a = math.radians(a0 + i * 10)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]

    return c.create_polygon(pts, **kw)
