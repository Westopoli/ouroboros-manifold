extends RefCounted

## The settlement look numbers (visible-game lane E1, piece VG-E1K, S-193): per-lot factor, stage rows, footprints,
## position jitter, contour yaw, slope. Constants and static functions only; no node, no state.
## Ports scenes/mockups/settlement/settlement_sim.gd (S) and settlement_mockup.gd (M) numbers (spec Rev 12d "E1k numbers").
## One mockup unit = one cell = 100 wu; the functions here work in mockup units and cells, the layer multiplies by CELL_WU.
## See also: settlement_layer.gd, settlement_streets.gd, tests/test_vg_e_e1k_parity.gd.

const CELL_WU := 100.0 # one mockup unit = one cell = 100 wu (spec E1k numbers; S:6)
const JITTER_CELLS := 0.22 # S:33, M:248-249
const YAW_JITTER := 0.25 # S:34
const CLIFF_SLOPE := 0.22 # S:19
const CLIFF_MAX_STAGE := 3 # S:20
const CONTOUR_SLOPE := 0.06 # S:32; gap g2 (Architect 2026-10-12): 0.06, not 0.22 (that was the cliff cap)
const DEPTH_RATIO := 0.85 # M:251
const SINK_UNITS := 0.12 # M:252
const V_BASE := 0.8 # S:304
const V_SPAN := 0.5 # S:304
const RISE_S := 0.9 # S:21
const SLOPE_NORM := 6.25 # FM:380-402 reference: PEAK_HEIGHT_WU * 0.25 / (SPACING * 2); csrc/economy_density.c:25; gap g1 (Architect 2026-10-12)
const CM_PER_WU := 100.0 # terrain heights are cm; FM works in wu (csrc/economy_density.c:19)
const RUBBLE_COLOR := Color(0.28, 0.2, 0.18) # S:306; gap g7 (Architect 2026-10-13)


## S:137-138.
static func hash01(i: int) -> float:
	return float(((i * 73856093) ^ (i * 19349663)) & 0xffff) / 65535.0


## Gap g3 (Architect 2026-10-12): the hash input is the sim lot id.
static func lot_key(_t: Dictionary, lot: Dictionary) -> int:
	return int(lot["id"])


## Gap g1 (Architect 2026-10-12): FM:380-402 / csrc/economy_density.c:73-90, mean |dh| over the orthogonal neighbours that exist,
## in wu per cell over SLOPE_NORM, clamped to 1. t["heights"] is cm, row-major, cells_w by cells_h.
static func slope_at(t: Dictionary, gx: int, gy: int) -> float:
	var w: int = int(t["cells_w"])
	var h: int = int(t["cells_h"])
	var hs: PackedInt32Array = t["heights"]
	var c: int = hs[gy * w + gx]
	var sum := 0.0
	var count := 0
	if gx > 0:
		sum += absf(float(c - hs[gy * w + gx - 1]))
		count += 1
	if gx < w - 1:
		sum += absf(float(c - hs[gy * w + gx + 1]))
		count += 1
	if gy > 0:
		sum += absf(float(c - hs[(gy - 1) * w + gx]))
		count += 1
	if gy < h - 1:
		sum += absf(float(c - hs[(gy + 1) * w + gx]))
		count += 1
	var avg := sum / float(count) / CM_PER_WU / CELL_WU if count > 0 else 0.0
	return clampf(avg / SLOPE_NORM, 0.0, 1.0)


## S:303-317 minus the colour: [height_units, footprint]. Stage 0 is rubble (S:305-306). A cliff row applies to stage 1 and up;
## the caller caps the stage at CLIFF_MAX_STAGE. Stage 5 draws as the stage-4 row (gap g6, Architect 2026-10-13; S:317 default branch).
static func vis(stage: int, cliff: bool, i: int) -> Array:
	var v := V_BASE + V_SPAN * hash01(i + 11)
	if stage <= 0:
		return [0.14, 0.7]
	if cliff:
		match stage:
			1: return [0.05, 0.6]
			2: return [0.22, 0.5]
			_: return [0.4 * v, 0.62]
	match stage:
		1: return [0.05, 0.8]
		2: return [0.3 * v, 0.7]
		3: return [0.7 * v, 0.72]
		_: return [1.5 * v, 0.8]


## N6: (x, z) offset in cells, S:33, M:248-249.
static func jitter(i: int) -> Vector2:
	return Vector2((hash01(i + 3) - 0.5) * 2.0 * JITTER_CELLS, (hash01(i + 5) - 0.5) * 2.0 * JITTER_CELLS)


## N7: M:273-280, with the slope of slope_at (gap g1) and CONTOUR_SLOPE (gap g2).
static func yaw(t: Dictionary, gx: int, gy: int, i: int) -> float:
	var w: int = int(t["cells_w"])
	var h: int = int(t["cells_h"])
	var hs: PackedInt32Array = t["heights"]
	var dx := float(hs[gy * w + mini(gx + 1, w - 1)] - hs[gy * w + maxi(gx - 1, 0)])
	var dz := float(hs[mini(gy + 1, h - 1) * w + gx] - hs[maxi(gy - 1, 0) * w + gx])
	var jit := (hash01(i + 7) - 0.5) * 2.0 * YAW_JITTER
	if slope_at(t, gx, gy) > CONTOUR_SLOPE and (absf(dx) + absf(dz)) > 0.0:
		return atan2(-dx, -dz) + jit
	return hash01(i + 9) * PI + jit
