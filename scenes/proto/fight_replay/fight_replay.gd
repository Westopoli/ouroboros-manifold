extends "res://scenes/proto/layout_shot/layout_shot.gd"

## H-040 part 3, fight replay: plays one `om-fight-1` file (docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md; JSON path in OM_FIGHT, unknown keys
## ignored) frame by frame. It extends the layout shot (H-025) so terrain, glyphs, side colours, facing arrows, legend, camera fit and the DRAFT drawing numbers are
## that scene's own; this file adds the frame cursor, the HUD, the dead marker and the target line. Frame 0 is drawn as the layout shot draws a layout; the camera
## then stays put for every frame, framed on the box of every position any unit takes in any frame plus FIT_MARGIN, so no unit walks out of the picture. When that
## box would shrink a unit under the glyph minimum (a wide field), the units keep it and the camera instead follows each frame's centroid (H-053 Replay readability).
## Rings: one per role per side, a line style per role (replay_marks.gd), per-unit rings behind key R. Six role glyphs, the legend names each.
## Space or Right steps forward, Left back (at either end the cursor stays put); OM_AUTOPLAY=1 steps at REPLAY_FPS; OM_SHOT_OUT=<dir> saves frame-<i>.png for each
## frame and quits. Every number below that the story does not give is a named DRAFT; Westley rules. See also scenes/proto/layout_shot/layout_shot.gd.

