extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-104-01@d9c166, R-235-01@4f35af, R-235-02@138056, R-235-03@14ac1a, R-235-04@a81fce

# VG-E1 piece E1w (scenes/tactical_c/tactical_view.gd wiring of scenes/economy/ticker_beats.gd and scenes/economy/map_markers.gd).
# Proves S-235 (docs/bible/epics/E-16-client-camera-hud-and-world-view.md:271-274) and R-104-01 (:70). Quoted word for word:
#
#   R-235-01  Given the map view (S-161) and the tactical view, When the economy's places are drawn, Then the economic locations,
#             the neutral settlements, the objective, the side's base of operations, its expansions and forward works, and on land
#             maps the strongpoints are marked (E-22 S-175, S-177; E-15).
#   R-235-02  Given an environmental trouble travelling across the map, When it is drawn, Then both sides see where it is as it moves
#             (E-15 holds what it does).
#   R-235-03  Given the ticker (R-104-01), When a base is occupied, a side falls back to an expansion, an expansion is founded, a
#             weather trouble arrives, or a strongpoint is taken or lost, Then the ticker names it; no other economy beat reaches
#             the ticker (Westley, 2026-10-12).
#   R-235-04  Given a shipment that does not arrive (E-22 S-176), When the ticker, the banners and the map are read, Then nothing on
#             them explains why.
#   R-104-01  Given a mission, When the HUD is drawn, Then the player can always see the objective list with progress (top-left)
#             and a quiet ticker of notable beats beneath it; the ticker recognizes structure captured, structure lost, force routed,
#             and objective threshold crossed, and nothing else at launch.
#
# Spec sentence (docs/northstar/plans/2026-10-07-visible-game-spec.md, "S-235 ticker (amends the E1m and E1n paragraphs; Q-235-01
# closed)"): "[B R-235-03] The ticker carries the four beats plus a strongpoint taken or lost; forward bases are not named. E1m, E1n
# and the S-235 play are unblocked; their drafters take the five beats as the inventory."
# Rulings that bind this file: G2 (b) (TickerBeats emits strongpoint_taken / strongpoint_lost from the structures rows joined to the
# ids of frame["strongpoints"]; events_feed.gd skips those ids for Structure captured / lost; one ticker line per event), G3 (a) (the
# other four kinds have no frame source and are STUB), G5 (the wiring names), G6 (MapMarkers: kinds strongpoint and home_base), G9
# (qa_state map_markers and the inventory count).
#
# Pinned contract (the brief's INTERFACE block): the view holds a node TickerBeats (class TickerBeats, a child of the view, not under
# Hud, found by get_tree().root.find_child) and a MapMarkers (after StructuresLayer); PIECES maps both names to the two scripts; the
# frame path calls TickerBeats.feed(frame, local_faction) beside the Events.feed line and MapMarkers.set_frame(frame, local_faction,
# world_scale, camera) beside the other 2D layer set_frame calls; qa_state gains map_markers (MapMarkers.markers()) and _inventory
# gains map_markers (the count); events_feed.gd's A8 connection receives TickerBeats.beat(kind, text) as add_beat(kind, text).
#
# Premises dumped 2026-10-19 on origin/main cf9d737c (one real run of the fixture view, see the report): qa_state top-level keys
# scene, tick, plants, canvas, scale, unit_count, units, units_px, focus_layer, local_faction, selected, camera, ground3d, space3d,
# objects_px, last_command, commands_sent_last_order, units_in_last_command, ground_layer, error_panel, inventory, settlement_lots;
# inventory keys fog_layer, objective_markers, cover_cells, obstacles, structures, shots_in_flight, wrecks, squads, abilities_fx,
# ambient, loading_overlay, hud{clock, objectives, selection, events, strip, comb, reinforcements}, settlement_lots; no TickerBeats and
# no MapMarkers node. PREMISE FIXED HERE: with the stock c_bridge the view's _ready runs the real live pipe and Events records the real
# mission's structure owners first ({0:0, 1:-1, 2:2, 3:2}); this file's stub bridge therefore serves the first frame itself through
# _load_live (load_tactical_live -> tactical_frame), so the first frame Events and TickerBeats see is the fixture frame F1.
# Live shape: the frames tactical_view gets are CBridge._reconstruct_tactical views: a full structures list, strongpoints from the last
# full frame (so their owner and state are STALE after a flip; the owner of record is the structures row), and never a
# structures_changed key (the view erases it). Events records owners from the list BEFORE it reads structures_changed, so a frame with
# both draws no line, and a live view draws no Structure captured / lost line today; that is reported as a finding, not tested. The
# Structure captured / lost control and the strongpoint skip are therefore driven by raw delta frames (structures_changed, no
# structures list: _delta(), the A8 test's form, PIN a8-feed) pushed through the view's qa_step, each followed by the reconstructed
# frame of the same flip; the assertions hold whether TickerBeats reads the list only or also structures_changed.
# Home base (R-235-01 "the side's base of operations"): the spec fixes no source; the client's home convention is the kind-7 map node
# nearest the own-unit centroid (tactical_view.gd SPAWN_NODE_KIND, A18 G3). The fixture puts all own units ON the one kind-7 node, so
# the centroid, the node and the units agree and any of those sources passes; no lots, no own non-strongpoint structure at the start.
#
# CONTROLS, green on the built tree (no TickerBeats, no MapMarkers): [CONTROL] the view instantiates with the fixture terrain, qa_state
# carries the existing keys, the helpers find a present name and miss an absent one, and Events draws an objective line (the line
# detector) and a Structure captured / lost line for a non-strongpoint structure (the detector the strongpoint cases are compared to).
# POSITIVE CONTROLS that must FAIL on a wrong build, named in the case: "wrong build A" (events_feed.gd keeps its Structure lost line
# for a strongpoint id, so two lines appear), "wrong build B" (TickerBeats emits on the first frame, or twice for one flip), "wrong
# build C" (MapMarkers shows the stale strongpoints owner, so the marker misses the flip).
# RED on the built tree for: no scenes/economy/ files, so PIECES lacks both names, no TickerBeats or MapMarkers node, no map_markers key.
# Not tested here (no accessor in the interface): the marker colours (G7) and the drawn screen position (G6 for the drawing site).

