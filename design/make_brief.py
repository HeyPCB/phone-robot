"""Writes boards/merch_phone_robot/board.json: Bolt, the phone stand robot (heypcb.ai merch 09).

    "$KICAD_PYTHON" boards/merch_phone_robot/make_brief.py

A robot that holds your phone in landscape and peeks over the top of it. Two kickstands pop out of
its belly (snap-off tabs), slot through its hips and become its hands: the phone rests on them and
leans on its chest. Its left foot is USB-C in from your charger, its right foot USB-C out to your
phone: a 5 V pass-through that switches on only when a phone is there, advertises what the charger
can give (up to 1.5 A), and measures the current. The two RGB eyes over the phone show it: hungry
while the phone draws a lot, content when it is full. Tap the gold antenna for night mode.
Edit this file, not board.json. Frame 86 x 129 mm, origin top-left, y down.

Geometry (all from the side view): the robot plate leans back THETA from vertical; each kickstand is
a plate perpendicular to it, standing on its own bottom edge, its front edge against the robot's
back, its tongue through a slot in the robot and out the front as the ledge the phone sits on.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import merch_kit as K  # noqa: E402

SLUG = "phone-robot"
W, H = 86.0, 129.0
CX = 43.0
Y0 = 127.0                       # the robot's feet (s = 0); s runs up the plate


def y(s):
    return Y0 - s


# ------------------------------------------------------------------------- stand geometry (mm, deg)
THETA = 20.0      # the robot's lean back from vertical: 70 degrees to the desk
T = 1.6           # board thickness
S_LEDGE = 19.0    # the ledge (tongue top) height, measured up the robot's front face
H_TONGUE = 7.0    # tongue height under the ledge, where it passes through the robot
P_TONGUE = 15.0   # tongue reach in front of the robot's face: phones up to 12.5 mm thick
LIP, LIP_T = 3.5, 2.5   # the lip at the tongue's tip: height over the ledge, thickness
B_TOP = 34.0      # how far up the robot's back each kickstand's front edge reaches
B_REAR = 34.0     # the kickstand's rear foot, behind the robot's front foot line
FLAT = 8.0        # the flats on the kickstand's top and rear foot, where its tabs land
U_STAND = 22.0    # each kickstand's offset from the centre line
CH = 2.0          # routed channel round each kickstand
SLOT_W, SLOT_C = 1.85, 0.1
WINDOW_S0 = 26.5  # the belly window's lowest point: 3 mm over the slots' tops
TAB_W = 5.0       # tab width: the five 0.5 mm mouse bites keep 0.55 mm from its sides


def side(s, n):
    """A point of the side view: s up the robot's front face, n behind it -> (x back, z up)."""
    th = math.radians(THETA)
    return (s * math.sin(th) + n * math.cos(th), s * math.cos(th) - n * math.sin(th))


def kickstand_side():
    """The kickstand's outline in its own plane (x back from the robot's front foot, z up)."""
    th = math.radians(THETA)
    foot = (T * math.tan(th) * math.sin(th) + T * math.cos(th), 0.0)
    top = side(B_TOP, T)
    return [foot,
            side(S_LEDGE - H_TONGUE, T),            # the tongue's underside, at the robot's back
            side(S_LEDGE - H_TONGUE, -P_TONGUE),    # its tip, underneath
            side(S_LEDGE + LIP, -P_TONGUE),         # the lip's front top
            side(S_LEDGE + LIP, -P_TONGUE + LIP_T),
            side(S_LEDGE, -P_TONGUE + LIP_T),       # the ledge the phone sits on
            side(S_LEDGE, T),                       # ... back to the robot's back face
            top,
            (top[0] + FLAT, top[1]),                # the top flat (a tab lands here)
            (B_REAR, FLAT),                         # the rear flat (a tab lands here)
            (B_REAR, 0.0)]


def to_board(pt, dx, dy):
    """A kickstand side-view point in the board frame, the kickstand upright (z up -> y down)."""
    return (dx + pt[0], dy - pt[1])


