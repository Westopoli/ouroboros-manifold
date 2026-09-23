extends SceneTree

const MOCKUP_SCENE := "res://scenes/mockups/units/units_mockup.tscn"
const KITS_DIR := "res://scenes/mockups/units/kits/"
const SCENARIOS_DIR := "res://scenes/mockups/units/scenarios/"
const CONTRACT_KEYS := ["seed", "hash", "kit", "scenario", "tick", "alive", "units", "units_px",
	"bboxes", "flashes_active", "wrecks_active", "timing_ms", "regen_count", "playing",
	"camera_pos", "drag_active", "drag_box_visible", "pings_active"]
const PLANTS := ["pass-through", "facing-fixed", "instant-fight", "silhouettes-same", "seed-ignored", "no-death-visual"]

var _failures := 0


func _initialize() -> void:
	_check_DET_1()
	_check_ROSTER_2()
	_check_SIL_3()
	_check_MIRROR_4()
	_check_SOLID_5()
	_check_FACE_6()
	_check_PLAIN_7()
	await _check_DEATH_8()
	_check_FORM_9()
	await _check_FOOT_12()
	await _check_JSON_10()
	_check_TIME_11()
	await _check_DRAG_13()
	await _check_PLAY_14()
	_check_PING_15()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _assert(cond: bool, msg: String) -> bool:
	if not cond:
		_failures += 1
		print("FAIL: %s" % msg)
	return cond


# --- loaders ---

func _load_scenario(name: String) -> Dictionary:
	var text := FileAccess.get_file_as_string(SCENARIOS_DIR + name + ".json")
	return JSON.parse_string(text)


func _load_roster(kit: String) -> Roster:
	return Roster.load_kit(KITS_DIR + kit + ".json")


func _sim_for(kit: String, name: String, p_seed: int) -> UnitsToySim:
	var sim := UnitsToySim.new()
	sim.reset(_load_roster(kit), _load_scenario(name), p_seed)
	return sim


func _sim_for_dict(kit: String, scenario: Dictionary, p_seed: int) -> UnitsToySim:
	var sim := UnitsToySim.new()
	sim.reset(_load_roster(kit), scenario, p_seed)
	return sim


func _run_n(sim: UnitsToySim, n: int) -> void:
	for i in range(n):
		sim.step()


func _boot_scene():
	var packed: PackedScene = load(MOCKUP_SCENE)
	var root = packed.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	return root


# --- checks ---

# plant: seed-ignored
func _check_DET_1() -> void:
	var sim_a := _sim_for("greek", "mirror_10v10", 11)
	_run_n(sim_a, 600)
	var sim_b := _sim_for("greek", "mirror_10v10", 11)
	_run_n(sim_b, 600)
	if not _assert(sim_a.compute_hash() == sim_b.compute_hash(), "seed 11 run twice must hash equal"):
		return
	var sim_c := _sim_for("greek", "flank_4v4", 11)
	_run_n(sim_c, 900)
	var sim_d := _sim_for("greek", "flank_4v4", 12)
	_run_n(sim_d, 900)
	_assert(sim_c.compute_hash() != sim_d.compute_hash(), "seed 12 must hash differently from seed 11 on flank_4v4")


# plant: none (data); self-test with a broken kit dict
func _check_ROSTER_2() -> void:
	for kit_name in ["greek", "settled_reach"]:
		var r := _load_roster(kit_name)
		if not _assert(_orderings_ok(r), "%s: role orderings (R-082-02..04) not satisfied" % kit_name):
			return
	_assert(not _orderings_ok(Roster.from_dict(_broken_kit_dict())), "positive control: broken kit not detected")


# plant: silhouettes-same
func _check_SIL_3() -> void:
	for kit_name in ["greek", "settled_reach"]:
		var r := _load_roster(kit_name)
		var sizes := _role_sizes(r)
		if not _assert(_bboxes_distinct(sizes), "%s: bboxes not pairwise distinct" % kit_name):
			return
		if not _assert(_sil_orderings_ok(r, sizes), "%s: SIL-3 size orderings not satisfied" % kit_name):
			return


# plant: instant-fight
func _check_MIRROR_4() -> void:
	var sim := _sim_for("greek", "mirror_10v10", 11)
	_run_n(sim, 900)
	var alive := sim.alive_counts()
	if not _assert(alive.get(0, 0) > 0 and alive.get(1, 0) > 0, "mirror_10v10: not both sides alive at tick 900 (R-085-01)"):
		return
	var sim2 := _sim_for_dict("greek", _line_vs_strike_variant(), 11)
	_run_n(sim2, 2400)
	var v_alive := _count_alive(sim2, 0)
	_assert(v_alive >= 5, "line-vs-Strike variant: %d Vanguard survivors, expected >=5" % v_alive)