const STUB_SRC := """extends "res://autoload/c_bridge.gd"
var fixture_mission: Dictionary = {}
var fixture_terrain: Dictionary = {}
var current: Dictionary = {}
var queue: Array = []
func mission() -> Dictionary:
	return fixture_mission
func terrain() -> Dictionary:
	return fixture_terrain
func load_tactical_live(_seed: int, _n_regions: int, _features: Array) -> bool:
	return true
func tactical_frame() -> Dictionary:
	return current
func tactical_step_n(_n: int) -> bool:
	if queue.is_empty():
		return false
	current = queue.pop_front()
	return true
"""

const TICKER_SRC := """extends Node
var calls: Array = []
signal beat(kind: String, text: String)
func feed(frame: Dictionary, local_faction: int) -> void:
	calls.append([int(frame.get("tick", -1)), local_faction])
"""

const MARKERS_SRC := """extends Node2D
var calls: Array = []
func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	calls.append([int(frame.get("tick", -1)), local_faction, world_scale, camera])
func markers() -> Array:
	return []
"""

const EXISTING_PIECES := {
	"MapLayer": "res://scenes/tactical_c/map_layer.gd",
	"StructuresLayer": "res://scenes/tactical_c/structures_layer.gd",
	"ObjectiveMarkers": "res://scenes/tactical_c/objective_markers.gd",
	"FogLayer": "res://scenes/tactical_c/fog_layer.gd",
	"LayerView": "res://scenes/tactical_c/layer_view.gd",
	"UnitSquads": "res://scenes/tactical_c/unit_squads.gd",
	"UnitVisuals": "res://scenes/tactical_c/unit_visuals.gd",
	"Events": "res://scenes/tactical_c/hud/events_feed.gd",
}
const EXISTING_QA_KEYS := ["scene", "tick", "plants", "canvas", "scale", "unit_count", "units", "units_px", "focus_layer", "local_faction", "selected", "camera", "ground3d", "space3d", "objects_px", "last_command", "commands_sent_last_order", "units_in_last_command", "ground_layer", "error_panel", "inventory", "settlement_lots"]
const EXISTING_INV_KEYS := ["fog_layer", "objective_markers", "cover_cells", "obstacles", "structures", "shots_in_flight", "wrecks", "squads", "abilities_fx", "ambient", "loading_overlay", "hud", "settlement_lots"]
const EXISTING_HUD_KEYS := ["clock", "objectives", "selection", "events", "strip", "comb", "reinforcements"]
const KINDS := ["base_occupied", "fallback", "expansion", "weather", "strongpoint_taken", "strongpoint_lost"]
const MARKER_KEYS := ["kind", "x", "y", "owner", "state"]

# Fixture frame. Structures: 5, 6 and 7 are strongpoints (ids in frame["strongpoints"]; 7 is ours from the first frame), 9 is not. Positions inside the fixture terrain.
const HOME := Vector2(250.0, 250.0)
const SP5 := Vector2(500.0, 500.0)
const SP6 := Vector2(150.0, 500.0)
const SP7 := Vector2(550.0, 250.0)
const ST9 := Vector2(450.0, 100.0)
const FOE_SPAWN := Vector2(850.0, 850.0)  # the enemy's kind-7 node