const REPLAY_SCENE_PATH := "res://scenes/proto/fight_replay/fight_replay.tscn"
const REPLAY_FPS := 1.0  # DRAFT-replay-fps (story): frames per second under OM_AUTOPLAY
const REPLAY_LANDSCAPE := "small_flat"  # the stage 1 floor (DEC-lab-stage1-floor-2026-10-31); the fallback for a fight file without a `landscape` key (lab-stage3 criterion 7)
const BETWEEN_FRAMES := 2  # story: render frames between saved shots
const DEAD_COLOUR := Color(0.5, 0.5, 0.5)  # DRAFT-replay-dead-grey: a fallen unit's flat marker
const TARGET_ALPHA := 0.8  # DRAFT-replay-target-alpha: the target line is its side's colour, thin (a one pixel line)
const SHOT_RING_WU := 30.0  # DRAFT-first-shot-ring-wu (H-053): radius of the ring drawn on the unit hurt on the first-shot frame
const SHOT_RING_SEGMENTS := 24  # DRAFT-first-shot-ring-segments
const SHOT_RING_COLOUR := Color(1.0, 0.9, 0.2)  # DRAFT-first-shot-ring-colour
const HUD_FONT := 22  # DRAFT-replay-hud-font
const HUD_TOP := 12.0  # DRAFT-replay-hud-top: pixels from the window top
const HUD_LINE := 32.0  # DRAFT-replay-hud-line: pixels one HUD line takes
const HUD_LINES := 5  # tick line, old end line, seed line, end label, rate label; the legend panel starts below them
const FIT_MARGIN := 0.10  # DRAFT-stage2-look (story): the fit box is the box of every position plus this fraction of its larger extent on each side
const FIT_MIN_WU := 100.0  # DRAFT-stage2-fit-min-wu: the least margin, for a fight whose units never move apart
const RING_ALPHA := 0.9  # DRAFT-stage2-ring-alpha: a role ring's line, in its side's colour
const FACING_MIN_PX := 8.0  # story: the facing tick is as long as the glyph, never under this
const BLOCKED_RING_WU := 45.0  # DRAFT-blocked-ring-wu (H-063): radius of the ring on a unit blocked by the ground, wider than the first-shot ring
const BLOCKED_COLOUR := Color(1.0, 0.45, 0.0)  # DRAFT-blocked-colour (H-063)
const SIGHT_ALPHA := 0.25  # DRAFT-sight-alpha (lab-stage4): a sight disc's line, in its side's colour
const HOLLOW_ALPHA := 0.35  # DRAFT-hollow-alpha (lab-stage4): the body of a unit no living enemy sees
const Marks := preload("res://scenes/proto/fight_replay/replay_marks.gd")

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
var _landscape := REPLAY_LANDSCAPE  # lab-stage3: the preset the fight file names, built in _ready
var _hud_end: Label
var _hud_run: Label  # H-053: the seed and the win rate, on a line of their own so the tick line stays short (it gained the blocked count in lab-stage3)
var _first_shot := -1  # H-053: index of the first frame in which some unit's hp is lower than in the frame before; -1 when none
var _ring_count := 0  # H-053: unit range rings drawn on the current frame (a role's range comes from the fight file's `ranges`; none without it)
var _hud_end_label: Label  # H-053: `end: A wins (wipe)` and the like, last frame only
var _hud_rate_label: Label  # H-053: the layout's rate verdict, every frame when a rate file exists
var _end_label := ""
var _rate_label := ""  # `rate A <m> vs target <p> (gap <n> pts, not scored); guess <A|B|draw>: AGREE|DISAGREE|NOT SCORED (mirror)` from the rate file, "" when there is none
var _role_rings: Array = []  # H-053: [{side, role, range, style, id}] one per role per side, id = the fight unit the ring follows (nearest the enemy at frame 0)
var _unit_rings := false  # key R: a ring on every living unit instead of the per-role rings
var _sight_units := false  # key V: a sight disc on every living unit instead of the per-role discs
var _wide := false  # the camera follows each frame's centroid instead of holding the whole fight
var _free_rect := Rect2()
var _fit: Array = [0.0, 0.0, 0.0, 0.0]  # the world box the camera shows: the whole fight, or the part round the centroid on a wide field
var _unit_px := 0.0
var _meshes: Dictionary = {}  # (role, side) -> glyph mesh
var _tick_mesh: ArrayMesh
var _feature_layer: Node3D  # H-063: the layout's features, drawn once through the layout shot's _add_feature
var _rate_a = null  # H-053: rate_a from <layout id>.rate.json beside the fight file, null when there is none


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
	_first_shot = _find_first_shot()
	var rate_path := path.get_base_dir().path_join("%s.rate.json" % String(_fight["layout_id"]))
	if FileAccess.file_exists(rate_path):
		var rate = JSON.parse_string(FileAccess.get_file_as_string(rate_path))
		if rate is Dictionary and rate.has("rate_a"):
			_rate_a = float(rate["rate_a"])
			var predict_rate := float(rate.get("predict_rate", 0.0))
			var guess := String(_fight.get("result", {}).get("predict", ""))
			var verdict := "NOT SCORED (mirror)" if rate.get("mirror", false) else ("AGREE" if rate.get("agree", false) else "DISAGREE")
			_rate_label = "rate A %.2f vs target %.2f (gap %d pts, not scored); guess %s: %s" % [_rate_a, predict_rate, roundi(absf(_rate_a - predict_rate) * 100.0), guess, verdict]
	var result: Dictionary = _fight.get("result", {})
	var ranges: Dictionary = _fight.get("ranges", {})  # om-fight-2 H-053: {role: range wu}; absent in older files
	_end_label = _end_label_for(result)
	_build_role_rings(ranges)
	var rows := {"A": [], "B": []}
	for u in _fight_frames[0]["units"]:
		rows[u["side"]].append({"role": u["role"], "x": u["x"], "y": u["y"], "facing": u["facing"], "layer": u["layer"], "range": float(ranges.get(u["role"], 0.0))})
	_landscape = String(_fight.get("landscape", REPLAY_LANDSCAPE))
	var id := 0
	for side in ["A", "B"]:
		for u in _fight_frames[0]["units"]:
			if u["side"] == side:
				_ordinal[int(u["id"])] = id
				id += 1
	_layout = {"id": String(_fight["layout_id"]), "situation": "fight_replay", "landscape": _landscape, "defender": "",
			"predict": String(result.get("predict", "")),
			"side_a": {"headcount": rows["A"].size(), "units": rows["A"]}, "side_b": {"headcount": rows["B"].size(), "units": rows["B"]}}
	_features = _load_features()
	var preset := _preset(_landscape)
	var floors: Array = []  # as the layout shot builds a tiered layout: one floor per layer of the preset
	for k in int(preset["layers"]):
		floors.append(k * BAND_HEIGHT_WU)
	_terrain = _tiered_terrain(int(preset["width"]), int(preset["height"]), floors)
	_ground = Ground3DHost.new()
	add_child(_ground)
	_ground.set_terrain(_terrain)
	_units3d = GroundUnits.new()
	_units3d.local_faction = 0
	_ground.add_layer(_units3d)
	_feature_layer = Node3D.new()
	_ground.add_layer(_feature_layer)
	_add_tier_tint(_feature_layer)
	for f in _features:
		_add_feature(_feature_layer, f)
	_overlay = Node3D.new()
	_ground.add_layer(_overlay)
	_collect_units()
	_units3d.set_units(_unit_rows(0), _terrain, floors, [])
	var panel := _add_legend()
	panel.position.y = HUD_TOP + float(HUD_LINES) * HUD_LINE
	_setup_camera(panel)
	_add_hud()
	_show(0)


