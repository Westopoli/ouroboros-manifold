extends SceneTree

# Transition mockup, pass 1 (docs/northstar/plans/2026-10-15-transition-mockup-spec.md; E-16 S-108).
# Tests first: every check below is RED until scenes/mockups/transition/transition_mockup.tscn exists.
#
#  T1 scene-instances-without-pipe   S-108 / R-108-03 (nothing the scene needs is the C sim; Mac, no pipe)
#  T2 five-shots-not-uniform         S-108 / R-108-03 (no cut, no fade to black: no shot is a blank or
#                                    near-uniform frame), R-108-01 (pull-back frame exists), R-108-06
#                                    (next battlefield materialises: shot 05 exists)
#  T3 camera-distance-monotone       R-108-01 (eased pull-back: distance to origin never falls while
#                                    pulling back), R-108-06 (push-in: never rises), R-108-03 (no snap)
#  T4 panel-38-percent-while-printing R-108-02 (galaxy resizes to 62 percent, panel is the other 38),
#                                    R-069-03 (lines print one at a time), R-108-05 (Proceed appears
#                                    after the last line)
#  CONTROL a stub Node3D with no camera motion that T3's checker must flag (and a good curve it must pass).
#
# Contract this test defines for the builder (the spec names only `--shot`):
#   - the mockup root has `camera_path_samples: Array` of floats, the camera's distance to the
#     battlefield origin, appended once per 0.1 s of scene time from the first frame, never cleared
#     until R resets;
#   - the mockup root has `panel_width_fraction: float`, scroll-panel width / viewport width (0 when
#     the panel is out);
#   - Space (key event reaching the viewport) starts the move; a visible Button whose text contains
#     "Proceed" appears when the last chronicle line has printed, and pressing it starts the push-in.
# Names this test chose where the spec is silent:
#   - pull-back / push-in are split at the first maximum of camera_path_samples (the galaxy hold is the
#     plateau at the top); samples must rise by at least DRAFT-min-travel and the last must fall below
#     the maximum by the same;
#   - "while printing" = the last panel_width_fraction read before the Proceed button becomes visible;
#   - near-uniform = busyness (the gate's frame_busyness in scripts/specfactory/merge_gate_support.py:
#     fraction of pixels not at the modal luminance) below DRAFT-look-busyness, OR luminance stddev
#     below DRAFT-look-stddev. The gate's own look stage has no threshold yet (warn-only), so both are drafts.
# Child Godot processes run windowed (a --headless renderer cannot save a viewport PNG).

const MOCKUP := "res://scenes/mockups/transition/transition_mockup.tscn"
const SHOTS := ["01_battlefield.png", "02_pullback_mid.png", "03_galaxy.png", "04_pushin_mid.png", "05_next_battlefield.png"]
const DRAFT_LOOK_STDDEV := 8.0
const DRAFT_LOOK_BUSYNESS := 0.02
const DRAFT_MIN_TRAVEL := 1.0       # world units of distance the camera must gain and lose
const EPS := 1e-4
const PANEL_FRACTION := 0.38
const PANEL_TOL := 0.01
const DRIVE_TIMEOUT_MS := 90000
const SHOT_TIMEOUT_S := 120

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Transition Mockup Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	await _test_positive_control()
	var packed = load(MOCKUP) if ResourceLoader.exists(MOCKUP) else null
	# T1
	_assert(packed is PackedScene, "T1 [S-108/R-108-03] %s does not exist or does not load as a PackedScene (scene missing)" % MOCKUP)
	var inst: Node = null
	if packed is PackedScene:
		inst = packed.instantiate()
	_assert(inst != null, "T1 [S-108/R-108-03] %s did not instantiate (scene missing)" % MOCKUP)
	# T2
	_test_shots()
	# T3 and T4 drive one live instance
	if inst == null:
		_assert(false, "T3 [R-108-01/R-108-06] no mockup instance to read camera_path_samples from (scene missing)")
		_assert(false, "T4 [R-108-02/R-069-03/R-108-05] no mockup instance to read panel_width_fraction from (scene missing)")
		return
	await _test_live(inst)