def kick_shape(dx, dy):
    return K.Shape.poly([to_board(p, dx, dy) for p in kickstand_side()]).rounded(0.8)


def nest(max_w=49.0):
    """Two kickstands stacked upright in the belly, the upper one slid sideways, as close as a CH
    channel allows; the pair no wider than `max_w`, as short as possible, its lowest point at
    WINDOW_S0 + CH and centred on CX. Returns [(dx, dy) lower, (dx, dy) upper]."""
    low = kick_shape(0.0, 0.0)
    best = None
    for dx2 in range(-40, 41, 2):
        dx = dx2 / 2.0
        for dy10 in range(-150, -800, -5):              # slide the upper one up until it clears
            dy = dy10 / 10.0
            up = kick_shape(dx, dy)
            if (low.offset(CH / 2) & up.offset(CH / 2)).area() <= 1e-6:
                x0, y0_, x1, y1 = (low | up).bbox()
                if x1 - x0 <= max_w:
                    key = (round(y1 - y0_, 2), round(x1 - x0, 2))
                    if best is None or key < best[0]:
                        best = (key, dx, dy)
                break
    if best is None:
        raise SystemExit("no stacking of two kickstands fits %.0f mm wide" % max_w)
    _, dx, dy = best
    x0, y0_, x1, y1 = (kick_shape(0, 0) | kick_shape(dx, dy)).bbox()
    ox, oy = CX - (x0 + x1) / 2, y(WINDOW_S0 + CH) - y1
    return [(ox, oy), (dx + ox, dy + oy)]


# ---------------------------------------------------------------------------------------- outline
feet = K.Shape.rect(CX - 40, y(17), CX + 40, y(0), r=3.0)
arch = K.Shape.rect(CX - 7, y(3.5), CX + 7, y(0) + 2.0, r=1.5)
body = K.Shape.rect(CX - 35, y(100), CX + 35, y(14), r=6.0)
neck = K.Shape.rect(CX - 9, y(102), CX + 9, y(97))
head = K.Shape.rect(CX - 28, y(118), CX + 28, y(99), r=6.0)
ears = K.Shape.circle(CX - 28.6, y(108.5), 3.2) | K.Shape.circle(CX + 28.6, y(108.5), 3.2)
antenna = K.Shape.capsule(CX, y(117), CX, y(121), 2.4) | K.Shape.circle(CX, y(121.8), 3.5)   # r 3.5: the SDK tests the D4 pad's box corners
robot = (feet - arch | body | neck | head | ears | antenna).rounded(1.0)

KICK = nest()
kicks = [kick_shape(*k) for k in KICK]
slots = []
for sx in (-1, 1):
    u = CX + sx * U_STAND
    slots.append(K.Shape.capsule(u, y(S_LEDGE - H_TONGUE - SLOT_C), u, y(S_LEDGE + LIP + SLOT_C), SLOT_W))


def flat(k, a, b):
    """The midpoint of kickstand k's edge between side-view points a and b, in the board frame."""
    pa, pb = to_board(a, *KICK[k]), to_board(b, *KICK[k])
    return ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)


top_side = side(B_TOP, T)
TABS = []        # (kickstand, centre on its edge, outward normal)
for k in (0, 1):
    TABS.append((k, flat(k, (B_REAR, FLAT), (B_REAR, 0.0)), (1.0, 0.0)))          # rear flat -> right strip
TABS.append((1, flat(1, top_side, (top_side[0] + FLAT, top_side[1])), (0.0, -1.0)))   # upper: top flat, up
foot0 = kickstand_side()[0]
TABS.append((0, flat(0, (foot0[0] + 9.0, 0.0), (foot0[0] + 17.0, 0.0)), (0.0, 1.0)))  # lower: base, down