## The features the fight file names: its `built_features` when it has them (stage 4 fix F2), else the layout's JSON twin beside its TOML (H-063). [] when the twin is not there.
func _load_features() -> Array:
	var built = _fight.get("built_features")  # stage 4 fix F2: the rectangles the engine blocks (snapped to its 100 wu cells), so drawn equals blocked
	if built is Array:
		return built
	var path := String(_fight.get("layout_path", ""))
	if path == "":
		return []
	path = path.get_basename() + ".json"
	if not path.is_absolute_path():
		path = "res://" + path
	if not FileAccess.file_exists(path):
		return []
	var twin = JSON.parse_string(FileAccess.get_file_as_string(path))
	var raw = twin.get("features", []) if twin is Dictionary else []
	return raw if raw is Array else []


## The unit ids the fight file lists as blocked on `frame` (the optional `blocked` key); [] when absent.
func _blocked_ids(frame: Dictionary) -> Array:
	var out: Array = []
	for id in frame.get("blocked", []):
		out.append(int(id))
	return out


## The rows GroundUnits draws for frame `i`, ids renumbered to the layout shot's.
func _unit_rows(i: int) -> Array:
	var out: Array = []
	for u in _fight_frames[i]["units"]:
		out.append({"id": _ordinal[int(u["id"])], "faction": 0 if u["side"] == "A" else 1, "type": maxi(ROLES.find(String(u["role"])), 0), "x": float(u["x"]),
				"y": float(u["y"]), "facing": float(u["facing"]), "layer": int(u["layer"])})
	return out


func _find_first_shot() -> int:
	for i in range(1, _fight_frames.size()):
		var before := {}
		for u in _fight_frames[i - 1]["units"]:
			before[int(u["id"])] = float(u["hp"])
		for u in _fight_frames[i]["units"]:
			if float(u["hp"]) < before.get(int(u["id"]), float(u["hp"])):
				return i
	return -1