# ---------------------------------------------------------------- T2

func _test_shots() -> void:
	var dir := OS.get_temp_dir().path_join("om_transition_shots_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(dir)
	var out: Array = []
	var code := OS.execute(OS.get_executable_path(),
		["--path", ProjectSettings.globalize_path("res://"), MOCKUP, "--", "--shot", dir],
		out, true)
	_assert(code == 0, "T2 [S-108] the scene run with --shot %s exited %d, not 0 (scene missing)" % [dir, code])
	for name in SHOTS:
		var p := dir.path_join(name)
		var exists := FileAccess.file_exists(p)
		_assert(exists, "T2 [S-108/R-108-03] shot %s was not written to the --shot dir (scene missing)" % name)
		if not exists:
			continue
		var img := Image.load_from_file(p)
		_assert(img != null and not img.is_empty(), "T2 [S-108] shot %s is not a readable PNG" % name)
		if img == null or img.is_empty():
			continue
		var st := _frame_stats(img)
		_assert(st.busyness >= DRAFT_LOOK_BUSYNESS and st.stddev >= DRAFT_LOOK_STDDEV,
			"T2 [R-108-03] shot %s is near-uniform: busyness %.4f (min %.2f), luminance stddev %.2f (min %.1f)" % [name, st.busyness, DRAFT_LOOK_BUSYNESS, st.stddev, DRAFT_LOOK_STDDEV])
	# the positive control of the detector itself: a flat frame must read as near-uniform
	var flat := Image.create(64, 64, false, Image.FORMAT_RGB8)
	flat.fill(Color(0.1, 0.1, 0.1))
	var fs := _frame_stats(flat)
	_assert(fs.busyness < DRAFT_LOOK_BUSYNESS and fs.stddev < DRAFT_LOOK_STDDEV, "CONTROL-T2 a flat frame was not flagged near-uniform")
	DirAccess.remove_absolute(dir)


func _frame_stats(img: Image) -> Dictionary:
	var w := img.get_width()
	var h := img.get_height()
	var counts := {}
	var sum := 0.0
	var sumsq := 0.0
	var n := w * h
	for y in range(h):
		for x in range(w):
			var c := img.get_pixel(x, y)
			var l := int(round((c.r * 0.299 + c.g * 0.587 + c.b * 0.114) * 255.0))
			counts[l] = int(counts.get(l, 0)) + 1
			sum += l
			sumsq += float(l) * l
	var mx := 0
	for k in counts:
		mx = max(mx, int(counts[k]))
	var mean := sum / n
	return {"busyness": 1.0 - float(mx) / n, "stddev": sqrt(max(0.0, sumsq / n - mean * mean))}


# ---------------------------------------------------------------- T3 checker

# Returns "" when the samples rise (non-decreasing) to their first maximum then fall
# (non-increasing) after it, with real travel both ways; else the first problem found.
func _shape_problem(samples: Array) -> String:
	if samples.size() < 10:
		return "only %d samples (need at least 10)" % samples.size()
	var peak := 0
	for i in range(samples.size()):
		if float(samples[i]) > float(samples[peak]) + EPS:
			peak = i
	for i in range(1, peak + 1):
		if float(samples[i]) < float(samples[i - 1]) - EPS:
			return "pull-back not monotone non-decreasing at sample %d (%.4f -> %.4f)" % [i, samples[i - 1], samples[i]]
	for i in range(peak + 1, samples.size()):
		if float(samples[i]) > float(samples[i - 1]) + EPS:
			return "push-in not monotone non-increasing at sample %d (%.4f -> %.4f)" % [i, samples[i - 1], samples[i]]
	if float(samples[peak]) - float(samples[0]) < DRAFT_MIN_TRAVEL:
		return "camera gained only %.4f distance in the pull-back (min %.1f): no camera motion" % [float(samples[peak]) - float(samples[0]), DRAFT_MIN_TRAVEL]
	if float(samples[peak]) - float(samples[samples.size() - 1]) < DRAFT_MIN_TRAVEL:
		return "camera lost only %.4f distance in the push-in (min %.1f)" % [float(samples[peak]) - float(samples[samples.size() - 1]), DRAFT_MIN_TRAVEL]
	return ""


func _test_positive_control() -> void:
	var stub := Node3D.new()
	var s: Array = []
	for i in range(100):
		s.append(50.0)
	stub.set("position", Vector3.ZERO)
	var problem := _shape_problem(s)
	_assert(problem != "", "CONTROL-T3 a stub with no camera motion was NOT flagged by the monotone check")
	if problem != "":
		print("CONTROL-T3 stub flagged as intended: " + problem)
	# a wobble in the pull-back must be flagged too
	var wob: Array = [10.0, 20.0, 30.0, 25.0, 40.0, 60.0, 60.0, 50.0, 30.0, 10.0]
	_assert(_shape_problem(wob) != "", "CONTROL-T3 a pull-back with a dip was NOT flagged")
	# and a clean eased curve must pass, so the check can go green
	var good: Array = []
	for i in range(30):
		good.append(10.0 + 90.0 * smoothstep(0.0, 1.0, i / 29.0))
	for i in range(10):
		good.append(100.0)
	for i in range(30):
		good.append(100.0 - 90.0 * smoothstep(0.0, 1.0, i / 29.0))
	_assert(_shape_problem(good) == "", "CONTROL-T3 a clean pull-back, hold and push-in was flagged: " + _shape_problem(good))
	stub.free()


# ---------------------------------------------------------------- T3 and T4, live

func _find_proceed(n: Node) -> Button:
	if n is Button and n.is_visible_in_tree() and String(n.text).to_lower().contains("proceed"):
		return n
	for c in n.get_children():
		var r := _find_proceed(c)
		if r != null:
			return r
	return null


func _test_live(inst: Node) -> void:
	root.add_child(inst)
	await process_frame
	await process_frame
	var has_samples := "camera_path_samples" in inst
	var has_frac := "panel_width_fraction" in inst
	_assert(has_samples, "T3 [R-108-01] mockup root has no camera_path_samples property")
	_assert(has_frac, "T4 [R-108-02] mockup root has no panel_width_fraction property")
	var space := InputEventKey.new()
	space.keycode = KEY_SPACE
	space.physical_keycode = KEY_SPACE
	space.pressed = true
	root.push_input(space)
	var t0 := Time.get_ticks_msec()
	var frac_before_proceed := -1.0
	var proceed: Button = null
	var pressed := false
	var done := false
	while Time.get_ticks_msec() - t0 < DRIVE_TIMEOUT_MS and not done:
		await process_frame
		if not has_frac:
			break
		if not pressed:
			proceed = _find_proceed(inst)
			if proceed == null:
				frac_before_proceed = float(inst.get("panel_width_fraction"))
			else:
				pressed = true
				proceed.emit_signal("pressed")
		elif has_samples:
			var s: Array = inst.get("camera_path_samples")
			# push-in finished when the last 5 samples are lower than the peak and flat
			if s.size() > 20 and Time.get_ticks_msec() - t0 > 3000:
				var n := s.size()
				var peak := 0.0
				for v in s:
					peak = max(peak, float(v))
				if float(s[n - 1]) < peak - DRAFT_MIN_TRAVEL and abs(float(s[n - 1]) - float(s[n - 6])) < EPS:
					done = true
	# T3
	if has_samples:
		var samples: Array = inst.get("camera_path_samples")
		var problem := _shape_problem(samples)
		_assert(problem == "", "T3 [R-108-01/R-108-06] camera distance: " + problem)
	# T4
	if has_frac:
		_assert(proceed != null, "T4 [R-108-05] no visible Proceed button appeared after the chronicle lines printed (timeout %d ms)" % DRIVE_TIMEOUT_MS)
		_assert(absf(frac_before_proceed - PANEL_FRACTION) <= PANEL_TOL,
			"T4 [R-108-02] panel_width_fraction while printing was %.4f, expected %.2f +/- %.2f" % [frac_before_proceed, PANEL_FRACTION, PANEL_TOL])
	inst.queue_free()