# plant: pass-through
func _check_SOLID_5() -> void:
	for name in ["formation_move", "flank_4v4"]:
		var sim := _sim_for("greek", name, 11)
		var obstacles: Array = _load_scenario(name).get("obstacles", [])
		for t in range(600):
			sim.step()
			if not _assert(_no_obstacle_overlap(sim, obstacles) and _min_separation_ok(sim), "%s: obstacle/collision violation at tick %d" % [name, t]):
				return


# plant: facing-fixed
func _check_FACE_6() -> void:
	var sim := _sim_for_dict("greek", _face6_variant(), 11)
	_run_n(sim, 60)
	if not _assert(_moving_units_face_heading(sim), "a moving unit's facing is off by more than 0.18 rad"):
		return
	var sim2 := _sim_for("greek", "mirror_10v10", 11)
	_run_n(sim2, 80)
	_assert(_attackers_face_targets(sim2), "an attacking unit is not facing its target")


# plant: none; self-test by issuing attack-move instead
func _check_PLAIN_7() -> void:
	var sim := _sim_for("greek", "plain_move_under_fire", 11)
	var start_x: float = sim.get_unit(0).pos.x
	_run_n(sim, 700)
	if not _assert(_movers_never_targeted(sim) and sim.get_unit(0).pos.x > start_x + 200.0, "plain-move unit acquired a target or failed to advance (R-096-01)"):
		return
	var variant: Dictionary = _load_scenario("plain_move_under_fire").duplicate(true)
	variant.commands[0].kind = "attack_move"
	var sim2 := _sim_for_dict("greek", variant, 11)
	_run_n(sim2, 700)
	_assert(_any_mover_targeted(sim2), "positive control: attack-move variant never engaged")


# plant: no-death-visual
func _check_DEATH_8() -> void:
	var root = await _boot_scene()
	root.qa_set("scenario", "bombards_1000")
	root.qa_seed(11)
	var death := _advance_to_first_death(root, 300)
	if not _assert(death.uid != -1, "no unit died within 300 ticks of bombards_1000"):
		root.queue_free()
		return
	root.qa_tick(60)
	var state: Dictionary = root.qa_state()
	_assert(int(state.wrecks_active) >= 1, "no wreck entry present 60 ticks after a death")
	root.queue_free()


# plant: none
func _check_FORM_9() -> void:
	var sim := _sim_for("greek", "formation_move", 11)
	var spread := _arrival_spread(sim, 2000)
	if not _assert(spread >= 0 and spread <= 40, "formation_move: arrival spread %d ticks, expected <=40" % spread):
		return
	var split: Dictionary = _load_scenario("formation_move").duplicate(true)
	split.commands = [{"tick": 0, "kind": "move", "uids": [0, 1, 2, 3], "point": [4000, 4000]}]
	var sim2 := _sim_for_dict("greek", split, 11)
	var t := _arrival_tick(sim2, 0, 1000)
	_assert(t >= 350 and t <= 450, "split formation_move: raider arrival %d ticks, expected ~400" % t)


# plant: none
func _check_JSON_10() -> void:
	var root = await _boot_scene()
	var state: Dictionary = root.qa_state()
	if not _assert(JSON.stringify(state) != "", "qa_state() did not survive JSON.stringify"):
		root.queue_free()
		return
	for key in CONTRACT_KEYS:
		if not _assert(state.has(key), "qa_state() missing key %s" % key):
			root.queue_free()
			return
	if not _assert(not root.qa_plant("nope"), "qa_plant('nope') must return false"):
		root.queue_free()
		return
	for id in PLANTS:
		if not _assert(root.qa_plant(id), "qa_plant(%s) must return true" % id):
			root.queue_free()
			return
	root.queue_free()


# plant: none
func _check_TIME_11() -> void:
	var sim := _sim_for("greek", "mirror_10v10", 11)
	var t0 := Time.get_ticks_usec()
	_run_n(sim, 200)
	var avg_ms := (float(Time.get_ticks_usec() - t0) / 1000.0) / 200.0
	_assert(avg_ms < 2.0, "tick_avg %.4fms for 20 units, expected < 2ms" % avg_ms)


