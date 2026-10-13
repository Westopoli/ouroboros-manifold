extends "res://tests/test_vg_e_e1k_parity.gd"
# NEEDS A DISPLAY (MultiMesh transforms read identity under the dummy renderer; FU-B22-pregate-display, E1k extension, ledger day32):
#   xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_e_e1k_park_parity.gd

# PARKED (Westley's numbers): every tolerance and epsilon of the E1k parity test lives in this file and nowhere else.
# Ledger row DRAFT-e1k-parity-tolerance (docs/northstar/plans/push_ledger_2026-09-22.md): the 0.02 fraction tolerance and the
# 0.05 height bucket are the Architect's gap g8 ruling (2026-10-13), the rest are the test writer's drafts; Westley owns all
# of them and may tighten them. Nothing here may be widened without him (CLAUDE.md "Tests are the spec").
# This file extends tests/test_vg_e_e1k_parity.gd and reuses its fixture (mockup run, lot list, terrain, port layer) and its
# premise dump; it is a park file: when it is red the clerk leaves it off the candidate and lists it.
#
# The rules and the verdict it proves are quoted word for word in the header of tests/test_vg_e_e1k_parity.gd (R-193-01,
# R-193-02, R-193-05, R-193-09, R-237-01 and Westley 2026-10-12 "Why are units so heavily stacked? ... Not approved yet.").
# Cases, each naming the sentence it proves:
#   P4  the fraction of drawn boxes whose yaw is not a multiple of a quarter turn: Westley 'the layout is super uniform and
#       square, not looks like the sister system to the biome engine at all' (port fraction > 0 so an axis-aligned
#       skeleton is red; port within TOL_FRACTION of the mockup's).
#   P3b per-stage height histogram bucketed at HEIGHT_BUCKET mockup units: Westley 'there's no perceptible difference in
#       level between the buildings' + R-193-05 'rises through its stages'.
#   P5  per-box scale (height, width, depth), yaw and centre of every settled disc box equal the mockup's (N5, N7, N8).
#   P5c rubble colour (N2) and slope_at against the mockup's stored slope (gap g1).

const HEIGHT_BUCKET := 0.05      # mockup units (gap g8 (b))
const BUCKET_EDGE_EPS := 0.01    # float guard on the bucket edge (a stage-1 box is exactly 0.05 = a bucket edge); part of the draft
const TOL_FRACTION := 0.02       # gap g8 (c)
const AXIS_EPS := 0.001          # radians: a yaw within this of a quarter-turn multiple reads as axis-aligned (draft)
const TOL_SCALE_WU := 0.001      # per-box scale, wu (draft; a reference port measured 2e-5)
const TOL_YAW := 0.001           # radians (draft; a reference port measured 1.1e-4, cm-quantised heights)
const TOL_POS_WU := 0.02         # box centre, wu (draft; heights are int cm, a reference port measured 0.005)
const TOL_COLOR := 0.005         # rubble colour channel (draft; a reference port measured 0)
const TOL_SLOPE := 0.0001        # slope_at against the mockup's slope (draft; a reference port measured 7.6e-6)


func _yaw_of(b: Basis) -> float:
	return atan2(-b.x.z, b.x.x)


func _off_axis(b: Basis) -> bool:
	var q := fposmod(_yaw_of(b), PI * 0.5)
	return minf(q, PI * 0.5 - q) > AXIS_EPS


func _bucket(h_units: float) -> int:
	return int(floor(h_units / HEIGHT_BUCKET + BUCKET_EDGE_EPS))


func _wrap(a: float) -> float:
	return absf(fposmod(a + PI, TAU) - PI)


