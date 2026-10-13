extends "res://tests/support/vg_c_case.gd"
# NEEDS A DISPLAY (MultiMesh transforms read identity under the dummy renderer; FU-B22-pregate-display, E1k extension, ledger day32):
#   xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_e_e1k_parity.gd

# Piece VG-E1K (scenes/settlement/settlement_look.gd, settlement_streets.gd, settlement_layer.gd), the parity test of
# rules.md section (d) "Prototype copies ship a parity test" (method rev 3): the port is drawn beside the approved
# mockup (scenes/mockups/settlement/settlement_sim.gd = S, settlement_mockup.gd = M, scenes/mockups/landscape/field_map.gd
# = FM) at the same density field. THIS file holds the exact comparisons (no tolerance anywhere in it); every tolerance
# and epsilon lives in tests/test_vg_e_e1k_park_parity.gd (extends this file, reuses the fixture), ledger row
# DRAFT-e1k-parity-tolerance. Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md "Rev 12d (2026-10-12)", the
# paragraph "E1k numbers" (NUMBERS N1 to N10 below), gap rulings g1 to g10 of the E1k script.
#
# The rules and the verdict this test proves, word for word:
#   R-193-01 (docs/bible/epics/E-17-map-generation.md:315): "Given a map, When population density is set, Then it is a
#     growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is
#     shaped by water, slope and the core's position, so districts follow rivers, coasts and contour lines and never
#     form rings, and walls follow defensible ground."
#   R-193-02 (:316): "Given difficult terrain, When density reaches it, Then the field never gives up and the city adapts
#     by placing buildings in wild locations, such as inside a cliff, underneath a waterfall or on a steep mountainside.
#     Difficult ground changes what gets built, not whether anything is. An opening in rock is cosmetic only: the layer
#     mask and the land flag are unchanged (Westley, 2026-10-06)."
#   R-193-05 (:319): "Given a lot, When the density at its cell passes a threshold, Then the lot rises through its stages,
#     starting under construction, with a construction animation between stages. There are five stages: empty, staked,
#     scaffold, small and large (Westley, 2026-10-06) [Q-191-05: the thresholds, drafted in the prototype]."
#   R-193-09 (:323): "Given a settlement, When armies and units cross it, Then there are always natural paths through it,
#     so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the
#     contour lines and rivers by rule (Westley, 2026-10-06)."
#   R-237-01 (docs/bible/epics/E-18-visual-style-and-combat-visuals.md:143): "Given a self-built building, When it first
#     appears, Then it is drawn under construction and rises to complete over time, and nothing about it snaps into
#     place (E-17 R-166-01)."
#   Westley, recorded 2026-10-12 (spec Rev 12d): [W 2026-10-12 S-237 0402: "Why are units so heavily stacked? On the
#     buildings, it's very uniform, there's no perceptible difference in level between the buildings, and the layout is
#     super uniform and square, not looks like the sister system to the biome engine at all. Not approved yet."]
# Replaces the wrong cites of tests/test_vg_e_e1k.gd: R-193-07 -> R-193-02 (cliff dwelling), R-193-06 -> R-193-09 (streets).
#
# Cases (each message names the sentence it proves):
#   P0 control, green today: the mockup instantiates under a display, grows, and its MultiMesh carries
#      scaled boxes; the skeleton SettlementLayer draws one instance per lot of a hand-built frame.
#   P1 the same density field: every mockup cell with state > 0 or rubble == 1 becomes one lot {id = cell index
#      (gap g3: the hash input is the lot id, so the port hashes what the mockup hashes), x,y = cell centre in wu,
#      stage = state (rubble: 0), building 0, owner 0}; the terrain is the mockup's elevation (wu) x 100 as int32 cm on
#      the 121 x 121 window. Premises are printed (PREMISE lines).
#   P3 stage histogram over a disc: EXACT equality of the port's lots_drawn() categories and the mockup's sim.counts()
#      categories (rubble, stage 1..4 off a cliff, cliff dwellings by stage), cliff decided by the port's slope (gap g1).
#   P6 constants table (B23 model, tests/test_vg_b_b23.gd): each copied constant and vis row of settlement_look.gd read
#      from the live script against the prototype as run, S/M/FM line beside each row. Red today because
#      scenes/settlement/settlement_look.gd does not exist.
#   Lane gaps and hidden routes (N9, gap g4): the layer draws no lot in a lane cell and any route mesh is hidden.
# The tolerance-bearing cases (P4 non-axis-aligned fraction, per-stage height buckets, P5 per-box scale, yaw, position,
# rubble colour, slope_at) are in tests/test_vg_e_e1k_park_parity.gd.
#
# Fixture parameters (gap g8: the writer chooses and lists them; they are fixture parameters, not thresholds):
#   mockup seed 11 (M:9 SEED, the scene's own), sim rng seed 7 (S reset), STEP_DT 0.25 s (M qa_advance's dt),
#   GROW_STEPS 1600 (400 s of mockup time; the probe shows the counts constant from step 1600 to 2400),
#   then DAMAGE_HITS 3 area hits at core + DAMAGE_OFFSET (S damage(), radius 6) so rubble exists, then SETTLE_STEPS 12
#   (3 s, under S REBUILD_DELAY_S 10), then up to EXTRA_SETTLE_MAX 12 more steps until no disc cell animates.
#   Disc: cells within DISC_R of the core cell (M qa_state "core"), wholly inside the window and EDGE_MARGIN from its edge.