# plant: none; render regression, catches what SIL-3 (data-only) cannot
func _check_FOOT_12() -> void:
	var root = await _boot_scene()
	root.qa_set("scenario", "lineup")
	var view = root.get_node("World/UnitView")
	var cam: Camera3D = root.get_node("CameraRig").get_camera()
	var state: Dictionary = root.qa_state()
	var lengths := {}
	for uid_s in state.units.keys():
		var ud: Dictionary = state.units[uid_s]
		var role: String = ud.role
		var pos := Vector2(ud.pos[0], ud.pos[1])
		var xf: Transform3D = view.get_unit_render_transform(role, pos, float(ud.facing))
		lengths[role] = _projected_length(xf * view.get_role_mesh_aabb(role), cam)
	if not _assert(_arg_max(lengths) == "artillery", "rendered footprint: longest is %s, expected artillery" % _arg_max(lengths)):
		root.queue_free()
		return
	_assert(_arg_min(lengths) == "flanker", "rendered footprint: shortest is %s, expected flanker" % _arg_min(lengths))
	root.queue_free()


# plant: none; mockup review 1 fix: no visible box while dragging, lingering overlay
func _check_DRAG_13() -> void:
	var root = await _boot_scene()
	var hud = root.get_node("HUD")
	root.qa_set("scenario", "lineup")
	if not _assert(not bool(root.qa_state().drag_box_visible), "drag box overlay visible before any drag"):
		root.queue_free()
		return
	var down := InputEventMouseButton.new()
	down.position = Vector2(100, 100)
	down.button_index = MOUSE_BUTTON_LEFT
	down.pressed = true
	hud._unhandled_input(down)
	var motion := InputEventMouseMotion.new()
	motion.position = Vector2(400, 300)
	hud._unhandled_input(motion)
	var mid_state: Dictionary = root.qa_state()
	if not _assert(bool(mid_state.drag_box_visible), "drag box not visible mid-drag"):
		root.queue_free()
		return
	var up := InputEventMouseButton.new()
	up.position = Vector2(400, 300)
	up.button_index = MOUSE_BUTTON_LEFT
	up.pressed = false
	hud._unhandled_input(up)
	var end_state: Dictionary = root.qa_state()
	_assert(not bool(end_state.drag_box_visible), "drag box overlay still visible after release (lingering-overlay bug)")
	root.queue_free()


# plant: none; mockup review 1 fix: units do not move, sim must stay paused under qa-mode
func _check_PLAY_14() -> void:
	var root = await _boot_scene()
	var hud = root.get_node("HUD")
	var s0: Dictionary = root.qa_state()
	if not _assert(not bool(s0.playing), "sim must start paused under --qa-script/headless"):
		root.queue_free()
		return
	var t0 := int(s0.tick)
	await process_frame
	await process_frame
	await process_frame
	var s1: Dictionary = root.qa_state()
	if not _assert(int(s1.tick) == t0, "tick drifted with no explicit qa_tick call while qa-mode paused"):
		root.queue_free()
		return
	root.qa_set("scenario", "lineup")
	hud.set_selection([0])
	hud._handle_right_click(Vector2(400, 400))
	var s2: Dictionary = root.qa_state()
	_assert(not bool(s2.playing), "qa-mode command must not auto-unpause (breaks determinism)")
	root.queue_free()


# plant: none; mockup review 1 fix: waypoints stay forever (never fade) while paused
func _check_PING_15() -> void:
	var root = await _boot_scene()
	var view = root.get_node("World/UnitView")
	root.qa_set("scenario", "lineup")
	view.add_ping(Vector2(4000, 4000), false)
	if not _assert(view.pings_active() == 1, "ping not registered"):
		root.queue_free()
		return
	view.set_playing(false)
	for p in view._pings:
		p.created_msec = Time.get_ticks_msec() - 2000
	view._process(0.0)
	_assert(view.pings_active() == 0, "ping did not expire on wall time while paused")
	root.queue_free()


func _projected_length(aabb: AABB, cam: Camera3D) -> float:
	var rect := Rect2(cam.unproject_position(aabb.get_endpoint(0)), Vector2.ZERO)
	for i in range(1, 8):
		rect = rect.expand(cam.unproject_position(aabb.get_endpoint(i)))
	return max(rect.size.x, rect.size.y)


# --- helpers ---