var _tick := 9  # _frame() increments first: F1 is tick 10
var _owners := {5: 1, 6: -1, 7: 0, 9: 1}
var _progress := 0.1
var _army := HOME  # where the own units stand


static func found(markers: Array, p: Vector2) -> Dictionary:
	for m in markers:
		if m is Dictionary and Vector2(float(m.get("x", -1.0e9)), float(m.get("y", -1.0e9))).distance_to(p) < 1.0:
			return m
	return {}


# A constant of a node's script (TickerBeats.TEXTS, TickerBeats.KINDS); null when the script has none.
static func const_of(n: Node, name: String) -> Variant:
	if n == null or n.get_script() == null:
		return null
	return (n.get_script() as Script).get_script_constant_map().get(name, null)


static func kinds_of(lines: Array) -> Array:
	var k := []
	for l in lines:
		k.append(String(l["kind"]))
	return k


static func mark_kinds(markers: Array) -> Array:
	var k := []
	for m in markers:
		k.append(String(m.get("kind", "")))
	return k


func _script(src: String) -> GDScript:
	var s := GDScript.new()
	s.source_code = src
	s.reload()
	return s


func _srow(id: int, pos: Vector2) -> Dictionary:
	return {"id": id, "type": 0, "owner": int(_owners[id]), "x": pos.x, "y": pos.y, "hp": 500.0, "stage": 0, "cap": 0, "nst": 150, "next_type": 0, "period": 100}


# A reconstructed full view (CBridge shape, the only shape the running view is given). `removed` ids leave the structures list (and
# are named in structures_removed). strongpoints are the last FULL frame's rows and stay stale (owner and state as at F1) on purpose.
func _frame(removed: Array = []) -> Dictionary:
	var fx := _fixture()
	var f: Dictionary = fx.frame().duplicate(true)
	_tick += 1
	f["tick"] = _tick
	f["player_faction"] = 0
	f["map"]["canvas"] = 1000.0
	f["map"]["nodes"].append({"x": HOME.x, "y": HOME.y, "kind": 7})
	f["map"]["nodes"].append({"x": FOE_SPAWN.x, "y": FOE_SPAWN.y, "kind": 7})
	for u in f["units"]:
		if int(u["faction"]) == 0:
			u["x"] = _army.x
			u["y"] = _army.y
	var rows := []
	for id in [5, 6, 7, 9]:
		if removed.has(id):
			continue
		rows.append(_srow(id, {5: SP5, 6: SP6, 7: SP7, 9: ST9}[id]))
	f["structures"] = rows
	f["strongpoints"] = [{"id": 5, "x": SP5.x, "y": SP5.y, "owner": 1, "state": 1}, {"id": 6, "x": SP6.x, "y": SP6.y, "owner": -1, "state": 0}, {"id": 7, "x": SP7.x, "y": SP7.y, "owner": 0, "state": 1}]
	f["objectives"] = [{"i": 0, "progress": _progress, "done": 0}]
	f["full"] = true
	if not removed.is_empty():
		f["structures_removed"] = removed.duplicate()
	return f


# A raw delta frame in the A8 test's form (PIN a8-feed): structures_changed with the new owner of `changed` ids and NO structures
# list. The running view is never given this shape (CBridge folds deltas into full views); it is the seam events_feed.gd's own
# Structure captured / lost lines read, so the skip for strongpoint ids is only reachable here. frame["strongpoints"] is present
# (G2 b: the skip keys on it, or on ids remembered from a full frame that carried it; both are satisfied).
func _delta(changed: Array) -> Dictionary:
	var f := _frame()
	f.erase("structures")
	f.erase("objectives")
	f["type"] = "tactical_delta"
	f["full"] = false
	var ch := []
	for id in changed:
		ch.append({"id": id, "owner": int(_owners[id])})
	f["structures_changed"] = ch
	return f


func _step(stub, v: Node, f: Dictionary) -> void:
	stub.queue.append(f)
	v.qa_step(1)
	await process_frame


