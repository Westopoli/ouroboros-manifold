extends Control
# Layout prototype pass 1: the view. Draws generator data only; no state of its own beyond hover.
# Text budget (hard rule, Westley 2026-10-04): one top bar line, one row of check dots, piece names
# of at most two words. Everything else is a tooltip at the cursor or a toggle (L labels, H help).
# See also: layout_mockup.gd (owns state and keys), layout_gen.gd (the data).

const TOP := 30.0
const BOTTOM := 36.0
const BG := Color(0.055, 0.065, 0.085)
const PANEL := Color(0.085, 0.10, 0.125)
const INK := Color(0.82, 0.86, 0.9)
const DIM := Color(0.5, 0.55, 0.62)
const KIND_COL := {
	"home": Color(0.45, 0.62, 0.95), "gate": Color(0.55, 0.75, 0.95), "crossing": Color(0.95, 0.55, 0.4),
	"heights": Color(0.95, 0.75, 0.35), "prize": Color(0.75, 0.55, 0.95), "commons": Color(0.55, 0.85, 0.6),
	"objective": Color(1.0, 0.85, 0.3), "hidden": Color(0.6, 0.65, 0.7),
}
const KIND_LABEL := {
	"home": "Home ground", "gate": "Gate", "crossing": "Crossing", "heights": "Heights", "prize": "Prize",
	"commons": "Commons", "objective": "Objective ground", "hidden": "Hidden approach",
}
const DISTRICT_COL := [
	Color(0.3, 0.5, 0.95, 0.16), Color(0.95, 0.35, 0.3, 0.16), Color(0.3, 0.5, 0.95, 0.07),
	Color(0.95, 0.35, 0.3, 0.07), Color(0.85, 0.8, 0.3, 0.09), Color(1.0, 0.85, 0.3, 0.2), Color(0.085, 0.10, 0.125, 0.0),
]
const EDGE_COL := {
	"route": Color(0.62, 0.68, 0.76), "loop": Color(0.35, 0.75, 0.75), "spur": Color(0.7, 0.55, 0.9),
	"backdoor": Color(0.7, 0.55, 0.9), "climb": Color(0.95, 0.65, 0.3), "hidden": Color(0.55, 0.6, 0.66),
	"objroute": Color(1.0, 0.85, 0.3), "link": Color(0.5, 0.56, 0.64),
}

signal opened(index: int)

var mode := "map"            # map | sheet | replay
var map: Dictionary = {}
var sheet: Array = []        # twelve maps
var sheet_dist: Array = []   # per map: nearest signature distance to the other eleven
var header := ""
var step := 999
var labels_on := false
var help_on := false
var mouse := Vector2(-1000, -1000)
var pinned := false          # screenshot mode: --hover fixes the cursor
var tip := PackedStringArray()
var hover_thumb := -1
var thumb_rects: Array = []
var font: Font
var text_px := 0.0           # area of default-visible text this frame (the text budget, hard rule)


func _ready() -> void:
	font = ThemeDB.fallback_font
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseMotion and not pinned:
		mouse = (ev as InputEventMouseMotion).position
		queue_redraw()
	elif ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT and mode == "sheet" and hover_thumb >= 0:
		opened.emit(hover_thumb)


# ---------- frame ----------

func _draw() -> void:
	var sz := size
	draw_rect(Rect2(Vector2.ZERO, sz), BG)
	tip = PackedStringArray()
	hover_thumb = -1
	text_px = 0.0
	if mode == "sheet":
		_draw_sheet(sz)
	elif not map.is_empty():
		var area := Rect2(0, TOP, sz.x, sz.y - TOP - BOTTOM)
		_draw_map(area, map, false)
		_draw_dots(sz)
	_draw_bar(sz)
	if help_on:
		_draw_help(sz)
	elif not tip.is_empty():
		_draw_tip()


func _draw_bar(sz: Vector2) -> void:
	draw_rect(Rect2(0, 0, sz.x, TOP - 6), Color(0, 0, 0, 0.55))
	draw_string(font, Vector2(12, 17), header, HORIZONTAL_ALIGNMENT_LEFT, sz.x - 24, 14, INK)
	text_px += font.get_string_size(header, HORIZONTAL_ALIGNMENT_LEFT, sz.x - 24, 14).x * 14.0