func _orderings_ok(r: Roster) -> bool:
	if not r.is_valid():
		return false
	var strike_speed_min := INF
	var line_speed_min := INF
	var line_speed_max := -INF
	var siege_speed_max := -INF
	var strike_sensor: Array = []
	var siege_sensor: Array = []
	var hp_by_role := {}
	for role in Roster.ROLE_ORDER:
		var stats := r.get_stats(role)
		var cat := String(stats.get("category", ""))
		var speed := float(stats.get("speed_wu_s", 0.0))
		hp_by_role[role] = float(stats.get("hp", 0.0))
		if cat == "Strike":
			strike_speed_min = min(strike_speed_min, speed)
			strike_sensor.append(float(stats.get("sensor_wu", 0.0)))
		elif cat == "Line":
			line_speed_min = min(line_speed_min, speed)
			line_speed_max = max(line_speed_max, speed)
		elif cat == "Siege":
			siege_speed_max = max(siege_speed_max, speed)
			siege_sensor.append(float(stats.get("sensor_wu", 0.0)))
	if strike_sensor.is_empty() or siege_sensor.is_empty() or line_speed_max < 0.0:
		return false
	if strike_speed_min <= line_speed_max or line_speed_min <= siege_speed_max:
		return false
	var second := 0.0
	var min_hp := INF
	var min_role := ""
	for role in hp_by_role.keys():
		var v: float = hp_by_role[role]
		if role != "anchor":
			second = max(second, v)
		if v < min_hp:
			min_hp = v
			min_role = role
	if float(hp_by_role.get("anchor", 0.0)) < 2.0 * second or min_role != "flanker":
		return false
	for s in strike_sensor:
		for g in siege_sensor:
			if float(s) <= float(g):
				return false
	return true


func _broken_kit_dict() -> Dictionary:
	var stub := {"shape": "wide_block", "size": [1, 1, 1], "squad": 1}
	return {
		"name": "broken",
		"palette": {},
		"roles": {
			"flanker": {"stats": {"hp": 999, "speed_wu_s": 10, "sensor_wu": 100, "category": "Strike"}, "silhouette": stub},
			"screen": {"stats": {"hp": 300, "speed_wu_s": 10, "sensor_wu": 100, "category": "Strike"}, "silhouette": stub},
			"frontliner": {"stats": {"hp": 400, "speed_wu_s": 50, "sensor_wu": 700, "category": "Line"}, "silhouette": stub},
			"support": {"stats": {"hp": 350, "speed_wu_s": 50, "sensor_wu": 700, "category": "Line"}, "silhouette": stub},
			"artillery": {"stats": {"hp": 400, "speed_wu_s": 200, "sensor_wu": 900, "category": "Siege"}, "silhouette": stub},
			"anchor": {"stats": {"hp": 500, "speed_wu_s": 200, "sensor_wu": 900, "category": "Siege"}, "silhouette": stub},
		},
	}


func _role_sizes(r: Roster) -> Dictionary:
	var sizes := {}
	for role in Roster.ROLE_ORDER:
		sizes[role] = r.get_silhouette(role).get("size", [0, 0, 0])
	return sizes


func _bboxes_distinct(sizes: Dictionary) -> bool:
	var roles: Array = sizes.keys()
	for i in range(roles.size()):
		for j in range(i + 1, roles.size()):
			var a: Array = sizes[roles[i]]
			var b: Array = sizes[roles[j]]
			var all_close := true
			for k in range(3):
				var av: float = float(a[k])
				var bv: float = float(b[k])
				var denom: float = max(av, bv)
				if denom > 0.0001 and absf(av - bv) / denom > 0.10:
					all_close = false
			if all_close:
				return false
	return true


func _sil_orderings_ok(r: Roster, sizes: Dictionary) -> bool:
	var vol := {}
	for role in sizes.keys():
		var s: Array = sizes[role]
		vol[role] = float(s[0]) * float(s[1]) * float(s[2])
	var min_role := _arg_min(vol)
	var max_role := _arg_max(vol)
	if r.get_category(min_role) != "Strike" or r.get_category(max_role) != "Siege":
		return false
	var anchor: Array = sizes["anchor"]
	if float(anchor[1]) <= float(anchor[0]):
		return false
	var art_len: float = float(sizes["artillery"][0])
	for role in sizes.keys():
		if role != "artillery" and float(sizes[role][0]) >= art_len:
			return false
	return true


func _arg_min(d: Dictionary) -> String:
	var best := ""
	var best_v := INF
	for k in d.keys():
		if d[k] < best_v:
			best_v = d[k]
			best = k
	return best


func _arg_max(d: Dictionary) -> String:
	var best := ""
	var best_v := -INF
	for k in d.keys():
		if d[k] > best_v:
			best_v = d[k]
			best = k
	return best


func _count_alive(sim: UnitsToySim, faction: int) -> int:
	var n := 0
	for u in sim.units:
		if u.alive and u.faction == faction:
			n += 1
	return n