const MOCKUP_SCENE := "res://scenes/mockups/settlement/settlement_mockup.tscn"
const SIM_PATH := "res://scenes/mockups/settlement/settlement_sim.gd"
const LAYER := "res://scenes/settlement/settlement_layer.gd"
const LOOK := "res://scenes/settlement/settlement_look.gd"
const WIN := 121
const CELL_WU := 100.0
const STEP_DT := 0.25
const GROW_STEPS := 1600
const DAMAGE_HITS := 3
const DAMAGE_OFFSET := Vector2i(10, 6)
const SETTLE_STEPS := 12
const EXTRA_SETTLE_MAX := 12
const DISC_R := 20
const EDGE_MARGIN := 6
const EPS_D := 1.0e-9   # derived double compare, not a threshold (B23 EPS model)
const EPS_F32 := 1.0e-4 # derived compare of a value read back from a float32 MultiMesh transform, not a threshold
const VIS_IDS := [0, 1, 7, 23, 24, 100, 5000, 14640]
const HASH_IDS := [0, 1, 2, 3, 7, 11, 23, 24, 100, 777, 5000, 14640, 14651]

var Sim: GDScript
var m: Node3D
var sim
var lots: Array = []
var idx_of := {}          # lot id -> layer instance index (ascending id)
var terr := {}
var layer: Node3D
var pmm: MultiMesh        # the port layer's MultiMesh
var disc: Array = []      # cell indices of the lots inside the disc, ascending
var animating := {}       # cell index -> true, disc cells still animating in the mockup at the read instant
var t_wall := 0
var ready_fixture := false


func _cell(i: int) -> Vector2i:
	return Vector2i(i % WIN, i / WIN)


func _cat_sim(i: int) -> String:
	if sim.rubble[i] == 1:
		return "rubble"
	var s: int = sim.state[i]
	return ("cliff%d" % s) if sim.is_cliff(i) else ("stage%d" % s)


func _cat_port(d: Dictionary) -> String:
	var s := int(d.get("stage", -1))
	if s == 0:
		return "rubble"
	return ("cliff%d" % s) if bool(d.get("cliff", false)) else ("stage%d" % s)


func _hist(cats: Array) -> Dictionary:
	var h := {}
	for c in cats:
		h[c] = int(h.get(c, 0)) + 1
	var keys := h.keys()
	keys.sort()
	var out := {}
	for k in keys:
		out[k] = h[k]
	return out


