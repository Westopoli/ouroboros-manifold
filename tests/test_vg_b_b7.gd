extends SceneTree
# test-timeout: 20000

# Lane B piece B7 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B;
# preflight_2026-10-07/3-galaxy-field.md; bible E-16 S-106/S-107/S-108): territory ownership
# change is tweened, never snapped. res://scenes/galaxy/territory_tween.gd, class TerritoryTween (RefCounted):
#   const DURATION_S := 2.0
#   func start(region_id: int, old_owner: int, new_owner: int, now_s: float) -> void
#   func step(now_s: float) -> Array      # of {region: int, owner: int, scale: float}
#   func active_count() -> int
# The field holds one owner per region, so step() returns ONE entry per active region (Architect
# ruling 2026-10-08, TD-VG-B-4): during the first half (0 to 1.0 s) the old owner with scale 1.0 -> 0.0
# (linear), during the second half (1.0 to 2.0 s) the new owner with scale 0.0 -> 1.0; at/after 2.0 s the
# first step returns the new owner at 1.0 and the region leaves the active set (active_count() 0).
# A second start on the same region replaces the first: its old owner is the previous start's new owner.
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


func _entry(entries: Array, region: int) -> Dictionary:
	for e in entries:
		if int(e.get("region", -999)) == region:
			return e
	return {}


func _scale_of(entries: Array, region: int) -> float:
	return float(_entry(entries, region).get("scale", -1.0))


func _owner_of(entries: Array, region: int) -> int:
	return int(_entry(entries, region).get("owner", -999))


func _max_jump(seq: Array) -> float:
	# seq: scales of the single entry per 0.1 s step; largest change between steps.
	var m := 0.0
	for i in range(1, seq.size()):
		m = maxf(m, absf(seq[i] - seq[i - 1]))
	return m


