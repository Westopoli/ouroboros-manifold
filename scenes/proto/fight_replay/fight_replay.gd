extends "res://scenes/proto/layout_shot/layout_shot.gd"

## H-040 part 3, fight replay: plays one `om-fight-1` file (docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md; JSON path in OM_FIGHT, unknown keys
## ignored) frame by frame. It extends the layout shot (H-025) so terrain, glyphs, side colours, facing arrows, legend, camera fit and the DRAFT drawing numbers are
## that scene's own; this file adds the frame cursor, the HUD, the dead marker and the target line. Frame 0 is drawn as the layout shot draws a layout; the camera
## then stays put for every frame, framed on the box of every position any unit takes in any frame plus CAMERA_MARGIN, so no unit walks out of the picture.
## Space or Right steps forward, Left back (at either end the cursor stays put); OM_AUTOPLAY=1 steps at REPLAY_FPS; OM_SHOT_OUT=<dir> saves frame-<i>.png for each
## frame and quits. Every number below that the story does not give is a named DRAFT; Westley rules. See also scenes/proto/layout_shot/layout_shot.gd.

const REPLAY_SCENE_PATH := "res://scenes/proto/fight_replay/fight_replay.tscn"
const REPLAY_FPS := 1.0  # DRAFT-replay-fps (story): frames per second under OM_AUTOPLAY
const REPLAY_LANDSCAPE := "small_flat"  # the stage 1 floor (DEC-lab-stage1-floor-2026-10-31); the fight file names no landscape
const BETWEEN_FRAMES := 2  # story: render frames between saved shots
const DEAD_COLOUR := Color(0.5, 0.5, 0.5)  # DRAFT-replay-dead-grey: a fallen unit's flat marker
const TARGET_ALPHA := 0.8  # DRAFT-replay-target-alpha: the target line is its side's colour, thin (a one pixel line)
const HUD_FONT := 22  # DRAFT-replay-hud-font
const HUD_TOP := 12.0  # DRAFT-replay-hud-top: pixels from the window top
const HUD_LINE := 32.0  # DRAFT-replay-hud-line: pixels one HUD line takes

var _fight: Dictionary = {}
var _fight_frames: Array = []
var _ordinal: Dictionary = {}  # fight unit id -> the layout shot's unit id (side A rows first, then side B, in frame 0 order)
var _cursor := 0
var _autoplay := false
var _clock := 0.0
var _units3d: Node3D
var _ground: Node
var _glyph_k := 1.0
var _overlay: Node3D
var _hud: Label
var _hud_end: Label


func _ready() -> void:
	_shot_path = OS.get_environment("OM_SHOT_OUT")
	_autoplay = OS.get_environment("OM_AUTOPLAY") == "1"
	var path := OS.get_environment("OM_FIGHT")
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path)) if path != "" else null
	if not parsed is Dictionary or not parsed.get("frames") is Array or parsed["frames"].is_empty():
		push_error("fight_replay: OM_FIGHT %r is not a fight JSON" % path)
		return
	_fight = parsed
	_fight_frames = _fight["frames"]
	var result: Dictionary = _fight.get("result", {})
	var rows := {"A": [], "B": []}
	for u in _fight_frames[0]["units"]:
		rows[u["side"]].append({"role": u["role"], "x": u["x"], "y": u["y"], "facing": u["facing"], "layer": u["layer"], "range": 0.0})
	var id := 0
	for side in ["A", "B"]:
		for u in _fight_frames[0]["units"]:
			if u["side"] == side:
				_ordinal[int(u["id"])] = id
				id += 1
	_layout = {"id": String(_fight["layout_id"]), "situation": "fight_replay", "landscape": REPLAY_LANDSCAPE, "defender": "",
			"predict": String(result.get("predict", "")),
			"side_a": {"headcount": rows["A"].size(), "units": rows["A"]}, "side_b": {"headcount": rows["B"].size(), "units": rows["B"]}}
	var preset := _preset(REPLAY_LANDSCAPE)
	var floors: Array = [0.0]
	_terrain = _tiered_terrain(int(preset["width"]), int(preset["height"]), floors)
	_ground = Ground3DHost.new()
	add_child(_ground)
	_ground.set_terrain(_terrain)
	_units3d = GroundUnits.new()
	_units3d.local_faction = 0
	_ground.add_layer(_units3d)
	_overlay = Node3D.new()
	_ground.add_layer(_overlay)
	_collect_units()
	_units3d.set_units(_unit_rows(0), _terrain, floors, [])
	var panel := _add_legend()
	panel.position.y = HUD_TOP + 2.0 * HUD_LINE
	var every_position := _units
	_units = _every_position()
	_frame_camera(_ground, panel)  # frames the box of every position in every frame
	_units = every_position
	_scale_glyphs(_ground, _units3d)
	_glyph_k = _units3d.unit_node(0).scale.x
	_add_hud()
	_show(0)