func _draw_dots(sz: Vector2) -> void:
	var checks: Array = map["checks"]
	var n := checks.size()
	var x0 := sz.x * 0.5 - (n - 1) * 13.0
	for i in n:
		var c: Dictionary = checks[i]
		var p := Vector2(x0 + i * 26.0, sz.y - 17)
		draw_circle(p, 7.0, Color(0.3, 0.8, 0.4) if c["ok"] else Color(0.92, 0.3, 0.3))
		if mouse.distance_to(p) < 11.0:
			tip = PackedStringArray([c["label"], c["line"]])


# ---------- map ----------

func _xf(area: Rect2, canvas: float, pad: float) -> Array:
	var side := minf(area.size.x, area.size.y) - pad * 2.0
	var o := area.position + (area.size - Vector2(side, side)) * 0.5
	return [o, side / canvas]


func _draw_map(area: Rect2, m: Dictionary, thumb: bool) -> void:
	var canvas: float = m["canvas"]
	var xf := _xf(area, canvas, 4.0 if thumb else 10.0)
	var o: Vector2 = xf[0]
	var s: float = xf[1]
	var side := canvas * s
	draw_rect(Rect2(o, Vector2(side, side)), PANEL)
	draw_texture_rect(_district_tex(m), Rect2(o, Vector2(side, side)), false)
	var nodes: Array = m["nodes"]
	var edges: Array = m["edges"]
	var last_step: int = mini(step, m["steps"].size() - 1) if mode == "replay" and not thumb else 9999
	var hover_edge := -1
	var hover_node := -1
	if not thumb:
		hover_node = _hit_node(m, o, s)
		if hover_node < 0:
			hover_edge = _hit_edge(m, o, s)
	# sight lines first, then routes, then pieces on top
	for e in edges:
		if e["kind"] == "overlook" and e["step"] <= last_step:
			var a: Vector2 = o + (nodes[e["a"]]["pos"] as Vector2) * s
			var b: Vector2 = o + (e["target"] as Vector2) * s
			draw_dashed_line(a, b, Color(1.0, 0.85, 0.3, 0.45), 1.5, 5.0)
	for e in edges:
		if e["kind"] != "overlook" and e["step"] <= last_step:
			_draw_edge(m, e, o, s, thumb, e["id"] == hover_edge, last_step)
	for n in nodes:
		if n["step"] > last_step:
			continue
		_draw_node(n, o, s, thumb, n["id"] == hover_node, last_step, side)
	if not thumb and labels_on:
		for e in edges:
			if e["kind"] != "overlook" and e["step"] <= last_step:
				var p := _edge_pts(m, e, o, s)
				var mid: Vector2 = p[p.size() / 2]
				var t := "%d wu · %d s" % [int(e["width"]), int(_elen(m, e) / m["walk"])]
				draw_string(font, mid + Vector2(5, -5), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.9, 0.92, 0.95, 0.85))
	if hover_node >= 0 and not thumb:
		tip = _node_tip(nodes[hover_node])
	elif hover_edge >= 0 and not thumb:
		tip = _edge_tip(m, edges[hover_edge])


# Districts as an 8x8 colour image stretched with linear filtering: soft regions, no visible grid.
func _district_tex(m: Dictionary) -> ImageTexture:
	if not m.has("_tex"):
		var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
		var dist: Array = m["districts"]
		for i in dist.size():
			img.set_pixel(i % 8, i / 8, DISTRICT_COL[dist[i]])
		m["_tex"] = ImageTexture.create_from_image(img)
	return m["_tex"]


func _elen(m: Dictionary, e: Dictionary) -> float:
	return (m["nodes"][e["a"]]["pos"] as Vector2).distance_to(m["nodes"][e["b"]]["pos"]) * e["meander"]