func _run() -> void:
	if not await _build():
		return
	var mmq: MultiMesh = m.lots.multimesh
	var core: Vector2i = sim.core
	var drawn: Array = layer.lots_drawn()
	var by_id := {}
	for d in drawn:
		by_id[int(d["id"])] = d
	var rows := []   # settled disc lots
	for i in disc:
		if not animating.has(i):
			rows.append(i)
	# Positive control: the mockup's own boxes are read, and its fraction is well above 0 (S:34, M:273-281 hashed and contour yaw).
	var m_off := 0
	var p_off := 0
	var m_hist := []
	var p_hist := []
	for i in rows:
		var mt := mmq.get_instance_transform(i)
		var pt := pmm.get_instance_transform(int(idx_of[i]))
		if _off_axis(mt.basis):
			m_off += 1
		if _off_axis(pt.basis):
			p_off += 1
		m_hist.append("%s|%d" % [_cat_sim(i), _bucket(mt.basis.y.length())])
		p_hist.append("%s|%d" % [_cat_port(by_id.get(i, {})), _bucket(pt.basis.y.length() / CELL_WU)])
	var n := rows.size()
	var m_frac := float(m_off) / maxf(n, 1)
	var p_frac := float(p_off) / maxf(n, 1)
	print("PREMISE not-axis-aligned fraction (yaw mod quarter turn beyond %.4f rad), %d settled disc boxes: mockup %d/%d = %.4f, port %d/%d = %.4f" % [AXIS_EPS, n, m_off, n, m_frac, p_off, n, p_frac])
	var mh := _hist(m_hist)
	var ph := _hist(p_hist)
	print("PREMISE height histogram (category|bucket of %.2f units), mockup: %s" % [HEIGHT_BUCKET, str(mh)])
	print("PREMISE height histogram (category|bucket of %.2f units), port:   %s" % [HEIGHT_BUCKET, str(ph)])
	_check(n > 50 and m_frac > 0.5, "[P4 control] the mockup's settled disc must hold boxes (%d) and most must be off-axis (fraction %.3f)" % [n, m_frac])
	_check(p_frac > 0.0, "[P4] Westley 'the layout is super uniform and square': the port's fraction of off-axis boxes must be greater than 0, got %d of %d (the skeleton draws every box axis-aligned)" % [p_off, n])
	_check(absf(p_frac - m_frac) <= TOL_FRACTION, "[P4] Westley 'not looks like the sister system to the biome engine': the port's off-axis fraction %.4f must be within %.2f of the mockup's %.4f" % [p_frac, TOL_FRACTION, m_frac])
	var first := ""
	for k in mh.keys():
		if int(ph.get(k, 0)) != int(mh[k]):
			first = "%s: mockup %d, port %d" % [k, mh[k], int(ph.get(k, 0))]
			break
	if first == "":
		for k in ph.keys():
			if not mh.has(k):
				first = "%s: mockup 0, port %d" % [k, ph[k]]
				break
	_check(ph == mh, "[P3b] Westley 'no perceptible difference in level between the buildings' + R-193-05: the per-stage height histogram (bucket %.2f units) must equal the mockup's, first difference: %s" % [HEIGHT_BUCKET, first])

	# P5: per-box scale, yaw and centre.
	var bad_scale := 0
	var bad_yaw := 0
	var bad_pos := 0
	var bad_col := 0
	var first_scale := ""
	var first_yaw := ""
	var first_pos := ""
	var rubble_seen := 0
	for i in rows:
		var mt := mmq.get_instance_transform(i)
		var pt := pmm.get_instance_transform(int(idx_of[i]))
		var ms := Vector3(mt.basis.x.length(), mt.basis.y.length(), mt.basis.z.length()) * CELL_WU   # N5: x = footprint, y = height, z = 0.85 footprint
		var ps := Vector3(pt.basis.x.length(), pt.basis.y.length(), pt.basis.z.length())
		if ms.distance_to(ps) > TOL_SCALE_WU:
			bad_scale += 1
			if first_scale == "":
				first_scale = "cell %s %s: mockup (w,h,d) wu %s, port %s" % [str(_cell(i)), _cat_sim(i), str(ms), str(ps)]
		if _wrap(_yaw_of(mt.basis) - _yaw_of(pt.basis)) > TOL_YAW:
			bad_yaw += 1
			if first_yaw == "":
				first_yaw = "cell %s: mockup yaw %.4f, port %.4f" % [str(_cell(i)), _yaw_of(mt.basis), _yaw_of(pt.basis)]
		# N6, N8: the centre relative to the cell centre; the mockup's cell centre is (gx, gy) units, the port's (gx + 0.5, gy + 0.5) cells.
		var c := _cell(i)
		var mp := Vector3((mt.origin.x - c.x) * CELL_WU, mt.origin.y * CELL_WU, (mt.origin.z - c.y) * CELL_WU)
		var pp := Vector3(pt.origin.x - (c.x + 0.5) * CELL_WU, pt.origin.y, pt.origin.z - (c.y + 0.5) * CELL_WU)
		if mp.distance_to(pp) > TOL_POS_WU:
			bad_pos += 1
			if first_pos == "":
				first_pos = "cell %s: mockup offset/height wu %s, port %s" % [str(_cell(i)), str(mp), str(pp)]
		if sim.rubble[i] == 1:
			rubble_seen += 1
			var mc := mmq.get_instance_color(i)
			var pc := pmm.get_instance_color(int(idx_of[i]))
			if absf(mc.r - pc.r) > TOL_COLOR or absf(mc.g - pc.g) > TOL_COLOR or absf(mc.b - pc.b) > TOL_COLOR:
				bad_col += 1
	_check(rows.size() > 0 and bad_scale == 0, "[P5] Westley 'no perceptible difference in level' + N3/N4/N5: every settled disc box's (width, height, depth) must equal the mockup's x 100 within %.3f wu; %d of %d differ, first: %s" % [TOL_SCALE_WU, bad_scale, n, first_scale])
	_check(rows.size() > 0 and bad_yaw == 0, "[P5] Westley 'super uniform and square' + N7 (contour yaw above CONTOUR_SLOPE 0.06, hashed elsewhere): every settled disc box's yaw must equal the mockup's within %.4f rad; %d of %d differ, first: %s" % [TOL_YAW, bad_yaw, n, first_yaw])
	_check(rows.size() > 0 and bad_pos == 0, "[P5] N6 jitter + N8 centre (ground + height/2 - 0.12 unit): every settled disc box's centre must equal the mockup's within %.3f wu; %d of %d differ, first: %s" % [TOL_POS_WU, bad_pos, n, first_pos])
	_check(rubble_seen > 0 and bad_col == 0, "[P5] R-237-01 + N2 rubble colour (0.28, 0.2, 0.18): every rubble box colour must equal the mockup's within %.3f; %d of %d differ" % [TOL_COLOR, bad_col, rubble_seen])

	# P5c: slope_at (gap g1, FM:380-402) against the mockup's stored slope on the disc cells.
	var L = load(LOOK) if ResourceLoader.exists(LOOK) else null
	var bad_slope := 0
	var first_slope := ""
	for i in disc:
		var c := _cell(i)
		var s: float = L.slope_at(terr, c.x, c.y) if L is GDScript else -1.0
		if absf(s - sim.slope[i]) > TOL_SLOPE:
			bad_slope += 1
			if first_slope == "":
				first_slope = "cell %s: live %.5f, mockup %.5f" % [str(c), s, sim.slope[i]]
	_check(L is GDScript and bad_slope == 0, "[P5c] R-193-02 + gap g1: slope_at(t, gx, gy) must equal the mockup's re-derived slope within %.4f on the disc; %d of %d differ, first: %s%s" % [TOL_SLOPE, bad_slope, disc.size(), first_slope, "" if L is GDScript else " (missing " + LOOK + ")"])
	print("PREMISE wall time of the test: %.1f s" % [(Time.get_ticks_msec() - t_wall) / 1000.0])