func _find_mmi(n: Node) -> MultiMeshInstance3D:
	for c in n.find_children("*", "MultiMeshInstance3D", true, false):
		return c
	return null


# Builds the mockup run, the lot list, the terrain and the port layer. Returns false (after a failed check) when the
# mockup cannot be built: the brief says STOP with a "gap:" reason then; no _flush is reimplemented here.
func _build() -> bool:
	t_wall = Time.get_ticks_msec()
	Sim = load(SIM_PATH)
	var ps = load(MOCKUP_SCENE) if ResourceLoader.exists(MOCKUP_SCENE) else null
	_check(ps is PackedScene, "gap: the settlement mockup scene does not load: " + MOCKUP_SCENE)
	if not (ps is PackedScene):
		return false
	m = ps.instantiate()
	root.add_child(m)
	await process_frame            # _ready runs (sim built from FieldMap seed 11)
	m.set_process(false)           # only this test advances the sim; M _process uses the wall-clock delta
	if m.get("sim") == null or m.get("lots") == null:
		_check(false, "gap: the mockup scene instantiated without sim/lots after one frame")
		return false
	sim = m.sim
	var slope_note := _rederive_slope()
	m.qa_reset()                   # t = 0, rng seed 7, every cell dirty, one flush: a run independent of frame timing
	for k in GROW_STEPS:
		sim.update(STEP_DT)
	m._flush()
	var core: Vector2i = sim.core
	for k in DAMAGE_HITS:
		sim.damage(core + DAMAGE_OFFSET)
	for k in SETTLE_STEPS:
		sim.update(STEP_DT)
	var extra := 0
	while extra < EXTRA_SETTLE_MAX and _disc_anim_count() > 0:
		sim.update(STEP_DT)
		extra += 1
	m._flush()
	# Lots: every cell with state > 0 or rubble == 1 (never the state-0 cliff cells the mockup draws as 0.4 v boxes, S:311).
	lots = []
	var hs := PackedInt32Array()
	hs.resize(WIN * WIN)
	var walk := PackedByteArray()
	walk.resize(WIN * WIN)
	walk.fill(1)
	for i in WIN * WIN:
		hs[i] = roundi(sim.elev[i] * 100.0)
		if sim.state[i] > 0 or sim.rubble[i] == 1:
			var c := _cell(i)
			lots.append({"id": i, "x": (c.x + 0.5) * CELL_WU, "y": (c.y + 0.5) * CELL_WU, "stage": 0 if sim.rubble[i] == 1 else int(sim.state[i]), "building": 0, "owner": 0})
			idx_of[i] = lots.size() - 1
	terr = {"cells_w": WIN, "cells_h": WIN, "heights": hs, "walkable": walk, "slopes": []}
	for i in WIN * WIN:
		var c := _cell(i)
		if (c - core).length_squared() <= DISC_R * DISC_R and idx_of.has(i):
			disc.append(i)
			if sim.anims.has(i):
				animating[i] = true
	print("PREMISE mockup: seed %d, dt %.2f, grow steps %d, damage %d hits at core%s, settle %d + %d extra steps, t %.2f s" % [m.SEED, STEP_DT, GROW_STEPS, DAMAGE_HITS, str(DAMAGE_OFFSET), SETTLE_STEPS, extra, sim.t])
	print("PREMISE " + slope_note)
	print("PREMISE window origin (%d, %d) in the field map, core cell %s, window %d x %d, sim.counts() %s" % [sim.ox, sim.oy, str(core), WIN, WIN, str(sim.counts())])
	print("PREMISE disc: radius %d cells around the core, margin check x %d..%d y %d..%d (edge margin %d), %d lots in the disc of %d, %d disc cells animating at the read instant (excluded from box comparisons)" % [DISC_R, core.x - DISC_R, core.x + DISC_R, core.y - DISC_R, core.y + DISC_R, EDGE_MARGIN, disc.size(), lots.size(), animating.size()])
	var sl := load(LAYER)
	if not (sl is GDScript):
		_check(false, "missing script (the piece is not built): " + LAYER)
		return false
	layer = sl.new()
	root.add_child(layer)
	layer.set_terrain(terr)
	layer.set_frame({"lots": lots})   # the first frame after load snaps: read without driving _process
	var mmi := _find_mmi(layer)
	pmm = mmi.multimesh if mmi != null else null
	ready_fixture = pmm != null
	return true