# Screen polyline for an edge; meander shows as a wiggle so a longer way looks longer.
func _edge_pts(m: Dictionary, e: Dictionary, o: Vector2, s: float) -> PackedVector2Array:
	var a: Vector2 = o + (m["nodes"][e["a"]]["pos"] as Vector2) * s
	var b: Vector2 = o + (m["nodes"][e["b"]]["pos"] as Vector2) * s
	var pts := PackedVector2Array()
	var mean: float = e["meander"]
	if mean < 1.04:
		pts.append(a)
		pts.append(b)
		return pts
	var d := b - a
	var L := d.length()
	var nrm := d.orthogonal().normalized()
	var waves := 2.0
	var amp := 0.5 * L * sqrt(mean * mean - 1.0) / (PI * waves)
	var n := 24
	for i in n + 1:
		var t := float(i) / n
		pts.append(a + d * t + nrm * sin(t * TAU * waves * 0.5) * amp * (1.0 if int(e["id"]) % 2 == 0 else -1.0))
	return pts


func _draw_edge(m: Dictionary, e: Dictionary, o: Vector2, s: float, thumb: bool, hot: bool, last_step: int) -> void:
	var col: Color = EDGE_COL.get(e["kind"], EDGE_COL["route"])
	var fx: bool = e.get("fx_step", 0) <= last_step  # a crossing or commons shows only from its own step
	if e["open"] and fx:
		col = col.lerp(Color(0.55, 0.85, 0.6), 0.5)
	var is_new: bool = mode == "replay" and not thumb and e["step"] == last_step
	if mode == "replay" and not thumb and not is_new:
		col.a = 0.55
	if hot:
		col = col.lightened(0.35)
	var pts := _edge_pts(m, e, o, s)
	var hw := maxf(1.0 if thumb else 1.8, float(e["width"]) * s * 0.28)
	if e["kind"] == "climb":
		hw = maxf(hw, 1.5)
	if e["hidden"] and not thumb:
		_dashed_poly(pts, col, hw * 1.4)
		return
	if e["kind"] in ["spur", "backdoor"] and not thumb:
		_dashed_poly(pts, col, hw * 1.6)
		return
	var h0 := hw
	var h1 := hw
	if e["choke"] and fx:
		# pinched at the crossing end, wider at the other
		var ka: String = m["nodes"][e["a"]]["kind"]
		var kb: String = m["nodes"][e["b"]]["kind"]
		if kb == "crossing":
			h1 = hw * 0.3
		elif ka == "crossing":
			h0 = hw * 0.3
		elif kb == "gate" or kb == "home":
			h1 = hw * 0.5
		else:
			h0 = hw * 0.5
	_strip(pts, h0, h1, col)
	if e["kind"] == "objroute" and not thumb:
		var n := pts.size()
		var tip_p := pts[n - 1]
		var dir := (pts[n - 1] - pts[n - 2]).normalized()
		var nm := dir.orthogonal()
		draw_colored_polygon(PackedVector2Array([tip_p + dir * 9, tip_p - dir * 3 + nm * 6, tip_p - dir * 3 - nm * 6]), col)
	if e.get("closed", false) and fx and not thumb:
		_hatch(pts, hw + 2.0, col)


func _strip(pts: PackedVector2Array, h0: float, h1: float, col: Color) -> void:
	var n := pts.size()
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in n:
		var d: Vector2
		if i == 0:
			d = pts[1] - pts[0]
		elif i == n - 1:
			d = pts[n - 1] - pts[n - 2]
		else:
			d = pts[i + 1] - pts[i - 1]
		var nm := d.orthogonal().normalized()
		var h := lerpf(h0, h1, float(i) / maxf(n - 1, 1))
		left.append(pts[i] + nm * h)
		right.append(pts[i] - nm * h)
	right.reverse()
	left.append_array(right)
	if Geometry2D.triangulate_polygon(left).is_empty():
		draw_polyline(pts, col, maxf(h0, h1) * 2.0, true)
	else:
		draw_colored_polygon(left, col)


func _dashed_poly(pts: PackedVector2Array, col: Color, w: float) -> void:
	for i in pts.size() - 1:
		draw_dashed_line(pts[i], pts[i + 1], col, maxf(w, 2.0), 7.0)


# Closed sides: short ticks along both banks.
func _hatch(pts: PackedVector2Array, off: float, col: Color) -> void:
	var c := Color(col.r, col.g, col.b, 0.8)
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		var L := a.distance_to(b)
		var d := (b - a) / maxf(L, 0.001)
		var nm := d.orthogonal()
		var k := int(L / 8.0)
		for j in k:
			var p := a + d * (j + 0.5) * 8.0
			draw_line(p + nm * off, p + nm * (off + 5.0) + d * 3.0, c, 1.0)
			draw_line(p - nm * off, p - nm * (off + 5.0) + d * 3.0, c, 1.0)