## The rows GroundUnits draws for frame `i`, ids renumbered to the layout shot's.
func _unit_rows(i: int) -> Array:
	var out: Array = []
	for u in _fight_frames[i]["units"]:
		out.append({"id": _ordinal[int(u["id"])], "faction": 0 if u["side"] == "A" else 1, "type": maxi(ROLES.find(String(u["role"])), 0), "x": float(u["x"]),
				"y": float(u["y"]), "facing": float(u["facing"]), "layer": int(u["layer"])})
	return out


func _every_position() -> Array:
	var out: Array = []
	for frame in _fight_frames:
		for u in frame["units"]:
			out.append({"x": float(u["x"]), "y": float(u["y"])})
	return out


func _add_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hud = _label("", Color.WHITE, HUD_FONT)
	_hud.name = "Hud"
	_hud.position = Vector2(24.0, HUD_TOP)
	layer.add_child(_hud)
	_hud_end = _label("", Color.WHITE, HUD_FONT)
	_hud_end.name = "HudEnd"
	_hud_end.position = Vector2(24.0, HUD_TOP + HUD_LINE)
	layer.add_child(_hud_end)


## Draw frame `i`: bodies at their positions, fallen units grey and flat with no arrow, a thin line from each unit to its target, the HUD.
func _show(i: int) -> void:
	_cursor = i
	var frame: Dictionary = _fight_frames[i]
	_units3d.set_units(_unit_rows(i), _terrain, [0.0], [])
	for child in _overlay.get_children():
		child.queue_free()
	var by_id := {}
	for u in frame["units"]:
		by_id[int(u["id"])] = u
	for u in frame["units"]:
		var node: Node3D = _units3d.unit_node(_ordinal[int(u["id"])])
		node.scale = Vector3.ONE * _glyph_k
		node.position.y += GLYPH_LIFT_WU
		if not bool(u["alive"]):
			(node as MeshInstance3D).material_override = _unshaded(DEAD_COLOUR)
			node.get_node("Arrow").visible = false
		elif u.get("target") != null and by_id.has(int(u["target"])):
			var t: Dictionary = by_id[int(u["target"])]
			var c: Color = SIDE_COLOURS[u["side"]]
			_overlay.add_child(_line(PackedVector3Array([_at(float(u["x"]), float(u["y"]), GLYPH_LIFT_WU), _at(float(t["x"]), float(t["y"]), GLYPH_LIFT_WU)]),
					Color(c.r, c.g, c.b, TARGET_ALPHA)))
	_hud.text = "tick %d  A %d  B %d  frame %d/%d" % [int(frame["tick"]), int(frame["alive"][0]), int(frame["alive"][1]), i, _fight_frames.size()]
	var res: Dictionary = _fight.get("result", {})
	if i == _fight_frames.size() - 1:
		_hud_end.text = "winner %s  predicted %s  %s" % [res.get("winner", ""), res.get("predict", ""), "agree" if res.get("agree", false) else "disagree"]
	else:
		_hud_end.text = ""
	_hud_end.visible = _hud_end.text != ""


func _step(d: int) -> void:
	var to := clampi(_cursor + d, 0, _fight_frames.size() - 1)
	if to != _cursor:
		_show(to)
	_clock = 0.0


func _input(event: InputEvent) -> void:
	if _fight_frames.is_empty() or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_SPACE or event.keycode == KEY_RIGHT:
		_step(1)
	elif event.keycode == KEY_LEFT:
		_step(-1)


func _process(delta: float) -> void:
	if _fight_frames.is_empty():
		return
	if _shot_path != "":
		if not _saving:
			_frames += 1
			if _frames >= SHOT_FRAMES:
				_saving = true
				_save_all_frames()
	elif _autoplay:
		_clock += delta
		if _clock >= 1.0 / REPLAY_FPS:
			_step(1)


func _save_all_frames() -> void:
	DirAccess.make_dir_recursive_absolute(_shot_path)
	for i in _fight_frames.size():
		if i > 0:
			_show(i)
			for _k in BETWEEN_FRAMES:
				await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var err := get_viewport().get_texture().get_image().save_png("%s/frame-%d.png" % [_shot_path, i])
		if err != OK:
			push_error("fight_replay: save_png frame-%d failed (%d)" % [i, err])
	get_tree().quit()


func qa_state() -> Dictionary:
	if _fight_frames.is_empty():
		return {"scene": REPLAY_SCENE_PATH}
	var frame: Dictionary = _fight_frames[_cursor]
	return {"scene": REPLAY_SCENE_PATH, "fight_id": String(_fight["layout_id"]), "frame": _cursor, "frame_count": _fight_frames.size(),
			"tick": int(frame["tick"]), "alive_a": int(frame["alive"][0]), "alive_b": int(frame["alive"][1]), "result": _fight.get("result", {}),
			"autoplay": _autoplay}
