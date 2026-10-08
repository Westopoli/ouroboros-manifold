extends SceneTree

# Lane B piece B3b tests (docs/northstar/plans/2026-10-07-visible-game-spec.md lane B; preflight 3-galaxy-field.md
# "B3b: faction labels and stand-in"). Story S-106 (E-16): R-106-03 (shell opacity by zoom band 0.50 / 0.12 / 0.05,
# faction names shown in the overview band only). Look approved 2026-10-07 (the mockup on origin/push/galaxy-field).
#
# Subject: res://scenes/galaxy/shell_renderer.gd (B3a creates it by copying the mockup's shell_renderer.gd; B3b is its
# faction Label3Ds and its Compatibility-renderer flat stand-in). Public surface this test FIXES (all from the mockup):
#   setup(data: Node, zoom_controller: Node); teardown(); get_faction_shell_count() -> int;
#   get_shell_viewport() -> SubViewport (null in the stand-in); get_territory_field() -> Node (null in the stand-in).
#   data node: signals territory_set / territory_updated / territory_removed (region_id), regions_cleared();
#   get_territory(id) -> {center: Vector3, radius: float, color: Color}; get_region(id) -> {faction_id: String, ...}.
#   zoom controller: vars current_band ("overview"|"regional"|"local"), blend_factor, blend_direction ("up"|"down"|"none").
# Faction identity is the territory colour. One Label3D child per faction; label text is get_region(...).faction_id with
# "_" replaced by " " and capitalised; label alpha follows the band (1.0 overview, lerp to 0 on a down blend, 0 otherwise).
# Stand-in (rendering method gl_compatibility): no field, no SubViewport, one MeshInstance3D per faction, mix-blended unshaded
# material whose alpha is band opacity x STAND_IN_OPACITY_MULTIPLIER (shell_labels.gd, 0.15). Field mode: one MeshInstance3D total.
# Pinned here though the mockup uses GalaxyGen constants that scenes/galaxy lacks: only the label offset DIRECTION (above
# the centroid), never its size (B4 retunes the scale).
#
# The stand-in proof needs the Compatibility renderer, which needs a display: when this runs under another renderer it
# re-launches itself with --rendering-method gl_compatibility (needs DISPLAY; run under `xvfb-run -a`). No display = FAIL.
# iGPU cost: the child prints an IGPU-COST line (adapter name, median frame ms with and without the renderer, 80 regions /
# 15 factions at 1920x1080); no threshold is asserted (nobody gave one), the number goes in the report.

const SHELL := "res://scenes/galaxy/shell_renderer.gd"
const STAND_IN_LABELS := "res://scenes/galaxy/shell_labels.gd"
# Read from the script constant, never a literal (rulings 2026-10-08 retired 1.8).
func _stand_in_mult() -> float:
	var c: Dictionary = load(STAND_IN_LABELS).get_script_constant_map()
	return float(c.get("STAND_IN_OPACITY_MULTIPLIER", 0.0))


var _pass := 0
var _fail := 0
var _msgs: Array[String] = []
var _cur := ""
var _child := false


class FakeData extends Node:
	signal territory_set(region_id: String)
	signal territory_updated(region_id: String)
	signal territory_removed(region_id: String)
	signal regions_cleared()
	var territories := {}
	var regs := {}

	func put(id: String, faction: String, center: Vector3, color: Color) -> void:
		var existed := territories.has(id)
		territories[id] = {"center": center, "radius": 6.0, "color": color}
		regs[id] = {"faction_id": faction}
		if existed:
			territory_updated.emit(id)
		else:
			territory_set.emit(id)

	func drop(id: String) -> void:
		territories.erase(id)
		territory_removed.emit(id)

	func wipe() -> void:
		territories.clear()
		regs.clear()
		regions_cleared.emit()

	func get_territory(id: String) -> Dictionary:
		return territories.get(id, {})

	func get_region(id: String) -> Dictionary:
		return regs.get(id, {})


class FakeZoom extends Node:
	var current_band := "regional"
	var blend_factor := 0.0
	var blend_direction := "none"


func _initialize() -> void:
	_child = "--child" in OS.get_cmdline_user_args()
	_run.call_deferred()


func _check(cond: bool, msg: String) -> void:
	if cond:
		_pass += 1
	else:
		_fail += 1
		_msgs.append("[%s] %s" % [_cur, msg])