# Premise found by running the scene (2026-10-13): the field map computes cell.slope at field_map.gd:76 and then cuts ramps
# and reacts the layout to the elevation (FM:106, :110), so the mockup's stored sim.slope no longer describes the final
# sim.elev it draws on (a perfect port, reading the final heights, disagrees on about a fifth of the disc). The port reads
# one terrain; so the fixture gives the mockup the same: sim.slope is re-derived from sim.elev by the FM formula
# (FM:380-402: mean |dh| over the orthogonal neighbours in the window, per SPACING, over PEAK_HEIGHT_WU * 0.25 / (SPACING * 2),
# clamped to 1; the constants are read from FieldMap), BEFORE the run, so growth, cliff and yaw all use it. The mockup's
# code is unchanged; only its slope input is made consistent. The count of changed classes is printed.
func _rederive_slope() -> String:
	var w := WIN
	var norm: float = FieldMap.PEAK_HEIGHT_WU * 0.25 / (FieldMap.SPACING * 2.0)
	var ns := PackedFloat32Array()
	ns.resize(w * w)
	var flip_cliff := 0
	var flip_contour := 0
	for gy in w:
		for gx in w:
			var i := gy * w + gx
			var h: float = sim.elev[i]
			var sum := 0.0
			var count := 0
			if gx > 0: sum += absf(h - sim.elev[i - 1]); count += 1
			if gx < w - 1: sum += absf(h - sim.elev[i + 1]); count += 1
			if gy > 0: sum += absf(h - sim.elev[i - w]); count += 1
			if gy < w - 1: sum += absf(h - sim.elev[i + w]); count += 1
			var avg: float = (sum / count) / FieldMap.SPACING if count > 0 else 0.0
			ns[i] = clampf(avg / norm, 0.0, 1.0)
			if (ns[i] > Sim.CLIFF_SLOPE) != (sim.slope[i] > Sim.CLIFF_SLOPE):
				flip_cliff += 1
			if (ns[i] > Sim.CONTOUR_SLOPE) != (sim.slope[i] > Sim.CONTOUR_SLOPE):
				flip_contour += 1
	sim.slope = ns
	return "slope re-derived from the final elevation (FM:76 stored it before ramps, FM:106/:110): %d of %d window cells change cliff class (> %.2f), %d change contour class (> %.2f)" % [flip_cliff, w * w, Sim.CLIFF_SLOPE, flip_contour, Sim.CONTOUR_SLOPE]


func _disc_anim_count() -> int:
	var n := 0
	var core: Vector2i = sim.core
	for i in WIN * WIN:
		if sim.anims.has(i) and (_cell(i) - core).length_squared() <= DISC_R * DISC_R:
			n += 1
	return n


func _run() -> void:
	if not await _build():
		return
	_p0_controls()
	_p1_premises()
	_p3_histogram()
	_lane_and_routes()
	_p6_constants()
	print("PREMISE wall time of the test: %.1f s" % [(Time.get_ticks_msec() - t_wall) / 1000.0])