# ---------- pieces ----------

func _draw_node(n: Dictionary, o: Vector2, s: float, thumb: bool, hot: bool, last_step: int, side_px: float) -> void:
	var p: Vector2 = o + (n["pos"] as Vector2) * s
	var kind: String = n["kind"]
	if kind == "waypoint":
		if not thumb:
			draw_circle(p, 2.5, Color(0.5, 0.56, 0.64, 0.6))
		return
	var r := maxf(3.5, side_px * 0.017) if thumb else clampf(side_px * 0.018, 11.0, 22.0)
	var col: Color = KIND_COL.get(kind, INK)
	if kind == "home" or kind == "gate":
		col = Color(0.45, 0.62, 0.95) if n["side"] == 0 else Color(0.95, 0.5, 0.45)
	if kind == "objective":
		r *= 1.25 if not n.get("moving", false) else 0.95
	var dim: bool = mode == "replay" and not thumb and n["step"] != last_step
	if dim:
		col.a = 0.6
	if hot:
		col = col.lightened(0.4)
	var shape := _shape(kind, r)
	for i in shape.size():
		shape[i] += p
	draw_colored_polygon(shape, Color(BG.r, BG.g, BG.b, 0.92))
	var closed := PackedVector2Array(shape)
	closed.append(shape[0])
	if kind == "hidden" and not thumb:
		for i in shape.size():
			draw_dashed_line(shape[i], shape[(i + 1) % shape.size()], col, 2.0, 4.0)
	else:
		draw_polyline(closed, col, 1.0 if thumb else 2.2, true)
	if thumb:
		return
	_glyph(kind, p, r, col, n)
	var name_s: String = n["name"]
	if name_s != "":
		var w := font.get_string_size(name_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		draw_string(font, p + Vector2(-w * 0.5, r + 14), name_s, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(INK.r, INK.g, INK.b, 0.5 if dim else 0.9))
		text_px += w * 12.0


func _shape(kind: String, r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	match kind:
		"home":
			for q in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1)]:
				pts.append(q * r * 0.9)
		"gate":
			for q in [Vector2(-0.8, 0.9), Vector2(-0.8, -0.2), Vector2(-0.4, -0.8), Vector2(0.4, -0.8), Vector2(0.8, -0.2), Vector2(0.8, 0.9)]:
				pts.append(q * r)
		"crossing":
			for i in 6:
				pts.append(Vector2.from_angle(i * TAU / 6.0) * r * 1.05)
		"heights":
			for q in [Vector2(0, -1.1), Vector2(1.05, 0.8), Vector2(-1.05, 0.8)]:
				pts.append(q * r)
		"prize":
			for q in [Vector2(0, -1.1), Vector2(1.1, 0), Vector2(0, 1.1), Vector2(-1.1, 0)]:
				pts.append(q * r)
		"objective":
			for i in 10:
				pts.append(Vector2.from_angle(-PI / 2.0 + i * TAU / 10.0) * r * (1.15 if i % 2 == 0 else 0.55))
		"hidden":
			for i in 8:
				pts.append(Vector2.from_angle(i * TAU / 8.0) * r * 0.75)
		_:
			for i in 16:
				pts.append(Vector2.from_angle(i * TAU / 16.0) * r)
	return pts