## The ids of the units whose hp dropped into frame `i` (the damaged units the first-shot ring marks).
func _hurt_ids(i: int) -> Array:
	var out: Array = []
	var before := {}
	for u in _fight_frames[i - 1]["units"]:
		before[int(u["id"])] = float(u["hp"])
	for u in _fight_frames[i]["units"]:
		if float(u["hp"]) < before.get(int(u["id"]), float(u["hp"])):
			out.append(int(u["id"]))
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
	_hud_run = _label("", Color.WHITE, HUD_FONT)
	_hud_run.name = "HudRun"
	_hud_run.position = Vector2(24.0, HUD_TOP + 2.0 * HUD_LINE)
	layer.add_child(_hud_run)
	_hud_end_label = _label("", Color.WHITE, HUD_FONT)
	_hud_end_label.name = "HudEndLabel"
	_hud_end_label.position = Vector2(24.0, HUD_TOP + 3.0 * HUD_LINE)
	layer.add_child(_hud_end_label)
	_hud_rate_label = _label("", Color.WHITE, HUD_FONT)
	_hud_rate_label.name = "HudRateLabel"
	_hud_rate_label.position = Vector2(24.0, HUD_TOP + 4.0 * HUD_LINE)
	layer.add_child(_hud_rate_label)


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
	var hollow := _hollow_ids(frame)
	for u in frame["units"]:
		var node: Node3D = _units3d.unit_node(_ordinal[int(u["id"])])
		node.scale = Vector3.ONE * _glyph_k
		node.position.y += GLYPH_LIFT_WU
		_dress(node as MeshInstance3D, String(u["role"]), String(u["side"]))
		(node as MeshInstance3D).material_override = null
		if bool(u["alive"]) and hollow.has(int(u["id"])):  # lab-stage4: no living enemy lists this unit in `seen`; the body fades, the arrow stays
			var mat: StandardMaterial3D = (node as MeshInstance3D).mesh.surface_get_material(0).duplicate()
			mat.albedo_color.a = HOLLOW_ALPHA
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			(node as MeshInstance3D).material_override = mat
		if not bool(u["alive"]):
			(node as MeshInstance3D).material_override = _unshaded(DEAD_COLOUR)
			node.get_node("Arrow").visible = false
		elif u.get("target") != null and by_id.has(int(u["target"])):
			var t: Dictionary = by_id[int(u["target"])]
			var c: Color = SIDE_COLOURS[u["side"]]
			_overlay.add_child(_line(PackedVector3Array([_at(float(u["x"]), float(u["y"]), GLYPH_LIFT_WU), _at(float(t["x"]), float(t["y"]), GLYPH_LIFT_WU)]),
					Color(c.r, c.g, c.b, TARGET_ALPHA)))
	_ring_count = 0
	var ranges: Dictionary = _fight.get("ranges", {})
	if _unit_rings:
		for u in frame["units"]:  # key R: a ring follows each living unit whose role has a range in the fight file
			var rng := float(ranges.get(u["role"], 0.0))
			if rng > 0.0 and bool(u["alive"]):
				var c: Color = SIDE_COLOURS[u["side"]]
				_overlay.add_child(_ring(Vector2(float(u["x"]), float(u["y"])), rng, Color(c.r, c.g, c.b, 0.55)))
				_ring_count += 1
	else:
		for r in _role_rings:  # default: one ring per role per side, on the unit it was centred on at frame 0, while that unit lives
			var anchor: Dictionary = by_id[int(r["id"])]
			if bool(anchor["alive"]):
				var c: Color = SIDE_COLOURS[r["side"]]
				for run in Marks.ring_runs(Vector2(float(anchor["x"]), float(anchor["y"])), float(r["range"]), String(r["style"])):
					var pts := PackedVector3Array()
					for p in run:
						pts.append(_at(p.x, p.y, LIFT_WU))
					_overlay.add_child(_line(pts, Color(c.r, c.g, c.b, RING_ALPHA)))
				_ring_count += 1
	for d in _sight_state(frame, true):  # lab-stage4: sight discs, drawn as the role rings are
		var c: Color = SIDE_COLOURS[d["side"]]
		for run in Marks.ring_runs(Vector2(d["centre"][0], d["centre"][1]), float(d["radius"]), Marks.STYLES[maxi(ROLES.find(String(d["role"])), 0)]):
			var pts := PackedVector3Array()
			for p in run:
				pts.append(_at(p.x, p.y, LIFT_WU))
			_overlay.add_child(_line(pts, Color(c.r, c.g, c.b, SIGHT_ALPHA)))
	if _wide:
		_follow(frame)
	if i == _first_shot:
		for id in _hurt_ids(i):
			var h: Dictionary = by_id[id]
			var ring := PackedVector3Array()
			for k in SHOT_RING_SEGMENTS + 1:
				var a := TAU * float(k) / float(SHOT_RING_SEGMENTS)
				ring.append(_at(float(h["x"]) + SHOT_RING_WU * cos(a), float(h["y"]) + SHOT_RING_WU * sin(a), GLYPH_LIFT_WU))
			_overlay.add_child(_line(ring, SHOT_RING_COLOUR))
	for id in _blocked_ids(frame):  # H-063: a unit the ground has held still for more than 2 s wears an orange ring
		if by_id.has(id):
			var b: Dictionary = by_id[id]
			var ring := PackedVector3Array()
			for k in SHOT_RING_SEGMENTS + 1:
				var a := TAU * float(k) / float(SHOT_RING_SEGMENTS)
				ring.append(_at(float(b["x"]) + BLOCKED_RING_WU * cos(a), float(b["y"]) + BLOCKED_RING_WU * sin(a), GLYPH_LIFT_WU))
			_overlay.add_child(_line(ring, BLOCKED_COLOUR))
	var sees := _hud_sight(frame)
	_hud.text = "tick %d  A %d  B %d  blocked %d  %sframe %d/%d" % [int(frame["tick"]), int(frame["alive"][0]), int(frame["alive"][1]), _blocked_ids(frame).size(),
			sees + "  " if sees != "" else "", i, _fight_frames.size()]
	_hud_run.text = "seed %d" % int(_fight.get("seed", 0))
	if _rate_a != null:
		_hud_run.text += "  rate %.2f" % _rate_a
	var res: Dictionary = _fight.get("result", {})
	var last := i == _fight_frames.size() - 1
	_hud_end.text = ""
	if last:
		if _rate_a == null:  # with a rate file the rate label is the verdict; without one the per-fight text stays
			_hud_end.text = "winner %s  predicted %s  %s" % [res.get("winner", ""), res.get("predict", ""), "agree" if res.get("agree", false) else "disagree"]
		if res.get("stall", false):
			_hud_end.text += "  STALL"
		if res.get("first_seen") is Dictionary:  # lab-stage4: the first sampled tick each side saw an enemy; null is never
			var fs: Dictionary = res["first_seen"]
			_hud_end.text += ("  " if _hud_end.text != "" else "") + "first seen A %s  B %s" % [_tick_or_never(fs.get("A")), _tick_or_never(fs.get("B"))]
	_hud_end.visible = _hud_end.text != ""
	_hud_end_label.text = _end_label if last else ""
	_hud_end_label.visible = _hud_end_label.text != ""
	_hud_rate_label.text = _rate_label
	_hud_rate_label.visible = _rate_label != ""


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
	elif event.keycode == KEY_R:
		_unit_rings = not _unit_rings
		_show(_cursor)
	elif event.keycode == KEY_V:
		_sight_units = not _sight_units
		_show(_cursor)


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
			"autoplay": _autoplay, "targets": _targets(frame), "first_shot_frame": _first_shot, "seed": int(_fight.get("seed", 0)), "rate_a": _rate_a, "ring_count": _ring_count,
			"camera": {"fit": _fit, "unit_px": _unit_px}, "facing_px": maxf(FACING_MIN_PX, _unit_px), "rings": _ring_state(frame), "glyphs": _glyph_state(),
			"end_label": _end_label if _cursor == _fight_frames.size() - 1 else "", "rate_label": _rate_label,
			"features": _features_state(), "blocked_units": _blocked_ids(frame), "landscape": _landscape, "hud_tick": _hud.text,
			"sight_rings": _sight_state(frame, false), "sight_mode": "unit" if _sight_units else "role", "hollow_units": _hollow_ids(frame), "hud_sight": _hud_sight(frame),
			"seen_counts": _seen_counts(frame)}


