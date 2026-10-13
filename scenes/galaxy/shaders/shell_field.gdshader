shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, cull_disabled;

// The territory shell, drawn in one full-screen pass for every faction by
// marching the baked field grid (territory_field.gd). Replaces
// shell_metaball.gdshader, which looped over every system at every step.
//
// Layers: the first surface of each faction along the ray, up to four factions
// per ray, whether the ray reaches a faction through open space or straight
// across a seam. A layer is drawn only for a faction the ray has not drawn yet,
// so no ridge appears inside a faction's own blob.
//
// Cost shape (tests/shader_cost.gd counts worst-case fetches): the march is
// GROUPS x SUB field fetches plus one id fetch per group; shading happens after
// the march, once per recorded layer: one fetch to refine the surface position
// (two secant steps) and a 4-tap tetrahedral normal. Worst case 100 fetches per
// pixel, no loop bounded by a system or faction count.

const int GROUPS = 16;
const int SUB = 4;
const int LAYERS = 4;
const float ISO = 0.6;

uniform sampler3D field : filter_linear, repeat_disable;    // R = net, G = seam term
uniform sampler3D id_tex : filter_nearest, repeat_disable;  // R = faction id / 255
uniform vec3 gmin = vec3(-64.0);
uniform float gsize = 128.0;
uniform float grid_n = 96.0;
uniform float shell_opacity = 0.12;
uniform vec3 palette[16];
// 0 = normal; 1 = every pixel opaque, ALBEDO.r = number of layers drawn / 16.
uniform int debug_mode = 0;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

vec2 fld2(vec3 p) {
	return texture(field, (p - gmin) / gsize).rg;
}

float fld(vec3 p) {
	return texture(field, (p - gmin) / gsize).r;
}

int id_at(vec3 p) {
	vec3 uvw = clamp((p - gmin) / gsize, vec3(0.0), vec3(0.9999));
	return int(texelFetch(id_tex, ivec3(uvw * grid_n), 0).r * 255.0 + 0.5);
}

