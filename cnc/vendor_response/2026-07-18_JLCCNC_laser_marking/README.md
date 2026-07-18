# JLCCNC laser-marking response — CM2-002 Rev B

This package answers JLCCNC's request to replace the too-fine machined lettering on the black-anodized aluminum bottom weight with laser marking.

## Send these three files

1. `CM2-002_LASER_ARTWORK_ONLY_RevB.dxf` — production laser artwork only. This is the safest file for import into the laser CAM system.
2. `CM2-002_LASER_PLACEMENT_REFERENCE_RevB.dxf` — the same artwork plus Ø94 part outline, groove, holes, and rear datum on clearly named `DO_NOT_MARK` layers.
3. `CM2-002_LASER_PLACEMENT_APPROVAL_RevB.pdf` — human-readable 1:1 approval sheet specifying side, orientation, process order, and appearance.

Copy the body of `EMAIL_REPLY.txt` into the reply email and attach the three files individually. Do not rely on the ZIP alone if their mail gateway blocks archives.

## Controlled manufacturing intent

- Part: `CM2-002_bottom_weight.step`
- CNC item: `CNC2607185001881-3086316A`
- Surface: underside / desk-facing angled plane
- Orientation: `+Y` is rear / thick edge / USB side
- Process: fine bead blast → black matte anodize → laser mark
- Appearance: natural aluminum / silver artwork on black
- Marking: solid/hatch-filled compound glyphs, with letter counters preserved
- Production layer: `LASER_MARK` only
- Coordinates: millimeters, scale 1:1, origin at part center
- Main line: `CODEX KEYBORED`, Arial Bold, 4.2 mm nominal CAD font size; outlined envelope 39.498 × 3.109 mm; center `(0, +4.000)`
- Strapline: `ABSOLUTELY VIBE-CODED`, Arial Regular, 2.1 mm nominal CAD font size; outlined envelope 27.122 × 1.556 mm; center `(0, −4.000)`

The DXFs contain no live font objects. The artwork consists of closed `LWPOLYLINE` contours so the factory does not need the source fonts.

## Reference-only files

- `CM2-002_LASER_PLACEMENT_PREVIEW_RevB.svg` — screen preview.
- `CM2-002_LASER_GEOMETRY_RevB.json` — machine-readable source geometry and measured bounds.

These are included for traceability but do not need to be emailed unless requested.