## The layout shot's `features` entry: {kind, x, y} per feature drawn.
func _features_state() -> Array:
	var out: Array = []
	for f in _features:
		out.append({"kind": f["kind"], "x": f["x"], "y": f["y"]})
	return out


## [unit id, target id] for each living unit of `frame` that has a target.
func _targets(frame: Dictionary) -> Array:
	var out: Array = []
	for u in frame["units"]:
		if bool(u["alive"]) and u.get("target") != null:
			out.append([int(u["id"]), int(u["target"])])
	return out


func _ring_state(frame: Dictionary) -> Array:
	var by_id := {}
	for u in frame["units"]:
		by_id[int(u["id"])] = u
	var out: Array = []
	for r in _role_rings:
		var anchor: Dictionary = by_id[int(r["id"])]
		out.append({"side": r["side"], "role": r["role"], "range": r["range"], "style": r["style"], "centre": [float(anchor["x"]), float(anchor["y"])]})
	return out


## lab-stage4: the sight discs, [{side, role, radius, centre}]. Role mode: one per role per side on the role ring's anchor (a role needs a ring, so a range, and a sight); with
## `drawn` only while the anchor lives. Unit mode (key V): one per living unit whose role has a sight. [] when the fight file has no `sights`.
func _sight_state(frame: Dictionary, drawn: bool) -> Array:
	var sights = _fight.get("sights")
	var out: Array = []
	if not sights is Dictionary:
		return out
	var by_id := {}
	for u in frame["units"]:
		by_id[int(u["id"])] = u
	if _sight_units:
		for u in frame["units"]:
			if bool(u["alive"]) and sights.has(u["role"]):
				out.append({"side": u["side"], "role": u["role"], "radius": float(sights[u["role"]]), "centre": [float(u["x"]), float(u["y"])]})
		return out
	for r in _role_rings:
		var anchor: Dictionary = by_id[int(r["id"])]
		if sights.has(r["role"]) and (bool(anchor["alive"]) or not drawn):
			out.append({"side": r["side"], "role": r["role"], "radius": float(sights[r["role"]]), "centre": [float(anchor["x"]), float(anchor["y"])]})
	return out