func _line_vs_strike_variant() -> Dictionary:
	var units: Array = []
	var vanguard_uids: Array = []
	var raider_uids: Array = []
	for i in range(10):
		units.append({"role": "frontliner", "faction": 0, "pos": [3875, 3595 + i * 90]})
		vanguard_uids.append(i)
	for i in range(10):
		units.append({"role": "flanker", "faction": 1, "pos": [4075, 3595 + i * 90]})
		raider_uids.append(10 + i)
	return {
		"units": units,
		"obstacles": [],
		"commands": [
			{"tick": 0, "kind": "attack_move", "uids": vanguard_uids, "point": [4900, 4000]},
			{"tick": 0, "kind": "attack_move", "uids": raider_uids, "point": [3100, 4000]},
		],
	}


func _no_obstacle_overlap(sim: UnitsToySim, obstacles: Array) -> bool:
	for u in sim.units:
		if not u.alive:
			continue
		for ob in obstacles:
			if u.pos.x > float(ob.x0) and u.pos.x < float(ob.x1) and u.pos.y > float(ob.z0) and u.pos.y < float(ob.z1):
				return false
	return true


func _min_separation_ok(sim: UnitsToySim) -> bool:
	for i in range(sim.units.size()):
		var a = sim.units[i]
		if not a.alive:
			continue
		for j in range(i + 1, sim.units.size()):
			var b = sim.units[j]
			if b.alive and a.pos.distance_to(b.pos) < 28.0:
				return false
	return true


func _moving_units_face_heading(sim: UnitsToySim) -> bool:
	for u in sim.units:
		if not u.alive or u.order.is_empty():
			continue
		var speed := float(sim.roster.get_stats(u.role).get("speed_wu_s", 0.0))
		if speed <= 1.0:
			continue
		var pt: Array = u.order.get("point", [])
		if pt.is_empty():
			continue
		var expected: float = (Vector2(float(pt[0]), float(pt[1])) - u.pos).angle()
		if absf(wrapf(expected - u.facing, -PI, PI)) > 0.18:
			return false
	return true


func _face6_variant() -> Dictionary:
	return {
		"units": [
			{"role": "flanker", "faction": 0, "pos": [1000, 1000]},
			{"role": "frontliner", "faction": 0, "pos": [1000, 3000]},
			{"role": "anchor", "faction": 0, "pos": [1000, 5000]},
		],
		"obstacles": [],
		"commands": [
			{"tick": 0, "kind": "move", "uids": [0], "point": [4000, 1500]},
			{"tick": 0, "kind": "move", "uids": [1], "point": [4000, 3600]},
			{"tick": 0, "kind": "move", "uids": [2], "point": [4000, 5800]},
		],
	}


func _attackers_face_targets(sim: UnitsToySim) -> bool:
	var any := false
	for u in sim.units:
		if not u.alive or u.target == null:
			continue
		var t = sim.get_unit(u.target)
		if t == null or not t.alive:
			continue
		any = true
		var expected: float = (t.pos - u.pos).angle()
		if absf(wrapf(expected - u.facing, -PI, PI)) > 0.18:
			return false
	return any


func _movers_never_targeted(sim: UnitsToySim) -> bool:
	for u in sim.units:
		if u.faction == 0 and u.target != null:
			return false
	return true


func _any_mover_targeted(sim: UnitsToySim) -> bool:
	for u in sim.units:
		if u.faction == 0 and u.target != null:
			return true
	return false


func _advance_to_first_death(root, max_ticks: int) -> Dictionary:
	for i in range(max_ticks):
		root.qa_tick(1)
		var state: Dictionary = root.qa_state()
		for uid_s in state.units.keys():
			if not state.units[uid_s].alive:
				return {"uid": int(uid_s), "tick": int(state.tick)}
	return {"uid": -1, "tick": -1}


func _arrival_spread(sim: UnitsToySim, max_ticks: int) -> int:
	var arrival := {}
	for t in range(max_ticks):
		sim.step()
		for u in sim.units:
			if not arrival.has(u.uid) and u.order.is_empty():
				arrival[u.uid] = t
		if arrival.size() == sim.units.size():
			break
	if arrival.size() != sim.units.size():
		return -1
	var mn := INF
	var mx := -INF
	for uid in arrival.keys():
		mn = min(mn, arrival[uid])
		mx = max(mx, arrival[uid])
	return int(mx - mn)


func _arrival_tick(sim: UnitsToySim, uid: int, max_ticks: int) -> int:
	for t in range(max_ticks):
		sim.step()
		if sim.get_unit(uid).order.is_empty():
			return t
	return -1
