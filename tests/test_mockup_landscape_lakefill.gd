extends "res://tests/support/vg_c_case.gd"
# Rule pins: none (prototype fix PROTO-landscape-lakefill: no S- or R- id; Westley 2026-10-18 verdict and FINDING-landscape-lakefill-stripes; spec docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "PROTO-landscape-lakefill")
# Run: scripts/run_godot_tests.sh tests/test_mockup_landscape_lakefill.gd   (headless, no display needed)
#
# Piece PROTO-landscape-lakefill (scenes/mockups/landscape/field_map.gd, _flood_lake). [W 2026-10-18: "very unnatural and
# almost man-made"]. The lake fill took its next cell with pop_back (a stack), which fills every second column; the fix runs
# the flood in queue order (pop_front) with the same cell cap. Test (spec): the land-to-water flips per row in a 60 by 60
# cell box over a lake are under DRAFT-lakefill-flips = 4 on seeds 1 and 3; positive control: the unfixed loop gives 14.9.
#
# UNSTATED INTERFACE CHOICES (the paragraph gives no definitions; each is a fixture choice, not a threshold):
#   1. Data read: FieldMap.new(); generate(seed) (default canvas 24000, stability 60); cell water = grid[idx].water, a cell is
#      WATER when water >= 0.5 (the same 0.5 threshold the coast trace uses, field_map.gd _march_squares(water, dim, 0.5)).
#   2. Lake cell: WATER and grid[idx].elevation >= 60.0 (smoothstep(60,-60) in _build_water is the sea ramp, so higher ground is
#      not sea). Rivers stamp water too and stay in the box; they are not removed.
#   3. The box: the 60 x 60 cell window (stepped by 5 cells) holding the most lake cells; the first such window in
#      row-major order wins a tie. A seed with no lake cell fails (the premise).
#   4. A flip: along a row, one step from a LAND cell to the next WATER cell (land-to-water only). Flips per row = total
#      flips over the 60 rows / 60.
#   5. Positive control (green on main, no product code needed): the same metric on a synthetic bowl flooded by a local copy of
#      the stack loop (pop_back) and of the queue loop (pop_front), 1,500-cell cap, 4-neighbour, fill_level seed + 150: the
#      stack must measure above 8 (the finding gives 14.9), the queue under 4. This proves the detector tells the two apart.
#      The spec's 14.9 is the real-map figure on the unfixed loop; the real seeds are asserted red/green only against 4.

const FIELD_MAP := "res://scenes/mockups/landscape/field_map.gd"
const BOX := 60
const BOX_STEP := 5
const SEA_ELEV_WU := 60.0
const DRAFT_LAKEFILL_FLIPS := 4.0  # DRAFT-lakefill-flips (ledger day37, Westley may veto)
const CAP := 1500


func _run() -> void:
	var fm_script := load(FIELD_MAP) as GDScript
	_check(fm_script != null, "missing script: " + FIELD_MAP)
	_control_detector()
	if fm_script == null:
		return
	for s in [1, 3]:
		_seed_case(fm_script, s)


# Flips per row of a water mask (Array of bool, d x d) over the box at (bx, by).
func _flips_per_row(water: Array, d: int, bx: int, by: int) -> float:
	var flips := 0
	for y in range(by, by + BOX):
		for x in range(bx, bx + BOX - 1):
			if not water[y * d + x] and water[y * d + x + 1]:
				flips += 1
	return float(flips) / float(BOX)


# S-none; FINDING-landscape-lakefill-stripes: land-to-water flips per row in the box over the lake stay under 4.
func _seed_case(fm_script: GDScript, p_seed: int) -> void:
	var fm = fm_script.new()
	fm.generate(p_seed)
	var d: int = fm.dim
	var water: Array = []
	var lake: Array = []
	water.resize(d * d)
	lake.resize(d * d)
	for i in range(d * d):
		var c: Dictionary = fm.grid[i]
		water[i] = float(c.water) >= 0.5
		lake[i] = water[i] and float(c.elevation) >= SEA_ELEV_WU
	# Box with most lake cells (summed per candidate window).
	var best := -1
	var bx := 0
	var by := 0
	for y in range(0, d - BOX + 1, BOX_STEP):
		for x in range(0, d - BOX + 1, BOX_STEP):
			var n := 0
			for yy in range(y, y + BOX):
				for xx in range(x, x + BOX):
					if lake[yy * d + xx]:
						n += 1
			if n > best:
				best = n
				bx = x
				by = y
	_check(best > 0, "seed %d: premise: no lake cell (water >= 0.5 above %s wu) anywhere on the map" % [p_seed, SEA_ELEV_WU])
	var fpr := _flips_per_row(water, d, bx, by)
	print("seed %d: box (%d,%d) lake cells %d, land-to-water flips per row %.2f" % [p_seed, bx, by, best, fpr])
	_check(fpr < DRAFT_LAKEFILL_FLIPS, "seed %d: lake fill draws %.2f land-to-water flips per row in the 60 x 60 box at (%d,%d), not under DRAFT-lakefill-flips %s (the stack fill stripes every second column; queue order gives about 2.3)" % [p_seed, fpr, bx, by, DRAFT_LAKEFILL_FLIPS])


# Local copy of the lake loop on a flat bowl, stack (pop_back) or queue (pop_front).
func _synthetic_flips(use_stack: bool) -> float:
	var d := 90
	var elev := PackedFloat32Array()
	elev.resize(d * d)
	for i in range(d * d):
		elev[i] = 100.0  # flat floor
	var seed_idx := 45 * d + 45
	var fill_level := elev[seed_idx] + 150.0
	var water: Array = []
	water.resize(d * d)
	water.fill(false)
	var visited := {seed_idx: true}
	var queue: Array = [seed_idx]
	var visits := 0
	while not queue.is_empty() and visits < CAP:
		var idx: int = queue.pop_back() if use_stack else queue.pop_front()
		visits += 1
		if elev[idx] > fill_level:
			continue
		water[idx] = true
		var gy := idx / d
		var gx := idx % d
		for off in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
			var nx: int = gx + off.x
			var ny: int = gy + off.y
			if nx < 0 or nx >= d or ny < 0 or ny >= d:
				continue
			var nidx: int = ny * d + nx
			if not visited.has(nidx) and elev[nidx] <= fill_level:
				visited[nidx] = true
				queue.append(nidx)
	return _flips_per_row(water, d, 15, 15)


# Positive control for the detector (spec: "positive control: the unfixed loop gives 14.9").
func _control_detector() -> void:
	var stack := _synthetic_flips(true)
	var queue := _synthetic_flips(false)
	print("control: stack %.2f, queue %.2f flips per row" % [stack, queue])
	_check(stack > 8.0, "CONTROL: the stack (pop_back) loop measures %.2f flips per row, the detector should see stripes (above 8)" % stack)
	_check(queue < DRAFT_LAKEFILL_FLIPS, "CONTROL: the queue (pop_front) loop measures %.2f flips per row, should be under %s" % [queue, DRAFT_LAKEFILL_FLIPS])