func _controls() -> void:
	var snap := [1.0, 1.0, 0.0, 1.0]
	_check("B7-control-jump", _max_jump(snap) > 0.6, "control: a snapping sequence must measure a jump over 0.6, got %f" % _max_jump(snap))
	var smooth := [1.0, 0.95, 0.9, 0.85]
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

	# One entry per region; scales at 0, 0.5, 1.0, 1.5, 2.0, 2.5 s; region 7, owner 3 -> 5, started at t = 10.
	tw.start(7, 3, 5, 10.0)
	_check("B7-active-count", tw.active_count() == 1, "one tween running, active_count=%d" % tw.active_count())
	var r0: Array = tw.step(10.0)
	_check("B7-one-entry", r0.size() == 1 and int(r0[0].get("region", -1)) == 7, "exactly one entry, region 7, while active: %s" % [r0])
	_check("B7-t0", _owner_of(r0, 7) == 3 and absf(_scale_of(r0, 7) - 1.0) < EPS, "t=0: old owner 3 at 1.0; got %s" % [r0])
	var r05: Array = tw.step(10.5)
	_check("B7-t0.5", r05.size() == 1 and _owner_of(r05, 7) == 3 and absf(_scale_of(r05, 7) - 0.5) < EPS, "t=0.5: old owner 3 at 0.5; got %s" % [r05])
	var r1: Array = tw.step(11.0)
	_check("B7-t1.0", r1.size() == 1 and _owner_of(r1, 7) == 5 and absf(_scale_of(r1, 7)) < EPS, "t=1.0: switch happens at scale 0: new owner 5 at 0.0; got %s" % [r1])
	_check("B7-still-active", tw.active_count() == 1, "still active at t=1.0")
	var r15: Array = tw.step(11.5)
	_check("B7-t1.5", r15.size() == 1 and _owner_of(r15, 7) == 5 and absf(_scale_of(r15, 7) - 0.5) < EPS, "t=1.5: new owner 5 at 0.5; got %s" % [r15])
	_check("B7-still-active-1.5", tw.active_count() == 1, "still active at t=1.5")
	var r2: Array = tw.step(12.0)
	_check("B7-t2.0", r2.size() == 1 and _owner_of(r2, 7) == 5 and absf(_scale_of(r2, 7) - 1.0) < EPS, "t=2.0: new owner 5 at 1.0; got %s" % [r2])
	_check("B7-done-count", tw.active_count() == 0, "finished tween is no longer active, active_count=%d" % tw.active_count())

	var tw2 = script.new()
	tw2.start(7, 3, 5, 10.0)
	var r25: Array = tw2.step(12.5)
	_check("B7-t2.5", r25.size() == 1 and _owner_of(r25, 7) == 5 and absf(_scale_of(r25, 7) - 1.0) < EPS, "t=2.5 (past the end): new owner 5 at 1.0; got %s" % [r25])
	_check("B7-t2.5-count", tw2.active_count() == 0, "past-the-end step clears active_count")

	# Two regions at once: one entry each.
	var tw3 = script.new()
	tw3.start(1, 0, 2, 0.0)
	tw3.start(2, 4, 6, 0.5)
	_check("B7-two-regions", tw3.active_count() == 2, "two regions tween at once, active_count=%d" % tw3.active_count())
	var rr: Array = tw3.step(1.0)
	_check("B7-two-regions-entries", rr.size() == 2 and _owner_of(rr, 1) == 2 and absf(_scale_of(rr, 1)) < EPS and _owner_of(rr, 2) == 4 and absf(_scale_of(rr, 2) - 0.5) < EPS, "one entry per region (1: owner 2 at 0.0; 2: owner 4 at 0.5): %s" % [rr])

	# A second start on the same region replaces the first; its old owner is the previous new owner.
	var tw4 = script.new()
	tw4.start(7, 3, 5, 0.0)
	tw4.step(0.5)
	tw4.start(7, 5, 9, 1.0)
	_check("B7-replace-count", tw4.active_count() == 1, "replacing start keeps one tween per region, active_count=%d" % tw4.active_count())
	var p0: Array = tw4.step(1.0)
	_check("B7-replace-t0", p0.size() == 1 and _owner_of(p0, 7) == 5 and absf(_scale_of(p0, 7) - 1.0) < EPS, "replacement t=0: old owner 5 at 1.0 (3 is gone); got %s" % [p0])
	var p1: Array = tw4.step(2.0)
	_check("B7-replace-t1.0", p1.size() == 1 and _owner_of(p1, 7) == 9 and absf(_scale_of(p1, 7)) < EPS, "replacement t=1.0 from its own start: new owner 9 at 0.0; got %s" % [p1])
	var p2: Array = tw4.step(3.0)
	_check("B7-replace-end", p2.size() == 1 and _owner_of(p2, 7) == 9 and absf(_scale_of(p2, 7) - 1.0) < EPS, "replacement ends on owner 9 at 1.0; got %s" % [p2])

	# Nothing snaps: steps 0.1 s apart never change the scale by more than 0.6, and the owner switch is at scale 0.
	var tw5 = script.new()
	tw5.start(7, 3, 5, 0.0)
	var seq: Array = []
	var owners: Array = []
	for i in range(0, 21):
		var es: Array = tw5.step(0.1 * i)
		seq.append(maxf(_scale_of(es, 7), 0.0))
		owners.append(_owner_of(es, 7))
	_check("B7-no-snap", _max_jump(seq) <= 0.6, "largest per-step scale change %f exceeds 0.6" % _max_jump(seq))
	var switch_scale := -1.0
	for i in range(1, owners.size()):
		if owners[i] != owners[i - 1]:
			switch_scale = minf(seq[i - 1], seq[i]) if switch_scale < 0.0 else switch_scale
	_check("B7-switch-at-zero", switch_scale >= 0.0 and switch_scale < 0.11, "the owner switch must happen at scale ~0 (steps are 0.1 s apart); scale at switch %f" % switch_scale)
	_check("B7-no-snap-ends", absf(seq[0] - 1.0) < EPS and owners[0] == 3 and absf(seq[20] - 1.0) < EPS and owners[20] == 5, "sequence runs owner 3 at 1.0 ... owner 5 at 1.0; first=%s/%s last=%s/%s" % [owners[0], seq[0], owners[20], seq[20]])
