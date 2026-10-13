extends RefCounted

# Fixture ground for lane C tests: the bridge's terrain() dict with section 2's `heights`
# (int32 cm per cell, row-major; the sim samples at cell centres (i + 0.5) * CELL_WU,
# csrc/terrain.c ts_height_q) plus a frame with units and a map.

const CELL_WU := 100.0
const W := 8
const H := 6


static func heights_cm(i: int, j: int) -> int:
	return i * 150 + j * 80 + (400 if (i == 3 and j == 2) else 0)


static func terrain() -> Dictionary:
	var heights := PackedInt32Array()
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	for j in H:
		for i in W:
			heights.append(heights_cm(i, j))
			bands.append(1 + (i + j) % 5)
			walk.append(0 if (i == 5 and j == 4) else 1)
	return {
		"cells_w": W, "cells_h": H, "bands": bands, "walkable": walk, "heights": heights,
		"slopes": [{"x0": 100, "y0": 100, "x1": 300, "y1": 100, "mx": 200.0, "my": 100.0,
			"length": 200.0, "lower_band": 1, "upper_band": 2}],
	}


static func ground_y(wx: float, wy: float) -> float:
	# bilinear between cell centres, in wu (100 cm = 1 wu)
	var fx := clampf(wx / CELL_WU - 0.5, 0.0, W - 1.0)
	var fy := clampf(wy / CELL_WU - 0.5, 0.0, H - 1.0)
	var i0 := mini(int(floor(fx)), W - 2)
	var j0 := mini(int(floor(fy)), H - 2)
	var tx := fx - i0
	var ty := fy - j0
	var a := lerpf(heights_cm(i0, j0), heights_cm(i0 + 1, j0), tx)
	var b := lerpf(heights_cm(i0, j0 + 1), heights_cm(i0 + 1, j0 + 1), tx)
	return lerpf(a, b, ty) / 100.0


static func frame() -> Dictionary:
	return {
		"tick": 10,
		"units": [
			{"id": 1, "faction": 0, "type": 0, "tier": 0, "x": 250.0, "y": 250.0, "hp": 100, "layer": 0, "facing": 0.0, "target": -1, "state": 0, "sight": 200},
			{"id": 2, "faction": 0, "type": 1, "tier": 0, "x": 450.0, "y": 350.0, "hp": 100, "layer": 2, "facing": 0.0, "target": -1, "state": 0, "sight": 200},
			{"id": 3, "faction": 1, "type": 0, "tier": 0, "x": 550.0, "y": 150.0, "hp": 100, "layer": 0, "facing": 0.0, "target": -1, "state": 0},
			{"id": 4, "faction": 0, "type": 0, "tier": 0, "x": 350.0, "y": 450.0, "hp": 100, "layer": 0, "facing": 0.0, "target": -1, "state": 5, "tl": 1, "ld": 40, "sight": 200},
		],
		"map": {
			"nodes": [{"x": 300.0, "y": 300.0}, {"x": 600.0, "y": 400.0}],
			"cover": [{"x": 200.0, "y": 400.0, "r": 60.0, "h": 1, "class": 0}],
			"obstacles": [{"x": 500.0, "y": 250.0, "r": 40.0}],
		},
	}


static func mission() -> Dictionary:
	return {"objectives": [{"node": 0, "radius": 80.0, "primary": true}, {"node": 1, "radius": 50.0, "primary": false}]}
