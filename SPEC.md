# 09 · Bolt, the phone stand robot: SPEC

## Who it's for, and the use case

Anyone with a phone and a desk: video calls, a recipe on the kitchen counter, a show while eating
lunch, the phone propped up next to the monitor all day. Bolt holds the phone in landscape at a
comfortable 70°, charges it through its feet, and tells you at a glance, over the top of the phone,
whether the phone is still charging or is full. It also answers a question nobody can answer from a
cable alone: is this phone actually charging right now, and how hard?

## The cute concept

A matte-black robot with gold eyes, a gold grille mouth, gold ear bolts and a gold antenna ball. It holds
your phone in its two hands and peeks over the top of it. The hands come out of its own belly: snap
them out, push them through its hips from behind, done. Its left foot says IN (the charger), its right
foot says OUT (the phone). While the phone eats, its eyes glow orange and pulse; when the phone is
full they turn a contented green.

## Features

| | |
|---|---|
| Stand | landscape phones up to 12.5 mm thick (case included) on two ledges 44 mm apart, leaning back at 70°; the ledges sit 18-22 mm above the desk |
| Assembly | two kickstands snap out of the belly (four 5 mm tabs with drilled mouse bites) and slot through 1.85 mm slots in the hips; no glue, no screws |
| USB-C in (left foot) | a 5 V sink: 5.1k Rd on both CC lines; the MCU reads the charger's CC level (default USB, 1.5 A or 3 A) |
| USB-C out (right foot) | a 5 V source for the phone: 22k Rp (1.5 A) when the charger offers 1.5 A or more, 56k Rp (default USB power) otherwise |
| Port switch | AO3401A P-FET with a soft start (0.2 ms); on only after the phone's Rd has been seen for 150 ms, off within 20 ms of unplugging, 10k bleeder on the port |
| Current sense | 20 mΩ shunt and INA180A2 (gain 50): 1 V per amp into the ADC, about 5 mA resolution |
| Protection | over 1.8 A (1.5 A offered) or 1.1 A (default offered) for 0.5 s, or over 3 A in two readings in a row (20 ms): port off, red eyes, retry after 5 s |
| Eyes | two WS2812C-2020 over the phone: soft blue blinking (no phone), orange pulsing faster with the current (eating, over 300 mA), yellow-green breathing (sipping, 60-300 mA), green (full: under 60 mA for a minute; dims after 5 minutes), red blinking (fault) |
| Antenna | a gold capacitive touch pad: tap for night mode (eyes dark); tap in night mode for a 3 s look, tap again within those 3 s to wake |
| MCU | CH32V003F4P6 from VBUS, five ADC channels (both port's CC lines, the current), firmware in [`firmware/`](firmware/) |
| Board | 2 layers, matte black mask, white silk, ENIG; single-sided SMT (the USB-C shells' tabs are through-hole) |

**Not USB Power Delivery.** Bolt passes 5 V only. A phone that would fast-charge at 9 V from your PD
charger charges at 5 V and at most 1.5 A (7.5 W) through Bolt. That is deliberate: forwarding PD needs
the phone and the charger to talk through the robot, which a passive pass-through gets right only for
one of the two plug orientations, and a 20 V rail would need a different switch, sense and MCU supply.
For a desk stand the phone sits on for hours, 7.5 W is enough; the SPEC says so and so does the store
copy.

## Power budget

Bolt has no battery; it runs from the charger.

| What | Current from 5 V |
|---|---|
| CH32V003, awake (no sleep; it samples every 10 ms) | about 5 mA (estimate) |
| INA180A2 | 0.2 mA (catalogue row) |
| Two WS2812C at the firmware's brightness (48 of 255) | 1-4 mA, plus their own quiescent current |
| **Bolt itself** | **about 10 mA, 0.05 W** |

Loss in the path to the phone at 1.5 A: the P-FET (about 60 mΩ at 5 V gate drive) 0.14 W, the shunt
0.045 W, copper and contacts a few tens of mW: under 0.25 W of 7.5 W, so the phone gets about 97 %. The
P-FET's 0.14 W in a SOT-23 on the GND-poured board is a rise of a few tens of degrees at most; at
3 A it would be 0.54 W, which is why Bolt never offers more than 1.5 A. Design estimates; no Bolt has
been built.

## BOM (100 units, live JLC/LCSC prices read 2026-10-05)

| Refs | Value | Qty | LCSC | MPN | Class | Unit @100 | Line |
|---|---|---|---|---|---|---|---|
| C1, C4 | 10uF (input, port) | 2 | C15850 | CL21A106KAYNNNE | basic | $0.0713 | $0.1426 |
| C2 | 10nF (soft start) | 1 | C57112 | 0603B103K500NT | basic | $0.0202 | $0.0202 |
| C3, C5 | 100nF | 2 | C14663 | CC0603KRX7R9BB104 | basic | $0.0106 | $0.0212 |
| C6, C7 | 100nF (eyes) | 2 | C1525 | CL05B104KO5NNNC | basic | $0.0060 | $0.0120 |
| D1, D2 | WS2812C-2020-V1 (eyes) | 2 | C2976072 | WS2812C-2020-V1 | extended | $0.0728 | $0.1456 |
| J1 | USB-C (in) | 1 | C165948 | TYPE-C-31-M-12 | extended | $0.1468 | $0.1468 |
| J2 | USB-C (out) | 1 | C165948 | TYPE-C-31-M-12 | extended | $0.1468 | $0.1468 |
| Q1 | AO3401A (port switch) | 1 | C15127 | AO3401A | basic | $0.0596 | $0.0596 |
| Q2 | AO3400A (its driver) | 1 | C20917 | AO3400A | basic | $0.0682 | $0.0682 |
| R1, R2 | 5.1k (Rd) | 2 | C25905 | 0402WGF5101TCE | basic | $0.0009 | $0.0018 |
| R3, R5 | 100k | 2 | C25803 | 0603WAF1003T5E | basic | $0.0016 | $0.0032 |
| R4, R7, R8 | 22k (gate, Rp 1.5 A) | 3 | C31850 | 0603WAF2202T5E | basic | $0.0014 | $0.0042 |
| R6 | 20 mΩ shunt (1206, 1 W) | 1 | C7420010 | FRM121WFR020TM | extended | $0.0350 | $0.0350 |
| R9, R10 | 56k (Rp default) | 2 | C23206 | 0603WAF5602T5E | basic | $0.0020 | $0.0040 |
| R11 | 10k (port bleeder) | 1 | C25744 | 0402WGF1002TCE | basic | $0.0029 | $0.0029 |
| R12 | 1k (antenna) | 1 | C21190 | 0603WAF1001T5E | basic | $0.0039 | $0.0039 |
| U1 | INA180A2 | 1 | C192764 | INA180A2IDBVR | extended | $0.1400 | $0.1400 |
| U2 | CH32V003F4P6 | 1 | C5187096 | CH32V003F4P6 | extended | $0.2227 | $0.2227 |
| | **Parts** | | | | | | **$1.18** |
| | Extended-part loading fee ($3 x 5 / 100 boards) | | | | | | $0.15 |
| | **BOM per board @100** | | | | | | **$1.33** |

Not in the BOM: the PCB (2 layers, ENIG, matte black, 80.1 x 125.4 mm: by far the largest cost of this
product), assembly labour, and a short USB-C to USB-C cable for the phone (worth including in the box).
TP1-TP4 are copper pads and H1-H4 drilled mouse bites, not parts. Machine-readable:
[`bom_cost.json`](bom_cost.json).

## Dimensions

80.1 x 125.4 mm (Edge.Cuts bounding box, pcbnew), 75.8 cm² including the two kickstands, 1.6 mm FR4.
Assembled: about 118 mm tall, 80 mm wide and 44 mm deep (the kickstands reach 34 mm behind
the robot's front feet and the ledges 10 mm in front of them).

## Mounting plan (no enclosure)

It is its own stand. The geometry, from the side: the robot plate leans back 20° from vertical and
stands on its feet; each kickstand is a plate at right angles to it, standing on its own bottom edge,
its front edge against the robot's back for 34 mm, and its tongue through the slot in the robot's hip.
The tongue comes out of the front as a 15 mm ledge with a 3.5 mm lip: the phone sits on the two ledges
and leans on the robot's chest. The robot's front feet and the two kickstands' bottom edges make a
stable triangle; the phone's centre of mass sits about 15 mm behind the front feet, well inside the
kickstands' 34 mm. Everything above the phone's top edge is head: the eyes are visible over phones up to
78 mm tall in landscape.

Portrait also works mechanically (the ledges are 44 mm apart, so the phone's USB-C port is between them),
but only with a right-angle cable: the ledges are 18 mm over the desk.

## Safety

5 V USB only, no battery, no mains. Every corner of the outline is rounded (1 mm minimum; the kickstands'
corners 0.8 mm). The phone port obeys the USB Type-C rules for a source: no voltage on it until a sink
is attached, a current advertisement no higher than what the charger itself offers (and never above
1.5 A), VBUS removed within 20 ms of unplugging and bled to 0 V. A short on the phone port trips the
firmware's over-current check (port off within 20 ms at more than 3 A, 0.5 s at more than 1.8 A); the
charger's own protection backs it up. The snapped tabs leave a slightly rough edge: file it.

## Verification (measured by KiCad 10.0.6 on the files in this folder)

ERC 0 errors / 0 warnings · netlist round trip identical (21 nets) · routing 76 → 0 open (315 tracks,
35 vias) · DRC 0 errors / 0 unconnected / 0 parity, 19 warnings, all deliberate: 16 `hole_to_hole`
between the mouse bites of the four breakaway tabs (0.5 mm holes at 0.85 mm pitch, KiCad's own
Panelization footprint) and 3 `lib_footprint_mismatch` (the two USB-C shells and the antenna pad, whose
silk is clipped at the edge) · DFM `jlcpcb_2layer` 0 errors (1 warning: stock footprint silk at 0.12 mm,
printed at the fab's 0.15 mm) · fab gate ready · QR modules 0.345 mm. Firmware: 2,996 B of 16 KB flash,
500 B of 2 KB RAM. Full numbers: [`report.json`](report.json), [`measured.json`](measured.json).

**Not built yet.** Not fabricated, assembled or powered. Things only a prototype can settle:
- the slot fit (1.85 mm for 1.6 mm board; FR4 is ±10 % thick) and that the kickstands hold the 70° under
  a 240 g phone;
- whether the fab accepts the breakaway kickstands as one design (four tabs, mouse bites) or charges
  them as a panel;
- the CC thresholds on a real phone (a dual-role phone toggles Rp/Rd before it settles as a sink) and
  the touch threshold on the antenna;
- the P-FET's temperature after an hour at 1.5 A.