func _run() -> void:
	# --- positive controls of the file's own detectors
	var probe := [{"kind": "strongpoint", "x": 5.0, "y": 6.0}]
	_check(not found(probe, Vector2(5.0, 6.0)).is_empty(), "CONTROL: found() misses a marker that is present")
	_check(found(probe, Vector2(50.0, 6.0)).is_empty(), "CONTROL: found() finds a marker that is absent")
	_check(kinds_of([{"kind": "a"}, {"kind": "b"}]) == ["a", "b"], "CONTROL: kinds_of() does not list the line kinds")

	var fx := _fixture()
	var stub = _script(STUB_SRC).new()
	stub.fixture_mission = fx.mission()
	stub.fixture_terrain = fx.terrain()
	stub.current = _frame()
	var SS = load("res://autoload/sim_session.gd")
	SS._bridge = stub
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.GROUND_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	# As tests/test_vg_e_e1p.gd _view(): the era is set again and the terrain given after the first frames (something resets the era
	# between _ready and here: _ground_era() read false in this file's first run), so the ground host exists.
	cfg.set_era(cfg.GROUND_ERA_ID)
	v.set_terrain(fx.terrain())
	await process_frame
	var ev: Node = v.find_child("Events", true, false)
	var qa: Dictionary = v.qa_state()

	# ---------------------------------------------------------------- [CONTROL] green on the built tree
	var g: Dictionary = qa.get("ground3d", {})
	_check(bool(g.get("present", false)) and int(g.get("cells_w", 0)) == fx.W and int(g.get("cells_h", 0)) == fx.H, "[CONTROL] the view with the fixture terrain has no ground3d (present/cells_w/cells_h): %s" % [g])
	_check(int(qa.get("tick", -1)) == 10 and int(qa.get("local_faction", -1)) == 0, "[CONTROL] premise: the fixture frame F1 was not served through _load_live (tick %s, local_faction %s)" % [qa.get("tick"), qa.get("local_faction")])
	for k in EXISTING_QA_KEYS:
		_check(qa.has(k), "[CONTROL] qa_state lacks the existing key %s; keys %s" % [k, qa.keys()])
	var inv: Dictionary = qa.get("inventory", {})
	for k in EXISTING_INV_KEYS:
		_check(inv.has(k), "[CONTROL] _inventory lacks the existing key %s; keys %s" % [k, inv.keys()])
	for k in EXISTING_HUD_KEYS:
		_check((inv.get("hud", {}) as Dictionary).has(k), "[CONTROL] _inventory.hud lacks the existing key %s" % k)
	_check(ev != null and ev.lines().is_empty(), "[BEAT] wrong build B: the first frame (strongpoint 7 already ours) left a line on the ticker; a first frame only records owners: %s" % [ev.lines() if ev != null else "no Events"])
	_check(int(inv.get("structures", -1)) == 4, "[CONTROL] premise: inventory.structures is not 4 for the fixture frame: %s" % [inv.get("structures")])
	_check(int(inv.get("hud", {}).get("reinforcements", -1)) == 1, "[CONTROL] premise: hud.reinforcements counts own structures (id 7), expected 1 at F1: %s" % [inv.get("hud")])

	# ---------------------------------------------------------------- [PIECES] PIECES maps both names to the two scripts
	var pieces: Dictionary = v.PIECES
	for n in EXISTING_PIECES:
		_check(String(pieces.get(n, "")) == EXISTING_PIECES[n], "[PIECES] CONTROL: the existing PIECES entry %s changed: %s" % [n, pieces.get(n)])
	_check(String(pieces.get("TickerBeats", "")) == "res://scenes/economy/ticker_beats.gd", "[PIECES] PIECES lacks TickerBeats -> res://scenes/economy/ticker_beats.gd: %s" % [pieces.get("TickerBeats")])
	_check(String(pieces.get("MapMarkers", "")) == "res://scenes/economy/map_markers.gd", "[PIECES] PIECES lacks MapMarkers -> res://scenes/economy/map_markers.gd: %s" % [pieces.get("MapMarkers")])

	# ---------------------------------------------------------------- [NODES] after load the view has both nodes
	var ticker: Node = root.find_child("TickerBeats", true, false)
	var mm: Node = v.find_child("MapMarkers", true, false)
	_check(ticker != null, "[NODES] R-235-03: no node named TickerBeats found from the root (A8 connects by that name)")
	_check(mm != null, "[NODES] R-235-01: the view has no MapMarkers node")
	if ticker != null:
		_check(ticker.get_parent() == v, "[NODES] TickerBeats is not a child of the view (parent %s)" % [ticker.get_parent()])
		var hud := v.find_child("Hud", true, false)
		_check(hud == null or not hud.is_ancestor_of(ticker), "[NODES] TickerBeats sits under Hud; it is a child of the view")
		_check(ticker.get_script() != null and (ticker.get_script() as Script).resource_path == "res://scenes/economy/ticker_beats.gd", "[NODES] TickerBeats is not the script scenes/economy/ticker_beats.gd (a placeholder?)")
	if mm != null:
		var sl := v.find_child("StructuresLayer", true, false)
		_check(sl != null and mm.get_parent() == sl.get_parent() and mm.get_index() > sl.get_index(), "[NODES] MapMarkers is not after StructuresLayer under the same parent")
		_check(mm.get_script() != null and (mm.get_script() as Script).resource_path == "res://scenes/economy/map_markers.gd", "[NODES] MapMarkers is not the script scenes/economy/map_markers.gd (a placeholder?)")
		_check(mm is Node2D, "[NODES] MapMarkers is not a Node2D layer (G6)")

	# ---------------------------------------------------------------- [KEYS] and R-235-01 markers from the first frame
	_check(qa.has("map_markers"), "[KEYS] qa_state lacks top-level key map_markers; keys %s" % [qa.keys()])
	_check(inv.has("map_markers"), "[KEYS] _inventory lacks map_markers; keys %s" % [inv.keys()])
	var marks: Array = qa.get("map_markers", []) if qa.get("map_markers", []) is Array else []
	if inv.has("map_markers"):
		_check(typeof(inv["map_markers"]) == TYPE_INT and int(inv["map_markers"]) == marks.size(), "[KEYS] _inventory.map_markers is not the int count of qa_state.map_markers: %s vs %d" % [inv["map_markers"], marks.size()])
	if mm != null and mm.has_method("markers"):
		_check(mm.markers() == marks, "[KEYS] qa_state.map_markers is not MapMarkers.markers()")
	_check(marks.size() == 4, "[KEYS] R-235-01: the fixture has three strongpoints and one home base, expected 4 markers, got %d: %s" % [marks.size(), marks])
	_check(mark_kinds(marks) == ["strongpoint", "strongpoint", "strongpoint", "home_base"], "[KEYS] R-235-01: marker kinds are not [strongpoint x3, home_base] (strongpoints ascending id, then the home base): %s" % [mark_kinds(marks)])
	for m in marks:
		var ok: bool = m is Dictionary
		for k in MARKER_KEYS:
			ok = ok and m.has(k)
		_check(ok and typeof(m["owner"]) == TYPE_INT and typeof(m["state"]) == TYPE_INT and typeof(m["x"]) == TYPE_FLOAT and typeof(m["y"]) == TYPE_FLOAT and typeof(m["kind"]) == TYPE_STRING, "[KEYS] R-235-01: marker %s lacks kind/x/y/owner/state of the right types" % [m])
	var m5 := found(marks, SP5)
	var m6 := found(marks, SP6)
	var m7 := found(marks, SP7)
	var mh := found(marks, HOME)
	_check(not m5.is_empty() and m5.get("kind") == "strongpoint" and int(m5.get("owner", -9)) == 1, "[KEYS] R-235-01: no strongpoint marker at structure 5 (%s) with owner 1: %s" % [SP5, m5])
	_check(not m6.is_empty() and m6.get("kind") == "strongpoint" and int(m6.get("owner", -9)) == -1, "[KEYS] R-235-01: no strongpoint marker at structure 6 (%s) with owner -1: %s" % [SP6, m6])
	_check(not m7.is_empty() and m7.get("kind") == "strongpoint" and int(m7.get("owner", -9)) == 0, "[KEYS] R-235-01: no strongpoint marker at structure 7 (%s) with owner 0: %s" % [SP7, m7])
	_check(not mh.is_empty() and mh.get("kind") == "home_base" and int(mh.get("owner", -9)) == 0, "[KEYS] R-235-01: no home_base marker at the kind-7 node (%s) owned by the local faction 0: %s" % [HOME, mh])
	_check(found(marks, ST9).is_empty(), "[KEYS] R-235-01: a non-strongpoint structure (id 9) is marked; only strongpoints and the home base are (G6): %s" % [marks])

	# ---------------------------------------------------------------- [BEAT] first frame: records owners, adds no line, emits no beat
	if ticker != null and ticker.has_method("beats_emitted"):
		_check(ticker.beats_emitted() == 0, "[BEAT] wrong build B: TickerBeats emitted %d beat(s) on the first frame; the first frame only records owners" % ticker.beats_emitted())
	else:
		_check(false, "[BEAT] TickerBeats has no beats_emitted()")

	# ---------------------------------------------------------------- [ORDER] one frame reaches TickerBeats.feed and MapMarkers.set_frame
	if ticker != null and mm != null:
		var real_t: Node = ticker
		var real_m: Node = mm
		var pt: Node = _script(TICKER_SRC).new()
		var pm: Node2D = _script(MARKERS_SRC).new()
		var t_parent := real_t.get_parent()
		var m_parent := real_m.get_parent()
		t_parent.remove_child(real_t)
		m_parent.remove_child(real_m)
		pt.name = "TickerBeats"
		pm.name = "MapMarkers"
		t_parent.add_child(pt)
		m_parent.add_child(pm)
		_progress = 0.3
		var f1b := _frame()
		await _step(stub, v, f1b)
		_check(pt.calls.size() == 1 and pt.calls[0][0] == _tick and pt.calls[0][1] == 0, "[ORDER] TickerBeats.feed(frame, local_faction) was not called once with the loaded frame and faction 0: %s" % [pt.calls])
		_check(pm.calls.size() == 1 and pm.calls[0][0] == _tick and pm.calls[0][1] == 0, "[ORDER] MapMarkers.set_frame(frame, local_faction, world_scale, camera) was not called once with the loaded frame and faction 0: %s" % [pm.calls])
		if pm.calls.size() == 1:
			_check(is_equal_approx(float(pm.calls[0][2]), float(v._world_scale)) and (pm.calls[0][3] as Vector2).is_equal_approx(v._camera), "[ORDER] MapMarkers.set_frame got scale %s camera %s; the view has %s and %s" % [pm.calls[0][2], pm.calls[0][3], v._world_scale, v._camera])
		t_parent.remove_child(pt)
		m_parent.remove_child(pm)
		pt.free()
		pm.free()
		t_parent.add_child(real_t)
		m_parent.add_child(real_m)
		ticker = real_t
		mm = real_m
	else:
		_check(false, "[ORDER] no TickerBeats or MapMarkers to swap for probes (frame calls not testable)")
		_progress = 0.3
		await _step(stub, v, _frame())

	# ---------------------------------------------------------------- [NOREGRESS] a frame without strongpoint events
	# Events still draws an objective line (the line detector; green on the built tree) and nothing else is added.
	_check(kinds_of(ev.lines()) == ["objective"], "[NOREGRESS] CONTROL: progress 0.1 -> 0.3 is not exactly one objective line on the ticker: %s" % [kinds_of(ev.lines())])
	var qa2: Dictionary = v.qa_state()
	var inv2: Dictionary = qa2.get("inventory", {})
	_check(int(inv2.get("hud", {}).get("events", -1)) == 1, "[NOREGRESS] hud.events is not 1 after one objective crossing: %s" % [inv2.get("hud")])
	_check(int(inv2.get("structures", -1)) == 4 and int(inv2.get("hud", {}).get("reinforcements", -1)) == 1 and int(inv2.get("objective_markers", -1)) == int(inv.get("objective_markers", -2)), "[NOREGRESS] an existing inventory value changed for a frame without strongpoint events: %s" % [inv2])
	for k in EXISTING_QA_KEYS:
		_check(qa2.has(k), "[NOREGRESS] qa_state lost the existing key %s" % k)
	for k in EXISTING_INV_KEYS:
		_check(inv2.has(k), "[NOREGRESS] _inventory lost the existing key %s" % k)
	if ticker != null and ticker.has_method("beats_emitted"):
		_check(ticker.beats_emitted() == 0, "[NOREGRESS] TickerBeats emitted a beat for a frame without a strongpoint event: %d" % ticker.beats_emitted())

	# ---------------------------------------------------------------- [BEAT] the strongpoint sequence through the view's frame path
	# Each step clears the ticker lines first (lines() is the live array) so a step's lines are exactly what that frame added.
	# S2: strongpoint 5 flips enemy -> local, reconstructed shape (a full list only). One Strongpoint taken line.
	ev.lines().clear()
	_owners[5] = 0
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["strongpoint_taken"], "[BEAT] R-235-03 (G2 b): enemy -> local on strongpoint 5 must add exactly one strongpoint_taken line and no Structure captured line, got %s" % [kinds_of(ev.lines())])
	if not ev.lines().is_empty():
		var ln: Dictionary = ev.lines()[0]
		var want_text := ""
		var texts0 = const_of(ticker, "TEXTS")
		if texts0 is Dictionary:
			want_text = String(texts0.get("strongpoint_taken", ""))
		_check(want_text != "" and String(ln["text"]) == want_text and String(ln["text"]).to_lower().contains("strongpoint"), "[BEAT] R-235-03: the line text %s is not TickerBeats.TEXTS[strongpoint_taken] %s naming the strongpoint" % [ln["text"], want_text])
	var mk: Array = v.qa_state().get("map_markers", [])
	_check(int(found(mk, SP5).get("owner", -9)) == 0, "[BEAT] wrong build C: the marker of strongpoint 5 must show the new owner 0 from the structures row (the strongpoints row is stale at 1): %s" % [found(mk, SP5)])
	if ticker != null and ticker.has_method("last_beat"):
		_check(ticker.beats_emitted() == 1 and String(ticker.last_beat().get("kind", "")) == "strongpoint_taken", "[BEAT] TickerBeats beats_emitted/last_beat disagree with one strongpoint_taken beat: %d, %s" % [ticker.beats_emitted(), ticker.last_beat()])
	# S2b: the identical frame again (next tick): one event is one line, not one per frame.
	ev.lines().clear()
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()).is_empty(), "[BEAT] wrong build B: the same owner on the next frame added lines %s; one event, one line" % [kinds_of(ev.lines())])
	# S3: local -> enemy as a raw delta (structures_changed names strongpoint 5), then as the reconstructed view of the same flip. The
	# ticker ends with exactly ONE strongpoint_lost line for the two frames and NO Structure lost line (wrong build A keeps the
	# events_feed.gd line on the delta: kinds [lost, strongpoint_lost]).
	ev.lines().clear()
	_owners[5] = 1
	await _step(stub, v, _delta([5]))
	_check(not kinds_of(ev.lines()).has("lost"), "[BEAT] wrong build A: R-235-03 (G2 b) a Structure lost line was drawn for strongpoint 5 (an id in frame[strongpoints]): %s" % [kinds_of(ev.lines())])
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["strongpoint_lost"], "[BEAT] R-235-03 (G2 b): local -> enemy on strongpoint 5 must leave exactly one strongpoint_lost line over the delta and the full frame, got %s" % [kinds_of(ev.lines())])
	_check(int(found(v.qa_state().get("map_markers", []), SP5).get("owner", -9)) == 1, "[BEAT] the marker of strongpoint 5 did not follow the owner back to 1")
	# S4: enemy -> local, delta then full: exactly one strongpoint_taken line, NO Structure captured line.
	ev.lines().clear()
	_owners[5] = 0
	await _step(stub, v, _delta([5]))
	_check(not kinds_of(ev.lines()).has("captured"), "[BEAT] wrong build A: R-235-03 (G2 b) a Structure captured line was drawn for strongpoint 5: %s" % [kinds_of(ev.lines())])
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["strongpoint_taken"], "[BEAT] R-235-03 (G2 b): enemy -> local on strongpoint 5 must leave exactly one strongpoint_taken line over the delta and the full frame, got %s" % [kinds_of(ev.lines())])
	# S5: local -> enemy, reconstructed shape only.
	ev.lines().clear()
	_owners[5] = 1
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["strongpoint_lost"], "[BEAT] R-235-03: local -> enemy on strongpoint 5, reconstructed shape, must add exactly one strongpoint_lost line, got %s" % [kinds_of(ev.lines())])
	# S6, S7: the NEGATIVE HALF (the control, green on the built tree): the same flips of a non-strongpoint structure (id 9) give the
	# Structure captured / lost line and no strongpoint line, and TickerBeats emits nothing for them.
	var beats_before := 0
	if ticker != null and ticker.has_method("beats_emitted"):
		beats_before = ticker.beats_emitted()
	ev.lines().clear()
	_owners[9] = 0
	await _step(stub, v, _delta([9]))
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["captured"], "[BEAT] CONTROL: a non-strongpoint structure (id 9) flipping to us must leave exactly the Structure captured line, got %s" % [kinds_of(ev.lines())])
	ev.lines().clear()
	_owners[9] = 1
	await _step(stub, v, _delta([9]))
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["lost"], "[BEAT] CONTROL: a non-strongpoint structure (id 9) flipping away from us must leave exactly the Structure lost line, got %s" % [kinds_of(ev.lines())])
	if ticker != null and ticker.has_method("beats_emitted"):
		_check(ticker.beats_emitted() == beats_before, "[BEAT] R-235-03: TickerBeats emitted for a non-strongpoint structure (%d -> %d); no other economy beat reaches the ticker" % [beats_before, ticker.beats_emitted()])
	# S8: a flip between two other factions is not a beat (to or from the local faction only).
	ev.lines().clear()
	_owners[5] = 2
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()).is_empty(), "[BEAT] R-235-03: strongpoint 5 passing from faction 1 to faction 2 (neither is ours) must add no line, got %s" % [kinds_of(ev.lines())])
	_check(int(found(v.qa_state().get("map_markers", []), SP5).get("owner", -9)) == 2, "[BEAT] the marker of strongpoint 5 did not follow the owner to 2")
	# S9: neutral -> local on strongpoint 6 is a strongpoint taken.
	ev.lines().clear()
	_owners[6] = 0
	await _step(stub, v, _frame())
	_check(kinds_of(ev.lines()) == ["strongpoint_taken"], "[BEAT] R-235-03: neutral -> local on strongpoint 6 must add exactly one strongpoint_taken line, got %s" % [kinds_of(ev.lines())])
	# S10: an own strongpoint that leaves the structures list (and structures_removed) counts as lost: one line.
	ev.lines().clear()
	await _step(stub, v, _frame([6]))
	_check(kinds_of(ev.lines()) == ["strongpoint_lost"], "[BEAT] R-235-03 (G2 b): an own strongpoint (6) that leaves structures_removed must add exactly one strongpoint_lost line, got %s" % [kinds_of(ev.lines())])

	# ---------------------------------------------------------------- [HOME] the base of operations does not follow the army
	# R-235-01 "the side's base of operations". A second kind-7 node is the enemy's spawn at FOE_SPAWN. The army marches onto it (the
	# play's live run, seed 1: a home base recomputed as the kind-7 node nearest the own-unit centroid jumped to the enemy's spawn once
	# the army reached it, at about tick 4,500). The home_base marker stays at HOME and the enemy's node is never marked home_base.
	ev.lines().clear()
	_army = FOE_SPAWN - Vector2(30.0, 30.0)
	await _step(stub, v, _frame())
	var hm: Array = v.qa_state().get("map_markers", [])
	var homes := []
	for m in hm:
		if m.get("kind") == "home_base":
			homes.append(m)
	_check(homes.size() == 1 and Vector2(float(homes[0]["x"]), float(homes[0]["y"])).distance_to(HOME) < 1.0, "[HOME] R-235-01: the home_base marker must stay at the own spawn %s after the army stands at %s, got %s" % [HOME, _army, homes])
	_check(found(hm, FOE_SPAWN).is_empty(), "[HOME] R-235-01: the enemy's spawn node %s is marked: %s" % [FOE_SPAWN, hm])
	_army = HOME

	# ---------------------------------------------------------------- [ORDER] the A8 listening path with the real signal
	# TickerBeats.beat(kind, text) reaches Events.add_beat(kind, text) as a ticker line; positive control: the objective line above came
	# through the same Events node.
	if ticker != null and ticker.has_method("emit_beat"):
		var tx: Dictionary = const_of(ticker, "TEXTS") if const_of(ticker, "TEXTS") is Dictionary else {}
		var kinds_const = const_of(ticker, "KINDS")
		_check(kinds_const is Array and (kinds_const as Array) == KINDS and tx.keys().size() == KINDS.size(), "[ORDER] TickerBeats.KINDS/TEXTS are not the six kinds %s: %s / %s" % [KINDS, kinds_const, tx.keys()])
		for k in KINDS:
			ev.lines().clear()
			var r: bool = ticker.emit_beat(k)
			_check(r, "[ORDER] emit_beat(%s) returned false for a kind in KINDS" % k)
			var one: bool = not ev.lines().is_empty() and kinds_of(ev.lines()) == [k] and String(ev.lines()[0]["text"]) == String(tx.get(k, "?"))
			_check(one, "[ORDER] R-235-03: emit_beat(%s) did not reach Events as exactly one line with TEXTS[%s]: %s" % [k, k, ev.lines()])
			_check(String(tx.get(k, "")) != "" and not String(tx.get(k, "")).to_lower().contains("shipment") and not String(tx.get(k, "")).to_lower().contains("forward"), "[ORDER] R-235-04 / spec: the text of %s is empty or names a shipment or a forward base: %s" % [k, tx.get(k)])
		# No other economy beat reaches the ticker (R-235-03), and nothing explains a missing shipment (R-235-04).
		for bad in ["shipment", "shipment_lost", "forward_base", "forward_base_occupied", ""]:
			ev.lines().clear()
			var before: int = ticker.beats_emitted()
			var r2: bool = ticker.emit_beat(bad)
			_check(not r2 and ev.lines().is_empty() and ticker.beats_emitted() == before, "[ORDER] R-235-03/R-235-04: emit_beat(%s) must return false and add no line; returned %s, lines %s" % [bad, r2, ev.lines()])
		_check(not String(ev.banner()).to_lower().contains("shipment"), "[ORDER] R-235-04: the banner mentions a shipment: %s" % ev.banner())
	else:
		_check(false, "[ORDER] no TickerBeats.emit_beat: the A8 listening path is not testable")

	# ---------------------------------------------------------------- [REACH] the wiring is on the path the running view uses
	# Every frame above reached the nodes through qa_step (the call _process makes for live play) and the first through _load_live;
	# the test never called feed() or set_frame() on the pieces itself. The one direct call below is the CONTROL that a node the view
	# did not feed stays empty: a bare MapMarkers made here has no markers.
	var bare = load("res://scenes/economy/map_markers.gd") if ResourceLoader.exists("res://scenes/economy/map_markers.gd") else null
	if bare != null:
		var bm = bare.new()
		root.add_child(bm)
		await process_frame
		_check(bm.markers().is_empty(), "[REACH] CONTROL: a MapMarkers nobody fed has markers before its first set_frame: %s" % [bm.markers()])
		bm.queue_free()
	else:
		_check(false, "[REACH] scenes/economy/map_markers.gd does not exist, so the wiring cannot be reached")
	var live_marks: Array = v.qa_state().get("map_markers", [])
	_check(not live_marks.is_empty() and not found(live_marks, HOME).is_empty(), "[REACH] R-235-01: after frames loaded only through the view's frame path the home_base marker is absent: %s" % [live_marks])

	SS._bridge = null
	cfg.set_era(cfg.SPACE_ERA_ID)
