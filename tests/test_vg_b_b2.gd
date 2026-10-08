extends SceneTree

# Piece B2 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B):
# res://scenes/galaxy/shaders/shell_field.gdshader is the territory-shell shader
# copied from origin/push/galaxy-field (scenes/mockups/galaxy/shaders/), one
# full-screen pass over the baked field grid. Proves S-106 (R-106-02 rivals keep a
# gap, seam term; R-106-03 shell as a layer): first surface per faction, 4 layers,
# ISO 0.6, seam term; COST-SHAPE (no loop bounded by a data count, <= 100 worst-case
# fetches per pixel); the source compiles as a Godot shader with the expected
# uniform interface. Every detector has a positive control.
# Westley thresholds: none here (REFILL 12 ms and FIELD-EQ 2% are other pieces).

const TARGET := "res://scenes/galaxy/shaders/shell_field.gdshader"
const FETCH_LIMIT := 100
const FETCH_FUNCS := ["texture", "texelFetch", "textureLod", "textureGrad", "textureProj", "textureGather"]

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	_run()
	print("\n=== VG-B B2 shell shader ===")
	print("PASS: %d  FAIL: %d" % [_pass, _fail])
	for m in _msgs:
		print("  - " + m)
	print("=== RED ===" if _fail > 0 else "=== GREEN ===")
	quit(1 if _fail > 0 else 0)


func _check(id: String, ok: bool, why: String) -> void:
	if ok:
		_pass += 1
		print("PASS %s" % id)
	else:
		_fail += 1
		_msgs.append("%s: %s" % [id, why])
		print("FAIL %s: %s" % [id, why])


func _read(path: String) -> String:
	var f := FileAccess.open(path, FileAccess.READ)
	return f.get_as_text() if f else ""


func _run() -> void:
	_controls()
	var exists := FileAccess.file_exists(TARGET)
	_check("B2-exists", exists, "missing feature: %s does not exist (shell shader not copied)" % TARGET)
	var src := _read(TARGET) if exists else ""
	var code := _strip_comments(src)
	_copy_checks(src, code)
	_cost_shape(src)
	_compiles(src)


# ---- copy checks ------------------------------------------------------------

func _const_val(code: String, name: String) -> String:
	var re := RegEx.new()
	re.compile("const\\s+(?:int|float)\\s+%s\\s*=\\s*([^;]+);" % name)
	var m := re.search(code)
	return m.get_string(1).strip_edges() if m else ""


func _copy_checks(src: String, code: String) -> void:
	_check("B2-spatial-fullscreen", code.contains("shader_type spatial") and code.contains("depth_test_disabled") and code.contains("POSITION = vec4(VERTEX.xy, 1.0, 1.0)"), "one full-screen spatial pass expected (depth_test_disabled, POSITION = vec4(VERTEX.xy,...))")
	_check("B2-iso-0.6", _const_val(code, "ISO") == "0.6", "ISO must be 0.6, got '%s'" % _const_val(code, "ISO"))
	_check("B2-layers-4", _const_val(code, "LAYERS") == "4", "LAYERS must be 4, got '%s'" % _const_val(code, "LAYERS"))
	_check("B2-march-16x4", _const_val(code, "GROUPS") == "16" and _const_val(code, "SUB") == "4", "march must be GROUPS 16 x SUB 4, got %s x %s" % [_const_val(code, "GROUPS"), _const_val(code, "SUB")])
	# first surface per faction: a faction already drawn (bit in mask) is not drawn again
	_check("B2-first-surface-per-faction", code.contains("(mask & (1 << id)) == 0") and code.contains("mask |= 1 << id") and code.contains("nl < LAYERS"), "per-faction mask (a faction draws only its first surface, at most LAYERS) not found")
	# seam term: field green channel carries it and brightens the boundary
	_check("B2-seam-term", code.contains("texture(field, (p - gmin) / gsize).rg") and code.contains("l_g[") and code.contains("smoothstep(0.15, 0.5, l_g[l])"), "seam term (field .g read per layer, smoothstep(0.15, 0.5, seam)) not found")
	for u in ["field", "id_tex", "gmin", "gsize", "grid_n", "shell_opacity", "palette", "debug_mode"]:
		_check("B2-uniform-" + u, _has_uniform(code, u), "uniform '%s' missing" % u)
	_check("B2-palette-16", code.contains("uniform vec3 palette[16]"), "palette must hold 16 factions")
	_check("B2-no-system-uniforms", not code.contains("system_count") and not code.contains("faction_count"), "shader must not depend on a system or faction count uniform")


