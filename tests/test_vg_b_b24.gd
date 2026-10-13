extends SceneTree
# NEEDS A DISPLAY (the frame rows read pixels and MultiMesh transforms; FU-B22-pregate-display-b24, Architect 2026-10-13):
#   xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_b_b24.gd
# test-timeout: 20000

# Piece VG-B24-layout (docs/northstar/plans/2026-10-07-visible-game-spec.md, Rev 12d, paragraph "VG-B24-layout",
# lane B, with the paragraph "B23, the prototype's numbers exactly" and Rev 12b "B23." for what B23 sets).
# Proves (bible E-16, docs/bible/epics/E-16-client-camera-hud-and-world-view.md):
#   S-106 "A 3D star map where territory glows, borders touch, and war flashes."
#   S-107 "Pan, zoom, orbit, focus a system, pick out a faction."
#   R-106-01  "Given the world view, When drawn, Then each system is a luminous point sized by significance, brightest
#             for the player's core, dim neutral for uncolonized."
#   R-106-02  "Given faction territory, When drawn, Then adjacent same-faction systems are joined by faction-colored
#             luminous filament arcs in 3D (border and both edges solid and bright, trade edges thinner and dimmer), and
#             each faction's systems share one translucent shell; rival shells keep a visible gap with a bright seam
#             where they nearly meet."
#   R-106-03  "Given camera distance d, When d >= 37.5 (Overview), Then shells render at 40 to 60 percent opacity,
#             filaments dim, nodes shrink, faction names float at shell centers; When 20 <= d < 32.5 (Regional,
#             default), Then filaments dominate, shells at 8 to 15 percent, border seams are the accent; When d < 12.5
#             (Local), Then the focused system brightens, its filaments thicken, shells fade to ground fog, distant
#             systems desaturate; between bands properties interpolate continuously, inside a band they are locked."
#   R-107-01  "Given the world view, When the player left-drags, Then the camera pans; scroll zooms along the forward
#             axis; right-drag orbits; clicking a system centers on it and zooms to Local."
# Westley, 2026-10-12: "civilizations having random regions in the galaxy is dumb and against the rules ... most of the
#   time they congregate regionally" (relayed by the Architect: "outliers infrequent and short-lived").
# The spec paragraph VG-B24-layout, word for word: "Placement follows the sim graph: regions are placed in breadth-first
#   order from the region of highest degree (ties by lower id); each region goes at the centroid of its already-placed
#   neighbours plus a hashed direction at a distance drawn by hash from [11, 18] wu ..., rejected and re-hashed (up to 16
#   tries) when nearer than 11 wu to any placed region or outside the ball; then 20 relaxation passes (edges spring toward
#   13 wu, pairs under 11 wu repel), all from the seed, no engine RNG. A disconnected component starts at the hashed free
#   position farthest from placed regions. Significance is continuous: `sig = 0.3 + 0.5 * rank / (n - 1)` by region
#   capacity (ties by id) [DRAFT-b24-sig], replacing `SIGNIFICANCE_BY_TIER`. Parity test (frame, not constants): at seed 1
#   the sim-edge median lies in [11, 18]; no edge over 30 wu; the Overview frame's filament pixel coverage (pixels whose
#   max(R, G, B) is above 200, discs masked at their drawn radius, Forward+, fixture `origin/push/galaxy-field` 99f35887
#   seed 1, Overview at d25 = camera distance 25, target origin, default pitch) is at most 1.5 times the prototype's
#   [DRAFT-b24-filament-cover]; discs on screen at d25 (a disc counts when its projected centre is inside the viewport) at
#   least 18 (B23's measured count) and the measured number reported [DRAFT-b24-discs]".
# Architect gap rulings 2026-10-12 (ledger row DRAFT-b24-relax, TD-VG-B-16): G1 an optional edges parameter; G3 one shared
#   significance function, rank ascending by capacity (the highest capacity gets 0.8), the second tier table goes; G4 "the
#   root sits at the ball centre; after 16 failed tries the region takes the best of those 16 candidates by distance to its
#   nearest placed region; a disconnected component compares 32 hashed candidates"; G5 "per pass, each edge moves both ends
#   toward 13 wu by a quarter of the error, each pair under 11 wu is pushed apart by half the deficit, updates in ascending
#   id order, positions clamped to R_BALL minus 2"; G7 the frame rows (brightness max(R, G, B) above 200, the disc mask is
#   the circle of each system at its drawn radius, Forward+, the prototype at 99f35887 seed 1, "Overview" = camera
#   distance 25).
#   NOTE (spec :308 says "Overview at d25"): distance 25 is the Regional band (galaxy_view.gd BAND_SPLIT_LOW 16.25 and
#   BAND_SPLIT_HIGH 35; R-106-03 names it "Regional, default"). "Overview frame" here is the S-106 default frame at camera
#   distance 25, the frame Westley judged "Looks good" on 2026-10-12.
#
# A test whose behaviour no quoted rule states is not written. Rows and the words that state each one:
#   (1) median sim-edge length in [11, 18], (2) no sim edge over 30   : the spec paragraph, R-106-02 ("adjacent ... joined by ... arcs")
#   (3) no engine RNG                                                  : the spec paragraph ("all from the seed, no engine RNG"), CLAUDE.md determinism
#   (4) continuous significance                                        : R-106-01, DRAFT-b24-sig, G3
#   (5) disconnected components, G4 root and candidates                : the spec paragraph, G4
#   (6) ownership congregates                                          : Westley 2026-10-12 ("most of the time they congregate regionally")
#   (7) the ball                                                       : the spec paragraph ("outside the ball"), G5 (R_BALL minus 2)
#   (8) the graph is what is read                                      : the spec paragraph ("Placement follows the sim graph")
#   (9) frame parity                                                   : the spec paragraph (parity test), G7, R-106-03 ("filaments dominate")
# Gap reported, not tested: the exact candidate choice of a second component (G4 "compares 32 hashed candidates", G11
# the hash) is observed relationally (row 5), not pinned to the hash; layout caching (G2) has no observable in qa_state.
#
# Controls first (green today on the built tree, before the feature): the view instantiates with the 80-region fixture
# (80 regions and 88 edges asserted from the file) and qa_state reports 80 systems; the generator returns 80 positions for
# the 80 ids; the same call twice gives identical positions. Red until built: every row below, each with its stated reason.
# Row (6a) (mean same-owner distance below the all-pairs mean) is green today by chance (measured 52.2 against 52.5 at B23);
# row (6b) is the one that is red today.
#
# Layout interface used (INTERFACE of the brief, G1): `layout(ids, seed, edges)` with `edges` the snapshot's list of
# {a, b, t} dictionaries; until the third parameter exists, helper _layout() calls the two-argument form, so every row
# still measures what the tree does today and row (0) reports the missing parameter.
#
# Westley's thresholds (pixel tolerances 40 per channel / 0.60 fraction, 5 isolated samples, 5 colours, REFILL 12 ms,
# WIDTH_MIN 60 percent of the width, FIELD-EQ 2 percent) are not read or changed here. Every number below is the spec's, a
# named draft's (cited) or a gap ruling's (cited). Derived float compares (EPS) are not thresholds.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const GEN_PATH := "res://scenes/galaxy/galaxy_gen.gd"
const ADAPTER_PATH := "res://scenes/galaxy/galaxy_adapter.gd"
const VIEW_PATH := "res://scenes/galaxy/galaxy_view.gd"
const FIXTURE_SEED := 1
const REGIONS := 80
const EDGES := 88
const EDGE_MIN := 11.0            # spec VG-B24-layout: distance drawn from [11, 18] wu
const EDGE_MAX := 18.0
const EDGE_LONGEST := 30.0        # spec: "no edge over 30 wu"
const SIG_LOW := 0.3              # DRAFT-b24-sig: sig = 0.3 + 0.5 * rank / (n - 1)
const SIG_SPAN := 0.5
const BALL_CLAMP_MARGIN := 2.0    # DRAFT-b24-relax (G5): positions clamped to R_BALL minus 2
const BRIGHT := 200               # G7: brightness is max(R, G, B) above 200
const FILAMENT_COVER_MAX := 1.5   # DRAFT-b24-filament-cover: at most 1.5 times the prototype's
const DISCS_MIN := 18             # DRAFT-b24-discs: at least 18 (B23's measured count), the measured number reported
const PROTO_SHA := "99f3588754bd45a372a0d54337d9b51e5b7b8459"   # origin/push/galaxy-field, the approved prototype
const SINGLETON_SEEDS := 16       # rows (5c): seeds 1..16
const MEAN_RADIUS_FRACTION := 0.75   # mean radius of a uniform ball (r = R cbrt(u)) is 3/4 R: derived, not a threshold
const EPS := 0.001                # derived float compare, not a threshold

