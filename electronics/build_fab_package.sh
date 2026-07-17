#!/bin/sh
set -eu

project_root="/Users/steve/Documents/CodexKB/codex-micro"
board="$project_root/electronics/kicad/codex_micro_wired_revA.kicad_pcb"
production="$project_root/electronics/production"
gerbers="$production/gerbers"
archive="$production/codex_micro_wired_revA_gerbers.zip"
kicad_cli="/Users/steve/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
kicad_config="$project_root/.kicad-config"

mkdir -p "$gerbers"
find "$gerbers" -type f -delete
rm -f "$archive"

KICAD_CONFIG_HOME="$kicad_config" "$kicad_cli" pcb drc \
  --output "$production/codex_micro_wired_revA_drc.json" \
  --format json --all-track-errors --severity-all --refill-zones --save-board \
  "$board"

unconnected=$(/usr/bin/jq '.unconnected_items | length' "$production/codex_micro_wired_revA_drc.json")
critical=$(/usr/bin/jq '[.violations[] | select(.type == "shorting_items" or .type == "clearance" or .type == "tracks_crossing" or .type == "hole_clearance" or .type == "copper_edge_clearance" or .type == "drill_out_of_range" or .type == "via_dangling" or .type == "hole_to_hole" or .type == "items_not_allowed" or .type == "isolated_copper" or .type == "starved_thermal")] | length' "$production/codex_micro_wired_revA_drc.json")
if [ "$unconnected" -ne 0 ] || [ "$critical" -ne 0 ]; then
  echo "Fabrication gate failed: $unconnected unconnected items, $critical critical DRC violations" >&2
  exit 2
fi

KICAD_CONFIG_HOME="$kicad_config" "$kicad_cli" pcb export gerbers \
  --output "$gerbers" \
  --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask --check-zones "$board"

KICAD_CONFIG_HOME="$kicad_config" "$kicad_cli" pcb export drill \
  --output "$gerbers" --format excellon --excellon-units mm \
  --excellon-separate-th --generate-map --map-format pdf \
  --generate-report --report-path "$production/codex_micro_wired_revA_drill_report.txt" \
  "$board"

(cd "$gerbers" && /usr/bin/zip -q -r "$archive" . -x '*.pdf')

echo "Built $archive"
