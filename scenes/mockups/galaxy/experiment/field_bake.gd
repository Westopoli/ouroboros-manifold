extends Node
# Throwaway experiment. Bakes the territory field into a 3D grid on the GPU.
# Field formulas are exactly shell_metaball.gdshader's (compact kernel
# (1-d^2/r^2)^3, r = R*(0.6+0.4*sig), own = sum, rival = max over other
# factions, net = own*(1-gap*smoothstep(0.3,1,rival/own))), restructured so one
# pass over the systems per cell serves every faction (per-faction sum and max,
# rival = best max among the other factions).
# Per-cell result: best net over factions (R), that faction's rival term (G),
# that faction's id (B). Stored as RGBAH 3D texture (A unused).

const R_INFLUENCE := GalaxyGen.INFLUENCE_RADIUS
const GAP := 0.5          # legacy_shell_renderer.gd sets gap_strength 0.5
const ISO := 0.6
const MAX_SYS := 1024
const MAX_FAC := 16

const BAKE_SHADER := """
shader_type canvas_item;
render_mode blend_disabled;
uniform sampler2D sys_a : filter_nearest;
uniform sampler2D sys_f : filter_nearest;
uniform int n_sys;
uniform int n_fac;
uniform int N;
uniform int cols;
uniform vec3 gmin;
uniform float cell;
uniform float R;
uniform float gap_strength;
void fragment() {
	ivec2 px = ivec2(FRAGCOORD.xy);
	ivec2 s = px / N;
	ivec2 c = px - s * N;
	int z = s.y * cols + s.x;
	COLOR = vec4(0.0);
	if (z < N) {
	vec3 p = gmin + (vec3(float(c.x), float(c.y), float(z)) + 0.5) * cell;
	float own[16];
	float mk[16];
	for (int f = 0; f < 16; f++) { own[f] = 0.0; mk[f] = 0.0; }
	for (int i = 0; i < 1024; i++) {
		if (i >= n_sys) break;
		float u = (float(i) + 0.5) / 1024.0;
		vec4 sys = texture(sys_a, vec2(u, 0.5));
		vec3 diff = p - sys.xyz;
		float r = R * (0.6 + sys.w * 0.4);
		float d2 = dot(diff, diff);
		if (d2 >= r * r) continue;
		float k = 1.0 - d2 / (r * r);
		k = k * k * k;
		int f = int(texture(sys_f, vec2(u, 0.5)).r + 0.5);
		own[f] += k;
		mk[f] = max(mk[f], k);
	}
	float m1 = 0.0; float m2 = 0.0; int m1f = -1;
	for (int f = 0; f < 16; f++) {
		if (f >= n_fac) break;
		if (mk[f] > m1) { m2 = m1; m1 = mk[f]; m1f = f; }
		else if (mk[f] > m2) { m2 = mk[f]; }
	}
	float best = 0.0; float best_rival = 0.0; int best_f = 0;
	for (int f = 0; f < 16; f++) {
		if (f >= n_fac) break;
		float o = own[f];
		if (o <= 0.0) continue;
		float rival = (f == m1f) ? m2 : m1;
		float ratio = rival / max(o, 0.001);
		float net = o * (1.0 - gap_strength * smoothstep(0.3, 1.0, ratio));
		if (net > best) { best = net; best_rival = rival; best_f = f; }
	}
	COLOR = vec4(best, best_rival, float(best_f), 0.0);
	}
}
"""

var n_cells := 96
var gmin := Vector3.ZERO
var gsize := 0.0
var _vp: SubViewport
var _rect: ColorRect
var _mat: ShaderMaterial
var _tex_a: ImageTexture
var _tex_f: ImageTexture
var cols := 1
var rows := 1
var last_gpu_ms := 0.0     # GPU time of the bake pass (viewport measure)
var last_wall_ms := 0.0    # wall time: data upload -> readback -> 3D texture built
var volume: ImageTexture3D
var systems: Dictionary = {}