func _p0_controls() -> void:
	var mm: MultiMesh = m.lots.multimesh
	var nonzero := 0
	for i in disc:
		if mm.get_instance_transform(i).basis.y.length() > 0.0:
			nonzero += 1
	_check(nonzero > 0 and nonzero == disc.size(), "[P0 control] the mockup's MultiMesh must carry a scaled box for each of the %d disc lots, got %d (the harness reads M _flush)" % [disc.size(), nonzero])
	var c: Dictionary = sim.counts()
	_check(int(c.stage1) + int(c.stage2) + int(c.stage3) + int(c.stage4) + int(c.cliff) + int(c.rubble) > 100, "[P0 control] sim.counts() must read a settlement after the run (got %s)" % [str(c)])
	# The skeleton or the built layer instantiates and draws one instance per lot of a hand-built frame.
	var sl := load(LAYER) as GDScript
	var probe: Node3D = sl.new()
	root.add_child(probe)
	var t := {"cells_w": 8, "cells_h": 8, "heights": PackedInt32Array(), "walkable": PackedByteArray(), "slopes": []}
	t["heights"].resize(64)
	t["walkable"].resize(64)
	probe.set_terrain(t)
	probe.set_frame({"lots": [{"id": 3, "x": 150.0, "y": 150.0, "stage": 2, "building": 0, "owner": 0}, {"id": 9, "x": 450.0, "y": 250.0, "stage": 4, "building": 0, "owner": 0}]})
	var pm := _find_mmi(probe)
	_check(pm != null and pm.multimesh != null and pm.multimesh.instance_count == 2 and probe.lots_drawn().size() == 2, "[P0 control] SettlementLayer must draw one MultiMesh instance per lot of a hand-built frame (2 lots)")
	probe.queue_free()


func _p1_premises() -> void:
	var core: Vector2i = sim.core
	_check(core.x - DISC_R >= EDGE_MARGIN and core.x + DISC_R <= WIN - 1 - EDGE_MARGIN and core.y - DISC_R >= EDGE_MARGIN and core.y + DISC_R <= WIN - 1 - EDGE_MARGIN, "[P2 premise] the disc around the core %s of radius %d must lie at least %d cells inside the %d window (the edge cells have fewer slope neighbours)" % [str(core), DISC_R, EDGE_MARGIN, WIN])
	_check(ready_fixture and pmm.instance_count == lots.size(), "[P1] R-193-01 'the same field map the landscape uses': the layer must draw one instance per lot of the mockup's density field (%d lots), got %d" % [lots.size(), pmm.instance_count if pmm != null else -1])
	# The window-wide mockup categories summed equal sim.counts() (control: the category function is the mockup's own).
	var cats := []
	for l in lots:
		cats.append(_cat_sim(int(l["id"])))
	var h := _hist(cats)
	var c: Dictionary = sim.counts()
	var cl := int(h.get("cliff1", 0)) + int(h.get("cliff2", 0)) + int(h.get("cliff3", 0))
	_check(int(h.get("stage1", 0)) == c.stage1 and int(h.get("stage2", 0)) == c.stage2 and int(h.get("stage3", 0)) == c.stage3 and int(h.get("stage4", 0)) == c.stage4 and cl == c.cliff and int(h.get("rubble", 0)) == c.rubble, "[P1 control] the lot list must reproduce sim.counts(): got %s vs %s" % [str(h), str(c)])


