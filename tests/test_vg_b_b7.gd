extends SceneTree
# test-timeout: 20000

# Lane B piece B7 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B;
# preflight_2026-10-07/3-galaxy-field.md; bible E-16 S-106/S-107/S-108): territory ownership
# change is tweened, never snapped. res://scenes/galaxy/territory_tween.gd, class TerritoryTween (RefCounted):
#   const DURATION_S := 2.0
#   func start(region_id: int, old_owner: int, new_owner: int, now_s: float) -> void
#   func step(now_s: float) -> Array      # of {region: int, owner: int, scale: float}
#   func active_count() -> int
# Over DURATION_S the old owner's scale goes 1.0 -> 0.0 and the new owner's 0.0 -> 1.0 (linear);
# both entries are present while active; at/after the end step returns only the new owner at 1.0
# (the first such step; later steps are not specified here), and active_count() is 0.
# A second start on the same region replaces the first: its old owner is the previous new owner.
# galaxy_view.gd (B14) feeds field.update_system(region, owner, significance * scale) per entry.
#   ~/.local/bin/godot.real --headless --path . -s tests/test_vg_b_b7.gd

const TARGET := "res://scenes/galaxy/territory_tween.gd"
const EPS := 0.001

var _pass := 0
var _fail := 0
var _msgs: Array = []


func _initialize() -> void:
	_run()
	print("\n=== VG-B B7 territory tween ===")
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


func _scale_of(entries: Array, owner: int) -> float:
	for e in entries:
		if int(e.get("owner", -999)) == owner:
			return float(e.get("scale", -1.0))
	return -1.0


func _has(entries: Array, owner: int) -> bool:
	return _scale_of(entries, owner) >= 0.0


func _max_jump(seq: Array) -> float:
	# seq: Array of [old_scale, new_scale] per 0.1 s step; largest change of either scale.
	var m := 0.0
	for i in range(1, seq.size()):
		m = maxf(m, absf(seq[i][0] - seq[i - 1][0]))
		m = maxf(m, absf(seq[i][1] - seq[i - 1][1]))
	return m