## lab-stage4: [A, B], the sizes of the unions of `seen` over each side's living units.
func _seen_counts(frame: Dictionary) -> Array:
	var seen := {"A": {}, "B": {}}
	for u in frame["units"]:
		if bool(u["alive"]):
			for id in u.get("seen", []):
				seen[u["side"]][int(id)] = true
	return [seen["A"].size(), seen["B"].size()]


## lab-stage4: the sorted ids of the living units no living enemy lists in `seen`; [] when no unit of the frame has a `seen` key.
func _hollow_ids(frame: Dictionary) -> Array:
	var out: Array = []
	var has_seen := false
	var listed := {}
	for u in frame["units"]:
		has_seen = has_seen or u.has("seen")
		if bool(u["alive"]):
			for id in u.get("seen", []):
				listed[int(id)] = true
	if not has_seen:
		return out
	for u in frame["units"]:
		if bool(u["alive"]) and not listed.has(int(u["id"])):
			out.append(int(u["id"]))
	out.sort()
	return out


## lab-stage4: `A sees %d  B sees %d` for a frame with `seen` keys, "" otherwise.
func _hud_sight(frame: Dictionary) -> String:
	for u in frame["units"]:
		if u.has("seen"):
			var n := _seen_counts(frame)
			return "A sees %d  B sees %d" % [n[0], n[1]]
	return ""


func _tick_or_never(t) -> String:
	return "never" if t == null else str(int(t))


func _glyph_state() -> Dictionary:
	var out := {}
	for k in ROLES.size():
		out[ROLES[k]] = Marks.SHAPES[k]
	return out


## `end: ...` for the last frame from the fight's result; "" for a v1 file (no end word).
func _end_label_for(res: Dictionary) -> String:
	if not res.has("end"):
		return ""
	var end := String(res["end"])
	var winner := String(res.get("winner", ""))
	if end == "wipe":
		if winner == "A" or winner == "B":
			return "end: %s wins (wipe)" % winner
		if winner == "none":
			return "end: mutual wipe, no winner"
	elif end == "silence":
		return "end: stall (silence)"
	return "end: %s" % end


