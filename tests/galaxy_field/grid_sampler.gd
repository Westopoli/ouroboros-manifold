extends RefCounted
# Copied from push/galaxy-field scenes/mockups/galaxy/tests/grid_sampler.gd (B0 pre-check; baker and comparator dropped).
# CPU-side reader for the field grid (and a small CPU baker for the detector
# positive controls). Slice z is an Image; the field slice is RGH (R = net,
# G = the winning faction's seam term, half floats, 4 bytes per cell) and the
# id slice is R8 (one byte per cell = faction id). Cell (x, y, z) is centred at
# gmin + (x + 0.5, y + 0.5, z + 0.5) * cell. Sampling is trilinear on net with
# texel-centre convention and edge clamp, the same as a linear-filtered 3D
# texture lookup at uvw = (p - gmin) / size; the id is the nearest cell's byte.

const ISO := 0.6

var n := 0
var gmin := Vector3.ZERO
var size := 0.0
var cell := 0.0
var _f: Array = []   # PackedByteArray per z
var _id: Array = []


static func from_field(field: Node) -> RefCounted:
	var s = load("res://tests/galaxy_field/grid_sampler.gd").new()
	s.n = int(field.GRID_CELLS)
	s.gmin = field.GRID_MIN
	s.size = float(field.GRID_SIZE)
	s.cell = s.size / float(s.n)
	for img in field.field_texture.get_data():
		s._f.append(img.get_data())
	for img in field.id_texture.get_data():
		s._id.append(img.get_data())
	return s


func cell_center(x: int, y: int, z: int) -> Vector3:
	return gmin + (Vector3(x, y, z) + Vector3(0.5, 0.5, 0.5)) * cell


func cell_net(x: int, y: int, z: int) -> float:
	return _f[z].decode_half((y * n + x) * 4)


func cell_rival(x: int, y: int, z: int) -> float:
	return _f[z].decode_half((y * n + x) * 4 + 2)


func cell_id(x: int, y: int, z: int) -> int:
	return _id[z][y * n + x]


func net(p: Vector3) -> float:
	var u := (p - gmin) / cell - Vector3(0.5, 0.5, 0.5)
	var fx := floorf(u.x)
	var fy := floorf(u.y)
	var fz := floorf(u.z)
	var tx := u.x - fx
	var ty := u.y - fy
	var tz := u.z - fz
	var x0 := clampi(int(fx), 0, n - 1)
	var x1 := clampi(int(fx) + 1, 0, n - 1)
	var y0 := clampi(int(fy), 0, n - 1)
	var y1 := clampi(int(fy) + 1, 0, n - 1)
	var z0 := clampi(int(fz), 0, n - 1)
	var z1 := clampi(int(fz) + 1, 0, n - 1)
	var c00 := lerpf(cell_net(x0, y0, z0), cell_net(x1, y0, z0), tx)
	var c10 := lerpf(cell_net(x0, y1, z0), cell_net(x1, y1, z0), tx)
	var c01 := lerpf(cell_net(x0, y0, z1), cell_net(x1, y0, z1), tx)
	var c11 := lerpf(cell_net(x0, y1, z1), cell_net(x1, y1, z1), tx)
	return lerpf(lerpf(c00, c10, ty), lerpf(c01, c11, ty), tz)


func id_at(p: Vector3) -> int:
	var u := (p - gmin) / cell
	return cell_id(clampi(int(floorf(u.x)), 0, n - 1), clampi(int(floorf(u.y)), 0, n - 1), clampi(int(floorf(u.z)), 0, n - 1))


# First point along o + d*t (t in [t0, t1], stepped by `step`) where `sampler`
# (Callable p -> float) reaches ISO from below, refined by 22 bisections.
# Starting inside the field returns t0. Returns -1.0 when there is none.
static func first_surface(sampler: Callable, o: Vector3, d: Vector3, t0: float, t1: float, step: float) -> float:
	var t := t0
	var prev: float = sampler.call(o + d * t)
	if prev >= ISO:
		return t0
	while t < t1:
		var tn := minf(t + step, t1)
		var cur: float = sampler.call(o + d * tn)
		if cur >= ISO:
			var lo := t
			var hi := tn
			for _i in 22:
				var mid := 0.5 * (lo + hi)
				if float(sampler.call(o + d * mid)) >= ISO:
					hi = mid
				else:
					lo = mid
			return 0.5 * (lo + hi)
		t = tn
		prev = cur
	return -1.0