func _has_uniform(code: String, name: String) -> bool:
	var re := RegEx.new()
	re.compile("uniform\\s+\\w+\\s+%s\\b" % name)
	return re.search(code) != null


# ---- compiles ---------------------------------------------------------------

func _compiles(src: String) -> void:
	if src == "":
		_check("B2-compiles", false, "missing feature: %s does not exist" % TARGET)
		return
	var sh := Shader.new()
	sh.code = src
	var names: Array = []
	for u in sh.get_shader_uniform_list():
		names.append(u.name)
	var want := ["field", "id_tex", "gmin", "gsize", "grid_n", "shell_opacity", "palette", "debug_mode"]
	var missing := want.filter(func(n): return not names.has(n))
	_check("B2-compiles", sh.get_mode() == Shader.MODE_SPATIAL and missing.is_empty(), "shader did not compile to the expected interface; uniforms=%s missing=%s" % [names, missing])


# ---- COST-SHAPE -------------------------------------------------------------

func _cost_shape(src: String) -> void:
	if src == "":
		_check("COST-SHAPE", false, "missing feature: %s does not exist" % TARGET)
		return
	var r := _analyze(src)
	_check("COST-SHAPE", r.problems.is_empty(), "problems=%s" % [r.problems])
	_check("COST-SHAPE-fetches", r.fetches > 0 and r.fetches <= FETCH_LIMIT, "%d worst-case fetches per pixel (want 1..%d)" % [r.fetches, FETCH_LIMIT])


func _controls() -> void:
	var a := _analyze("const int N = 8;\nvoid fragment() {\n for (int i = 0; i < N; i++) { vec4 x = texture(t, uv); }\n vec4 y = texture(t, uv);\n}")
	_check("COST-SHAPE-control-count", a.fetches == 9 and a.problems.is_empty(), "8-trip loop + 1 fetch: fetches=%d problems=%s (expect 9, none)" % [a.fetches, a.problems])
	var b := _analyze("vec4 f(vec3 p) { return texture(t, p); }\nvoid fragment() {\n for (int i = 0; i < 128; i++) { vec4 x = f(p); }\n}")
	_check("COST-SHAPE-control-limit", b.fetches == 128 and b.problems.size() == 1, "128 fetches via helper: fetches=%d problems=%s (expect 128, one problem)" % [b.fetches, b.problems])
	var c := _analyze("uniform int system_count;\nvoid fragment() {\n for (int i = 0; i < system_count; i++) { }\n while (true) { }\n}")
	_check("COST-SHAPE-control-bounds", c.problems.size() >= 3, "data-count uniform + non-constant bound + while: problems=%s (expect >= 3)" % [c.problems])
	var d := _analyze("uniform sampler2D systems;\nvoid fragment() { }")
	_check("COST-SHAPE-control-sampler", d.problems.size() >= 1, "per-system 2D table sampler must be flagged: %s" % [d.problems])
	# compile control: broken source exposes no uniforms, valid source does
	var bad := Shader.new()
	bad.code = "shader_type spatial;\nuniform float a;\nvoid fragment() { this is not glsl }"
	var good := Shader.new()
	good.code = "shader_type spatial;\nuniform float a;\nvoid fragment() { ALBEDO = vec3(a); }"
	_check("B2-compiles-control", good.get_shader_uniform_list().size() == 1 and bad.get_shader_uniform_list().size() == 0, "control: valid shader lists 1 uniform (%d), broken lists 0 (%d)" % [good.get_shader_uniform_list().size(), bad.get_shader_uniform_list().size()])


func _strip_comments(s: String) -> String:
	var re := RegEx.new()
	re.compile("/\\*[\\s\\S]*?\\*/")
	s = re.sub(s, " ", true)
	var re2 := RegEx.new()
	re2.compile("//[^\\n]*")
	return re2.sub(s, " ", true)


func _analyze(src: String) -> Dictionary:
	var a := ShaderCostAnalysis.new()
	return a.run(_strip_comments(src))


