"""8-switch panel box: 830-hole breadboard (Pico at its left end) + 8 mini toggles + 8 LEDs.

Generates base.stl and lid.stl (both print without supports, fit a 180 x 180 bed) and preview.png.
All dimensions in mm. Coordinates: x = left->right, y = front (user side) -> rear, z = up.
"""
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType, Manifold
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

# ---- Parameters -------------------------------------------------------------
SEG = 48
WALL, FLOOR, LID_T = 2.2, 2.0, 3.0
CORNER_R = 3.0

BB_L, BB_W, BB_H = 160.0, 60.0, 10.0      # breadboard
BB_X = 3.0                                 # breadboard left end -> inner left wall
FRONT_ZONE = 48.0                          # switch/LED area in front of the breadboard
BB_REAR_GAP = 8.0                          # keeps the rear screw bosses clear of the breadboard

IW = BB_X + BB_L + 3.0                     # interior width
ID = FRONT_ZONE + BB_W + BB_REAR_GAP       # interior depth
IH = 35.0                                  # interior height (breadboard + Pico + jumper wires)
BB_Y = FRONT_ZONE                          # breadboard front edge (interior coords)

RAIL_H, RAIL_T, RAIL_CLEAR = 3.0, 1.6, 0.5  # low frame that locates the breadboard

BOSS_R, SCREW_PILOT_D = 3.5, 2.6           # M3 self-tapping into base bosses
SCREW_DEPTH = 22.0                         # M3x21 screws: 3 mm lid + 18 mm into the boss, plus margin
SCREW_CLEAR_D, CSINK_D, CSINK_H = 3.4, 6.5, 1.8

# USB-C of the Pico points out of the left wall, centred on the breadboard width.
# Measured: top of the Pico's USB-C sits 12 mm above the floor; cable plug head is 10.5 x 7.5 mm.
USB_W, USB_H = 12.0, 9.0
USB_Z = 12.0 - 1.6                         # centre of the USB-C receptacle above the floor

SWITCH_HOLE_D, LED_HOLE_D = 6.3, 5.1
PITCH = 20.0
SWITCH_Y, LED_Y = 22.0, 38.0               # interior coords (lever throws along y)
LABEL_Y = 8.0
LABELS = ["ENGINE", "BATT", "ALT", "AVION", "FUEL\nPUMP", "BEACON", "NAV", "▲LAND\n▼TAXI"]
GROUPS = [("ENGINE & ELECTRICAL", 0, 4), ("LIGHTS", 5, 7)]   # header text, first, last switch
TEXT_DEPTH = 0.6

OW, OD = IW + 2 * WALL, ID + 2 * WALL
BASE_H = FLOOR + IH


def ix(v):  # interior -> outer coordinates
    return WALL + v


def switch_x(i):
    return ix(BB_X + PITCH / 2 + i * PITCH)


def rounded_box(w, d, h, r):
    cs = CrossSection.square([w - 2 * r, d - 2 * r]).translate([r, r]).offset(
        r, JoinType.Round, circular_segments=SEG)
    return cs.extrude(h)


def cyl(h, d, x, y, z=0.0, d_top=None):
    r2 = -1.0 if d_top is None else d_top / 2
    return Manifold.cylinder(h, d / 2, r2, circular_segments=SEG).translate([x, y, z])