# One small glyph inside each outline so a piece reads at a glance.
func _glyph(kind: String, p: Vector2, r: float, col: Color, n: Dictionary) -> void:
	match kind:
		"home":
			draw_polyline(PackedVector2Array([p + Vector2(-0.5, 0.1) * r, p + Vector2(0, -0.45) * r, p + Vector2(0.5, 0.1) * r]), col, 1.8)
			draw_rect(Rect2(p + Vector2(-0.3, 0.1) * r, Vector2(0.6, 0.5) * r), col, false, 1.5)
		"gate":
			draw_line(p + Vector2(-0.3, 0.8) * r, p + Vector2(-0.3, -0.1) * r, col, 1.8)
			draw_line(p + Vector2(0.3, 0.8) * r, p + Vector2(0.3, -0.1) * r, col, 1.8)
		"crossing":
			draw_colored_polygon(PackedVector2Array([p + Vector2(-0.75, -0.45) * r, p, p + Vector2(-0.75, 0.45) * r]), col)
			draw_colored_polygon(PackedVector2Array([p + Vector2(0.75, -0.45) * r, p, p + Vector2(0.75, 0.45) * r]), col)
		"heights":
			for b in int(n.get("band", 1)):
				draw_line(p + Vector2(-0.4 + b * 0.0, 0.35 - b * 0.35) * r, p + Vector2(0.4, 0.35 - b * 0.35) * r, col, 1.6)
		"prize":
			draw_circle(p, r * 0.28, col)
		"commons":
			for q in [Vector2(-0.4, -0.2), Vector2(0.4, -0.2), Vector2(0, 0.45)]:
				draw_circle(p + q * r, r * 0.16, col)
		"objective":
			draw_circle(p, r * 0.22, col)
		"hidden":
			draw_line(p + Vector2(-0.4, 0.4) * r, p + Vector2(0.4, -0.4) * r, col, 1.6)


# ---------- hover ----------

func _hit_node(m: Dictionary, o: Vector2, s: float) -> int:
	var best := -1
	var bd := 1e9
	for n in m["nodes"]:
		if n["kind"] == "waypoint" or n["step"] > (mini(step, m["steps"].size() - 1) if mode == "replay" else 9999):
			continue
		var d := mouse.distance_to(o + (n["pos"] as Vector2) * s)
		if d < 20.0 and d < bd:
			bd = d
			best = n["id"]
	return best


func _hit_edge(m: Dictionary, o: Vector2, s: float) -> int:
	var best := -1
	var bd := 1e9
	for e in m["edges"]:
		if e["kind"] == "overlook" or e["step"] > (mini(step, m["steps"].size() - 1) if mode == "replay" else 9999):
			continue
		var a: Vector2 = o + (m["nodes"][e["a"]]["pos"] as Vector2) * s
		var b: Vector2 = o + (m["nodes"][e["b"]]["pos"] as Vector2) * s
		var c := Geometry2D.get_closest_point_to_segment(mouse, a, b)
		var d := mouse.distance_to(c)
		if d < maxf(7.0, float(e["width"]) * s * 0.3 + 3.0) and d < bd:
			bd = d
			best = e["id"]
	return best


func _node_tip(n: Dictionary) -> PackedStringArray:
	var lines := PackedStringArray()
	lines.append("%s · %s (%s)" % [n["name"], KIND_LABEL.get(n["kind"], n["kind"]), n["variant"]])
	if n["choice"] != "":
		lines.append(n["choice"])
	var nums := PackedStringArray()
	for k in n["nums"]:
		var v = n["nums"][k]
		match k:
			"width", "choke_width":
				nums.append("width %d wu" % int(v))
			"bypass":
				nums.append("way round %.1fx" % float(v))
			"extra_s":
				nums.append("round +%d s" % int(v))
			"band":
				nums.append("%d bands" % int(v))
			"climb":
				nums.append("climb %d wu wide" % int(v))
			"second_way_s":
				nums.append("2nd way +%d s" % int(v))
			"radius":
				nums.append("radius %d wu" % int(v))
			"wall":
				nums.append("walls %d bands" % int(v))
			"spur_wu":
				nums.append("spur %d wu" % int(v))
			"stops":
				nums.append("%d stops" % int(v))
			"back_door":
				nums.append("back door")
	if not nums.is_empty():
		lines.append(" · ".join(nums))
	return lines


func _edge_tip(m: Dictionary, e: Dictionary) -> PackedStringArray:
	var names := {"route": "Route", "loop": "Way round", "spur": "Spur", "backdoor": "Back door", "climb": "Climb", "hidden": "Hidden way",
		"objroute": "Objective route", "link": "Link"}
	var t := "%s · width %d wu · %d s to walk" % [names.get(e["kind"], "Route"), int(e["width"]), int(_elen(m, e) / m["walk"])]
	if e["meander"] > 1.04:
		t += " (winding x%.2f)" % e["meander"]
	return PackedStringArray([t])


# ---------- sheet ----------