# Static cost analysis, rules as in the field branch's tests/shader_cost.gd:
# constant trip counts only, braces on every for, no while/do, no int uniform that
# looks like a count, only sampler3D samplers, worst-case fetches in fragment()
# with user functions expanded at their call sites.
class ShaderCostAnalysis:
	var consts := {}
	var funcs := {}
	var memo := {}
	var problems: Array = []

	func run(src: String) -> Dictionary:
		var re := RegEx.new()
		re.compile("const\\s+(?:int|uint|float)\\s+(\\w+)\\s*=\\s*([^;]+);")
		for m in re.search_all(src):
			var v = _eval(m.get_string(2))
			if v != null:
				consts[m.get_string(1)] = v
		var ru := RegEx.new()
		ru.compile("uniform\\s+(?:lowp\\s+|mediump\\s+|highp\\s+)?(\\w+)\\s+(\\w+)")
		for m in ru.search_all(src):
			var ty := m.get_string(1)
			var nm := m.get_string(2)
			if ty.begins_with("sampler") and ty != "sampler3D":
				problems.append("per-system style texture: uniform %s %s (only sampler3D)" % [ty, nm])
			if (ty == "int" or ty == "uint") and (nm.contains("count") or nm.contains("num") or nm.contains("n_")):
				problems.append("count-like uniform %s %s" % [ty, nm])
		_collect_funcs(src)
		var f := 0
		if not funcs.has("fragment"):
			problems.append("no fragment() function")
		else:
			f = _cost("fragment")
		if f > 100:
			problems.append("worst-case %d texture fetches per pixel (limit 100)" % f)
		return {"problems": problems, "fetches": f}

	func _eval(expr: String):
		var e := Expression.new()
		if e.parse(expr.strip_edges(), PackedStringArray(consts.keys())) != OK:
			return null
		var r = e.execute(consts.values(), null, false)
		return null if e.has_execute_failed() else r

	func _match_close(s: String, open_i: int, o: String, c: String) -> int:
		var depth := 0
		for i in range(open_i, s.length()):
			var ch := s[i]
			if ch == o:
				depth += 1
			elif ch == c:
				depth -= 1
				if depth == 0:
					return i
		return -1

	func _collect_funcs(src: String) -> void:
		var re := RegEx.new()
		re.compile("(?:^|[;}\\s])(?:void|float|int|bool|vec[234]|ivec[234]|mat[234])\\s+(\\w+)\\s*\\([^)]*\\)\\s*\\{")
		for m in re.search_all(src):
			var open_i := m.get_end() - 1
			var close_i := _match_close(src, open_i, "{", "}")
			if close_i > 0:
				funcs[m.get_string(1)] = src.substr(open_i + 1, close_i - open_i - 1)

	func _cost(fname: String) -> int:
		if memo.has(fname):
			return memo[fname]
		memo[fname] = 0
		var c := _block_cost(funcs[fname])
		memo[fname] = c
		return c

	func _block_cost(body: String) -> int:
		var total := 0
		var i := 0
		var rf := RegEx.new()
		rf.compile("\\b(for|while|do)\\b")
		while i < body.length():
			var m := rf.search(body, i)
			if m == null:
				total += _calls_cost(body.substr(i))
				break
			total += _calls_cost(body.substr(i, m.get_start() - i))
			var kw := m.get_string(1)
			if kw != "for":
				problems.append("%s loop (trip count not constant)" % kw)
				i = m.get_end()
				continue
			var po := body.find("(", m.get_end())
			var pc := _match_close(body, po, "(", ")")
			var head := body.substr(po + 1, pc - po - 1)
			var trips := _trips(head)
			var j := pc + 1
			while j < body.length() and body[j] in [" ", "\n", "\t", "\r"]:
				j += 1
			if j >= body.length() or body[j] != "{":
				problems.append("for without braces")
				i = pc + 1
				continue
			var bc := _match_close(body, j, "{", "}")
			total += trips * _block_cost(body.substr(j + 1, bc - j - 1))
			i = bc + 1
		return total

	func _trips(head: String) -> int:
		var parts := head.split(";")
		if parts.size() != 3:
			problems.append("unparsable for header '%s'" % head)
			return 1
		var re := RegEx.new()
		re.compile("(\\w+)\\s*<\\s*(\\w+)")
		var m := re.search(parts[1])
		if m == null:
			problems.append("for bound not '<': %s" % parts[1])
			return 1
		var b := m.get_string(2)
		var v = int(b) if b.is_valid_int() else consts.get(b, null)
		if v == null:
			problems.append("non-constant loop bound '%s'" % b)
			return 1
		return int(v)

	func _calls_cost(text: String) -> int:
		var total := 0
		var re := RegEx.new()
		re.compile("\\b(\\w+)\\s*\\(")
		for m in re.search_all(text):
			var n := m.get_string(1)
			if n in FETCH_FUNCS:
				total += 1
			elif funcs.has(n) and n != "fragment":
				total += _cost(n)
		return total