tabs = []
for k, (cx, cy), (nx, ny) in TABS:
    ax, ay = cx - nx * 0.6, cy - ny * 0.6                  # 0.6 into the kickstand
    bx, by = cx + nx * (CH + 0.6), cy + ny * (CH + 0.6)    # across the channel, 0.6 into the robot
    tx, ty = -ny * TAB_W / 2, nx * TAB_W / 2
    tabs.append(K.Shape.poly([(ax + tx, ay + ty), (bx + tx, by + ty), (bx - tx, by - ty), (ax - tx, ay - ty)]))

window = (kicks[0] | kicks[1]).offset(CH)
cut = window - kicks[0] - kicks[1]
for t_ in tabs:
    cut = cut - t_
CUTOUTS = [K.Shape.poly(ring) for ring, holes in cut.rings()] + slots
board_region = robot
for c in CUTOUTS:
    board_region = board_region - c

# ---------------------------------------------------------------------------------------- blocks
MCU_PINS = {"U?.1": "ISENSE", "U?.6": "OUT_CC1", "U?.5": "OUT_CC2", "U?.19": "IN_CC1", "U?.20": "IN_CC2",
            "U?.3": "TOUCH", "U?.16": "LED_DIN", "U?.13": "VBUS_EN", "U?.11": "RP_15", "U?.12": "RP_DEF"}
MCU_NC = ["U?.%d" % p for p in (2, 4, 8, 10, 14, 15, 17)]

BLOCKS = [
    {"block": "usb_c_data_5v", "as": "in", "title": "Left foot: USB-C in from the charger (5 V sink, Rd 5.1k)",
     "nets": {"CC1": "IN_CC1", "CC2": "IN_CC2"}},
    {"block": "merch_vbus_switch", "as": "sw", "title": "VBUS to the phone: P-FET, soft start",
     "nets": {"IN": "VBUS", "OUT": "VBUS_SW", "DRV": "SW_DRV"}},
    {"block": "merch_lowside_fet", "as": "drv", "title": "Switch driver", "nets": {"LOAD": "SW_DRV", "EN": "VBUS_EN"}},
    {"block": "merch_ina180_sense", "as": "isense", "title": "Charge current: 20 mOhm and INA180A2, 1 V per amp",
     "nets": {"HI": "VBUS_SW", "LO": "VBUS_OUT", "VDD": "VBUS", "OUT": "ISENSE"}},
    {"block": "merch_usbc_source_out", "as": "out", "title": "Right foot: USB-C out to the phone (Rp 1.5 A / default)",
     "nets": {"VBUS_OUT": "VBUS_OUT", "CC1": "OUT_CC1", "CC2": "OUT_CC2", "RP_15": "RP_15", "RP_DEF": "RP_DEF"}},
    {"block": "merch_mcu_ch32v003", "as": "mcu", "title": "CH32V003: CC detection, switch, current, eyes",
     "nets": {"VDD": "VBUS"}, "pinNets": MCU_PINS, "no_connect": MCU_NC},
    {"block": "irisring_pixel", "as": "eye_l", "title": "Left eye: WS2812C-2020",
     "nets": {"VDD": "VBUS"}, "pinNets": {"D?.3": "LED_DIN", "D?.1": "LED_CHAIN"}},
    {"block": "irisring_pixel", "as": "eye_r", "title": "Right eye: WS2812C-2020",
     "nets": {"VDD": "VBUS"}, "pinNets": {"D?.3": "LED_CHAIN"}, "no_connect": ["D?.1"]},
    {"block": "merch_touch_pad", "as": "touch", "title": "The antenna: tap for night mode", "nets": {"TOUCH": "TOUCH"}},
] + [{"block": "merch_breakline", "as": "tab%d" % i, "title": "Kickstand tab %d" % i} for i in range(1, 5)]