func _near(a: float, b: float, eps := 0.005) -> bool:
	return absf(a - b) <= eps


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _make() -> Array:
	var script: GDScript = load(SHELL)
	if script == null:
		return []
	var r: Node = script.new()
	var data := FakeData.new()
	var zoom := FakeZoom.new()
	root.add_child(data)
	root.add_child(zoom)
	root.add_child(r)
	r.setup(data, zoom)
	return [r, data, zoom]


func _kill(parts: Array) -> void:
	parts[0].teardown()
	for n in parts:
		n.queue_free()


func _labels(r: Node) -> Array:
	return r.get_children().filter(func(c): return c is Label3D)


func _meshes(r: Node) -> Array:
	return r.find_children("*", "MeshInstance3D", true, false)


func _run() -> void:
	var stand_in := RenderingServer.get_current_rendering_method() == "gl_compatibility"
	_cur = "B3b-exists"
	_check(ResourceLoader.exists(SHELL), "S-106 R-106-03: %s does not exist; B3b (faction labels + Compatibility stand-in) is not built" % SHELL)
	if ResourceLoader.exists(SHELL):
		await _labels_checks()
		await _opacity_table(stand_in)
		if stand_in:
			await _stand_in_checks()
			if _child:
				await _igpu_cost()
		else:
			await _field_mode_checks()
	if not stand_in and not _child:
		_cur = "B3b-stand-in-proof"
		_run_child()
	_finish()


func _labels_checks() -> void:
	_cur = "B3b-labels"
	var p := _make()
	var r: Node = p[0]
	var d: FakeData = p[1]
	var z: FakeZoom = p[2]
	var red := Color(0.9, 0.1, 0.1)
	var blue := Color(0.1, 0.2, 0.9)
	var green := Color(0.1, 0.8, 0.2)
	d.put("r1", "iron_pact", Vector3(0, 0, 0), red)
	d.put("r2", "iron_pact", Vector3(10, 0, 20), red)
	d.put("b1", "sea_league", Vector3(50, 4, 0), blue)
	d.put("b2", "sea_league", Vector3(60, 4, 10), blue)
	d.put("g1", "free_towns", Vector3(-40, 0, 30), green)
	await _frames(2)
	_check(r.get_faction_shell_count() == 3, "5 regions in 3 colours: faction count %d, want 3" % r.get_faction_shell_count())
	var labs := _labels(r)
	_check(labs.size() == 3, "one Label3D per faction: %d, want 3" % labs.size())
	var texts: Array = labs.map(func(l): return l.text)
	texts.sort()
	_check(texts == ["Free Towns", "Iron Pact", "Sea League"], "label texts %s, want faction_id with underscores spaced and capitalised" % [texts])
	for l: Label3D in labs:
		_check(l.billboard == BaseMaterial3D.BILLBOARD_ENABLED, "label '%s' must billboard" % l.text)
		_check(l.no_depth_test, "label '%s' must draw over the shells (no_depth_test)" % l.text)
	var iron := labs.filter(func(l): return l.text == "Iron Pact")
	if iron.size() == 1:
		var l: Label3D = iron[0]
		_check(_near(l.position.x, 5.0, 0.01) and _near(l.position.z, 10.0, 0.01), "Iron Pact label x/z at the centroid (5,10): %s" % [l.position])
		_check(l.position.y > 0.0, "Iron Pact label sits above the centroid y=0: %s" % [l.position])
		_check(l.outline_modulate.r < red.r and l.outline_modulate.g <= red.g and l.outline_modulate.b <= red.b + 0.001, "label outline is a darker shade of the faction colour: %s" % [l.outline_modulate])
	else:
		_check(false, "exactly one 'Iron Pact' label expected, got %d" % iron.size())
	# R-106-03: names show in the overview band only.
	var alphas := {}
	for case in [["overview", 0.0, "none", 1.0], ["overview", 0.25, "down", 0.75], ["overview", 1.0, "down", 0.0],
			["regional", 0.0, "none", 0.0], ["regional", 0.5, "down", 0.0], ["local", 0.0, "none", 0.0]]:
		z.current_band = case[0]
		z.blend_factor = case[1]
		z.blend_direction = case[2]
		await _frames(2)
		for l: Label3D in _labels(r):
			_check(_near(l.modulate.a, case[3]), "label alpha in %s blend %.2f %s: %.3f, want %.3f" % [case[0], case[1], case[2], l.modulate.a, case[3]])
	# Positive control: the labels really change between bands (a flat-zero reading would pass every row above but one).
	z.current_band = "overview"
	z.blend_factor = 0.0
	z.blend_direction = "none"
	await _frames(2)
	var shown := _labels(r).filter(func(l): return l.modulate.a > 0.9).size()
	z.current_band = "local"
	await _frames(2)
	var hidden := _labels(r).filter(func(l): return l.modulate.a < 0.1).size()
	_check(shown == 3 and hidden == 3, "control: 3 labels visible in overview then 3 hidden in local, got %d / %d" % [shown, hidden])
	# Conquest: the only green region turns blue, so the green faction (and its label) goes away.
	d.put("g1", "sea_league", Vector3(-40, 0, 30), blue)
	await _frames(2)
	_check(r.get_faction_shell_count() == 2, "after recolour: faction count %d, want 2" % r.get_faction_shell_count())
	var live := _labels(r).filter(func(l): return not l.is_queued_for_deletion())
	_check(live.size() == 2, "after recolour: %d live labels, want 2 (the empty faction's label goes)" % live.size())
	d.drop("b1")
	d.drop("b2")
	d.drop("g1")
	await _frames(2)
	_check(r.get_faction_shell_count() == 1, "after removals: faction count %d, want 1" % r.get_faction_shell_count())
	d.wipe()
	await _frames(2)
	_check(r.get_faction_shell_count() == 0, "regions_cleared: faction count %d, want 0" % r.get_faction_shell_count())
	_check(_labels(r).filter(func(l): return not l.is_queued_for_deletion()).is_empty(), "regions_cleared leaves no live label")
	_kill(p)


