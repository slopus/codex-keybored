"""Generate the manufacture-oriented Codeks Keybored wired Rev A PCB in KiCad 10.

The board is intentionally a wired, USB-C STM32F072 revision.  Its 90 x 90 mm
outline, four M3 mounting holes, switch grid, controls, USB aperture and lower
clearance remain compatible with a future BLE/battery PCB replacement. Six
copper layers provide dedicated ground/+5 V planes and four routing layers.
"""

from pathlib import Path
import json
import math

import pcbnew

ROOT = Path("/Users/steve/Documents/CodexKB/codex-micro/electronics")
OUT = ROOT / "kicad"
BOARD_PATH = OUT / "codex_micro_wired_revA.kicad_pcb"
FP_ROOT = Path(
    "/Users/steve/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
)


def mm(value):
    return pcbnew.FromMM(value)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


board = pcbnew.BOARD()
# Six copper layers leave four routing layers around two low-impedance planes.
# The first four-layer trial could not complete this dense LED/matrix fan-out.
board.SetCopperLayerCount(6)
board.SetLayerName(pcbnew.In1_Cu, "GND_PLANE")
board.SetLayerName(pcbnew.In2_Cu, "SIGNAL_1")
board.SetLayerName(pcbnew.In3_Cu, "SIGNAL_2")
board.SetLayerName(pcbnew.In4_Cu, "+5V_PLANE")
settings = board.GetDesignSettings()
settings.m_MinClearance = mm(0.10)
settings.m_TrackMinWidth = mm(0.15)
settings.m_ViasMinSize = mm(0.40)
settings.m_ViasMinDrill = mm(0.2)
settings.m_MinThroughDrill = mm(0.2)
settings.m_HoleClearance = mm(0.20)
settings.m_HoleToHoleMin = mm(0.20)
settings.m_CopperEdgeClearance = mm(0.20)
default_class = settings.m_NetSettings.GetDefaultNetclass()
default_class.SetClearance(mm(0.10))
default_class.SetTrackWidth(mm(0.20))
default_class.SetViaDiameter(mm(0.60))
default_class.SetViaDrill(mm(0.30))


NETS = {}


def net(name):
    if name not in NETS:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
        NETS[name] = item
    return NETS[name]


for name in [
    "GND", "+5V", "+3V3",
    "USB_DP_CONN", "USB_DM_CONN", "USB_DP_PROT", "USB_DM_PROT",
    "NRST", "BOOT0", "SWCLK", "SWD",
    "ROW0", "ROW1", "ROW2", "ROW3",
    "COL0", "COL1", "COL2", "COL3",
    "ENC_A", "ENC_B", "ENC_SW", "TOUCH", "TOUCH_ELECTRODE",
    "JOY_X", "JOY_Y", "RGB_3V3", "RGB_5V",
]:
    net(name)