# ---------------------------------------------------------------------------------------- parts
parts = K.design_footprints(BLOCKS, os.path.join(os.path.dirname(HERE), "..", "blocks"))
L = K.Layout(parts)
# feet: the ports open sideways, mouths 0.6 mm proud of the outline
L.lock("in:J?", CX - 40 + 3.6, y(8.0), 270, "left foot: USB-C in, mouth out to the left", overhang=True)
L.lock("out:J?", CX + 40 - 3.6, y(8.0), 90, "right foot: USB-C out, mouth out to the right", overhang=True)
L.lock("in:R1?", 13.2, y(10.6), 90, "Rd on CC1")
L.lock("in:R2?", 13.2, y(6.4), 90, "Rd on CC2")
L.lock("in:C?", 16.2, y(13.6), 90, "input bulk")
L.lock("sw:Q?", 17.0, y(6.8), 0, "the P-FET, by the input")
L.lock("sw:R1?", 23.0, y(4.8), 0, "gate pull-up")
L.lock("sw:C?", 23.0, y(7.0), 0, "soft start")
L.lock("sw:R2?", 23.0, y(9.2), 0, "gate series")
L.lock("drv:Q?", 27.4, y(7.0), 0, "switch driver")
L.lock("drv:R?", 27.4, y(10.2), 0, "driver pull-down")
L.lock("isense:R?", 31.0, y(14.6), 0, "the shunt")
L.lock("isense:U?", 31.2, y(19.0), 90, "INA180A2")
L.lock("isense:C?", 27.0, y(19.6), 90, "INA bypass")
L.lock("mcu:U?", CX + 6.0, y(13.2), 0, "MCU, between the hips")
L.lock("mcu:C?", CX + 6.0, y(19.4), 0, "MCU bypass")
for i in range(3):
    L.lock("mcu:TP%d?" % (i + 1), CX + 3.5 + 2.54 * i, y(5.8), 0, "SWIO pads (VDD, SWIO, GND)")
L.lock("out:R1?", 58.6, y(10.6), 90, "Rp 1.5 A, CC1")
L.lock("out:R2?", 58.6, y(6.4), 90, "Rp 1.5 A, CC2")
L.lock("out:R3?", 72.4, y(14.6), 0, "Rp default, CC1")
L.lock("out:R4?", 72.4, y(16.4), 0, "Rp default, CC2")
L.lock("out:C?", 69.8, y(3.8), 0, "output bulk")
L.lock("out:R5?", 62.0, y(4.6), 90, "VBUS_OUT bleeder")
# head: eyes, their caps, the antenna
EYE_S, EYE_DX = 109.0, 10.0
L.lock("eye_l:D?", CX - EYE_DX, y(EYE_S), 0, "left eye")
L.lock("eye_r:D?", CX + EYE_DX, y(EYE_S), 0, "right eye")
L.lock("eye_l:C?", CX - 19.5, y(EYE_S), 90, "left eye's bypass")
L.lock("eye_r:C?", CX + 19.5, y(EYE_S), 90, "right eye's bypass")
L.lock("touch:TP?", CX, y(121.8), 0, "the antenna ball: a gold touch pad")
L.lock("touch:R?", CX, y(116.0), 0, "touch series resistor, at the antenna's root")
for i, (k, (cx, cy), (nx, ny)) in enumerate(TABS):
    rot = 0 if nx == 0 else 90
    L.lock("tab%d:H?" % (i + 1), cx - nx * 0.15, cy - ny * 0.15, rot,
           "mouse bites across tab %d, 0.15 mm inside the kickstand's edge" % (i + 1), overhang=True)

# ---------------------------------------------------------------------------------------- art
art = []
# head: gold-ringed eyes, a gold grille mouth, gold ear bolts, a name on the forehead
for sx in (-1, 1):
    ex, ey = CX + sx * EYE_DX, y(EYE_S)
    ring = K.Shape.circle(ex, ey, 4.4) - K.Shape.circle(ex, ey, 3.1)
    gap = K.Shape.rect(ex - 1.5, ey, ex + 1.5, ey + 5.0)                  # the traces' way in
    art += K.gold(ring - gap, "eye_ring")
    art += K.silk_ring(K.Shape.circle(ex, ey, 5.6), "eye_disc", 0.25)
    art += K.gold(K.Shape.circle(CX + sx * 28.6, y(108.5), 1.9), "ear_bolt")
