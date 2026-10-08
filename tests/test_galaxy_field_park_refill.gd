extends SceneTree
# PARK file (lane B, B0 pre-check; spec 2026-10-07-visible-game-spec.md rev 4): REFILL, one whole-grid
# refill after an owner change on the game's 80-region fixture, median <= 12 ms. 12 ms is Westley's:
# a red here is parked for him, never widened by a builder. Same contract and run line as
# tests/test_galaxy_field_park_field_eq.gd (real Vulkan device; headless fails DEVICE on purpose).
# Method follows origin/push/galaxy-field gpu_checks.gd _check_refill: 14 alternating owner flips
# on one owned system, the first 2 discarded, median of the rest.
# See also: tests/test_galaxy_field_park_field_eq.gd.

const Fixture := preload("res://tests/galaxy_field/game_fixture.gd")
var FIELD_PATH := "res://scenes/galaxy/territory_field.gd"
const REFILL_MAX_MS := 12.0   # Westley's REFILL budget
const FLIPS := 14
const WARMUP := 2

var _failures := 0


func _initialize() -> void:
	await _run()
	print("REFILL PARK %s" % ("FAILED: %d" % _failures if _failures > 0 else "OK"))
	quit(1 if _failures > 0 else 0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _run() -> void:
	if OS.get_environment("TERRITORY_FIELD_SCRIPT") != "":
		FIELD_PATH = OS.get_environment("TERRITORY_FIELD_SCRIPT")
	var headless := DisplayServer.get_name() == "headless"
	_check("DEVICE", not headless, "renderer %s on %s" % [RenderingServer.get_video_adapter_name(), DisplayServer.get_name()])
	# Positive control: the median helper must flag a slow series.
	_check("REFILL-control-slow", not (_median([20.0, 21.0, 22.0]) <= REFILL_MAX_MS), "a 20 ms series must fail the budget")
	_check("REFILL-control-fast", _median([1.0, 2.0, 3.0]) <= REFILL_MAX_MS, "a 2 ms series must pass the budget")
	if not ResourceLoader.exists(FIELD_PATH):
		_check("REFILL", false, "%s does not exist" % FIELD_PATH)
		return
	if headless:
		return
	var field: Node = (load(FIELD_PATH) as GDScript).new()
	root.add_child(field)
	await process_frame
	await process_frame
	var systems := Fixture.systems()
	field.set_systems(systems.duplicate(true))
	field.refill()
	var sid := -1
	for i in systems.size():
		if int(systems[i].owner) == 0:
			sid = i
			break
	var times: Array = []
	var wired := true
	for i in FLIPS:
		field.set_system_owner(sid, 1 if i % 2 == 0 else 0)
		if not field.is_dirty():
			wired = false
		var t0 := Time.get_ticks_usec()
		field.refill()
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		if i >= WARMUP:
			times.append(ms)
		await process_frame
		await process_frame
	times.sort()
	_check("REFILL", wired and _median(times) <= REFILL_MAX_MS, "owner change marked the field dirty=%s; refill median %.2f ms max %.2f ms over %d (<= %.0f ms) on %s" % [wired, _median(times), times[times.size() - 1], times.size(), REFILL_MAX_MS, RenderingServer.get_video_adapter_name()])
	field.queue_free()


func _median(a: Array) -> float:
	var s := a.duplicate()
	s.sort()
	return float(s[s.size() / 2])
