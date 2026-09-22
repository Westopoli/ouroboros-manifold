extends Control

const STAR_COUNT := 220
const CORE_RADIUS := 34.0
const ROTATE_SPEED := 0.015

var _stars: Array = []
var _t := 0.0
var _seed := 11


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.7
	_generate(_seed)
	set_process(true)


func qa_seed(n: int) -> void:
	_seed = n
	_generate(n)


func _generate(n: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = n
	_stars.clear()
	for i in range(STAR_COUNT):
		_stars.append({
			"r": rng.randf_range(40.0, 900.0),
			"a": rng.randf_range(0.0, TAU),
			"s": rng.randf_range(1.0, 3.0),
			"bright": rng.randf() < 0.18,
		})
	queue_redraw()


func _process(delta: float) -> void:
	if not visible:
		return
	_t += delta
	queue_redraw()


func _draw() -> void:
	var center: Vector2 = size * 0.5
	var core: Vector2 = center + Vector2(120.0, 0.0)
	for star in _stars:
		var angle: float = star.a + _t * ROTATE_SPEED
		var pos: Vector2 = center + Vector2(cos(angle), sin(angle)) * star.r
		var col: Color = Color(0.85, 0.78, 0.55, 0.9) if star.bright else Color(0.6, 0.6, 0.65, 0.5)
		draw_rect(Rect2(pos, Vector2(star.s, star.s)), col)
	draw_circle(core, CORE_RADIUS * 2.2, Color(0.92, 0.90, 0.75, 0.12))
	draw_circle(core, CORE_RADIUS, Color(0.92, 0.90, 0.75, 0.95))