## One ring per role per side: centred on that side's unit of the role nearest the opposing centroid at frame 0 (ties to the lowest unit id).
func _build_role_rings(ranges: Dictionary) -> void:
	var units: Array = _fight_frames[0]["units"]
	for side in ["A", "B"]:
		var opp := Vector2.ZERO
		var n := 0
		for u in units:
			if u["side"] != side:
				opp += Vector2(float(u["x"]), float(u["y"]))
				n += 1
		if n == 0:
			continue
		opp /= float(n)
		for k in ROLES.size():
			var rng := float(ranges.get(ROLES[k], 0.0))
			var best := -1
			var best_d := INF
			for u in units:
				if u["side"] == side and u["role"] == ROLES[k]:
					var d := Vector2(float(u["x"]), float(u["y"])).distance_squared_to(opp)
					if d < best_d or (d == best_d and int(u["id"]) < best):
						best = int(u["id"])
						best_d = d
			if best >= 0 and rng > 0.0:
				_role_rings.append({"side": side, "role": ROLES[k], "range": rng, "style": Marks.STYLES[k], "id": best})


## The layout shot's legend, with each role row drawn in its replay glyph and named with its shape, and a line for each ring: `<side> <role> <range> wu <style>`.
func _add_legend() -> Control:
	var panel: Control = super()
	var box: VBoxContainer = panel.get_child(0)
	for row in box.get_children():
		if row is HBoxContainer:
			var text: Label = row.get_child(1)
			var k := ROLES.find(text.text.get_slice(":", 0))
			var poly: Polygon2D = row.get_child(0).get_child(0)
			var pts := PackedVector2Array()
			for p in Marks.shape_points(k):
				pts.append(p * 12.0)
			poly.polygon = pts
			text.text += " (%s)" % Marks.SHAPES[k]
	for r in _role_rings:
		var rng := float(r["range"])
		var line := "%s %s %s wu %s" % [r["side"], r["role"], str(int(rng)) if rng == roundf(rng) else str(rng), r["style"]]
		box.add_child(_label(line, SIDE_COLOURS[r["side"]].lerp(Color.WHITE, LEGEND_LIGHTEN * 0.5), LEGEND_FONT))
	return panel


## Fit the whole fight's box (every position in every frame plus FIT_MARGIN) and scale the glyphs to the minimum; if that took more than the natural size
## (a wide field), zoom to the natural size instead and follow each frame's centroid.
func _setup_camera(panel: Control) -> void:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in _every_position():
		lo = Vector2(minf(lo.x, p["x"]), minf(lo.y, p["y"]))
		hi = Vector2(maxf(hi.x, p["x"]), maxf(hi.y, p["y"]))
	for f in _features:  # the ground is part of the picture: the fit box holds it too
		for p in _feature_points(f):
			lo = Vector2(minf(lo.x, p.x), minf(lo.y, p.y))
			hi = Vector2(maxf(hi.x, p.x), maxf(hi.y, p.y))
	var m := maxf(FIT_MARGIN * maxf(hi.x - lo.x, hi.y - lo.y), FIT_MIN_WU)
	var box_lo := lo - Vector2(m, m)
	var box_hi := hi + Vector2(m, m)
	var left := panel.position.x + panel.get_combined_minimum_size().x + 24.0
	var screen := Ground3DHost.SCREEN_SIZE
	_free_rect = Rect2(left, 24.0, screen.x - left - 24.0, screen.y - 48.0)
	_fit_box(box_lo, box_hi)
	_fit = [box_lo.x, box_lo.y, box_hi.x, box_hi.y]
	_scale_glyphs(_ground, _units3d)
	_glyph_k = _units3d.unit_node(0).scale.x
	_unit_px = _glyph_px
	_wide = _glyph_k > 1.0
	if _wide:
		var c := _centroid(_fight_frames[0])
		_zoom_to_natural(c)
		_scale_glyphs(_ground, _units3d)
		_glyph_k = _units3d.unit_node(0).scale.x


