"""Print centers of layout-control bodies for safe one-shot migrations."""

import json

import adsk.core
import adsk.fusion


NAMES = [
    "Clickable_Encoder_Body_PLACEHOLDER",
    "Encoder_Shaft_D6",
    "Codex_Dial_D19",
    "Codex_Dial_Raised_Fin",
    "Planar_Joystick_RKJXY_CANDIDATE",
    "Rubber_Joystick_Cap_D14p5",
    "SW12_Command_R4_C3",
    "SW12_Command_R4_C4",
    "SW13_Command_R4_C4",
    "PBT_1U_5_Command_R4_C3",
    "PBT_1U_5_Command_R4_C4",
    "PBT_1U_6_Command_R4_C4",
]


def run(_context):
    design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    root = design.rootComponent
    bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    result = {}
    for name in NAMES:
        matches = [body for body in bodies if body.name == name]
        result[name] = []
        for body in matches:
            box = body.boundingBox
            result[name].append([
                round((box.minPoint.x + box.maxPoint.x) * 5, 3),
                round((box.minPoint.y + box.maxPoint.y) * 5, 3),
                round((box.minPoint.z + box.maxPoint.z) * 5, 3),
            ])
    cap_feature = root.features.baseFeatures.itemByName(
        "MFG_CM2_004_Joystick_Cap_POM_or_TPU"
    )
    if cap_feature and cap_feature.bodies.count:
        box = cap_feature.bodies.item(0).boundingBox
        result["MFG_CAP_CENTER"] = [
            round((box.minPoint.x + box.maxPoint.x) * 5, 3),
            round((box.minPoint.y + box.maxPoint.y) * 5, 3),
            round((box.minPoint.z + box.maxPoint.z) * 5, 3),
        ]
    result["migration_parameter"] = bool(
        design.userParameters.itemByName("cm_layout_v2_applied")
    )
    print(json.dumps(result))