void fragment() {
	vec4 vv = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, 1.0, 1.0);
	vec3 d = normalize((INV_VIEW_MATRIX * vec4(normalize(vv.xyz / vv.w), 0.0)).xyz);
	vec3 cam = INV_VIEW_MATRIX[3].xyz;

	vec3 inv_d = 1.0 / (d + vec3(1e-6));
	vec3 t1 = (gmin - cam) * inv_d;
	vec3 t2 = (gmin + vec3(gsize) - cam) * inv_d;
	vec3 t_mn = min(t1, t2);
	vec3 t_mx = max(t1, t2);
	float t0 = max(max(max(t_mn.x, t_mn.y), t_mn.z), 0.0);
	float t_end = min(min(t_mx.x, t_mx.y), t_mx.z);

	int nl = 0;
	int mask = 0;
	float l_lo[LAYERS];
	float l_hi[LAYERS];
	float l_flo[LAYERS];
	float l_fhi[LAYERS];
	float l_g[LAYERS];
	float l_ref[LAYERS];
	int l_id[LAYERS];
	for (int i = 0; i < LAYERS; i++) {
		l_lo[i] = 0.0;
		l_hi[i] = 0.0;
		l_flo[i] = 0.0;
		l_fhi[i] = 0.0;
		l_g[i] = 0.0;
		l_ref[i] = 0.0;
		l_id[i] = 0;
	}

	if (t0 < t_end) {
		float dt = (t_end - t0) / float(GROUPS * SUB);
		// A camera inside a bubble sees its first sample already inside: that counts
		// as an entry out of f_prev = 0, so the bubble's faction is the first layer.
		bool was_in = false;
		float t_prev = t0;
		float f_prev = 0.0;
		float t = t0 + 0.5 * dt;
		for (int g = 0; g < GROUPS; g++) {
			float e_tp = 0.0;
			float e_tc = 0.0;
			float e_fp = 0.0;
			float e_fc = 0.0;
			float e_g = 0.0;
			bool entered = false;
			float in_t = -1.0;
			float in_tp = 0.0;
			float in_f = 0.0;
			float in_fp = 0.0;
			float in_g = 0.0;
			for (int j = 0; j < SUB; j++) {
				vec2 fv = fld2(cam + d * t);
				bool in_now = fv.x >= ISO;
				if (in_now && !was_in) {
					entered = true;
					e_tp = t_prev;
					e_tc = t;
					e_fp = f_prev;
					e_fc = fv.x;
					e_g = fv.y;
				}
				if (in_now) {
					in_t = t;
					in_tp = t_prev;
					in_f = fv.x;
					in_fp = f_prev;
					in_g = fv.y;
				}
				was_in = in_now;
				t_prev = t;
				f_prev = fv.x;
				t += dt;
			}
			if (in_t >= 0.0) {
				float ts = entered ? e_tc : in_t;
				int id = id_at(cam + d * ts);
				if ((mask & (1 << id)) == 0 && nl < LAYERS) {
					mask |= 1 << id;
					l_id[nl] = id;
					if (entered) {
						l_lo[nl] = e_tp;
						l_hi[nl] = e_tc;
						l_flo[nl] = e_fp;
						l_fhi[nl] = e_fc;
						l_g[nl] = e_g;
						l_ref[nl] = 1.0;
					} else {
						l_lo[nl] = in_tp;
						l_hi[nl] = in_t;
						l_flo[nl] = in_fp;
						l_fhi[nl] = in_f;
						l_g[nl] = in_g;
					}
					nl++;
				}
			}
			if (nl >= LAYERS) {
				break;
			}
		}
	}

	float T = 1.0;
	vec3 C = vec3(0.0);
	float h = gsize / grid_n;
	vec3 k0 = vec3(1.0, -1.0, -1.0);
	vec3 k1 = vec3(-1.0, -1.0, 1.0);
	vec3 k2 = vec3(-1.0, 1.0, -1.0);
	vec3 k3 = vec3(1.0, 1.0, 1.0);
	for (int l = 0; l < LAYERS; l++) {
		if (l < nl && T > 0.02) {
			float th = l_hi[l];
			if (l_ref[l] > 0.5) {
				// secant estimate of the iso crossing, one fetch, then a second secant
				// between the refined bracket (no stepping terraces, no bisection chain)
				float lo = l_lo[l];
				float hi = l_hi[l];
				float flo = l_flo[l];
				float fhi = l_fhi[l];
				float ts = lo + (ISO - flo) / max(fhi - flo, 1e-5) * (hi - lo);
				float fs = fld(cam + d * ts);
				if (fs >= ISO) {
					hi = ts;
					fhi = fs;
				} else {
					lo = ts;
					flo = fs;
				}
				th = lo + (ISO - flo) / max(fhi - flo, 1e-5) * (hi - lo);
			}
			vec3 p = cam + d * th;
			// tetrahedral gradient, one cell wide: smooths the grid's trilinear facets
			vec3 n = normalize(k0 * fld(p + k0 * h) + k1 * fld(p + k1 * h) + k2 * fld(p + k2 * h) + k3 * fld(p + k3 * h) + vec3(1e-6));
			float rim = 1.0 - abs(dot(n, -d));
			rim = rim * rim;
			float bi = smoothstep(0.15, 0.5, l_g[l]);
			vec3 col = palette[clamp(l_id[l], 0, 15)];
			vec3 glow = mix(col, vec3(1.0), 0.6);
			float a = shell_opacity * (0.4 + rim * 1.5);
			a = mix(a, shell_opacity * 2.5, bi);
			// unshaded: only ALBEDO reaches the output (EMISSION is ignored), as in the old shader
			C += T * a * mix(col, glow, bi * 0.7);
			T *= (1.0 - a);
		}
	}
	float A = 1.0 - T;
	if (debug_mode == 1) {
		ALBEDO = vec3(float(nl) / 16.0, 0.0, 0.0);
		ALPHA = 1.0;
	} else if (A < 0.0005) {
		ALPHA = 0.0;
		ALBEDO = vec3(0.0);
	} else {
		ALPHA = A;
		ALBEDO = C / A;
	}
}
