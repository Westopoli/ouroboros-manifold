#!/usr/bin/env bash
# Input probe, run by hand on the Mac: opens a bare window for 25 s and prints which input events the trackpad or mouse send (the repo is not touched). Diagnoses W8 and the zoom report of 2026-11-07.
# See also: scripts/play_mac.sh
set -e
D=/tmp/om_input_probe; rm -rf "$D"; mkdir -p "$D"
cat > "$D/project.godot" <<'P'
config_version=5
[application]
config/name="probe"
run/main_scene="res://main.tscn"
[display]
window/size/viewport_width=700
window/size/viewport_height=400
P
cat > "$D/main.tscn" <<'P'
[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://main.gd" id="1"]
[node name="Main" type="Node"]
script = ExtResource("1")
P
cat > "$D/main.gd" <<'P'
extends Node
var counts := {}
var t := 0.0
func _input(e: InputEvent) -> void:
	if e is InputEventMouseMotion:
		return
	var k := e.get_class()
	counts[k] = int(counts.get(k, 0)) + 1
	var extra := ""
	if e is InputEventMouseButton:
		extra = " button=%d factor=%.3f pressed=%s" % [e.button_index, e.factor, e.pressed]
	elif e is InputEventPanGesture:
		extra = " delta=%s" % [e.delta]
	elif e is InputEventMagnifyGesture:
		extra = " factor=%.3f" % e.factor
	if counts[k] <= 8:
		print("EVENT ", k, extra)
func _process(d: float) -> void:
	t += d
	if t > 25.0:
		print("PROBE SUMMARY ", counts)
		get_tree().quit()
P
GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"; [ -x "$GODOT" ] || { echo "PROBE: no Godot at $GODOT (set GODOT)"; exit 1; }
echo "PROBE: window is open 25 s. Over it: 1) two-finger scroll up/down, 2) two-finger scroll left/right, 3) pinch in/out, 4) click, 5) tilt wheel if you have a mouse."
"$GODOT" --path "$D" 2>&1 | grep -E "^(EVENT|PROBE)"
