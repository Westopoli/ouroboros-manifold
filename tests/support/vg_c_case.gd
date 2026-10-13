extends SceneTree

# Shared base for the visible-game lane C tests (docs/northstar/plans/2026-10-07-visible-game-spec.md
# rev 4, lane C and section 2). A test overrides _run(); _check() records, _load() reports a missing
# script as a failure (the red-on-main reason) instead of crashing.

const SCENES := "res://scenes/ground3d/"
const TCAM := "res://scenes/tactical_c/"
const FIXTURE := "res://tests/support/vg_c_fixture.gd"

var _passed := 0
var _failed: Array[String] = []


func _initialize() -> void:
	await _run()
	print("PASS: %d  FAIL: %d" % [_passed, _failed.size()])
	for m in _failed:
		print("  - " + m)
	print("=== RED ===" if _failed.size() > 0 else "=== GREEN ===")
	quit(1 if _failed.size() > 0 else 0)


func _run() -> void:
	pass


func _check(cond: bool, msg: String) -> void:
	if cond:
		_passed += 1
	else:
		_failed.append(msg)


func _load(path: String) -> GDScript:
	var s = load(path) if ResourceLoader.exists(path) else null
	_check(s is GDScript, "missing script (the piece is not built): " + path)
	return s as GDScript


func _fixture() -> GDScript:
	return load(FIXTURE) as GDScript


# Lane C10 helpers: two different non-uniform projectors (world wu -> screen px). A re-projected layer must
# follow whichever one it is given (rulebook row 31; spec lane C "C10 re-projection").
static func proj_a(w: Vector2) -> Vector2:
	return Vector2(w.x * 0.5 + w.y * 0.1 + 30.0, w.y * 0.3 + 20.0)


static func proj_b(w: Vector2) -> Vector2:
	return Vector2(w.x * 0.2 + 400.0, w.y * 0.7 - w.x * 0.05)


static func has_near(got: Array, want: Vector2) -> bool:
	for g in got:
		if g is Vector2 and (g as Vector2).distance_to(want) < 0.5:
			return true
	return false


# Runs one C10 layer: `path`, expected world points, an optional builder for the frame sequence.
# The layer must expose set_projector(Callable), set_frame(frame, mission, local_faction), screen_points() -> Array[Vector2].
func _c10(path: String, story: String, want_world: Array, frames: Array) -> void:
	var s := _load(path)
	if s == null:
		return
	var fx := _fixture()
	for pair in [[Callable(self, "proj_a"), Callable(self, "proj_b")], [Callable(self, "proj_b"), Callable(self, "proj_a")]]:
		var layer = s.new()
		root.add_child(layer)
		await process_frame
		_check(layer.has_method("set_projector") and layer.has_method("screen_points"), "%s: %s lacks set_projector/screen_points" % [story, path])
		if not (layer.has_method("set_projector") and layer.has_method("screen_points")):
			return
		layer.set_projector(pair[0])
		for f in frames:
			layer.set_frame(f, fx.mission(), 0)
		var got: Array = layer.screen_points()
		for w in want_world:
			_check(has_near(got, pair[0].call(w)), "%s: no drawn point at the projection of %s (got %s)" % [story, w, got])
			# CONTROL: the other projector's image of the same world point must be absent
			_check(not has_near(got, pair[1].call(w)), "CONTROL %s: output also matches the other projector for %s" % [story, w])