def load_fp(lib, name, ref, value, x, y, side="F", rotation=0, dnp=False):
    fp = pcbnew.FootprintLoad(str(FP_ROOT / f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(rotation)
    board.Add(fp)
    if side == "B":
        fp.Flip(fp.GetPosition(), False)
    fp.SetDNP(dnp)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    return fp


def pads(fp, number):
    return [pad for pad in fp.Pads() if pad.GetNumber() == str(number)]


def assign(fp, number, net_name):
    found = pads(fp, number)
    if not found:
        raise RuntimeError(f"{fp.GetReference()} has no pad {number}")
    for pad in found:
        pad.SetNet(net(net_name))


def set_map(fp, mapping):
    for number, net_name in mapping.items():
        assign(fp, number, net_name)


def custom_fp(ref, value, x, y, dnp=False):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(vec(x, y))
    fp.SetDNP(dnp)
    fp.SetAllowMissingCourtyard(True)
    board.Add(fp)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    return fp


def add_pad(fp, number, dx, dy, sx, sy, drill=None, net_name=None,
            shape=pcbnew.PAD_SHAPE_CIRCLE, side="THT", copper_only=False):
    pad = pcbnew.PAD(fp)
    pad.SetNumber(str(number))
    pad.SetShape(shape)
    pad.SetSize(vec(sx, sy))
    pad.SetPosition(fp.GetPosition() + vec(dx, dy))
    if side == "THT":
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetDrillSize(vec(drill, drill))
        pad.SetLayerSet(pcbnew.PAD.PTHMask())
    elif side == "NPTH":
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetDrillSize(vec(drill, drill))
        pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
    else:
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        layers = pcbnew.LSET()
        copper_layer = pcbnew.F_Cu if side == "F" else pcbnew.B_Cu
        layers.AddLayer(copper_layer)
        if not copper_only:
            layers.AddLayer(pcbnew.F_Paste if side == "F" else pcbnew.B_Paste)
            layers.AddLayer(pcbnew.F_Mask if side == "F" else pcbnew.B_Mask)
        pad.SetLayerSet(layers)
    if net_name:
        pad.SetNet(net(net_name))
    fp.Add(pad)
    return pad


def add_switch(ref, x, y, row_net, node_net):
    fp = custom_fp(ref, "Gateron_KS-33_H10B050NN-Y24", x, y, dnp=True)
    # Official KS-33 drawing: central locating hole Ø5.25; terminals Ø1.00
    # at X=-2.60/+4.40, Y=+5.75 relative to the switch center.
    add_pad(fp, "", 0, 0, 5.3, 5.3, drill=5.3, side="NPTH")
    add_pad(fp, 1, -2.6, 5.75, 1.9, 1.9, drill=1.2, net_name=row_net)
    add_pad(fp, 2, 4.4, 5.75, 1.9, 1.9, drill=1.2, net_name=node_net)
    return fp


def add_mount(ref, x, y, diameter=3.2):
    fp = custom_fp(ref, "MountingHole_M3", x, y, dnp=True)
    add_pad(fp, "", 0, 0, diameter, diameter, drill=diameter, side="NPTH")
    return fp


def add_text(text, x, y, layer=pcbnew.F_SilkS, size=1.0, rotation=0, mirrored=False):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(vec(x, y))
    item.SetLayer(layer)
    item.SetTextSize(vec(size, size))
    item.SetTextThickness(mm(0.15))
    item.SetTextAngleDegrees(rotation)
    item.SetMirrored(mirrored)
    board.Add(item)
    return item


def add_line(start, end, layer, width=0.15):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetStart(vec(*start))
    shape.SetEnd(vec(*end))
    shape.SetLayer(layer)
    shape.SetWidth(mm(width))
    board.Add(shape)


def add_arc(start, mid, end, layer, width=0.15):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_ARC)
    shape.SetArcGeometry(vec(*start), vec(*mid), vec(*end))
    shape.SetLayer(layer)
    shape.SetWidth(mm(width))
    board.Add(shape)


def tune_reverse_led_window(fp, x, y):
    """Replace the library cutout with a JLC-friendly rounded 3.38 x 2.98 mm window.

    The stock KiCad 3.49 x 3.09 mm opening leaves only about 0.16 mm from a
    0.15 mm trace exiting the inner edge of each SK6812MINI-E pad.  The LED
    body is 3.2 x 2.8 mm, so this still leaves roughly 0.09 mm per side while
    restoring more than the required 0.20 mm copper-to-routed-edge clearance.
    """
    scale_x = 3.38 / 3.487868
    scale_y = 2.98 / 3.087868

    def scaled(point):
        px = pcbnew.ToMM(point.x)
        py = pcbnew.ToMM(point.y)
        return vec(x + (px - x) * scale_x, y + (py - y) * scale_y)

    for graphic in fp.GraphicalItems():
        if graphic.GetLayer() != pcbnew.Edge_Cuts:
            continue
        start = scaled(graphic.GetStart())
        end = scaled(graphic.GetEnd())
        if graphic.GetShape() == pcbnew.SHAPE_T_ARC:
            graphic.SetArcGeometry(start, scaled(graphic.GetArcMid()), end)
        else:
            graphic.SetStart(start)
            graphic.SetEnd(end)


# 90 x 90 mm rounded-R4 outline; screw pattern matches the Fusion housing.
add_line((4, 0), (86, 0), pcbnew.Edge_Cuts)
add_arc((86, 0), (88.828, 1.172), (90, 4), pcbnew.Edge_Cuts)
add_line((90, 4), (90, 86), pcbnew.Edge_Cuts)
add_arc((90, 86), (88.828, 88.828), (86, 90), pcbnew.Edge_Cuts)
add_line((86, 90), (4, 90), pcbnew.Edge_Cuts)
add_arc((4, 90), (1.172, 88.828), (0, 86), pcbnew.Edge_Cuts)
add_line((0, 86), (0, 4), pcbnew.Edge_Cuts)
add_arc((0, 4), (1.172, 1.172), (4, 0), pcbnew.Edge_Cuts)

for index, (x, y) in enumerate(((6, 6), (84, 6), (6, 84), (84, 84)), 1):
    add_mount(f"H{index}", x, y)


# Official installed layout has 12 keyboard switches.  Work Louder/OpenAI's
# published "13x mechanical switches" includes the encoder push switch:
# encoder / switch / switch / joystick, then 4 / 4, then touch / 2U / 1U.
PITCH = 19.05
COL_X = [16.425, 35.475, 54.525, 73.575]
ROW_Y = [16.425, 35.475, 54.525, 73.575]
SWITCH_DATA = [
    ("SW1", COL_X[1], ROW_Y[0], "ROW0", "SW1_D"),
    ("SW2", COL_X[2], ROW_Y[0], "ROW0", "SW2_D"),
    ("SW3", COL_X[0], ROW_Y[1], "ROW1", "SW3_D"),
    ("SW4", COL_X[1], ROW_Y[1], "ROW1", "SW4_D"),
    ("SW5", COL_X[2], ROW_Y[1], "ROW1", "SW5_D"),
    ("SW6", COL_X[3], ROW_Y[1], "ROW1", "SW6_D"),
    ("SW7", COL_X[0], ROW_Y[2], "ROW2", "SW7_D"),
    ("SW8", COL_X[1], ROW_Y[2], "ROW2", "SW8_D"),
    ("SW9", COL_X[2], ROW_Y[2], "ROW2", "SW9_D"),
    ("SW10", COL_X[3], ROW_Y[2], "ROW2", "SW10_D"),
    ("SW11", 45.0, ROW_Y[3], "ROW3", "SW11_D"),
    ("SW12", COL_X[3], ROW_Y[3], "ROW3", "SW12_D"),
]
for _, _, _, _, node_name in SWITCH_DATA:
    net(node_name)

switches = []
diodes = []
key_leds = []
col_for_switch = [1, 2, 0, 1, 2, 3, 0, 1, 2, 3, 1, 3]
for index, (ref, x, y, row_name, node_name) in enumerate(SWITCH_DATA, 1):
    switches.append(add_switch(ref, x, y, row_name, node_name))
    diode_x, diode_y = x + 7.1, y + 5.75
    if index == 1:
        diode_x, diode_y = 42.575, 16.425
    elif index == 2:
        diode_x, diode_y = 59.0, 18.0
    elif index == 6:
        diode_x = x + 5.50
    diode = load_fp(
        "Diode_SMD", "D_SOD-123", f"D{index}", "1N4148W", diode_x, diode_y,
        side="B", rotation=90,
    )
    set_map(diode, {1: node_name, 2: f"COL{col_for_switch[index - 1]}"})
    diodes.append(diode)
    led = load_fp(
        "LED_SMD", "LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount",
        f"LED{index}", "SK6812MINI-E", x, y - 5.0, side="B",
    )
    net(f"LED_D{index - 1}")
    net(f"LED_D{index}")
    set_map(led, {1: "+5V", 2: f"LED_D{index}", 3: "GND", 4: f"LED_D{index - 1}"})
    tune_reverse_led_window(led, x, y - 5.0)
    key_leds.append(led)

# Stabilizer holes for the 2U key, centered around SW11.
for index, x in enumerate((45.0 - 11.9, 45.0 + 11.9), 1):
    add_mount(f"HSTAB{index}", x, ROW_Y[3], diameter=3.3)


# Planar Alps RKJXY mechanics.  The discontinued original uses a four-wire
# flexible tail (VDD/GND/Xout/Yout); an FFC connector is placed on the back.
joy = custom_fp("JOY1", "Alps_RKJXY100000A_MECHANICAL", COL_X[3], ROW_Y[0], dnp=True)
for idx, (dx, dy) in enumerate(((-8.25, -6.8), (8.25, -6.8), (-8.0, 6.8), (8.0, 6.8)), 1):
    add_pad(joy, "", dx, dy, 1.9, 1.9, drill=1.9, side="NPTH")
joy_ffc = load_fp(
    "Connector_FFC-FPC", "Molex_200528-0040_1x04-1MP_P1.00mm_Horizontal",
    "J2", "RKJXY_4WIRE_FFC", 73.575, 25.0, side="B", rotation=180, dnp=True,
)
set_map(joy_ffc, {1: "+3V3", 2: "GND", 3: "JOY_X", 4: "JOY_Y"})

encoder = load_fp(
    "Rotary_Encoder", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm_MountingHoles",
    "ENC1", "EC11E_VERTICAL_CLICK", COL_X[0], ROW_Y[0], dnp=True,
)
set_map(encoder, {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "ENC_SW", "S2": "GND"})
# The stock EC11E footprint's 2.0 mm switch pads miss the adjacent KS-33 pad
# by only 0.139 mm at the published 19.05 mm pitch. A 1.60 mm annulus around
# the existing 1.0 mm drill preserves the encoder pin while restoring 0.30 mm+
# copper clearance without shifting the visible dial center.
for pad in encoder.Pads():
    if pad.GetNumber() in ("S1", "S2"):
        pad.SetSize(vec(1.60, 1.60))


# USB-C and crystal-less STM32 controller island.  The LQFP package keeps this
# a single directly assembled PCB while avoiding HDI/via-in-pad fabrication.
usb = load_fp(
    "Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "J1", "USB_C_HRO_TYPE-C-31-M-12", 45.0, 5.10, side="F",
)
for p in ("A1", "A12", "B1", "B12", "SH"):
    assign(usb, p, "GND")
for p in ("A4", "A9", "B4", "B9"):
    assign(usb, p, "+5V")
for p in ("A6", "B6"):
    assign(usb, p, "USB_DP_CONN")
for p in ("A7", "B7"):
    assign(usb, p, "USB_DM_CONN")

mcu = load_fp(
    "Package_QFP", "LQFP-48_7x7mm_P0.5mm",
    "U1", "STM32F072CBT6", 45.0, 27.0, side="B", rotation=0,
)
# Official STM32F072CBT6 LQFP48 pinout. USB uses PA11/PA12 and the internal
# HSI48+CRS clock, so no crystal or external flash is required.
set_map(mcu, {
    1: "+3V3", 7: "NRST", 8: "GND", 9: "+3V3",
    10: "JOY_X", 11: "JOY_Y",
    12: "ROW0", 13: "ROW1", 14: "ROW2", 15: "ROW3",
    16: "COL0", 17: "COL1", 18: "COL2", 19: "COL3",
    20: "ENC_A", 21: "ENC_B", 22: "ENC_SW",
    23: "GND", 24: "+3V3", 25: "TOUCH", 26: "RGB_3V3",
    32: "USB_DM_PROT", 33: "USB_DP_PROT", 34: "SWD",
    35: "GND", 36: "+3V3", 37: "SWCLK", 44: "BOOT0",
    47: "GND", 48: "+3V3",
})

esd = load_fp("Package_TO_SOT_SMD", "SOT-23-6", "U4", "USBLC6-2SC6", 45, 11.0, side="B")
set_map(esd, {1: "USB_DP_CONN", 2: "GND", 3: "USB_DM_CONN", 4: "USB_DM_PROT", 5: "+5V", 6: "USB_DP_PROT"})

ldo = load_fp("Package_TO_SOT_SMD", "SOT-23-5", "U3", "ME6211C33M5G", 64.0, 16.0, side="B")
# ME6211Cxx SOT-23-5: 1 VIN, 2 VSS, 3 CE, 4 NC, 5 VOUT.
set_map(ldo, {1: "+5V", 2: "GND", 3: "+5V", 5: "+3V3"})

level = load_fp("Package_TO_SOT_SMD", "SOT-23-5", "U5", "SN74AHCT1G125DBVR", 63.0, 36.0, side="B")
set_map(level, {1: "GND", 2: "RGB_3V3", 3: "GND", 4: "RGB_5V", 5: "+5V"})
assign(key_leds[0], 4, "RGB_5V")

touch_ic = load_fp("Package_TO_SOT_SMD", "SOT-23-6", "U6", "TTP223-BA6-TD", 27.0, 66.0, side="B")
# TonTouch TTP223-BA6: 1 Q, 2 VSS, 3 sensor, 4 AHLB, 5 VDD,
# 6 TOG. Grounding AHLB/TOG selects direct active-high output.
set_map(touch_ic, {
    1: "TOUCH", 2: "GND", 3: "TOUCH_ELECTRODE",
    4: "GND", 5: "+3V3", 6: "GND",
})
electrode = custom_fp("E1", "CAP_TOUCH_14MM", 16.425, 73.575, dnp=True)
add_pad(electrode, 1, 0, 0, 14.0, 14.0, net_name="TOUCH_ELECTRODE", shape=pcbnew.PAD_SHAPE_CIRCLE, side="F", copper_only=True)


# USB-C CC resistors, reset/boot bias and local power bypass.
passives = []
def resistor(ref, value, x, y, a, b, rotation=0):
    fp = load_fp("Resistor_SMD", "R_0603_1608Metric", ref, value, x, y, side="B", rotation=rotation)
    set_map(fp, {1: a, 2: b})
    passives.append(fp)
    return fp


def capacitor(ref, value, x, y, a, b="GND", rotation=0, footprint="C_0603_1608Metric"):
    fp = load_fp("Capacitor_SMD", footprint, ref, value, x, y, side="B", rotation=rotation)
    set_map(fp, {1: a, 2: b})
    passives.append(fp)
    return fp


resistor("R1", "5.1k_CC1", 39.0, 7.5, "USB_CC1", "GND")
resistor("R2", "5.1k_CC2", 43.0, 7.5, "USB_CC2", "GND")
net("USB_CC1"); net("USB_CC2")
assign(usb, "A5", "USB_CC1"); assign(usb, "B5", "USB_CC2")
resistor("R3", "10k_NRST_PULLUP", 51.0, 19.0, "+3V3", "NRST", rotation=90)
resistor("R4", "10k_BOOT0_PULLDOWN", 45.75, 19.5, "BOOT0", "GND", rotation=90)

capacitor("C1", "10uF", 68.0, 14.0, "+3V3")
capacitor("C2", "10uF", 68.0, 19.0, "+5V")
for idx, (x, y, rotation) in enumerate(
    ((39.0, 23.8, 90), (39.0, 25.8, 90), (39.0, 27.8, 90),
     (51.0, 23.8, 90), (51.0, 25.8, 90)), 3
):
    capacitor(
        f"C{idx}", "100nF_3V3", x, y, "+3V3", rotation=rotation,
        footprint="C_0402_1005Metric",
    )
capacitor(
    "C8", "1uF_VDDA", 51.0, 27.8, "+3V3", rotation=90,
    footprint="C_0402_1005Metric",
)
capacitor("C9", "4.7uF_3V3_BULK", 49.0, 19.5, "+3V3", rotation=90)
capacitor("C10", "100nF_TOUCH", 31.0, 66.0, "+3V3")
rgb_bulk = load_fp(
    "Capacitor_SMD", "C_1210_3225Metric", "C19", "CL32A107MQVNNNE_100uF_6V3",
    64.0, 30.0, side="B",
)
set_map(rgb_bulk, {1: "+5V", 2: "GND"})

reset = load_fp("Button_Switch_SMD", "SW_SPST_TL3342", "SW13", "RESET", 27.0, 30.0, side="B", dnp=True)
set_map(reset, {1: "NRST", 2: "GND"})
boot = load_fp("Button_Switch_SMD", "SW_SPST_TL3342", "SW14", "BOOT", 27.0, 39.0, side="B", dnp=True)
set_map(boot, {1: "BOOT0", 2: "+3V3"})


# Nine underglow LEDs and three layer/status LEDs complete the 24-LED chain.
extra_led_xy = [
    (14, 8), (30, 8), (60, 8), (76, 8),
    (8, 45), (82, 45), (30, 84), (45, 82), (60, 84),
    (6.0, 64.0), (6.0, 72.0), (14.0, 84.0),
]
all_leds = list(key_leds)
for led_index, (x, y) in enumerate(extra_led_xy, len(key_leds) + 1):
    net(f"LED_D{led_index}")
    led = load_fp(
        "LED_SMD", "LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount",
        f"LED{led_index}", "SK6812MINI-E", x, y, side="B",
    )
    set_map(led, {1: "+5V", 2: f"LED_D{led_index}", 3: "GND", 4: f"LED_D{led_index - 1}"})
    tune_reverse_led_window(led, x, y)
    all_leds.append(led)


# SWD test pads and power/ground test points.
for ref, label, x, net_name in (
    ("TP1", "SWCLK", 64, "SWCLK"), ("TP2", "SWD", 68, "SWD"),
    ("TP3", "3V3", 72, "+3V3"), ("TP4", "GND", 76, "GND"),
):
    tp = custom_fp(ref, label, x, 87.0, dnp=True)
    add_pad(tp, 1, 0, 0, 1.8, 1.8, net_name=net_name, side="B", copper_only=True)


# Parody identity and explicit prototype caveats on silkscreen.
add_text("CODEX KEYBORED", 45, 87.4, size=1.1)
add_text("WORK LOAFER EDITION // REV A2", 45, 85.7, size=0.8)
add_text("JOY: ALPS RKJXY 4-WIRE FFC", 73.6, 27.5, size=0.8)
add_text("ENC", 16.4, 28.4, size=0.8)
add_text(
    "LQFP48 / CRYSTAL-LESS USB / PRESS KEYS, SHIP BUGS",
    45, 89.0, layer=pcbnew.B_SilkS, size=0.8, mirrored=True,
)

# Assembly courtyards and stock footprint outlines overlap intentionally in
# this keyboard layout (reverse LEDs sit under switches). Keep those drawings
# in Fab documentation and reserve the manufactured silkscreen for the custom
# labels above; this prevents clipped or misleading component ink.
layer_cleanup = {
    pcbnew.F_CrtYd: pcbnew.F_Fab,
    pcbnew.B_CrtYd: pcbnew.B_Fab,
    pcbnew.F_SilkS: pcbnew.F_Fab,
    pcbnew.B_SilkS: pcbnew.B_Fab,
}
for footprint in board.GetFootprints():
    for graphic in footprint.GraphicalItems():
        if graphic.GetLayer() in layer_cleanup:
            graphic.SetLayer(layer_cleanup[graphic.GetLayer()])


# Electrical placement/routing is completed by a separate deterministic pass.
board.SynchronizeNetsAndNetClasses(False)
OUT.mkdir(parents=True, exist_ok=True)
pcbnew.SaveBoard(str(BOARD_PATH), board)

summary = {
    "board": str(BOARD_PATH),
    "size_mm": [90.0, 90.0],
    "layers": 6,
    "keyboard_switches": 12,
    "mechanical_inputs_including_encoder_push": 13,
    "rgb_leds": len(all_leds),
    "footprints": len(list(board.GetFootprints())),
    "nets": board.GetNetCount(),
    "status": "placement generated; routing and DRC pending",
}
print(json.dumps(summary, indent=2))
