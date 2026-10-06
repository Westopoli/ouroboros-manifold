extends SceneTree
# Layout prototype pass 1: headless self-test. 3 archetypes x 12 seeds x 3 symmetry modes = 108 maps.
# Run: godot --headless -s scenes/mockups/layout/layout_selftest.gd
# Prints one line per map, then check failures and the mean signature distance per archetype.

const Gen := preload("res://scenes/mockups/layout/layout_gen.gd")
const Checks := preload("res://scenes/mockups/layout/layout_checks.gd")


func _init() -> void:
	var g := Gen.new()
	var total := 0
	var disconnected := 0
	var fails := {}
	var t0 := Time.get_ticks_msec()
	for arch in Gen.ARCHETYPES:
		for sym in Gen.SYM_MODES:
			var sigs := []
			for seed_ in range(1, 13):
				var m := g.make(arch, seed_, {"sym": sym, "recent": sigs})
				sigs.append(m["signature"])
				total += 1
				var bad := []
				for c in m["checks"]:
					if not c["ok"]:
						bad.append(c["id"])
						fails[c["id"]] = fails.get(c["id"], 0) + 1
				if "connected" in bad:
					disconnected += 1
				print("%s %-9s seed %2d  %-7s loops %d  nodes %2d  checks %d/%d  sigmin %s  %s" % [
					arch, sym, seed_, m["division"], m["loops"], m["nodes"].size(), Checks.pass_count(m), m["checks"].size(),
					("%.1f" % m["sig_min_distance"]) if m["sig_min_distance"] != INF else "-", ("FAIL " + ",".join(bad)) if not bad.is_empty() else "ok"])
			var mean := 0.0
			var cnt := 0
			for i in sigs.size():
				for j in range(i + 1, sigs.size()):
					mean += Checks.sig_distance(sigs[i], sigs[j])
					cnt += 1
			print("== %s %s: mean pairwise signature distance %.2f over %d pairs" % [arch, sym, mean / maxf(cnt, 1), cnt])
	var controls := _controls(g)
	print("maps: %d, disconnected: %d, check failures: %s, ms: %d" % [total, disconnected, str(fails), Time.get_ticks_msec() - t0])
	print("positive controls (each broken map must turn its check red): %s" % str(controls))
	quit(0 if disconnected == 0 and not controls.values().has(false) else 1)


# Positive control for every detector: break a good map on purpose and demand the red dot.
func _controls(g) -> Dictionary:
	var kits: Dictionary = g.kits
	var base: Dictionary = g.make("assault", 4, {"sym": "mirror"})
	var out := {}
	var run := func(m: Dictionary, recent := []) -> Dictionary:
		Checks.run(m, kits, recent)
		var d := {}
		for c in m["checks"]:
			d[c["id"]] = c["ok"]
		return d
	var m1: Dictionary = base.duplicate(true)
	for e in m1["edges"]:
		if e["a"] == Checks.home_id(m1, 1) or e["b"] == Checks.home_id(m1, 1):
			e["kind"] = "overlook"
	out["connected"] = not run.call(m1)["connected"]
	var m2: Dictionary = base.duplicate(true)
	for e in m2["edges"]:
		if e["kind"] == "route" and e.has("lane"):
			e["meander"] = 1.6 if e["id"] % 2 == 0 else 1.0
	m2["edges"][0]["meander"] = 4.0
	for e in m2["edges"]:
		if e["a"] == Checks.home_id(m2, 0):
			e["meander"] = 4.0
	out["equal"] = not run.call(m2)["equal"]
	var m3: Dictionary = base.duplicate(true)
	for e in m3["edges"]:
		if e["kind"] == "loop":
			e["meander"] = 0.2
	out["bypass"] = not run.call(m3)["bypass"]
	var m4: Dictionary = base.duplicate(true)
	var o: int = Checks.objective_ids(m4)[0]
	var kept := 0
	for e in m4["edges"]:
		if (e["a"] == o or e["b"] == o) and e["kind"] != "overlook":
			kept += 1
			if kept > 1:
				e["kind"] = "overlook"
	out["approaches"] = not run.call(m4)["approaches"]
	var m5: Dictionary = base.duplicate(true)
	m5["required"] = m5["required"] + ["fortress"]
	out["choices"] = not run.call(m5)["choices"]
	var m6: Dictionary = base.duplicate(true)
	m6["homes"]["b"]["width"] = m6["homes"]["b"]["width"] * 2.0
	out["matched"] = not run.call(m6)["matched"]
	var m7: Dictionary = base.duplicate(true)
	m7["recent"] = null
	out["distinct"] = not run.call(m7, [base["signature"]])["distinct"]
	var m8: Dictionary = base.duplicate(true)
	nodes_holder_swap(m8)
	out["objective"] = not run.call(m8)["objective"]
	return out


func nodes_holder_swap(m: Dictionary) -> void:
	var o: int = Checks.objective_ids(m)[0]
	m["nodes"][o]["holder"] = 1 - int(m["nodes"][o]["holder"])
