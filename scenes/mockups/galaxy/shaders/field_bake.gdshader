shader_type canvas_item;
render_mode blend_disabled;

// Territory field bake: one pass per grid cell, laid out as a sheet of z-slices
// (cols slices across). The field maths is shell_metaball.gdshader's three
// field functions, run once per cell for every faction at once:
//   per faction f, normalised by f's own max significance M_f (the legacy code
//   normalised rivals by the EVALUATING faction's max, a quirk kept on purpose):
//     r = R * (0.6 + 0.4 * clamp(sig / M_f, 0, 1)),  k = (1 - d^2/r^2)^3 inside r
//     own_f = sum of k over f's systems, rival_f = max k over every other system
//     net_f = own_f * (1 - gap * smoothstep(0.3, 1.0, rival_f / max(own_f, 0.001)))
//   cell = the faction with the highest net (ties: lowest id).
// mode 0 writes (net, rival, 0, 0) to a half-float sheet; mode 1 writes the
// winning faction id / 255 to an 8-bit sheet.

uniform sampler2D sys_a : filter_nearest, repeat_disable; // xyz = position, w = raw significance
uniform sampler2D sys_o : filter_nearest, repeat_disable; // r = owner id
uniform int n_sys = 0;
uniform int n_fac = 0;
uniform int N = 96;
uniform int cols = 16;
uniform vec3 gmin = vec3(-64.0);
uniform float cell = 1.3333;
uniform float R = 14.0;
uniform float gap_strength = 0.5;
uniform float max_sig[16];
uniform int mode = 0;

void fragment() {
	ivec2 px = ivec2(FRAGCOORD.xy);
	ivec2 s = px / N;
	ivec2 c = px - s * N;
	int z = s.y * cols + s.x;
	COLOR = vec4(0.0);
	if (z < N) {
	vec3 p = gmin + (vec3(float(c.x), float(c.y), float(z)) + 0.5) * cell;
	float own[16];
	float rival[16];
	for (int f = 0; f < 16; f++) {
		own[f] = 0.0;
		rival[f] = 0.0;
	}
	for (int i = 0; i < 1024; i++) {
		if (i >= n_sys) {
			break;
		}
		vec4 sys = texelFetch(sys_a, ivec2(i, 0), 0);
		vec3 diff = p - sys.xyz;
		float d2 = dot(diff, diff);
		if (d2 >= R * R) {
			continue;
		}
		int owner = int(texelFetch(sys_o, ivec2(i, 0), 0).r + 0.5);
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
	if (mode == 0) {
		COLOR = vec4(best, best_rival, 0.0, 0.0);
	} else {
		COLOR = vec4(float(best_f) / 255.0, 0.0, 0.0, 0.0);
	}
	}
}
