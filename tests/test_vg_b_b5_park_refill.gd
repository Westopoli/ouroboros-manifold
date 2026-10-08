extends SceneTree

# Piece VG-B B5 PARK test: Westley's REFILL threshold, median owner-flip
# refill() under 12 ms (docs/northstar/plans/2026-10-07-visible-game-spec.md
# lane B). Same scene contract as tests/test_vg_b_b5.gd. Left off the candidate
# when red and kept on push/vg-parked; never widened without Westley.
# Run under xvfb with Vulkan (forward_plus), not --headless.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const REFILL_MAX_MS := 12.0
const SAMPLES := 14
const WARMUP := 2

var _fail := ""


func _initialize() -> void:
	await _run()
	if _fail != "":
		print("REFILL PARK RED: " + _fail)
		print("PASS: 0  FAIL: 1")
		quit(1)
	else:
		print("REFILL PARK GREEN")
		print("PASS: 1  FAIL: 0")
		quit(0)


func _run() -> void:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	var packed = load(SCENE_PATH)
	if not (snap is Dictionary) or not (packed is PackedScene):
		_fail = "fixture or scene missing"
		return
	var view: Node = (packed as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	view.set_snapshot(snap)
	await process_frame
	await process_frame
	var shell: Node = view.get_node_or_null("ShellRenderer")
	if shell == null or not shell.has_method("get_territory_field"):
		_fail = "no ShellRenderer.get_territory_field() on galaxy_view (feature missing)"
		return
	if DisplayServer.get_name() == "headless":
		_fail = "headless: no GPU to time"
		return
	var field: Node = shell.get_territory_field()
	await process_frame
	var old_owner: int = int(snap["regions"][0]["owner"])
	var times: Array = []
	for i in SAMPLES:
		field.set_system_owner(0, (old_owner + 1 + (i % 2)) % 4)
		var t0 := Time.get_ticks_usec()
		field.refill()
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		if i >= WARMUP:
			times.append(ms)
		await process_frame
	times.sort()
	var med: float = times[times.size() / 2]
	print("REFILL median %.2f ms (limit %.0f) on %s" % [med, REFILL_MAX_MS, RenderingServer.get_video_adapter_name()])
	if med > REFILL_MAX_MS:
		_fail = "refill median %.2f ms > %.0f ms" % [med, REFILL_MAX_MS]