# The child process: opens the prototype's own scene (galaxy_mockup.tscn at PROTO_SHA, 217 systems and 398 edges at seed 1),
# seed 1, qa_camera(25) (target the origin, default pitch 55), hides the HUD, saves the frame and each dot's projected
# centre and drawn radius. Runs in a scratch project made from `git archive` of the prototype; nothing in this repo changes.
const PROTO_FRAME_GD := """extends SceneTree

func _hide_canvas(n: Node) -> void:
	if n is CanvasLayer:
		(n as CanvasLayer).visible = false
	for c in n.get_children():
		_hide_canvas(c)

func _find_mm(n: Node) -> MultiMeshInstance3D:
	if n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh != null and (n as MultiMeshInstance3D).multimesh.mesh is SphereMesh:
		return n
	for c in n.get_children():
		var r := _find_mm(c)
		if r != null:
			return r
	return null

func _initialize() -> void:
	var out_dir := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	var m: Node = (load("res://scenes/mockups/galaxy/galaxy_mockup.tscn") as PackedScene).instantiate()
	get_root().add_child(m)
	for i in 3:
		await process_frame
	m.qa_seed(1)
	for i in 3:
		await process_frame
	m.qa_camera(25.0, -1)
	_hide_canvas(m)
	for i in 8:
		await process_frame
	await RenderingServer.frame_post_draw
	var img := get_root().get_texture().get_image()
	img.save_png(out_dir + "/proto.png")
	var st: Dictionary = m.qa_state()
	var mmi := _find_mm(m)
	var cam: Camera3D = m.get_node("OrbitCamera/Camera3D")
	var discs := []
	if mmi != null:
		var mm := mmi.multimesh
		var rad: float = (mm.mesh as SphereMesh).radius
		for i in mm.instance_count:
			var t := mm.get_instance_transform(i)
			var c: Vector3 = t.origin
			if cam.is_position_behind(c):
				continue
			var r_world := rad * t.basis.x.length()
			var p := cam.unproject_position(c)
			var pe := cam.unproject_position(c + cam.global_transform.basis.x * r_world)
			discs.append([p.x, p.y, p.distance_to(pe)])
	var out := {"system_count": st["system_count"], "edge_counts": st["edge_counts"], "distance": st["distance"], "hash": st["hash"],
		"size": [img.get_width(), img.get_height()], "discs": discs, "method": RenderingServer.get_current_rendering_method()}
	var f := FileAccess.open(out_dir + "/proto.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	f.close()
	quit(0)
"""

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []
var _ctrl_pass := 0
var _ctrl_fail := 0


