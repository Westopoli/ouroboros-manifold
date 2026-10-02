extends RefCounted
# Static cost analysis of a Godot shader source, for COST-SHAPE. Lives with the
# tests. Rules it enforces on the drawing shader:
#   - every `for` loop has a compile-time-constant trip count (literals and
#     `const` values only) and uses braces; no `while` / `do`
#   - no int/uint uniform that looks like a count (system / faction / rival
#     count): a loop that early-outs on a data count is the old cost shape
#   - every sampler uniform is a sampler3D (the field and the id grid); a 2D
#     sampler named like a per-system table is the old cost shape
#   - worst-case texture fetches per pixel in fragment(): every texture /
#     texelFetch / textureLod / textureGrad call counted once per trip of every
#     enclosing loop, user functions expanded at their call sites
# analyze() returns {problems: Array[String], fetches: int}.

const FETCH_FUNCS := ["texture", "texelFetch", "textureLod", "textureGrad", "textureProj", "textureGather"]

var _consts := {}
var _funcs := {}      # name -> body text
var _memo := {}
var problems: Array = []


static func analyze(src: String) -> Dictionary:
	var a = load("res://scenes/mockups/galaxy/tests/shader_cost.gd").new()
	return a._run(src)


func _run(src: String) -> Dictionary:
	src = _strip_comments(src)
	_collect_consts(src)
	_check_uniforms(src)
	_collect_funcs(src)
	var fetches := 0
	if not _funcs.has("fragment"):
		problems.append("no fragment() function")
	else:
		fetches = _cost("fragment")
	if fetches > 100:
		problems.append("worst-case %d texture fetches per pixel (limit 100)" % fetches)
	return {"problems": problems, "fetches": fetches}


func _strip_comments(s: String) -> String:
	var re := RegEx.new()
	re.compile("/\\*[\\s\\S]*?\\*/")
	s = re.sub(s, " ", true)
	var re2 := RegEx.new()
	re2.compile("//[^\\n]*")
	return re2.sub(s, " ", true)


func _collect_consts(src: String) -> void:
	var re := RegEx.new()
	re.compile("const\\s+(?:int|uint|float)\\s+(\\w+)\\s*=\\s*([^;]+);")
	for m in re.search_all(src):
		var v = _eval(m.get_string(2))
		if v != null:
			_consts[m.get_string(1)] = v


func _eval(expr: String):
	var names := PackedStringArray(_consts.keys())
	var vals: Array = _consts.values()
	var e := Expression.new()
	if e.parse(expr.strip_edges(), names) != OK:
		return null
	var r = e.execute(vals, null, false)
	if e.has_execute_failed():
		return null
	return r


func _check_uniforms(src: String) -> void:
	var re := RegEx.new()
	re.compile("uniform\\s+(?:lowp\\s+|mediump\\s+|highp\\s+)?(\\w+)\\s+(\\w+)")
	for m in re.search_all(src):
		var type := m.get_string(1)
		var name := m.get_string(2)
		if type.begins_with("sampler") and type != "sampler3D":
			problems.append("per-system style texture: uniform %s %s (only sampler3D grids allowed)" % [type, name])
		if (type == "int" or type == "uint") and _looks_like_count(name):
			problems.append("count uniform `%s`: a loop bounded or cut off by a system/faction count" % name)


func _looks_like_count(name: String) -> bool:
	var n := name.to_lower()
	return n.ends_with("count") or n.begins_with("n_") or n.begins_with("num_") or n.ends_with("_n")


func _collect_funcs(src: String) -> void:
	var re := RegEx.new()
	re.compile("(?:^|\\n)\\s*(?:float|int|uint|bool|void|vec[234]|ivec[234]|mat[234])\\s+(\\w+)\\s*\\([^)]*\\)\\s*\\{")
	for m in re.search_all(src):
		var open := m.get_end() - 1
		var close := _match_brace(src, open)
		if close < 0:
			continue
		_funcs[m.get_string(1)] = src.substr(open + 1, close - open - 1)


func _match_brace(s: String, open: int) -> int:
	var depth := 0
	for i in range(open, s.length()):
		var c := s[i]
		if c == "{":
			depth += 1
		elif c == "}":
			depth -= 1
			if depth == 0:
				return i
	return -1


func _match_paren(s: String, open: int) -> int:
	var depth := 0
	for i in range(open, s.length()):
		var c := s[i]
		if c == "(":
			depth += 1
		elif c == ")":
			depth -= 1
			if depth == 0:
				return i
	return -1


func _cost(fn: String) -> int:
	if _memo.has(fn):
		return _memo[fn]
	_memo[fn] = 0   # no recursion in GLSL; guards a malformed input
	var c := _block_cost(_funcs[fn])
	_memo[fn] = c
	return c


func _block_cost(text: String) -> int:
	var total := 0
	var rest := ""
	var i := 0
	var re_kw := RegEx.new()
	re_kw.compile("\\b(for|while|do)\\b")
	while i < text.length():
		var m := re_kw.search(text, i)
		if m == null:
			rest += text.substr(i)
			break
		rest += text.substr(i, m.get_start() - i)
		var kw := m.get_string(1)
		if kw != "for":
			problems.append("`%s` loop (only constant-bound `for` loops are allowed)" % kw)
			i = m.get_end()
			continue
		var po := text.find("(", m.get_end())
		var pc := _match_paren(text, po)
		var header := text.substr(po + 1, pc - po - 1)
		var j := pc + 1
		while j < text.length() and text[j] in [" ", "\t", "\n", "\r"]:
			j += 1
		var body := ""
		if j < text.length() and text[j] == "{":
			var close := _match_brace(text, j)
			body = text.substr(j + 1, close - j - 1)
			i = close + 1
		else:
			problems.append("`for` loop without braces: %s" % header.strip_edges())
			var semi := text.find(";", j)
			body = text.substr(j, semi - j + 1)
			i = semi + 1
		total += _trips(header) * _block_cost(body)
	# calls in the loop-free text
	var re_call := RegEx.new()
	re_call.compile("\\b(\\w+)\\s*\\(")
	for c in re_call.search_all(rest):
		var name := c.get_string(1)
		if FETCH_FUNCS.has(name):
			total += 1
		elif _funcs.has(name):
			total += _cost(name)
	return total


func _trips(header: String) -> int:
	var parts := header.split(";")
	if parts.size() != 3:
		problems.append("unparsable `for` header: %s" % header.strip_edges())
		return 1
	var re_init := RegEx.new()
	re_init.compile("=\\s*(.+)$")
	var mi := re_init.search(parts[0].strip_edges())
	var re_cond := RegEx.new()
	re_cond.compile("^\\s*\\w+\\s*(<=|<)\\s*(.+)$")
	var mc := re_cond.search(parts[1])
	if mi == null or mc == null:
		problems.append("loop header not of the form `i = A; i < B`: %s" % header.strip_edges())
		return 1
	var a = _eval(mi.get_string(1))
	var b = _eval(mc.get_string(2))
	if a == null or b == null:
		problems.append("loop bound `%s` is not a compile-time constant" % header.strip_edges())
		return 1
	var trips := int(b) - int(a) + (1 if mc.get_string(1) == "<=" else 0)
	return maxi(trips, 0)