func _controls() -> void:
	var snap := [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
	_check("B7-control-jump", _max_jump(snap) > 0.6, "control: a snapping sequence must measure a jump over 0.6, got %f" % _max_jump(snap))
	var smooth := [[1.0, 0.0], [0.95, 0.05], [0.9, 0.1]]
	_check("B7-control-smooth", _max_jump(smooth) <= 0.6, "control: a smooth sequence must measure at most 0.6")


func _run() -> void:
	_controls()
	var exists := FileAccess.file_exists(TARGET)
	_check("B7-exists", exists, "missing feature: %s does not exist (territory tween not written)" % TARGET)
	if not exists:
		return
	var script = load(TARGET)
	_check("B7-loads", script != null and script.can_instantiate(), "%s did not load as an instantiable script" % TARGET)
	if script == null or not script.can_instantiate():
		return
	var tw = script.new()
	_check("B7-duration", float(script.get_script_constant_map().get("DURATION_S", -1.0)) == 2.0, "DURATION_S must be 2.0")
	_check("B7-idle", tw.active_count() == 0 and tw.step(0.0).is_empty(), "a fresh tween has no active entries and steps to []")

	# Linear scales at 0, 0.5, 1.0, 2.0, 2.5 s; region 7, owner 3 -> 5, started at t = 10.
	tw.start(7, 3, 5, 10.0)
	_check("B7-active-count", tw.active_count() == 1, "one tween running, active_count=%d" % tw.active_count())
	var r0: Array = tw.step(10.0)
	_check("B7-both-present", r0.size() == 2 and _has(r0, 3) and _has(r0, 5), "both owners present while active: %s" % [r0])
	_check("B7-region-field", r0.all(func(e): return int(e.get("region", -1)) == 7), "every entry carries region 7: %s" % [r0])
	_check("B7-t0", absf(_scale_of(r0, 3) - 1.0) < EPS and absf(_scale_of(r0, 5)) < EPS, "t=0: old 1.0, new 0.0; got %s" % [r0])
	var r05: Array = tw.step(10.5)
	_check("B7-t0.5", absf(_scale_of(r05, 3) - 0.75) < EPS and absf(_scale_of(r05, 5) - 0.25) < EPS, "t=0.5: old 0.75, new 0.25; got %s" % [r05])
	var r1: Array = tw.step(11.0)
	_check("B7-t1.0", absf(_scale_of(r1, 3) - 0.5) < EPS and absf(_scale_of(r1, 5) - 0.5) < EPS, "t=1.0: both 0.5; got %s" % [r1])
	_check("B7-both-present-1", r1.size() == 2, "both entries at t=1.0: %s" % [r1])
	_check("B7-still-active", tw.active_count() == 1, "still active at t=1.0")
	var r2: Array = tw.step(12.0)
	_check("B7-t2.0", r2.size() == 1 and _has(r2, 5) and absf(_scale_of(r2, 5) - 1.0) < EPS and not _has(r2, 3), "t=2.0: only the new owner at 1.0; got %s" % [r2])
	_check("B7-done-count", tw.active_count() == 0, "finished tween is no longer active, active_count=%d" % tw.active_count())

	var tw2 = script.new()
	tw2.start(7, 3, 5, 10.0)
	var r25: Array = tw2.step(12.5)
	_check("B7-t2.5", r25.size() == 1 and absf(_scale_of(r25, 5) - 1.0) < EPS and not _has(r25, 3), "t=2.5 (past the end): only the new owner at 1.0; got %s" % [r25])
	_check("B7-t2.5-count", tw2.active_count() == 0, "past-the-end step clears active_count")

	# Two regions at once.
	var tw3 = script.new()
	tw3.start(1, 0, 2, 0.0)
	tw3.start(2, 4, 6, 0.5)
	_check("B7-two-regions", tw3.active_count() == 2, "two regions tween at once, active_count=%d" % tw3.active_count())
	var rr: Array = tw3.step(1.0)
	var regions := {}
	for e in rr:
		regions[int(e.get("region", -1))] = true
	_check("B7-two-regions-entries", rr.size() == 4 and regions.has(1) and regions.has(2), "four entries over regions 1 and 2: %s" % [rr])

	# A second start on the same region replaces the first; its old owner is the previous new owner.
	var tw4 = script.new()
	tw4.start(7, 3, 5, 0.0)
	tw4.step(0.5)
	tw4.start(7, 5, 9, 1.0)
	_check("B7-replace-count", tw4.active_count() == 1, "replacing start keeps one tween per region, active_count=%d" % tw4.active_count())
	var p0: Array = tw4.step(1.0)
	_check("B7-replace-t0", _has(p0, 5) and _has(p0, 9) and not _has(p0, 3), "after the replacing start only owners 5 and 9 appear (3 is gone): %s" % [p0])
	_check("B7-replace-scales", absf(_scale_of(p0, 5) - 1.0) < EPS and absf(_scale_of(p0, 9)) < EPS, "replacement t=0: old(5) 1.0, new(9) 0.0; got %s" % [p0])
	var p1: Array = tw4.step(2.0)
	_check("B7-replace-t1.0", absf(_scale_of(p1, 5) - 0.5) < EPS and absf(_scale_of(p1, 9) - 0.5) < EPS, "replacement t=1.0 from its own start: both 0.5; got %s" % [p1])
	var p2: Array = tw4.step(3.0)
	_check("B7-replace-end", p2.size() == 1 and _has(p2, 9) and absf(_scale_of(p2, 9) - 1.0) < EPS, "replacement ends on owner 9 at 1.0; got %s" % [p2])

	# Nothing snaps: steps 0.1 s apart never jump a scale by more than 0.6, across the end too.
	var tw5 = script.new()
	tw5.start(7, 3, 5, 0.0)
	var seq: Array = []
	for i in range(0, 31):
		var es: Array = tw5.step(0.1 * i)
		var o := _scale_of(es, 3)
		var n := _scale_of(es, 5)
		seq.append([maxf(o, 0.0), maxf(n, 0.0)])
	_check("B7-no-snap", _max_jump(seq) <= 0.6, "largest per-step scale jump %f exceeds 0.6" % _max_jump(seq))
	_check("B7-no-snap-ends", absf(seq[0][0] - 1.0) < EPS and absf(seq[30][1] - 1.0) < EPS and absf(seq[30][0]) < EPS, "sequence runs old 1.0 -> 0.0 and new 0.0 -> 1.0; first=%s last=%s" % [seq[0], seq[30]])
