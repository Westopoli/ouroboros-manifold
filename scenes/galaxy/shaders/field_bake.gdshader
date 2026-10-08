shader_type canvas_item;
render_mode blend_disabled;

// Territory field bake: one pass per grid cell, laid out as a sheet of z-slices
// stacked down one column (N wide, N*N tall), so each slice is one contiguous run
// of bytes when the sheet is read back. The field maths is shell_metaball.gdshader's three
// field functions, run once per cell for every faction at once:
//   per faction f, normalised by f's own max significance M_f (the legacy code
//   normalised rivals by the EVALUATING faction's max, a quirk kept on purpose):
//     r = R * (0.6 + 0.4 * clamp(sig / M_f, 0, 1)),  k = (1 - d^2/r^2)^3 inside r
//     own_f = sum of k over f's systems, rival_f = max k over every other system
//     net_f = own_f * (1 - gap * smoothstep(0.3, 1.0, rival_f / max(own_f, 0.001)))
//   cell = the faction with the highest net (ties: lowest id).
// Systems arrive sorted by z with, per slice, the range of systems whose
// influence can reach it (ranges texture), so a cell scans a slab, not the whole
// galaxy. mode 0 writes (net, rival, id / 255, 0) to a half-float sheet; mode 1
// reads that sheet back and writes its id channel alone, to an 8-bit sheet.

uniform sampler2D sys_a : filter_nearest, repeat_disable; // xyz = position, w = raw significance
uniform sampler2D sys_o : filter_nearest, repeat_disable; // r = owner id
uniform int n_fac = 0;
uniform int N = 96;
uniform vec3 gmin = vec3(-64.0);
uniform float cell = 1.3333;
uniform float R = 16.0;
uniform float gap_strength = 0.5;
uniform float max_sig[16];
uniform sampler2D ranges : filter_nearest, repeat_disable; // per slice: r = first system, g = one past the last
uniform sampler2D field_sheet : filter_nearest, repeat_disable;
uniform int mode = 0;

void fragment() {
	ivec2 px = ivec2(FRAGCOORD.xy);
	int z = px.y / N;
	ivec2 c = ivec2(px.x, px.y - z * N);
	COLOR = vec4(0.0);
	if (mode == 1) {
		COLOR = vec4(texelFetch(field_sheet, px, 0).b, 0.0, 0.0, 0.0);
	} else if (z < N) {
		ivec2 rg = ivec2(texelFetch(ranges, ivec2(z, 0), 0).rg + 0.5);
		vec3 p = gmin + (vec3(float(c.x), float(c.y), float(z)) + 0.5) * cell;
		float own[16];
		float rival[16];
		for (int f = 0; f < 16; f++) {
			own[f] = 0.0;
			rival[f] = 0.0;
		}
		for (int i = 0; i < 1024; i++) {
			if (rg.x + i >= rg.y) {
				break;
			}
			vec4 sys = texelFetch(sys_a, ivec2(rg.x + i, 0), 0);
			vec3 diff = p - sys.xyz;
			float d2 = dot(diff, diff);
			if (d2 >= R * R) {
				continue;
			}
			int owner = int(texelFetch(sys_o, ivec2(rg.x + i, 0), 0).r + 0.5);
			for (int f = 0; f < 16; f++) {
				if (f >= n_fac) {
					break;
				}
				float sn = clamp(sys.w / max(max_sig[f], 0.01), 0.0, 1.0);
				float r = R * (0.6 + 0.4 * sn);
				if (d2 >= r * r) {
					continue;
				}
				float k = 1.0 - d2 / (r * r);
				k = k * k * k;
				if (owner == f) {
					own[f] += k;
				} else {
					rival[f] = max(rival[f], k);
				}
			}
		}
		float best = 0.0;
		float best_rival = 0.0;
		int best_f = 0;
		for (int f = 0; f < 16; f++) {
			if (f >= n_fac) {
				break;
			}
			if (own[f] <= 0.0) {
				continue;
			}
			float ratio = rival[f] / max(own[f], 0.001);
			float net = own[f] * (1.0 - gap_strength * smoothstep(0.3, 1.0, ratio));
			if (net > best) {
				best = net;
				best_rival = rival[f];
				best_f = f;
			}
		}
		COLOR = vec4(best, best_rival, float(best_f) / 255.0, 0.0);
	}
}