func _initialize() -> void:
	await _run()
	print("\n=== VG-B24 layout: PASS %d FAIL %d (controls %d green, %d red) ===" % [_pass, _fail, _ctrl_pass, _ctrl_fail])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])   # the summary line scripts/run_godot_tests.sh reads
	for m in _msgs:
		print("  - " + m)
	print("=== %s ===" % ("RED" if _fail > 0 else "GREEN"))
	quit(1 if _fail > 0 else 0)


func _check(c: bool, msg: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


# A positive-control row: counted like any check, its result line printed so the report can paste it.
func _ctrl(c: bool, msg: String) -> void:
	if c:
		_ctrl_pass += 1
		print("CONTROL ok: " + msg)
	else:
		_ctrl_fail += 1
	_check(c, "control: " + msg)


func _consts(path: String) -> Dictionary:
	return (load(path) as GDScript).get_script_constant_map()


func _frames(n: int) -> void:
	for _i in n:
		await process_frame


func _new_view(snap: Dictionary) -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await _frames(2)
	v.set_snapshot(snap)
	await _frames(3)
	return v


# True when galaxy_gen.layout takes the edges parameter (G1: the optional third parameter).
func _has_edges_param(gen: Object) -> bool:
	for m in gen.get_script().get_script_method_list():
		if m["name"] == "layout":
			return (m["args"] as Array).size() >= 3
	return false


# The layout through the G1 signature when it exists, else the two-argument form the tree has today.
func _layout(gen: Object, ids: Array, p_seed: int, edges: Array) -> Dictionary:
	if _has_edges_param(gen):
		return gen.layout(ids, p_seed, edges)
	return gen.layout(ids, p_seed)


func _sim_ids(snap: Dictionary) -> Array:
	var ids: Array = []
	for r in snap.get("regions", []):
		ids.append(int(r.get("i", -1)))
	ids.sort()
	return ids


func _edge_lengths(snap: Dictionary, pos: Dictionary) -> Array:
	var out: Array = []
	for e in snap.get("edges", []):
		out.append((pos[int(e["a"])] as Vector3).distance_to(pos[int(e["b"])]))
	out.sort()
	return out


func _median(sorted_vals: Array) -> float:
	var n := sorted_vals.size()
	if n == 0:
		return NAN
	if n % 2 == 1:
		return float(sorted_vals[n / 2])
	return (float(sorted_vals[n / 2 - 1]) + float(sorted_vals[n / 2])) * 0.5


func _min_pair(pos: Dictionary) -> float:
	var ids: Array = pos.keys()
	ids.sort()
	var m := INF
	for ai in ids.size():
		for bi in range(ai + 1, ids.size()):
			m = minf(m, (pos[ids[ai]] as Vector3).distance_to(pos[ids[bi]]))
	return m


func _r_max(pos: Dictionary) -> float:
	var m := 0.0
	for k in pos:
		m = maxf(m, (pos[k] as Vector3).length())
	return m


func _same(a: Dictionary, b: Dictionary) -> bool:
	if a.size() != b.size():
		return false
	for k in a:
		if not b.has(k) or not (a[k] as Vector3).is_equal_approx(b[k]):
			return false
	return true


# DRAFT-b24-sig: sig = 0.3 + 0.5 * rank / (n - 1), rank ascending by capacity, ties by id; n of 1 gives 0.3.
func _rank_sig(regions: Array) -> Dictionary:
	var rows: Array = []
	for r in regions:
		rows.append([float(r.get("capacity", 0.0)), int(r.get("i", -1))])
	rows.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	var out := {}
	for rank in rows.size():
		out[rows[rank][1]] = SIG_LOW + (SIG_SPAN * float(rank) / float(rows.size() - 1) if rows.size() > 1 else 0.0)
	return out


func _snap_with(snap: Dictionary, region_idx: Array, edges: Array) -> Dictionary:
	var s: Dictionary = snap.duplicate(true)
	var regs: Array = []
	for k in region_idx:
		regs.append((snap["regions"] as Array)[k].duplicate(true))
	s["regions"] = regs
	s["edges"] = edges
	return s


# Source text without comments, to scan for banned calls (a comment that says "no RandomNumberGenerator" is not a use).
func _code_only(path: String) -> String:
	var out := ""
	for line in FileAccess.get_file_as_string(path).split("\n"):
		var hash_at: int = line.find("#")
		out += (line if hash_at < 0 else line.substr(0, hash_at)) + "\n"
	return out


# ---- the frame rows (9) ----

# Every dot of a MultiMeshInstance3D as [x px, y px, radius px]: the instance origin projected, the radius the sphere is drawn at.
func _discs_of(mmi: MultiMeshInstance3D, cam: Camera3D) -> Array:
	var out: Array = []
	var mm: MultiMesh = mmi.multimesh
	var rad: float = (mm.mesh as SphereMesh).radius
	for i in mm.instance_count:
		var t := mm.get_instance_transform(i)
		if cam.is_position_behind(t.origin):
			continue
		var r_world := rad * t.basis.x.length()
		var p := cam.unproject_position(t.origin)
		var pe := cam.unproject_position(t.origin + cam.global_transform.basis.x * r_world)
		out.append([p.x, p.y, p.distance_to(pe)])
	return out


# Share of the frame's pixels whose max(R, G, B) is above BRIGHT (G7), outside every disc (the circle at its drawn radius).
func _coverage(img: Image, discs: Array) -> Dictionary:
	img.convert(Image.FORMAT_RGBA8)
	var w := img.get_width()
	var h := img.get_height()
	var masked := PackedByteArray()
	masked.resize(w * h)
	for d in discs:
		var cx: float = d[0]
		var cy: float = d[1]
		var r: float = d[2]
		var x0 := maxi(0, int(floor(cx - r)))
		var x1 := mini(w - 1, int(ceil(cx + r)))
		var y0 := maxi(0, int(floor(cy - r)))
		var y1 := mini(h - 1, int(ceil(cy + r)))
		for y in range(y0, y1 + 1):
			for x in range(x0, x1 + 1):
				var dx := float(x) + 0.5 - cx
				var dy := float(y) + 0.5 - cy
				if dx * dx + dy * dy <= r * r:
					masked[y * w + x] = 1
	var data := img.get_data()
	var bright := 0
	var unmasked := 0
	for i in w * h:
		if masked[i] == 1:
			continue
		unmasked += 1
		var o := i * 4
		if maxi(data[o], maxi(data[o + 1], data[o + 2])) > BRIGHT:
			bright += 1
	return {"bright": bright, "unmasked": unmasked, "total": w * h, "cover": float(bright) / float(w * h)}


func _hide_canvas(n: Node) -> void:
	if n is CanvasLayer:
		(n as CanvasLayer).visible = false
	for c in n.get_children():
		_hide_canvas(c)


# Runs the prototype in a child process (a scratch project from `git archive` of PROTO_SHA); returns
# {"ok": bool, "why": String, "json": Dictionary, "png": Image}.
func _run_prototype() -> Dictionary:
	var tmp := DirAccess.create_temp("om_b24_proto")
	if tmp == null:
		return {"ok": false, "why": "DirAccess.create_temp failed"}
	var dir := tmp.get_current_dir()
	var repo := ProjectSettings.globalize_path("res://").rstrip("/")
	var out: Array = []
	var code := OS.execute("sh", ["-c", "git -C '%s' archive %s scenes/mockups/galaxy scenes/mockups/_shared | tar -x -C '%s'" % [repo, PROTO_SHA, dir]], out, true)
	if code != 0:
		return {"ok": false, "why": "git archive of %s failed (exit %d): %s" % [PROTO_SHA, code, str(out)]}
	var pf := FileAccess.open(dir + "/project.godot", FileAccess.WRITE)
	pf.store_string("config_version=5\n\n[application]\n\nconfig/name=\"b24_proto\"\nconfig/features=PackedStringArray(\"4.6\", \"Forward Plus\")\n")
	pf.close()
	var gf := FileAccess.open(dir + "/frame.gd", FileAccess.WRITE)
	gf.store_string(PROTO_FRAME_GD)
	gf.close()
	var exe := OS.get_executable_path()
	out.clear()
	code = OS.execute("timeout", ["600", exe, "--headless", "--import", "--path", dir], out, true)
	if code != 0:
		return {"ok": false, "why": "prototype --import exit %d" % code}
	out.clear()
	code = OS.execute("timeout", ["600", exe, "--path", dir, "--resolution", "1920x1080", "--rendering-method", "forward_plus", "-s", "res://frame.gd", "--", "--out=" + dir], out, true)
	if code != 0 or not FileAccess.file_exists(dir + "/proto.json"):
		return {"ok": false, "why": "prototype frame run exit %d: %s" % [code, str(out).right(400)]}
	var j = JSON.parse_string(FileAccess.get_file_as_string(dir + "/proto.json"))
	var img := Image.load_from_file(dir + "/proto.png")
	if not (j is Dictionary) or img == null:
		return {"ok": false, "why": "prototype output unreadable"}
	return {"ok": true, "why": "", "json": j, "png": img}


func _in_viewport(px: Dictionary, vp: Vector2) -> int:
	var n := 0
	for k in px:
		var p = px[k]
		if p[0] >= 0.0 and p[0] <= vp.x and p[1] >= 0.0 and p[1] <= vp.y:
			n += 1
	return n


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_ctrl(snap is Dictionary, "fixture snapshot_seed1_tick10.json readable")
	if not (snap is Dictionary):
		return
	var ids := _sim_ids(snap)
	var edges: Array = snap.get("edges", [])
	_ctrl(ids.size() == REGIONS, "fixture file holds %d regions, want %d" % [ids.size(), REGIONS])
	_ctrl(edges.size() == EDGES, "fixture file holds %d edges, want %d" % [edges.size(), EDGES])

	# ---- positive controls: green today on the built tree ----
	var gen = load(GEN_PATH).new()
	var p1: Dictionary = _layout(gen, ids, FIXTURE_SEED, edges)
	var p2: Dictionary = _layout(gen, ids, FIXTURE_SEED, edges)
	_ctrl(p1.size() == REGIONS, "galaxy_gen layout returns %d positions for the %d ids, want %d" % [p1.size(), ids.size(), REGIONS])
	_ctrl(_same(p1, p2), "galaxy_gen layout twice with the same ids, seed and edges gives identical positions (determinism)")
	var view: Node = await _new_view(snap)
	var st: Dictionary = view.qa_state()
	_ctrl(int(st.get("system_count", -1)) == REGIONS, "the view instantiates with the fixture and qa_state.system_count is %s, want %d" % [st.get("system_count"), REGIONS])
	var vpos: Dictionary = view.get_positions()
	_ctrl(vpos.size() == REGIONS, "view.get_positions holds %d positions, want %d" % [vpos.size(), REGIONS])
	if vpos.size() != REGIONS:
		return

	# ---- premises dumped from this one run (the report pastes these lines) ----
	var lens := _edge_lengths(snap, vpos)
	var owner_of := {}
	var owner_n := {}
	for r in snap["regions"]:
		owner_of[int(r["i"])] = int(r["owner"])
		owner_n[int(r["owner"])] = int(owner_n.get(int(r["owner"]), 0)) + 1
	var sig_now: Dictionary = st.get("shell_renderer", {}).get("significance", {})
	var sig_vals: Array = sig_now.values()
	sig_vals.sort()
	var comps := _components(ids, edges)
	print("PREMISES regions=%d edges=%d components=%d owners=%s median_edge=%.3f max_edge=%.3f min_pair=%.3f r_max=%.3f layout_fallbacks=%s hash=%s distance=%s band=%s rendering=%s" % [
		ids.size(), edges.size(), comps, str(owner_n), _median(lens), lens[lens.size() - 1], _min_pair(vpos), _r_max(vpos),
		st.get("layout_fallbacks"), st.get("hash"), st.get("distance"), st.get("band"), RenderingServer.get_current_rendering_method()])
	print("PREMISES qa_state keys used: system_count, systems_px, hash, layout_fallbacks, distance, band, owners, shell_renderer.significance (%d values, distinct %d, low %s, high %s)" % [
		sig_vals.size(), _distinct(sig_vals), str(sig_vals.slice(0, 3)), str(sig_vals.slice(-3))])

	# ---- (0) interface: the optional edges parameter (G1) ----
	_check(_has_edges_param(gen), "VG-B24 (0): galaxy_gen.layout has no third (edges) parameter; its signature is layout(region_ids, p_seed) (G1, Architect 2026-10-12: an optional edges parameter)")

	# ---- (1) and (2): the view's layout on the fixture at seed 1, wired through galaxy_view _relayout ----
	var med := _median(lens)
	_check(med >= EDGE_MIN and med <= EDGE_MAX,
		"VG-B24 (1): sim-edge median %.3f wu at seed %d (view, fixture edges), want in [%s, %s] (spec VG-B24-layout; prototype median 13.07)" % [med, FIXTURE_SEED, EDGE_MIN, EDGE_MAX])
	var longest: float = lens[lens.size() - 1]
	var over := 0
	for l in lens:
		if l > EDGE_LONGEST:
			over += 1
	_check(over == 0, "VG-B24 (2): %d of %d sim edges are longer than %s wu (longest %.3f), want none (spec VG-B24-layout: no edge over 30 wu)" % [over, lens.size(), EDGE_LONGEST, longest])

	# ---- (3) no engine RNG in the generator (read the file text, comments stripped) ----
	var code := _code_only(GEN_PATH)
	for banned in ["RandomNumberGenerator", "randf", "randi"]:
		_check(code.find(banned) < 0, "VG-B24 (3): galaxy_gen.gd code uses %s; the spec says all from the seed, no engine RNG" % banned)

	# ---- (4) continuous significance through qa_state shell_renderer.significance (R-106-01, DRAFT-b24-sig, G3) ----
	var want_sig := _rank_sig(snap["regions"])
	var bad := 0
	var first_bad := ""
	for k in want_sig:
		var got = sig_now.get(k, null)
		if got == null or absf(float(got) - float(want_sig[k])) > 1.0e-5:
			bad += 1
			if first_bad == "":
				first_bad = "region %d has %s, want %.5f" % [k, str(got), float(want_sig[k])]
	_check(bad == 0, "VG-B24 (4): %d of %d regions have a significance other than 0.3 + 0.5 * rank / (n - 1) by capacity, ties by id (DRAFT-b24-sig); first: %s" % [bad, want_sig.size(), first_bad])
	var lowest := -1
	var highest := -1
	var lo_cap := INF
	var hi_cap := -INF
	for r in snap["regions"]:
		var cap := float(r["capacity"])
		if cap < lo_cap or (cap == lo_cap and int(r["i"]) < lowest):
			lo_cap = cap
			lowest = int(r["i"])
		if cap > hi_cap:
			hi_cap = cap
			highest = int(r["i"])
	_check(sig_now.has(lowest) and absf(float(sig_now[lowest]) - 0.3) < 1.0e-5,
		"VG-B24 (4): the lowest-capacity region %d (capacity %.2f) has significance %s, want 0.3" % [lowest, lo_cap, str(sig_now.get(lowest, null))])
	_check(sig_now.has(highest) and absf(float(sig_now[highest]) - 0.8) < 1.0e-5,
		"VG-B24 (4): the highest-capacity region %d (capacity %.2f) has significance %s, want 0.8 (G3: the highest capacity gets 0.8)" % [highest, hi_cap, str(sig_now.get(highest, null))])
	_check(_distinct(sig_vals) == REGIONS, "VG-B24 (4): %d distinct significance values over %d regions, want %d (rank gives one value per region, even on equal capacity)" % [_distinct(sig_vals), REGIONS, REGIONS])
	# ties by id: the neutral regions share capacity 0.0 on the fixture, so their significance must rise with the id
	var tie_ids: Array = []
	for r in snap["regions"]:
		if float(r["capacity"]) == lo_cap:
			tie_ids.append(int(r["i"]))
	tie_ids.sort()
	var tie_ok := tie_ids.size() > 1
	for i in range(1, tie_ids.size()):
		if not (sig_now.has(tie_ids[i]) and sig_now.has(tie_ids[i - 1]) and float(sig_now[tie_ids[i]]) > float(sig_now[tie_ids[i - 1]])):
			tie_ok = false
	_check(tie_ok, "VG-B24 (4): %d regions share capacity %.2f; their significance must rise strictly with the id (ties by id), it does not" % [tie_ids.size(), lo_cap])
	# one region and two regions: 0.3, and (0.3, 0.8), no division by zero
	var one_view: Node = await _new_view(_snap_with(snap, [0], []))
	var one_sig: Dictionary = one_view.qa_state().get("shell_renderer", {}).get("significance", {})
	_check(one_sig.size() == 1 and absf(float(one_sig.values()[0]) - 0.3) < 1.0e-5, "VG-B24 (4): a one-region snapshot gives significance %s, want {0.3} (n of 1: no division by zero)" % str(one_sig))
	one_view.queue_free()
	var two_snap := _snap_with(snap, [0, 1], [])
	var two_view: Node = await _new_view(two_snap)
	var two_sig: Dictionary = two_view.qa_state().get("shell_renderer", {}).get("significance", {})
	var two_want := _rank_sig(two_snap["regions"])
	var two_ok := two_sig.size() == 2
	for k in two_want:
		two_ok = two_ok and two_sig.has(k) and absf(float(two_sig[k]) - float(two_want[k])) < 1.0e-5
	_check(two_ok, "VG-B24 (4): a two-region snapshot gives significance %s, want %s (0.3 for the lower capacity, 0.8 for the higher)" % [str(two_sig), str(two_want)])
	two_view.queue_free()
	# the tier tables are gone (G3: one shared function; the second tier table goes)
	_check(not _consts(ADAPTER_PATH).has("SIGNIFICANCE_BY_TIER"), "VG-B24 (4): galaxy_adapter.gd still has the SIGNIFICANCE_BY_TIER constant (DRAFT-b24-sig: replaced)")
	_check(not _consts(VIEW_PATH).has("TIER_SIGNIFICANCE"), "VG-B24 (4): galaxy_view.gd still has the TIER_SIGNIFICANCE constant (G3: the second tier table goes)")

	# ---- (5) disconnected components (spec: a component starts at a hashed free position; G4) ----
	var r_ball := float(_consts(GEN_PATH).get("R_BALL", 50.0))
	var min_spacing := float(_consts(GEN_PATH).get("MIN_SPACING", 11.0))
	# two components of ten regions: a star (hub 0, leaves 1..9) and a path (10..19)
	var two_ids: Array = range(20)
	var two_edges: Array = []
	for i in range(1, 10):
		two_edges.append({"a": 0, "b": i, "t": 0})
	for i in range(10, 19):
		two_edges.append({"a": i, "b": i + 1, "t": 0})
	var gen2 = load(GEN_PATH).new()
	var two_pos: Dictionary = _layout(gen2, two_ids, FIXTURE_SEED, two_edges)
	_check(two_pos.size() == 20, "VG-B24 (5): two components of ten regions: %d of 20 regions placed" % two_pos.size())
	if two_pos.size() == 20:
		var mp := _min_pair(two_pos)
		_check(mp >= min_spacing - EPS, "VG-B24 (5): two components of ten: minimum pairwise distance %.4f, want >= MIN_SPACING %s (no two regions nearer; the spec: pairs under 11 wu repel; EPS is float noise only)" % [mp, min_spacing])
	_check(int(gen2.last_fallbacks()) == 0, "VG-B24 (5): two components of ten: layout_fallbacks %s, want 0" % gen2.last_fallbacks())
	# an edgeless graph: every region placed, spacing kept
	var free_ids: Array = range(30)
	var gen3 = load(GEN_PATH).new()
	var free_pos: Dictionary = _layout(gen3, free_ids, FIXTURE_SEED, [])
	_check(free_pos.size() == 30, "VG-B24 (5): a graph with no edges: %d of 30 regions placed" % free_pos.size())
	if free_pos.size() == 30:
		_check(_min_pair(free_pos) >= min_spacing - EPS, "VG-B24 (5): a graph with no edges: minimum pairwise distance %.4f, want >= MIN_SPACING %s (EPS is float noise only)" % [_min_pair(free_pos), min_spacing])
	# G4: "the root sits at the ball centre": a lone region (no edges, no relaxation target) sits exactly there
	var gen4 = load(GEN_PATH).new()
	var lone: Dictionary = _layout(gen4, [5], FIXTURE_SEED, [])
	_check(lone.has(5) and (lone[5] as Vector3).length() <= EPS, "VG-B24 (5): a lone region sits at %s, want the ball centre (0, 0, 0) (G4: the root sits at the ball centre)" % str(lone.get(5, null)))
	# G4: a second component compares 32 hashed candidates and keeps the one farthest from the placed regions (spec: "the
	# hashed free position farthest from placed regions"): over SINGLETON_SEEDS seeds the second of two edgeless regions never
	# lands closer to the first than the mean radius of a uniform ball (3/4 R_BALL, derived), where one hashed draw would
	# often land nearer
	var nearest := INF
	for s in range(1, SINGLETON_SEEDS + 1):
		var gen5 = load(GEN_PATH).new()
		var two_free: Dictionary = _layout(gen5, [3, 7], s, [])
		if two_free.size() == 2:
			nearest = minf(nearest, (two_free[3] as Vector3).distance_to(two_free[7]))
		else:
			nearest = -1.0
			break
	_check(nearest >= MEAN_RADIUS_FRACTION * r_ball,
		"VG-B24 (5): over seeds 1..%d the second of two edgeless regions came as near as %.3f to the first, want >= %.2f (3/4 R_BALL: the farthest of 32 hashed candidates, G4)" % [SINGLETON_SEEDS, nearest, MEAN_RADIUS_FRACTION * r_ball])

	# ---- (6) ownership congregates (Westley 2026-10-12; relational, no number) ----
	var same_sum := 0.0
	var same_n := 0
	var all_sum := 0.0
	var all_n := 0
	for ai in ids.size():
		for bi in range(ai + 1, ids.size()):
			var d: float = (vpos[ids[ai]] as Vector3).distance_to(vpos[ids[bi]])
			all_sum += d
			all_n += 1
			if owner_of[ids[ai]] >= 0 and owner_of[ids[ai]] == owner_of[ids[bi]]:
				same_sum += d
				same_n += 1
	var same_mean := same_sum / float(same_n)
	var all_mean := all_sum / float(all_n)
	_check(same_mean < all_mean, "VG-B24 (6a): mean distance between same-owner regions %.3f, mean over all pairs %.3f; same-owner pairs must be nearer (Westley: they congregate regionally)" % [same_mean, all_mean])
	# (6b): an owned region's nearest region has the same owner more often than owner sizes alone would give by chance
	var nn_same := 0
	var owned := 0
	var chance := 0.0
	for a in ids:
		if owner_of[a] < 0:
			continue
		owned += 1
		chance += float(int(owner_n[owner_of[a]]) - 1) / float(ids.size() - 1)
		var best := -1
		var best_d := INF
		for b in ids:
			if b != a and (vpos[a] as Vector3).distance_to(vpos[b]) < best_d:
				best_d = (vpos[a] as Vector3).distance_to(vpos[b])
				best = b
		if owner_of[best] == owner_of[a]:
			nn_same += 1
	var nn_frac := float(nn_same) / float(owned)
	var chance_frac := chance / float(owned)
	print("PREMISES ownership: same_owner_mean=%.3f all_pairs_mean=%.3f nearest_same_owner=%.4f chance=%.4f" % [same_mean, all_mean, nn_frac, chance_frac])
	_check(nn_frac > chance_frac, "VG-B24 (6b): %.1f percent of owned regions have a same-owner nearest region, chance level %.1f percent; they must congregate (Westley: most of the time)" % [nn_frac * 100.0, chance_frac * 100.0])

	# ---- (7) the ball: every position inside R_BALL (spec) and inside R_BALL minus 2 (DRAFT-b24-relax, G5 clamp) ----
	var rmax := _r_max(vpos)
	_check(rmax <= r_ball + EPS, "VG-B24 (7): farthest region %.3f from the origin, want <= R_BALL %s" % [rmax, r_ball])
	_check(rmax <= r_ball - BALL_CLAMP_MARGIN + EPS, "VG-B24 (7): farthest region %.3f from the origin, want <= R_BALL - 2 = %s (DRAFT-b24-relax, G5: positions clamped to R_BALL minus 2)" % [rmax, r_ball - BALL_CLAMP_MARGIN])
	for s in [2, 3]:
		var gs = load(GEN_PATH).new()
		var ps: Dictionary = _layout(gs, ids, s, edges)
		_check(_r_max(ps) <= r_ball - BALL_CLAMP_MARGIN + EPS, "VG-B24 (7): seed %d, fixture edges: farthest region %.3f, want <= R_BALL - 2 = %s (G5 clamp)" % [s, _r_max(ps), r_ball - BALL_CLAMP_MARGIN])

	# ---- (8) the graph is what is read: removing every edge changes the layout ----
	var bare: Dictionary = _layout(gen, ids, FIXTURE_SEED, [])
	_check(not _same(bare, p1), "VG-B24 (8): galaxy_gen.layout gives the same 80 positions with and without the fixture's 88 edges (the layout is edge-blind)")
	var bare_view: Node = await _new_view(_snap_with(snap, range(REGIONS), []))
	var bare_hash = bare_view.qa_state().get("hash")
	_check(bare_hash != st.get("hash"), "VG-B24 (8): the view's qa_state.hash is %s with and without the fixture's edges (the view's layout is edge-blind: _relayout does not pass the edges)" % str(bare_hash))
	bare_view.queue_free()

	# ---- (9) FRAME PARITY, measured in this run: the prototype in a child process, the game here ----
	await _frame_rows(snap, view)
	view.queue_free()


# Number of connected components of the sim graph.
func _components(ids: Array, edges: Array) -> int:
	var parent := {}
	for i in ids:
		parent[i] = i
	for e in edges:
		var a := int(e["a"])
		var b := int(e["b"])
		while parent[a] != a:
			a = parent[a]
		while parent[b] != b:
			b = parent[b]
		if a != b:
			parent[a] = b
	var roots := {}
	for i in ids:
		var r: int = i
		while parent[r] != r:
			r = parent[r]
		roots[r] = true
	return roots.size()


func _distinct(vals: Array) -> int:
	var seen := {}
	for v in vals:
		seen[snappedf(float(v), 1.0e-6)] = true
	return seen.size()


func _frame_rows(snap: Dictionary, view: Node) -> void:
	var vp := Vector2(get_root().size)
	var method := RenderingServer.get_current_rendering_method()
	_ctrl(method == "forward_plus", "the frame rows run under Forward+ (G7), rendering method is %s" % method)
	_ctrl(vp == Vector2(1920.0, 1080.0), "the viewport is 1920x1080, it is %s" % str(vp))
	var proto := _run_prototype()
	_ctrl(bool(proto["ok"]), "the prototype at %s runs in a child process and writes its frame: %s" % [PROTO_SHA, str(proto["why"])])
	# the game frame: default pitch, target the origin, camera distance 25 (the Overview frame of the spec, Regional band)
	view.qa_camera(25.0, -1)
	_hide_canvas(view)
	await _frames(8)
	await RenderingServer.frame_post_draw
	var img := get_root().get_texture().get_image()
	var rig = view.get_node_or_null("OrbitCamera")
	var cam: Camera3D = rig.get_camera() if rig != null else null
	var points: MultiMeshInstance3D = view.get_node_or_null("World/Points")
	_ctrl(cam != null and points != null and points.multimesh != null and points.multimesh.mesh is SphereMesh, "the view has an OrbitCamera and World/Points with a SphereMesh MultiMesh")
	if cam == null or points == null or points.multimesh == null:
		return
	var qs: Dictionary = view.qa_state()
	_ctrl(absf(float(qs.get("distance", -1.0)) - 25.0) < 0.001, "the game frame is at camera distance %s, want 25" % str(qs.get("distance")))
	var game_discs := _discs_of(points, cam)
	var game_cov := _coverage(img, game_discs)
	var on_screen := _in_viewport(qs.get("systems_px", {}), vp)
	_ctrl(img.get_width() == 1920 and img.get_height() == 1080 and game_cov["bright"] >= 0, "the game frame is %dx%d" % [img.get_width(), img.get_height()])
	# discs on screen: the measured number is reported either way
	print("PREMISES frame game: discs_on_screen=%d (centre inside the viewport, qa_state.systems_px), drawn_discs=%d, bright_pixels=%d of %d (outside the discs: %d), cover=%.6f" % [
		on_screen, game_discs.size(), game_cov["bright"], game_cov["total"], game_cov["unmasked"], game_cov["cover"]])
	_check(on_screen >= DISCS_MIN, "VG-B24 (9) discs: %d discs on screen at d25 (projected centre inside the viewport), want at least %d (DRAFT-b24-discs: B23's measured count)" % [on_screen, DISCS_MIN])
	if not bool(proto["ok"]):
		_check(false, "VG-B24 (9) filament coverage: the prototype frame could not be measured: %s" % str(proto["why"]))
		return
	var pj: Dictionary = proto["json"]
	var proto_discs: Array = pj["discs"]
	var proto_cov := _coverage(proto["png"], proto_discs)
	var proto_on_screen := 0
	for d in proto_discs:
		if d[0] >= 0.0 and d[0] <= vp.x and d[1] >= 0.0 and d[1] <= vp.y:
			proto_on_screen += 1
	print("PREMISES frame prototype: systems=%s edges=%s distance=%s method=%s discs_on_screen=%d, bright_pixels=%d of %d (outside the discs: %d), cover=%.6f" % [
		str(pj["system_count"]), str(pj["edge_counts"]), str(pj["distance"]), str(pj["method"]), proto_on_screen,
		proto_cov["bright"], proto_cov["total"], proto_cov["unmasked"], proto_cov["cover"]])
	_ctrl(int(pj["system_count"]) > 0 and float(pj["distance"]) == 25.0 and proto_cov["bright"] > 0, "the prototype frame has %s systems at distance %s and %d bright pixels" % [str(pj["system_count"]), str(pj["distance"]), proto_cov["bright"]])
	if proto_cov["cover"] <= 0.0:
		return
	var ratio: float = game_cov["cover"] / proto_cov["cover"]
	print("PREMISES frame ratio: game cover %.6f / prototype cover %.6f = %.4f" % [game_cov["cover"], proto_cov["cover"], ratio])
	_check(ratio <= FILAMENT_COVER_MAX, "VG-B24 (9) filament coverage: game %.6f is %.3f times the prototype's %.6f at d25, want at most %s (DRAFT-b24-filament-cover)" % [game_cov["cover"], ratio, proto_cov["cover"], FILAMENT_COVER_MAX])
