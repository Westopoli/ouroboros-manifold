extends Control

## H-023 unit-scale scene: the drawing. Top-down plan of the stage at true scale (one pixel size for the whole stage) and a
## magnified gallery of each role beside a human-height reference. Reads the model; owns no numbers of its own except colours.

const Model := preload("res://scenes/proto/unit_scale/unit_scale_model.gd")

const ROLE_COLOURS := {
	"Raider": Color(0.95, 0.35, 0.30), "Interceptor": Color(0.95, 0.65, 0.25), "Vanguard": Color(0.90, 0.85, 0.30),
	"Warden": Color(0.35, 0.80, 0.45), "Bombard": Color(0.35, 0.65, 0.95), "Bastion": Color(0.70, 0.45, 0.90),
}
const GROUND := Color(0.16, 0.20, 0.17)
const LINE := Color(0.85, 0.88, 0.85)
const GALLERY_PX_PER_WU := 3.0  # DRAFT-gallery-magnification: the gallery draws 3 px per world unit; the stage draws far fewer

var values: Dictionary = {}
var stage_rect := Rect2()    # where the stage is drawn, in this control's pixels
var gallery_rect := Rect2()  # where the gallery is drawn
var _font: Font = ThemeDB.fallback_font


func stage_px_per_wu() -> float:
	return stage_rect.size.x / Model.STAGE_W


func _p(w: Vector2) -> Vector2:
	return stage_rect.position + w * stage_px_per_wu()