mouth = K.Shape.rect(CX - 7.0, y(104.6), CX + 7.0, y(101.4), r=1.2)
for k in range(5):
    gx = CX - 4.8 + 2.4 * k
    mouth = mouth - K.Shape.rect(gx - 0.45, y(104.0), gx + 0.45, y(102.0), r=0.3)
art += K.gold(mouth, "mouth")
art += K.text("BOLT", CX, y(112.6), size=1.3, bold=True, name="name_front")
# feet: what plugs in where, and the brand
art += K.text("IN", CX - 34.0, y(14.6), size=1.3, bold=True, name="label_in")
art += K.text("OUT", CX + 33.6, y(14.6), size=1.3, bold=True, name="label_out")
art += K.text("charger", CX - 34.0, y(2.2), size=0.8, name="hint_in")
art += K.text("phone", CX + 33.6, y(2.2), size=0.8, name="hint_out")
art += K.text("heypcb.ai", CX - 13.5, y(2.0), size=0.9, bold=True, name="brand_front")
# chest: gold rivets at the corners of the belly
for rx, rs in ((CX - 31.0, 92.0), (CX + 31.0, 92.0), (CX - 31.0, 22.0), (CX + 31.0, 22.0)):
    art += K.gold(K.Shape.circle(rx, y(rs), 1.1), "rivet")
# side strips: a charge meter on the left, a bolt on the right (silk only: traces run under them)
BAT_X0, BAT_X1, BAT_S0, BAT_S1 = CX - 32.5, CX - 26.5, 38.0, 78.0
art += K.silk_ring(K.Shape.rect(BAT_X0, y(BAT_S1), BAT_X1, y(BAT_S0), r=1.0), "battery", 0.3)
art += K.silk_fill(K.Shape.rect(CX - 30.7, y(BAT_S1 + 1.6), CX - 28.3, y(BAT_S1 + 0.2), r=0.3), "battery_nub")
for i in range(4):
    b0 = BAT_S0 + 1.4 + 8.6 * i
    art += K.silk_fill(K.Shape.rect(BAT_X0 + 1.2, y(b0 + 7.0), BAT_X1 - 1.2, y(b0), r=0.4), "battery_bar")
bolt = K.Shape.poly([(CX + 31.4, y(66.0)), (CX + 27.6, y(57.0)), (CX + 29.9, y(57.0)), (CX + 28.4, y(49.0)),
                     (CX + 32.4, y(59.0)), (CX + 30.1, y(59.0))])
art += K.silk_fill(bolt, "bolt")
art += K.text("5 V", CX + 30.0, y(45.6), size=1.1, bold=True, name="volts")
# kickstands: which hand, "snap out", a gold heart
for k, (dx, dy) in enumerate(KICK):
    hx, hy = to_board(side(S_LEDGE - H_TONGUE / 2, -P_TONGUE + 5.0), dx, dy)
    art += K.text("hand %d" % (k + 1), hx + 0.8, hy, size=0.9, bold=True, name="hand%d" % k)
    sx_, sy_ = to_board((B_REAR - 11.0, 9.0), dx, dy)
    art += K.text("snap out", sx_, sy_, size=0.8, name="snap%d" % k)
    art += K.gold(K.heart(sx_, sy_ - 4.0, 3.2), "heart%d" % k)
# back: the QR behind the head, how to build it, the brand
art += K.qr(K.world_url(SLUG), CX, y(108.0), size=10.0, side="B")
art += K.text("heypcb.ai", CX, y(98.6), size=1.0, side="B", bold=True, name="brand_back")
HOWTO = ["1  snap both hands out of my belly",
         "2  push them through my hips from behind",
         "3  charger to IN, phone cable to OUT",
         "4  phone on my hands, sideways; tap my antenna for night"]
for i, line in enumerate(HOWTO):
    art += K.text(line, CX, y(10.2 - 1.8 * i), size=0.8, side="B", name="howto%d" % i)

