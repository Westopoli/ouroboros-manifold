extends RefCounted

# Height field sampling and ray pick for the 3D ground (S-236, S-207 R-207-06/07). Heights are
# int32 cm per cell at cell centres (csrc/terrain.c ts_height_q), 100 cm = 1 wu.
# Ray march + bisect after scenes/mockups/landscape/pass4_ui.gd _pick.

const CELL_WU := 100.0
const STEP := 50.0
const MAX_T := 80000.0
const BISECT := 12


static func height_at(t: Dictionary, wx: float, wy: float) -> float:
	var w := int(t.get("cells_w", 0))
	var h := int(t.get("cells_h", 0))
	var hs: PackedInt32Array = t.get("heights", PackedInt32Array())
	if w < 1 or h < 1 or hs.size() < w * h:
		return 0.0
	var fx := clampf(wx / CELL_WU - 0.5, 0.0, w - 1.0)
	var fy := clampf(wy / CELL_WU - 0.5, 0.0, h - 1.0)
	var i0 := maxi(mini(int(floor(fx)), w - 2), 0)
	var j0 := maxi(mini(int(floor(fy)), h - 2), 0)
	var i1 := mini(i0 + 1, w - 1)
	var j1 := mini(j0 + 1, h - 1)
	var tx := fx - i0
	var ty := fy - j0
	var a := lerpf(hs[j0 * w + i0], hs[j0 * w + i1], tx)
	var b := lerpf(hs[j1 * w + i0], hs[j1 * w + i1], tx)
	return lerpf(a, b, ty) / 100.0


static func world_to_3d(t: Dictionary, wx: float, wy: float) -> Vector3:
	return Vector3(wx, height_at(t, wx, wy), wy)


static func _inside(t: Dictionary, p: Vector3) -> bool:
	return p.x >= 0.0 and p.z >= 0.0 and p.x <= int(t.get("cells_w", 0)) * CELL_WU and p.z <= int(t.get("cells_h", 0)) * CELL_WU


static func pick(t: Dictionary, origin: Vector3, dir: Vector3) -> Variant:
	if dir.y >= 0.0 and origin.y > height_at(t, origin.x, origin.z):
		return null
	var d := dir.normalized()
	var s := 0.0
	while s < MAX_T:
		var p := origin + d * s
		if _inside(t, p) and p.y <= height_at(t, p.x, p.z):
			var a := maxf(s - STEP, 0.0)
			var b := s
			for _k in BISECT:
				var m := (a + b) * 0.5
				var pm := origin + d * m
				if pm.y <= height_at(t, pm.x, pm.z):
					b = m
				else:
					a = m
			var hit := origin + d * b
			return Vector2(hit.x, hit.z)
		s += STEP
	return null