static func system_data(g: Galaxy) -> Dictionary:
	var pos := PackedVector3Array()
	var sn := PackedFloat32Array()
	var fid := PackedInt32Array()
	var maxsig := {}
	for s in g.systems:
		if s.owner >= 0:
			maxsig[s.owner] = maxf(maxsig.get(s.owner, 0.0), s.significance)
	for s in g.systems:
		if s.owner >= 0:
			pos.append(s.pos)
			sn.append(clampf(s.significance / maxf(maxsig[s.owner], 0.01), 0.0, 1.0))
			fid.append(s.owner)
	return {"pos": pos, "sn": sn, "fid": fid, "nfac": g.factions.size()}

static func bounds_for_ball() -> Vector2:
	# returns (min_coord, size) of the cube: ball radius + one influence radius
	var half := GalaxyGen.BALL_RADIUS + R_INFLUENCE
	return Vector2(-half, 2.0 * half)

func setup(p_cells: int) -> void:
	n_cells = p_cells
	var b := bounds_for_ball()
	gmin = Vector3(b.x, b.x, b.x)
	gsize = b.y
	cols = 16 if n_cells > 64 else 8   # atlas columns: 64 -> 8x8, 96 -> 16x6, 128 -> 16x8
	rows = int(ceil(float(n_cells) / float(cols)))
	if _vp == null:
		_vp = SubViewport.new()
		_vp.disable_3d = true
		_vp.use_hdr_2d = true
		_vp.transparent_bg = true
		_vp.msaa_2d = Viewport.MSAA_DISABLED
		_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		add_child(_vp)
		_rect = ColorRect.new()
		_mat = ShaderMaterial.new()
		var sh := Shader.new()
		sh.code = BAKE_SHADER
		_mat.shader = sh
		_rect.material = _mat
		_vp.add_child(_rect)
		RenderingServer.viewport_set_measure_render_time(_vp.get_viewport_rid(), true)
	var sz := Vector2i(cols * n_cells, rows * n_cells)
	_vp.size = sz
	_rect.size = Vector2(sz)
	_rect.position = Vector2.ZERO

func _upload(data: Dictionary) -> void:
	var n: int = data.pos.size()
	var img_a := Image.create(MAX_SYS, 1, false, Image.FORMAT_RGBAF)
	var img_f := Image.create(MAX_SYS, 1, false, Image.FORMAT_RF)
	for i in n:
		var p: Vector3 = data.pos[i]
		img_a.set_pixel(i, 0, Color(p.x, p.y, p.z, data.sn[i]))
		img_f.set_pixel(i, 0, Color(float(data.fid[i]), 0, 0, 1))
	if _tex_a == null:
		_tex_a = ImageTexture.create_from_image(img_a)
		_tex_f = ImageTexture.create_from_image(img_f)
	else:
		_tex_a.update(img_a)
		_tex_f.update(img_f)
	_mat.set_shader_parameter("sys_a", _tex_a)
	_mat.set_shader_parameter("sys_f", _tex_f)
	_mat.set_shader_parameter("n_sys", n)
	_mat.set_shader_parameter("n_fac", int(data.nfac))
	_mat.set_shader_parameter("N", n_cells)
	_mat.set_shader_parameter("cols", cols)
	_mat.set_shader_parameter("gmin", gmin)
	_mat.set_shader_parameter("cell", gsize / float(n_cells))
	_mat.set_shader_parameter("R", R_INFLUENCE)
	_mat.set_shader_parameter("gap_strength", GAP)