## Back the camera off until the box is inside the free rectangle, then narrow the lens in between the rig's steps (the layout shot's fit, with the replay's margin).
func _fit_box(box_lo: Vector2, box_hi: Vector2) -> void:
	var corners := [box_lo, Vector2(box_hi.x, box_lo.y), box_hi, Vector2(box_lo.x, box_hi.y)]
	var centre := (box_lo + box_hi) * 0.5
	var rig: Node3D = _ground.camera_rig()
	var cam: Camera3D = rig.get_camera()
	rig.pan_to(centre)
	rig.zoom_by(-1000)
	while not _box_fits(_ground, rig, corners, centre, _free_rect) and rig.camera_height() < rig.ZOOM_MAX_MIN:
		rig.zoom_by(1)
	var wide := cam.fov
	var narrow := FOV_MIN_DEG
	for _i in FOV_ITERATIONS:
		cam.fov = (wide + narrow) * 0.5
		if _box_fits(_ground, rig, corners, centre, _free_rect):
			wide = cam.fov
		else:
			narrow = cam.fov
	cam.fov = wide
	_box_fits(_ground, rig, corners, centre, _free_rect)


## Zoom in as far as keeps a natural-size glyph at the glyph minimum at `c` (the lens and rig height are the layout shot's).
func _zoom_to_natural(c: Vector2) -> void:
	var rig: Node3D = _ground.camera_rig()
	var want := GLYPH_MIN_PX * GLYPH_MARGIN
	rig.pan_to(c)
	rig.zoom_by(-1000)
	while rig.camera_height() < rig.ZOOM_MAX_MIN:
		rig.zoom_by(1)
		if _glyph_width_px(_ground, c.x, c.y, 1.0) < want:
			rig.zoom_by(-1)
			break


func _centroid(frame: Dictionary) -> Vector2:
	var sum := Vector2.ZERO
	for u in frame["units"]:
		sum += Vector2(float(u["x"]), float(u["y"]))
	return sum / float(frame["units"].size())


## Wide field: centre the camera on the frame's centroid and report the world box now in view.
func _follow(frame: Dictionary) -> void:
	var c := _centroid(frame)
	_box_fits(_ground, _ground.camera_rig(), [], c, _free_rect)
	var wx := absf(_ground.to_screen(c.x + 100.0, c.y).x - _ground.to_screen(c.x, c.y).x) / 100.0  # screen px per wu along x and y
	var wy := absf(_ground.to_screen(c.x, c.y + 100.0).y - _ground.to_screen(c.x, c.y).y) / 100.0
	var half := Vector2(_free_rect.size.x / wx, _free_rect.size.y / wy) * 0.5
	_fit = [c.x - half.x, c.y - half.y, c.x + half.x, c.y + half.y]
	_unit_px = _glyph_width_px(_ground, c.x, c.y, _glyph_k)


## The role's glyph and the white facing tick on a unit's body node (the tick cancels the manifest's facing offset so it points along the real facing).
func _dress(node: MeshInstance3D, role: String, side: String) -> void:
	var k := ROLES.find(role)
	var key := "%s%s" % [role, side]
	if not _meshes.has(key):
		_meshes[key] = Marks.glyph_mesh(maxi(k, 0), GroundUnits.BODY_RADIUS_WU, SIDE_COLOURS[side], UnitVisuals.facing_offset(maxi(k, 0)))
	if _tick_mesh == null:
		_tick_mesh = Marks.tick_mesh(GroundUnits.BODY_RADIUS_WU, GroundUnits.ARROW_LIFT_WU)
	node.mesh = _meshes[key]
	var tick: MeshInstance3D = node.get_node("Arrow")
	tick.mesh = _tick_mesh
	tick.rotation.y = UnitVisuals.facing_offset(maxi(k, 0))