func _p3_histogram() -> void:
	var want := []
	for i in disc:
		want.append(_cat_sim(i))
	var want_h := _hist(want)
	var drawn: Array = layer.lots_drawn()
	var by_id := {}
	for d in drawn:
		by_id[int(d["id"])] = d
	var got := []
	for i in disc:
		got.append(_cat_port(by_id.get(i, {})))
	var got_h := _hist(got)
	print("PREMISE stage histogram, mockup (disc): %s" % [str(want_h)])
	print("PREMISE stage histogram, port   (disc): %s" % [str(got_h)])
	# Positive control: the disc holds every category the comparison is about.
	var cliffs := int(want_h.get("cliff1", 0)) + int(want_h.get("cliff2", 0)) + int(want_h.get("cliff3", 0))
	_check(int(want_h.get("stage1", 0)) > 0 and int(want_h.get("stage2", 0)) > 0 and int(want_h.get("stage3", 0)) > 0 and int(want_h.get("stage4", 0)) > 0 and int(want_h.get("rubble", 0)) > 0 and cliffs > 0, "[P3 control] the mockup disc must hold rubble, stages 1 to 4 and cliff dwellings, got %s" % [str(want_h)])
	_check(got_h == want_h, "[P3] R-193-05 'the lot rises through its stages' + Westley 'no perceptible difference in level between the buildings' + R-193-02 'inside a cliff, ... on a steep mountainside': the port's disc stage histogram must equal the mockup's. port %s vs mockup %s" % [str(got_h), str(want_h)])
	# Cliff decided by the port's slope (gap g1) against the mockup's is_cliff on the same cells, lot by lot.
	var bad := 0
	var first := ""
	for i in disc:
		var d: Dictionary = by_id.get(i, {})
		if bool(d.get("cliff", false)) != sim.is_cliff(i):
			bad += 1
			if first == "":
				first = "cell %s: port cliff=%s, mockup slope %.4f (is_cliff %s)" % [str(_cell(i)), str(d.get("cliff", "<no key>")), sim.slope[i], str(sim.is_cliff(i))]
	_check(bad == 0, "[P3] R-193-02 + gap g1 (field-map slope, CLIFF_SLOPE 0.22 S:19): the port's cliff flag must equal the mockup's is_cliff on every disc lot; %d of %d differ, first: %s" % [bad, disc.size(), first])
	# Drawn stage is the target stage with the cliff cap applied (S:20 CLIFF_MAX_STAGE).
	var badstage := 0
	for i in disc:
		var d: Dictionary = by_id.get(i, {})
		var want_stage := 0 if sim.rubble[i] == 1 else int(sim.state[i])
		if int(d.get("stage", -1)) != want_stage:
			badstage += 1
	_check(badstage == 0, "[P3] R-193-05: lots_drawn() stage must equal the mockup's state on every disc lot (cliff cap included); %d differ" % badstage)


func _lane_and_routes() -> void:
	# N9: the sim leaves lane cells without lots; the layer must not fill them in (R-193-09 'open streets ... by rule').
	var lanes := 0
	for i in WIN * WIN:
		lanes += int(sim.lane[i])
	_check(lanes > 0, "[N9 control] the mockup window must carry lane cells (S:35 LANE_PERIOD 4), got %d" % lanes)
	var in_lane := 0
	for d in layer.lots_drawn():
		if sim.lane[int(d["id"])] == 1:
			in_lane += 1
	_check(in_lane == 0 and layer.lots_drawn().size() == lots.size(), "[N9] R-193-09 'there are always natural paths through it': the layer must draw nothing on lane cells and no extra lot (drawn %d, lots %d, in lanes %d)" % [layer.lots_drawn().size(), lots.size(), in_lane])
	# Routes hidden by default as the mockup ships them (gap g4 (3): M:116 path_view.visible = false; DRAFT-e1k-streets).
	_check(m.path_view.visible == false, "[P0 control] the mockup's route mesh is hidden by default (M:116)")
	var shown := 0
	for mi in layer.find_children("*", "MeshInstance3D", true, false):
		if mi.visible:
			shown += 1
	_check(shown == 0, "[N9] R-193-09 + gap g4: any route mesh of the layer must be hidden by default, %d visible" % shown)


