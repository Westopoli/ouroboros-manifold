extends SceneTree

const MOCKUP_SCENE := "res://scenes/mockups/walkers/walkers_mockup.tscn"
const FRAME_CAP := 4000

var _failures := 0


func _initialize() -> void:
	var m = load(MOCKUP_SCENE).instantiate()
	get_root().add_child(m)
	await process_frame
	await process_frame
	var g = m.grid
	var u = m.units
	var start: Vector2 = u.units[0].pos
	var target := start
	for k in range(60):
		var t: Vector2 = g.cell_pos(g.main_cells[(k * 7919 + 13) % g.main_cells.size()])
		if start.distance_to(t) > 5000.0:
			target = t
			break
	for kind in ["w", "f"]:
		m.sel = []
		for i in range(u.units.size()):
			if u.units[i].kind == kind:
				m.sel.append(i)
		m.order_to(target)
		var n := 0
		while n < FRAME_CAP:
			var any := false
			for i in m.sel:
				any = any or u.moving(u.units[i])
			if not any:
				break
			u.step(1.0)
			n += 1
		_assert(n < FRAME_CAP, "%s group did not finish within the cap" % kind)
		for i in m.sel:
			var x: Dictionary = u.units[i]
			var r: Dictionary = x.route
			_assert(u.arrived(x), "%s unit %d not arrived" % [kind, i])
			_assert(x.pos.distance_to(r.end) < 1.0, "%s unit %d not at route end" % [kind, i])
			if kind == "w":
				for p in r.points:
					_assert(g.walkable_at(p), "walker route enters steep or water ground")
				if not r.reached:
					_assert(r.end.distance_to(x.route.points[r.points.size() - 1]) < 1.0, "stopped short but not at the nearest cell")
		_assert(not u.last.is_empty() and u.last.seconds > 0.0, "read-out missing for %s order" % kind)
		print("order ", kind, ": ", u.last)
	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _assert(ok: bool, msg: String) -> void:
	if not ok:
		_failures += 1
		print("FAIL: " + msg)