keep = {}
for i, it in enumerate(a for a in art if "F.Cu" in a.get("layers", [])):
    keep["gold%d" % i] = K.Shape.poly(it["points"]).offset(0.3)
for i, sl in enumerate(slots):
    keep["slot%d" % i] = sl.offset(1.0)
if os.environ.get("MERCH_PREVIEW"):
    K.preview(os.environ["MERCH_PREVIEW"], board_region, L, art, keep)
K.check_art(board_region, art)
L.check(board_region, edge=0.5, keep=keep)

wx0, wy0, wx1, wy1 = window.bbox()
brief = {
    "name": "phone_robot",
    "title": "Bolt - phone stand robot: USB-C pass-through that measures your phone charging, RGB eyes",
    "revision": "A",
    "brief": "A robot-shaped phone stand. Two kickstands snap out of its belly and slot through its hips to "
             "hold a phone in landscape; its head peeks over the phone. USB-C in (5 V sink) on its left foot, "
             "USB-C out on its right foot: a CH32V003 reads the charger's CC level, advertises 1.5 A or default "
             "USB power to the phone with GPIO-driven Rp, switches VBUS on through a soft-started P-FET only "
             "when it sees the phone's Rd, and measures the charge current with a 20 mOhm shunt and an "
             "INA180A2. Two WS2812C eyes show it; the gold antenna is a touch pad for night mode. 2 layers, "
             "single-sided SMT, matte black mask, white silk, ENIG.",
    "blocks": BLOCKS,
    "pwrFlags": ["GND", "VBUS"],
    "netClasses": [{"name": "PWR", "nets": ["VBUS", "VBUS_SW", "VBUS_OUT"], "track": 0.6, "clearance": 0.2,
                    "via": [0.6, 0.3], "why": "up to 1.5 A to the phone"}],
    "board": {
        "width": W, "height": H, "corner_radius": 0.0, "layers": 2, "origin": [100.0, 100.0],
        "shape": {"type": "polygon", "points": K.outline_points(robot), "fillet": 0},
        "cutouts": [{"type": "polygon", "points": K.outline_points(c), "fillet": 0} for c in CUTOUTS],
        "keepouts": [{"name": "kickstands", "rect": [round(wx0 - 0.6, 2), round(wy0 - 0.6, 2),
                                                     round(wx1 + 0.6, 2), round(wy1 + 0.6, 2)],
                      "layers": "all", "no": ["tracks", "vias", "pour"]}],
        "rules": {"clearance": 0.2, "track": 0.2, "via": [0.6, 0.3], "edge_clearance": 0.5,
                  "hole_to_hole": 0.5, "min_through_hole": 0.3, "min_track": 0.15},
        "finish": {"mask": "Matte Black", "silk": "White", "copper": "ENIG",
                   "why": "a black robot with gold eyes, mouth, bolts and hearts"},
        "unpoured": ["F.Cu"],
        "notes": "2 layers; the face is unpoured, GND plane on the back. The kickstands are held by four "
                 "5 mm tabs with drilled mouse bites; tracks, vias and pour keep off them.",
    },
    "placement": L.locks,
    "route": {"passes": 30, "fanout": True, "solve_s": 300},
    "stitch_pitch": 6.0,
    "silk": {"designators": "hide",
             "title": [{"text": "Bolt", "y": round(y(15.6) - 2.2, 2), "size": 1.8, "bold": True},
                       {"text": "phone stand robot  rev {revision}", "y": round(y(13.2) - 2.2, 2), "size": 0.9}]},
    "art": art,
    "captions": {"done_3d": "Bolt: a phone stand robot with gold eyes, USB-C feet and pop-out hands."},
}
K.write_brief(os.path.join(HERE, "board.json"), brief)
print("wrote board.json: %d outline points, %d cutouts, %d art items, %d locks, QR -> %s"
      % (len(brief["board"]["shape"]["points"]), len(CUTOUTS), len(art), len(L.locks), K.world_url(SLUG)))