# Full fill (or refill: same call). Returns atlas Image (RGBAH) too.
func bake(data: Dictionary) -> void:
	systems = data
	var t0 := Time.get_ticks_usec()
	_upload(data)
	_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	RenderingServer.force_draw(false, 0.0)   # synchronous, no present: avoids Xvfb present stalls in timings
	var t1 := Time.get_ticks_usec()
	var atlas := _vp.get_texture().get_image()
	var t2 := Time.get_ticks_usec()
	var imgs: Array[Image] = []
	for z in n_cells:
		var cx := (z % cols) * n_cells
		var cy := (z / cols) * n_cells
		imgs.append(atlas.get_region(Rect2i(cx, cy, n_cells, n_cells)))
	if volume == null:
		volume = ImageTexture3D.new()
		volume.create(atlas.get_format(), n_cells, n_cells, n_cells, false, imgs)
	else:
		volume.update(imgs)
	var t3 := Time.get_ticks_usec()
	last_wall_ms = (t3 - t0) / 1000.0
	last_gpu_ms = RenderingServer.viewport_get_measured_render_time_gpu(_vp.get_viewport_rid())
	last_parts = {"draw_wait_ms": (t1 - t0) / 1000.0, "readback_ms": (t2 - t1) / 1000.0, "slice_upload_ms": (t3 - t2) / 1000.0, "atlas_format": atlas.get_format()}
	last_images = imgs

var last_parts := {}
var last_images: Array[Image] = []

# Coarse skip grid: max net per block (block = n_cells/S cells, widened by one
# cell on every side so trilinear taps near a block edge are covered).
func build_skip(S := 16) -> ImageTexture3D:
	var n := n_cells
	var bs := float(n) / float(S)
	var mx := PackedFloat32Array()
	mx.resize(S * S * S)
	for z in n:
		var data: PackedByteArray = last_images[z].get_data()
		var bz0 := maxi(int(floor((z - 1) / bs)), 0)
		var bz1 := mini(int(floor((z + 1) / bs)), S - 1)
		for y in n:
			var by0 := maxi(int(floor((y - 1) / bs)), 0)
			var by1 := mini(int(floor((y + 1) / bs)), S - 1)
			var row := y * n * 8
			for x in n:
				var v := data.decode_half(row + x * 8)
				if v < 0.3:
					continue
				var bx0 := maxi(int(floor((x - 1) / bs)), 0)
				var bx1 := mini(int(floor((x + 1) / bs)), S - 1)
				for bz in range(bz0, bz1 + 1):
					for by in range(by0, by1 + 1):
						for bx in range(bx0, bx1 + 1):
							var i := (bz * S + by) * S + bx
							if v > mx[i]:
								mx[i] = v
	var imgs: Array[Image] = []
	for bz in S:
		var img := Image.create(S, S, false, Image.FORMAT_RF)
		for by in S:
			for bx in S:
				var m := mx[(bz * S + by) * S + bx]
				img.set_pixel(bx, by, Color(m, 0, 0, 1))
		imgs.append(img)
	var t := ImageTexture3D.new()
	t.create(Image.FORMAT_RF, S, S, S, false, imgs)
	return t

# Raw dump for the python accuracy script: system json + RGBAH slices (z, y, x).
func dump(prefix: String) -> void:
	var f := FileAccess.open(prefix + ".bin", FileAccess.WRITE)
	for img in last_images:
		f.store_buffer(img.get_data())
	f.close()
	var sys: Array = []
	for i in systems.pos.size():
		sys.append([systems.pos[i].x, systems.pos[i].y, systems.pos[i].z, systems.sn[i], systems.fid[i]])
	var j := FileAccess.open(prefix + ".json", FileAccess.WRITE)
	j.store_string(JSON.stringify({"n": n_cells, "gmin": [gmin.x, gmin.y, gmin.z], "gsize": gsize, "nfac": systems.nfac, "R": R_INFLUENCE, "gap": GAP, "systems": sys}))
	j.close()

static func palette_for(g: Galaxy) -> PackedVector3Array:
	var p := PackedVector3Array()
	for f in g.factions:
		var c := Color.from_hsv(f.hue, 0.65, 0.95 if f.id == 0 else 0.85, 1.0)
		p.append(Vector3(c.r, c.g, c.b))
	return p