# R-106-03 table: overview 0.50, regional 0.12, local 0.05, lerped on a down blend.
func _opacity_table(stand_in: bool) -> void:
	_cur = "B3b-opacity-table"
	var p := _make()
	var r: Node = p[0]
	var d: FakeData = p[1]
	var z: FakeZoom = p[2]
	d.put("a1", "iron_pact", Vector3(0, 0, 0), Color(0.9, 0.1, 0.1))
	await _frames(2)
	var rows := [["overview", 0.0, "none", 0.50], ["regional", 0.0, "none", 0.12], ["local", 0.0, "none", 0.05],
		["overview", 0.5, "down", 0.31], ["regional", 0.5, "down", 0.085]]
	var seen := {}
	for row in rows:
		z.current_band = row[0]
		z.blend_factor = row[1]
		z.blend_direction = row[2]
		await _frames(2)
		var got := _read_opacity(r, stand_in)
		seen[row[3]] = got
		_check(got >= 0.0 and _near(got, row[3], 0.003), "%s blend %.1f %s: shell opacity %.4f, want %.3f" % [row[0], row[1], row[2], got, row[3]])
	# Positive control: the reader tells 0.50 from 0.05 (a constant reader would pass a table of equal values).
	_check(not _near(seen[0.50], seen[0.05], 0.1), "control: the opacity reader sees overview and local differ (%.3f vs %.3f)" % [seen[0.50], seen[0.05]])
	_kill(p)


# Stand-in: alpha / STAND_IN_OPACITY_MULTIPLIER of the single faction mesh. Field mode: the quad's shell_opacity uniform. -1 when unreadable.
func _read_opacity(r: Node, stand_in: bool) -> float:
	var ms := _meshes(r)
	if ms.is_empty():
		return -1.0
	var m: MeshInstance3D = ms[0]
	if stand_in:
		var sm := m.material_override as StandardMaterial3D
		return sm.albedo_color.a / _stand_in_mult() if sm and _stand_in_mult() > 0.0 else -1.0
	var shm := m.material_override as ShaderMaterial
	return float(shm.get_shader_parameter("shell_opacity")) if shm else -1.0


func _field_mode_checks() -> void:
	_cur = "B3b-field-mode"
	var p := _make()
	var r: Node = p[0]
	var d: FakeData = p[1]
	d.put("a1", "iron_pact", Vector3(0, 0, 0), Color(0.9, 0.1, 0.1))
	d.put("b1", "sea_league", Vector3(30, 0, 0), Color(0.1, 0.2, 0.9))
	await _frames(2)
	_check(_meshes(r).size() == 1, "field mode draws every faction with one MeshInstance3D, got %d" % _meshes(r).size())
	_check(r.get_territory_field() != null, "field mode has a territory field")
	_kill(p)