func _text(pos: Vector2, s: String, size: int = 13, col: Color = LINE) -> void:
	draw_string(_font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


func _dashed_circle(c: Vector2, r_px: float, col: Color) -> void:
	var n := 40
	for i in n:
		if i % 2 == 0:
			draw_arc(c, r_px, TAU * i / n, TAU * (i + 1) / n, 4, col, 1.5)


func _draw() -> void:
	_draw_stage()
	_draw_gallery()


func _draw_stage() -> void:
	var k := stage_px_per_wu()
	draw_rect(stage_rect, GROUND)
	# slope with height bands (three bands, one LAYER_STEP_WU apart, along SLOPE_LENGTH)
	var band_w := Model.SLOPE_LENGTH / 3.0
	for b in 3:
		var shade := 0.25 + 0.17 * b
		draw_rect(Rect2(_p(Vector2(3000.0 + b * band_w, 300.0)), Vector2(band_w, 300.0) * k), Color(shade, shade * 0.9, shade * 0.6))
		_text(_p(Vector2(3000.0 + b * band_w + 20.0, 340.0)), "band %d" % b, 11)
		_text(_p(Vector2(3000.0 + b * band_w + 20.0, 440.0)), "+%d wu" % int(b * Model.LAYER_STEP_WU), 11)
	_text(_p(Vector2(3000.0, 270.0)), "slope, 600 wu, height bands", 12)
	# city footprint with buildings, and the objective inside it
	var cc := _p(Model.CITY_CENTRE)
	draw_circle(cc, Model.CITY_RADIUS * k, Color(0.30, 0.30, 0.36))
	for i in 9:
		var off := Vector2(((i % 3) - 1) * 220.0, ((i / 3) - 1) * 200.0)
		draw_rect(Rect2(_p(Model.CITY_CENTRE + off - Vector2(70.0, 60.0)), Vector2(140.0, 120.0) * k), Color(0.50, 0.50, 0.58))
	_dashed_circle(cc, Model.CAPTURE_RADIUS * k, Color(1.0, 0.9, 0.3))
	draw_circle(cc, 5.0, Color(1.0, 0.9, 0.3))
	_text(cc + Vector2(-60.0, -Model.CITY_RADIUS * k - 6.0), "city footprint (r %d wu)" % int(Model.CITY_RADIUS), 12)
	_text(cc + Vector2(-50.0, 18.0), "objective (capture r 300)", 11, Color(1.0, 0.9, 0.3))
	# staging zone
	var sp := _p(Vector2(400.0, 1100.0))
	draw_rect(Rect2(sp - Vector2(250.0, 250.0) * k, Vector2(500.0, 500.0) * k), Color(0.25, 0.35, 0.50, 0.5), false, 1.5)
	_text(sp + Vector2(-60.0, -250.0 * k - 6.0), "staging", 12)
	# the six roles standing at true scale in the staging zone
	for i in Model.ROLES.size():
		var role: String = Model.ROLES[i]
		var pos := sp + Vector2((i % 3 - 1) * 120.0, (i / 3 - 0.5) * 120.0) * k
		var v: Dictionary = values[role]
		draw_circle(pos, float(v["visual_scale"]) * Model.BASE_RADIUS * k, ROLE_COLOURS[role])
		draw_arc(pos, float(v["radius"]) * k, 0.0, TAU, 16, Color.WHITE, 1.0)
	# transit
	var t0 := _p(Vector2(700.0, 1100.0))
	var t1 := _p(Vector2(1450.0, 1100.0))
	draw_line(t0, t1, Color(0.6, 0.8, 1.0), 2.0)
	draw_line(t1, t1 + Vector2(-8.0, -5.0), Color(0.6, 0.8, 1.0), 2.0)
	draw_line(t1, t1 + Vector2(-8.0, 5.0), Color(0.6, 0.8, 1.0), 2.0)
	_text(_p(Vector2(850.0, 1060.0)), "transit", 12, Color(0.6, 0.8, 1.0))
	# chokepoint: two walls with a CHOKE_WIDTH gap, and the ALG-71 obstacle radius
	var gap_top := Model.CHOKE_CENTRE.y - Model.CHOKE_WIDTH / 2.0
	var gap_bot := Model.CHOKE_CENTRE.y + Model.CHOKE_WIDTH / 2.0
	draw_rect(Rect2(_p(Vector2(1600.0, 0.0)), Vector2(300.0, gap_top) * k), Color(0.45, 0.38, 0.30))
	draw_rect(Rect2(_p(Vector2(1600.0, gap_bot)), Vector2(300.0, Model.STAGE_H - gap_bot) * k), Color(0.45, 0.38, 0.30))
	_dashed_circle(_p(Model.CHOKE_CENTRE), Model.CHOKE_RADIUS * k, Color(0.9, 0.6, 0.3))
	_text(_p(Vector2(1230.0, 1260.0)), "chokepoint (gap %d wu, r 600)" % int(Model.CHOKE_WIDTH), 12, Color(0.9, 0.6, 0.3))
	# flank route
	var fr := [Vector2(550.0, 1350.0), Vector2(1000.0, 1950.0), Vector2(2400.0, 2000.0), Vector2(2900.0, 1900.0)]
	for i in fr.size() - 1:
		draw_dashed_line(_p(fr[i]), _p(fr[i + 1]), Color(0.5, 0.9, 0.5), 2.0, 6.0)
	_text(_p(Vector2(1300.0, 2100.0)), "flank_route", 12, Color(0.5, 0.9, 0.5))
	# vantage
	var vp := _p(Vector2(2200.0, 450.0))
	draw_colored_polygon(PackedVector2Array([vp + Vector2(0.0, -12.0), vp + Vector2(-12.0, 8.0), vp + Vector2(12.0, 8.0)]), Color(0.9, 0.9, 0.5))
	_dashed_circle(vp, Model.VANTAGE_RADIUS * k, Color(0.9, 0.9, 0.5))
	_text(vp + Vector2(14.0, 6.0), "vantage (r 700)", 12, Color(0.9, 0.9, 0.5))
	# hazard anchor
	var hp := _p(Vector2(2500.0, 1700.0))
	draw_circle(hp, 6.0, Color(0.95, 0.25, 0.25))
	_dashed_circle(hp, Model.HAZARD_RADIUS * k, Color(0.95, 0.25, 0.25))
	_text(hp + Vector2(-40.0, 20.0), "hazard_anchor (r 500)", 12, Color(0.95, 0.25, 0.25))
	# cover obstacles
	for c in [Vector2(2100.0, 1050.0), Vector2(2250.0, 1150.0), Vector2(2380.0, 1040.0)]:
		draw_rect(Rect2(_p(c), Vector2(120.0, 60.0) * k), Color(0.40, 0.45, 0.40))
	_text(_p(Vector2(2050.0, 1000.0)), "cover obstacle", 12)
	draw_rect(stage_rect, LINE, false, 1.5)


func _draw_gallery() -> void:
	draw_rect(gallery_rect, Color(0.10, 0.11, 0.13))
	var cell := gallery_rect.size.x / Model.ROLES.size()
	var base_y := gallery_rect.end.y - 50.0
	var hh := Model.human_height_wu() * GALLERY_PX_PER_WU
	var hw := Model.human_shoulder_wu() * GALLERY_PX_PER_WU
	for i in Model.ROLES.size():
		var role: String = Model.ROLES[i]
		var v: Dictionary = values[role]
		var cx := gallery_rect.position.x + cell * (i + 0.5)
		var r_vis := float(v["visual_scale"]) * Model.BASE_RADIUS * GALLERY_PX_PER_WU
		var r_col := float(v["radius"]) * GALLERY_PX_PER_WU
		var uc := Vector2(cx + 20.0, base_y - maxf(r_vis, r_col))
		draw_circle(uc, r_vis, ROLE_COLOURS[role])
		draw_arc(uc, r_col, 0.0, TAU, 48, Color.WHITE, 1.5)
		# human reference: shoulders hw wide, hh tall, standing beside the unit footprint (plan footprint is a circle, human is drawn upright)
		var hx := cx - cell * 0.5 + 18.0
		draw_rect(Rect2(Vector2(hx, base_y - hh), Vector2(hw, hh)), Color(0.9, 0.8, 0.7))
		_text(Vector2(cx - cell * 0.5 + 6.0, base_y + 16.0), "human 1.8 m = %d wu" % int(Model.human_height_wu()), 10)
		_text(Vector2(cx - cell * 0.5 + 6.0, base_y + 32.0), "%s  r %.1f wu" % [role, float(v["radius"])], 12, ROLE_COLOURS[role])
	_text(gallery_rect.position + Vector2(6.0, 14.0), "gallery at %d px per wu: filled = visual body, white ring = collision radius, tan bar = human (plan footprint; height of units not modelled)" % int(GALLERY_PX_PER_WU), 11)