def text(s, size, cx, cy, z, depth, line_gap=1.25):
    lines = s.split("\n")
    out = Manifold()
    for n, line in enumerate(lines):
        tp = TextPath((0, 0), line, size=size, prop=FontProperties(family="DejaVu Sans", weight="bold"))
        polys = [p for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
        cs = CrossSection(polys, FillRule.EvenOdd)
        x0, y0, x1, y1 = cs.bounds()
        ly = cy + ((len(lines) - 1) / 2 - n) * size * line_gap
        out = out + cs.extrude(depth).translate([cx - (x0 + x1) / 2, ly - (y0 + y1) / 2, z])
    return out


def boss_centers():
    o = WALL + BOSS_R - 0.8   # sink slightly into the walls so the union is clean
    return [(o, o), (OW / 2, o), (OW - o, o), (o, OD - o), (OW - o, OD - o)]


def build_base():
    base = rounded_box(OW, OD, BASE_H, CORNER_R) - Manifold.cube([IW, ID, IH + 1]).translate([WALL, WALL, FLOOR])

    for (x, y) in boss_centers():
        boss = cyl(IH + 0.01, 2 * BOSS_R, x, y, FLOOR - 0.01)
        # fill the gap between the round boss and the wall(s) it touches
        fy = WALL - 0.5 if y < OD / 2 else OD - WALL - BOSS_R + 0.5
        boss = boss + Manifold.cube([2 * BOSS_R, BOSS_R, IH + 0.01]).translate([x - BOSS_R, fy, FLOOR - 0.01])
        if x < OW / 4 or x > 3 * OW / 4:
            fx = WALL - 0.5 if x < OW / 2 else OW - WALL - BOSS_R + 0.5
            boss = boss + Manifold.cube([BOSS_R, 2 * BOSS_R, IH + 0.01]).translate([fx, y - BOSS_R, FLOOR - 0.01])
        base = base + boss - cyl(SCREW_DEPTH + 0.01, SCREW_PILOT_D, x, y, BASE_H - SCREW_DEPTH)

    # breadboard locating frame (open at the left end so the Pico/USB side is free)
    x0, y0 = ix(BB_X) - RAIL_CLEAR, ix(BB_Y) - RAIL_CLEAR
    x1, y1 = ix(BB_X + BB_L) + RAIL_CLEAR, ix(BB_Y + BB_W) + RAIL_CLEAR
    rails = [
        Manifold.cube([x1 - x0 - 20, RAIL_T, RAIL_H]).translate([x0 + 20, y0 - RAIL_T, FLOOR - 0.01]),
        Manifold.cube([x1 - x0 - 20, RAIL_T, RAIL_H]).translate([x0 + 20, y1, FLOOR - 0.01]),
        Manifold.cube([RAIL_T, y1 - y0 + 2 * RAIL_T, RAIL_H]).translate([x1, y0 - RAIL_T, FLOOR - 0.01]),
    ]
    for r in rails:
        base = base + r

    usb_y = ix(BB_Y + BB_W / 2)
    base = base - Manifold.cube([WALL + 2, USB_W, USB_H]).translate(
        [-1, usb_y - USB_W / 2, FLOOR + USB_Z - USB_H / 2])
    return base


def build_lid():
    lid = rounded_box(OW, OD, LID_T, CORNER_R)
    for (x, y) in boss_centers():
        lid = lid - cyl(LID_T + 1, SCREW_CLEAR_D, x, y, -0.5)
        lid = lid - cyl(CSINK_H + 0.01, SCREW_CLEAR_D, x, y, LID_T - CSINK_H, d_top=CSINK_D)

    top = LID_T - TEXT_DEPTH
    for i, label in enumerate(LABELS):
        x = switch_x(i)
        lid = lid - cyl(LID_T + 1, SWITCH_HOLE_D, x, ix(SWITCH_Y), -0.5)
        lid = lid - cyl(LID_T + 1, LED_HOLE_D, x, ix(LED_Y), -0.5)
        lid = lid - text(label, 2.9 if "\n" in label else 3.3, x, ix(LABEL_Y), top, TEXT_DEPTH + 1)

    # group headers with a thin engraved bracket line under each
    hy = ix(LED_Y + 11)
    for title, a, b in GROUPS:
        xa, xb = switch_x(a) - PITCH / 2 + 2, switch_x(b) + PITCH / 2 - 2
        lid = lid - text(title, 3.6, (xa + xb) / 2, hy + 3.5, top, TEXT_DEPTH + 1)
        lid = lid - Manifold.cube([xb - xa, 0.8, TEXT_DEPTH + 1]).translate([xa, hy - 0.4, top])
    return lid


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)


def preview(base, lid, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12, 10))
    # left: base with a stand-in breadboard; right: lid top view
    ax = fig.add_subplot(2, 1, 1, projection="3d")
    bb = Manifold.cube([BB_L, BB_W, BB_H]).translate([ix(BB_X), ix(BB_Y), FLOOR])
    light = np.array([-0.4, -0.6, 0.7]) / np.linalg.norm([-0.4, -0.6, 0.7])
    for m, color in ((base, "#b9bec7"), (bb, "#f2f2f2")):
        t = to_trimesh(m)
        k = 0.45 + 0.55 * np.clip(t.face_normals @ light, 0, 1)
        ax.add_collection3d(Poly3DCollection(t.triangles, facecolors=np.outer(k, matplotlib.colors.to_rgb(color)),
                                             edgecolors="none"))
    ax.set_xlim(0, OW); ax.set_ylim(0, OD); ax.set_zlim(0, BASE_H)
    ax.set_box_aspect((OW, OD, BASE_H)); ax.view_init(35, -65); ax.set_axis_off()

    ax2 = fig.add_subplot(2, 1, 2)
    t = to_trimesh(lid)
    up = t.face_normals[:, 2] > 0.9
    tops = t.triangles[up]
    z = tops[:, :, 2].mean(axis=1)
    from matplotlib.collections import PolyCollection
    colors = np.where(z > LID_T - 0.1, "#5b6b82", "#e8e8e8")
    ax2.add_collection(PolyCollection(tops[:, :, :2], facecolors=colors, edgecolors="none"))
    ax2.set_xlim(0, OW); ax2.set_ylim(0, OD); ax2.set_aspect("equal"); ax2.set_axis_off()
    plt.tight_layout()
    plt.savefig(path, dpi=110)


if __name__ == "__main__":
    base, lid = build_base(), build_lid()
    for name, m in (("base", base), ("lid", lid)):
        t = to_trimesh(m)
        assert t.is_watertight, name
        t.export(f"{name}.stl")
        print(name, "ok, bbox", np.round(t.extents, 1))
    preview(base, lid, "preview.png")