func _stand_in_checks() -> void:
	_cur = "B3b-stand-in"
	var p := _make()
	var r: Node = p[0]
	var d: FakeData = p[1]
	_check(r.get_territory_field() == null, "stand-in has no territory field")
	_check(r.get_shell_viewport() == null, "stand-in has no shell SubViewport")
	d.put("a1", "iron_pact", Vector3(0, 0, 0), Color(0.9, 0.1, 0.1))
	d.put("a2", "iron_pact", Vector3(12, 0, 0), Color(0.9, 0.1, 0.1))
	d.put("b1", "sea_league", Vector3(60, 0, 0), Color(0.1, 0.2, 0.9))
	await _frames(3)
	var ms := _meshes(r)
	_check(ms.size() == 2, "stand-in: one flat mesh per faction, got %d for 2 factions" % ms.size())
	for m: MeshInstance3D in ms:
		var sm := m.material_override as StandardMaterial3D
		_check(sm != null, "stand-in mesh has a StandardMaterial3D")
		if sm:
			_check(sm.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED, "stand-in is unshaded")
			_check(sm.blend_mode == BaseMaterial3D.BLEND_MODE_MIX, "stand-in blends with BLEND_MODE_MIX")
			_check(sm.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA, "stand-in uses alpha transparency")
	# The stand-in grows with the faction's reach: the two-region faction's mesh is wider than a one-region faction's.
	var widths := ms.map(func(m): return m.scale.x).duplicate()
	widths.sort()
	_check(widths.size() == 2 and widths[1] > widths[0], "stand-in of the 2-region faction is larger than the 1-region one: %s" % [widths])
	# Losing a faction frees its stand-in.
	d.drop("b1")
	await _frames(2)
	_check(_meshes(r).filter(func(m): return not m.is_queued_for_deletion()).size() == 1, "dropped faction's stand-in goes")
	_kill(p)


func _igpu_cost() -> void:
	_cur = "B3b-igpu-cost"
	var p := _make()
	var r: Node = p[0]
	var d: FakeData = p[1]
	var z: FakeZoom = p[2]
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in 80:
		var f := i % 15
		d.put("c%d" % i, "faction_%d" % f, Vector3(rng.randf_range(-60, 60), rng.randf_range(-6, 6), rng.randf_range(-60, 60)), Color.from_hsv(f / 15.0, 0.7, 0.9))
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 40, 120)
	cam.look_at(Vector3.ZERO)
	cam.current = true
	z.current_band = "overview"
	await _frames(10)
	var with_r := await _median_frame_ms(120)
	r.visible = false
	await _frames(5)
	var without_r := await _median_frame_ms(120)
	print("IGPU-COST adapter=\"%s\" method=%s window=%s with_renderer_ms=%.2f without_renderer_ms=%.2f delta_ms=%.2f (80 regions, 15 factions, overview band; read the adapter name: llvmpipe is software GL, a discrete GPU is not an iGPU)" % [
		RenderingServer.get_video_adapter_name(), RenderingServer.get_current_rendering_method(), root.size, with_r, without_r, with_r - without_r])
	_check(with_r > 0.0 and without_r > 0.0, "frame timing was measured")
	cam.queue_free()
	_kill(p)


func _median_frame_ms(n: int) -> float:
	var ts: Array[float] = []
	var last := Time.get_ticks_usec()
	for i in n:
		await process_frame
		var now := Time.get_ticks_usec()
		ts.append((now - last) / 1000.0)
		last = now
	ts.sort()
	return ts[n / 2]


func _run_child() -> void:
	if OS.get_environment("DISPLAY") == "":
		_check(false, "stand-in proof needs the Compatibility renderer, which needs a display; run under xvfb-run -a")
		return
	var out: Array = []
	var args := ["--path", ProjectSettings.globalize_path("res://"), "--rendering-driver", "opengl3", "--rendering-method", "gl_compatibility",
		"--resolution", "1920x1080", "--script", "res://tests/test_vg_b_b3b.gd", "--", "--child"]
	var code := OS.execute(OS.get_executable_path(), args, out, true)
	var text := "\n".join(out)
	for line in text.split("\n"):
		if line.begins_with("IGPU-COST") or line.begins_with("CHILD-FAIL") or line.begins_with("CHILD-PASS"):
			print(line)
	_check(code == 0 and text.contains("CHILD-PASS"), "stand-in child run (Compatibility renderer) failed with exit %d" % code)


func _finish() -> void:
	if _child:
		print("CHILD-%s passes=%d fails=%d" % ["PASS" if _fail == 0 else "FAIL", _pass, _fail])
	else:
		print("test_vg_b_b3b: %d passed, %d failed" % [_pass, _fail])
	for m in _msgs:
		print("FAIL ", m)
	quit(0 if _fail == 0 else 1)