func _p6_constants() -> void:
	var L = load(LOOK) if ResourceLoader.exists(LOOK) else null
	var cm := {}
	if L is GDScript:
		cm = L.get_script_constant_map()
	# Prototype as run.
	var proto = Sim.new()
	var rows := [
		# [name, spec literal (NUMBERS), prototype as run, prototype file:line]
		["JITTER_CELLS", 0.22, Sim.JITTER_CELLS, "S:33 / M:248-249"],
		["YAW_JITTER", 0.25, Sim.YAW_JITTER, "S:34"],
		["CLIFF_SLOPE", 0.22, Sim.CLIFF_SLOPE, "S:19"],
		["CLIFF_MAX_STAGE", 3, Sim.CLIFF_MAX_STAGE, "S:20"],
		["CONTOUR_SLOPE", 0.06, Sim.CONTOUR_SLOPE, "S:32 (gap g2: not 0.22)"],
		["RISE_S", 0.9, Sim.RISE_S, "S:21"],
		["CELL_WU", 100.0, Sim.SPACING_WU, "S:6 (one mockup unit = one cell = 100 wu)"],
		["RUBBLE_COLOR", Color(0.28, 0.2, 0.18), proto._vis_of(0, 0, true)[2], "S:305-306"],
	]
	for r in rows:
		var name: String = r[0]
		var live = cm.get(name, null)
		_ctrl(_same(r[1], r[2]), "%s: the NUMBERS literal %s equals the prototype as run %s (%s)" % [name, str(r[1]), str(r[2]), r[3]])
		_check(live != null and _same(live, r[2]), "[P6] R-237-01 / Westley 'sister system': %s in settlement_look.gd must equal the prototype's %s (%s); live: %s" % [name, str(r[2]), r[3], "<missing: " + LOOK + ">" if L == null else str(live)])
	# Derived rows: V_BASE and V_SPAN from two as-run stage-2 heights (S:304, 315: height = 0.3 v), DEPTH_RATIO and SINK_UNITS
	# from the mockup's drawn transforms (M:251-252).
	var sl := PackedFloat32Array()
	sl.resize(WIN * WIN)
	proto.slope = sl
	var h1: float = proto._hash(7 + 11)
	var h2: float = proto._hash(24 + 11)
	var v1: float = proto._vis_of(7, 2, false)[0] / 0.3
	var v2: float = proto._vis_of(24, 2, false)[0] / 0.3
	var v_span: float = (v1 - v2) / (h1 - h2)
	var v_base: float = v1 - v_span * h1
	_ctrl(absf(v_base - 0.8) < EPS_D and absf(v_span - 0.5) < EPS_D, "V_BASE 0.8 and V_SPAN 0.5 (N1) equal the prototype as run (%f, %f) (S:304)" % [v_base, v_span])
	_check(cm.has("V_BASE") and absf(float(cm["V_BASE"]) - v_base) < EPS_D, "[P6] V_BASE in settlement_look.gd must equal the prototype's %f (S:304); live: %s" % [v_base, str(cm.get("V_BASE", "<missing>"))])
	_check(cm.has("V_SPAN") and absf(float(cm["V_SPAN"]) - v_span) < EPS_D, "[P6] V_SPAN in settlement_look.gd must equal the prototype's %f (S:304); live: %s" % [v_span, str(cm.get("V_SPAN", "<missing>"))])
	var depth := -1.0
	var sink := -99.0
	var mmq: MultiMesh = m.lots.multimesh
	for i in disc:
		if not animating.has(i) and sim.rubble[i] == 0 and sim.state[i] >= 2:
			var tr := mmq.get_instance_transform(i)
			depth = tr.basis.z.length() / tr.basis.x.length()
			sink = sim.elev[i] / 100.0 + tr.basis.y.length() * 0.5 - tr.origin.y
			break
	_ctrl(absf(depth - 0.85) < EPS_F32 and absf(sink - 0.12) < EPS_F32, "DEPTH_RATIO 0.85 and SINK_UNITS 0.12 (N5, N8) equal the mockup's drawn box (depth/width %f, sink %f) (M:251-252)" % [depth, sink])
	_check(cm.has("DEPTH_RATIO") and absf(float(cm["DEPTH_RATIO"]) - depth) < EPS_F32, "[P6] DEPTH_RATIO in settlement_look.gd must equal the mockup's drawn depth/width %f (M:251); live: %s" % [depth, str(cm.get("DEPTH_RATIO", "<missing>"))])
	_check(cm.has("SINK_UNITS") and absf(float(cm["SINK_UNITS"]) - sink) < EPS_F32, "[P6] SINK_UNITS in settlement_look.gd must equal the mockup's drawn sink %f (M:252); live: %s" % [sink, str(cm.get("SINK_UNITS", "<missing>"))])
	# Static functions: hash, lot key, jitter, vis table.
	var bad_hash := 0
	var bad_jit := 0
	var live_ok: bool = L is GDScript
	for i in HASH_IDS:
		if not live_ok or absf(float(L.hash01(i)) - float(proto._hash(i))) > EPS_D:
			bad_hash += 1
		var jx: float = (float(proto._hash(i + 3)) - 0.5) * 2.0 * Sim.JITTER_CELLS
		var jz: float = (float(proto._hash(i + 5)) - 0.5) * 2.0 * Sim.JITTER_CELLS
		if not live_ok or (L.jitter(i) as Vector2).distance_to(Vector2(jx, jz)) > EPS_D:
			bad_jit += 1
	_check(bad_hash == 0, "[P6] N1: settlement_look.gd hash01(i) must equal the prototype's _hash (S:137-138) for the %d probe ids; %d differ%s" % [HASH_IDS.size(), bad_hash, "" if live_ok else " (missing " + LOOK + ")"])
	_check(bad_jit == 0, "[P6] N6 position jitter: settlement_look.gd jitter(i) must equal ((hash(i+3)-0.5)*2*0.22, (hash(i+5)-0.5)*2*0.22) cells (S:33, M:248-249) for the %d probe ids; %d differ%s" % [HASH_IDS.size(), bad_jit, "" if live_ok else " (missing " + LOOK + ")"])
	_check(live_ok and L.lot_key({}, {"id": 4321}) == 4321, "[P6] gap g3: lot_key(t, lot) must be the sim lot id (the hash input), 4321 expected")
	var bad_vis := 0
	var first := ""
	var rows_n := 0
	for i in VIS_IDS:
		for s in 6:
			for cliff in [false, true]:
				if s == 0 and cliff:
					continue
				if cliff and (s == 0 or s > 3):
					continue   # cliff rows exist for stages 1 to 3: the caller applies the cap (S:20)
				var arr := PackedFloat32Array()
				arr.resize(WIN * WIN)
				arr[i] = 0.5 if cliff else 0.0
				proto.slope = arr
				var want: Array = proto._vis_of(i, s, s == 0)   # stage 5 reaches the default branch = the stage-4 row (gap g6, S:317)
				rows_n += 1
				var got: Array = L.vis(s, cliff, i) if live_ok else []
				if got.size() < 2 or absf(float(got[0]) - float(want[0])) > EPS_D or absf(float(got[1]) - float(want[1])) > EPS_D:
					bad_vis += 1
					if first == "":
						first = "vis(stage %d, cliff %s, id %d): live %s, prototype [%f, %f]" % [s, str(cliff), i, str(got), want[0], want[1]]
	_check(rows_n > 0 and bad_vis == 0, "[P6] R-193-05 + Westley 'no perceptible difference in level': vis(stage, cliff, id) = [height units, footprint] must equal S:303-317 on all %d rows; %d differ, first: %s%s" % [rows_n, bad_vis, first, "" if live_ok else " (missing " + LOOK + ")"])


func _same(a, b) -> bool:
	if a is float or b is float:
		return absf(float(a) - float(b)) < EPS_D
	return a == b


# A positive-control row: counted like any check, its result line is printed so the report can paste it.
func _ctrl(c: bool, msg: String) -> void:
	if c:
		print("CONTROL ok: " + msg)
	_check(c, "control: " + msg)