func _draw_sheet(sz: Vector2) -> void:
	thumb_rects = []
	var area := Rect2(10, TOP + 4, sz.x - 20, sz.y - TOP - 14)
	var cols := 4
	var rows := 3
	var cw := area.size.x / cols
	var ch := area.size.y / rows
	for i in sheet.size():
		var cell := Rect2(area.position + Vector2(i % cols * cw, i / cols * ch), Vector2(cw, ch))
		var tr := Rect2(cell.position, Vector2(cw, ch - 16))
		thumb_rects.append(tr)
		var m: Dictionary = sheet[i]
		_draw_map(tr, m, true)
		var bad := 0
		for c in m["checks"]:
			if not c["ok"]:
				bad += 1
		var side := minf(tr.size.x, tr.size.y)
		var ox := tr.position.x + (tr.size.x - side) * 0.5
		var oy := tr.position.y + (tr.size.y - side) * 0.5
		if bad > 0:
			draw_rect(Rect2(ox + 2, oy + 2, side - 4, side - 4), Color(0.92, 0.3, 0.3, 0.8), false, 1.5)
		var num := "%.1f" % sheet_dist[i]
		draw_string(font, Vector2(cell.position.x + cw * 0.5 - 12, cell.position.y + ch - 3), num, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, DIM)
		text_px += font.get_string_size(num, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x * 11.0
		if tr.has_point(mouse):
			hover_thumb = i
			var sg: Dictionary = m["signature"]
			tip = PackedStringArray(["Seed %d · %s · %d loops" % [m["seed"], m["division"], m["loops"]],
				"Side A: %s   Side B: %s" % [sg["route_a"], sg["route_b"]], "Click to open. Number = signature distance to the nearest other seed."])


# ---------- tooltip and help ----------

func _draw_tip() -> void:
	var wmax := 300.0
	var total := Vector2(0, 0)
	var sizes := []
	for l in tip:
		var sz := font.get_multiline_string_size(l, HORIZONTAL_ALIGNMENT_LEFT, wmax, 13)
		sizes.append(sz)
		total.x = maxf(total.x, sz.x)
		total.y += sz.y + 3.0
	var pos := mouse + Vector2(16, 16)
	if pos.x + total.x + 16 > size.x:
		pos.x = mouse.x - total.x - 24
	if pos.y + total.y + 12 > size.y:
		pos.y = mouse.y - total.y - 20
	draw_rect(Rect2(pos - Vector2(6, 4), total + Vector2(12, 10)), Color(0.02, 0.03, 0.04, 0.94))
	draw_rect(Rect2(pos - Vector2(6, 4), total + Vector2(12, 10)), Color(0.4, 0.45, 0.52), false, 1.0)
	var y := pos.y
	for i in tip.size():
		draw_multiline_string(font, Vector2(pos.x, y + 12), tip[i], HORIZONTAL_ALIGNMENT_LEFT, wmax, 13, -1, INK if i > 0 else Color(1, 0.9, 0.5))
		y += sizes[i].y + 3.0


func _draw_help(sz: Vector2) -> void:
	var lines := [
		"Layout prototype, pass 1 (flat diagram). Hover anything for its numbers.",
		"A  archetype     Left / Right  seed     S  sides: mirror, rotate, separate",
		"G  growth on/off (off leaves home slots and the spine only)",
		"V  view: map, sheet, replay     Tab  map <-> sheet     [ ]  replay step",
		"L  route labels     H  this card     Esc  close card",
		"Dots (bottom): connected, sides matched, equal distance, way round, approaches, choices, objective, distinct.",
		"Pieces: house = home, arch = gate, hexagon = crossing, triangle = heights, diamond = prize,",
		"ring = commons, star = objective, dashed = hidden. Thick lane = wide route; pinched = choke;",
		"ticks along a lane = closed sides; dashed lane = spur or hidden way; wiggle = winding route.",
	]
	var w := 700.0
	var h := lines.size() * 20.0 + 20.0
	var r := Rect2((sz.x - w) * 0.5, (sz.y - h) * 0.5, w, h)
	draw_rect(r, Color(0.02, 0.03, 0.04, 0.95))
	draw_rect(r, Color(0.4, 0.45, 0.52), false, 1.0)
	for i in lines.size():
		draw_string(font, r.position + Vector2(14, 26 + i * 20.0), lines[i], HORIZONTAL_ALIGNMENT_LEFT, w - 28, 13, INK)
