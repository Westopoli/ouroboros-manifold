extends SceneTree
# Static and draw-count checks: COST-SHAPE, ONE-DRAW (spec 2026-10-02, Step 2).
# Frozen after the "galaxy field: failing tests" commit; builders do not edit.
# Runs headless (dummy renderer): tests/run_fast.sh static.
#
# COST-SHAPE: shaders/shell_field.gdshader has no loop bounded by system or
#   faction count, no per-system texture, at most 100 texture fetches per
#   pixel worst case (analysis in tests/shader_cost.gd). Positive control: the
#   old shader (kept as tests/fixtures/old_shell_metaball.gdshader.txt, so the
#   control survives its deletion) must fail it. To see the real shader's
#   verdict on the old file: COST_SHAPE_TARGET=res://.../shell_metaball.gdshader.
# ONE-DRAW: GalaxyView/ShellRenderer holds exactly one MeshInstance3D (the one
#   shell draw) at 4, 8 and 15 factions. Positive control: the old renderer
#   (tests/fixtures/old_shell_renderer.gd.txt) draws one per faction.
# Contract used: GalaxyView.build(galaxy), GalaxyView.get_faction_shell_count(),
#   child node "ShellRenderer" of GalaxyView.

const ShaderCost := preload("res://scenes/mockups/galaxy/tests/shader_cost.gd")
const BigGalaxy := preload("res://scenes/mockups/galaxy/tests/big_galaxy.gd")
const SHADER_PATH := "res://scenes/mockups/galaxy/shaders/shell_field.gdshader"
const OLD_SHADER := "res://scenes/mockups/galaxy/tests/fixtures/old_shell_metaball.gdshader.txt"
const OLD_RENDERER := "res://scenes/mockups/galaxy/tests/fixtures/old_shell_renderer.gd.txt"
const MOCKUP_SCENE := "res://scenes/mockups/galaxy/galaxy_mockup.tscn"

var _failures := 0


func _initialize() -> void:
	_cost_shape()
	await _one_draw()
	if _failures > 0:
		print("STATIC TESTS FAILED: %d" % _failures)
		quit(1)
	else:
		print("STATIC TESTS OK")
		quit(0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _read(path: String) -> String:
	var f := FileAccess.open(path, FileAccess.READ)
	return f.get_as_text() if f != null else ""


# ---- COST-SHAPE ----------------------------------------------------------

func _cost_shape() -> void:
	# analyser self-tests
	var a := ShaderCost.analyze("const int N = 8;\nvoid fragment() {\n for (int i = 0; i < N; i++) { vec4 x = texture(t, uv); }\n vec4 y = texture(t, uv);\n}")
	_check("COST-SHAPE-selftest-count", a.fetches == 9 and a.problems.is_empty(), "8-trip loop + 1 fetch: fetches=%d problems=%s (expect 9, none)" % [a.fetches, a.problems])
	var b := ShaderCost.analyze("vec4 f(vec3 p) { return texture(t, p); }\nvoid fragment() {\n for (int i = 0; i < 128; i++) { vec4 x = f(p); }\n}")
	_check("COST-SHAPE-selftest-limit", b.fetches == 128 and b.problems.size() == 1, "128 fetches via a helper: fetches=%d problems=%s (expect 128, one over-limit problem)" % [b.fetches, b.problems])
	var c := ShaderCost.analyze("uniform int system_count;\nvoid fragment() {\n for (int i = 0; i < system_count; i++) { }\n while (true) { }\n}")
	_check("COST-SHAPE-selftest-bounds", c.problems.size() >= 3, "uniform count + non-constant bound + while: problems=%s (expect >= 3)" % [c.problems])

	# positive control: the old shader must fail
	var old := ShaderCost.analyze(_read(OLD_SHADER))
	_check("COST-SHAPE-control", old.problems.size() >= 3 and old.fetches > 100, "old shader must FAIL: %d fetches, problems=%s" % [old.fetches, old.problems])

	var target := OS.get_environment("COST_SHAPE_TARGET")
	if target == "":
		target = SHADER_PATH
	var src := _read(target)
	if src == "":
		_check("COST-SHAPE", false, "%s does not exist" % target)
		return
	var r := ShaderCost.analyze(src)
	_check("COST-SHAPE", r.problems.is_empty(), "%s: %d fetches per pixel worst case (<= 100); problems=%s" % [target, r.fetches, r.problems])


# ---- ONE-DRAW ------------------------------------------------------------

func _count_draws(n: Node) -> int:
	var c := 0
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		c += 1
	for ch in n.get_children():
		c += _count_draws(ch)
	return c


func _one_draw() -> void:
	await process_frame
	# positive control: old renderer, one draw per faction
	var src := _read(OLD_RENDERER)
	src = src.replace("load(\"res://scenes/mockups/galaxy/shaders/shell_metaball.gdshader\")", "Shader.new()")
	var scr := GDScript.new()
	scr.source_code = src
	var err := scr.reload()
	if err != OK:
		_check("ONE-DRAW-control", false, "cannot compile the old-renderer fixture (error %d)" % err)
	else:
		var wv := Node.new()
		wv.set_script(load("res://scenes/mockups/galaxy/legacy_world_view_data.gd"))
		root.add_child(wv)
		var old := Node3D.new()
		old.set_script(scr)
		root.add_child(old)
		old.setup(wv, null)
		var g := BigGalaxy.make(5, 120, 4, 10.0)
		for s in g.systems:
			if s.owner >= 0:
				wv.set_territory(str(s.id), s.pos, s.significance, Color.from_hsv(float(s.owner) * 0.17, 0.65, 0.85))
		var n := _count_draws(old)
		_check("ONE-DRAW-control", n == 4, "old renderer with 4 factions: %d shell draws (must be 4, i.e. not one, so the detector catches it)" % n)
		old.teardown()
		old.queue_free()
		wv.queue_free()
		await process_frame

	var packed: PackedScene = load(MOCKUP_SCENE)
	var mock: Node = packed.instantiate()
	root.add_child(mock)
	await process_frame
	await process_frame
	var view: Node = mock.get_node("World/GalaxyView")
	for nf in [4, 8, 15]:
		var g := BigGalaxy.make(5, 120, nf, 10.0)
		view.build(g)
		await process_frame
		await process_frame
		var shell: Node = view.get_node_or_null("ShellRenderer")
		if shell == null:
			_check("ONE-DRAW", false, "%d factions: GalaxyView has no ShellRenderer child" % nf)
			continue
		var draws := _count_draws(shell)
		_check("ONE-DRAW", draws == 1, "%d factions: %d shell draw(s) (must be 1)" % [nf, draws])
		_check("ONE-DRAW-factions", view.get_faction_shell_count() == nf, "%d factions: get_faction_shell_count()=%d (must equal the number of owning factions)" % [nf, view.get_faction_shell_count()])
