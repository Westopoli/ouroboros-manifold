shader_type spatial;
render_mode unshaded, cull_front, blend_mix;

uniform sampler2D system_positions : filter_nearest;
uniform int system_count = 0;
uniform sampler2D rival_positions : filter_nearest;
uniform int rival_count = 0;
uniform vec3 shell_color = vec3(0.3, 0.6, 1.0);
uniform float influence_radius = 0.25;
uniform float iso_threshold = 0.6;
uniform float shell_opacity = 0.12;
uniform float gap_strength = 0.8;
uniform vec3 box_min_world;
uniform vec3 box_max_world;

varying vec3 v_world_pos;

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float eval_own_field(vec3 p) {
	float field = 0.0;
	for (int i = 0; i < 512; i++) {
		if (i >= system_count) break;
		float u = (float(i) + 0.5) / 512.0;
		vec4 sys = texture(system_positions, vec2(u, 0.5));
		vec3 diff = p - sys.xyz;
		float r = influence_radius * (0.6 + sys.w * 0.4);
		float d2 = dot(diff, diff);
		field += (r * r) / (d2 + r * r);
	}
	return field;
}

float eval_rival_field(vec3 p) {
	float best = 0.0;
	for (int i = 0; i < 2048; i++) {
		if (i >= rival_count) break;
		float u = (float(i) + 0.5) / 2048.0;
		vec4 sys = texture(rival_positions, vec2(u, 0.5));
		vec3 diff = p - sys.xyz;
		float r = influence_radius * (0.6 + sys.w * 0.4);
		float d2 = dot(diff, diff);
		best = max(best, (r * r) / (d2 + r * r));
	}
	return best;
}

float eval_net_field(vec3 p) {
	float own = eval_own_field(p);
	float rival = eval_rival_field(p);
	float ratio = rival / max(own, 0.001);
	float gap_factor = gap_strength * smoothstep(0.3, 1.0, ratio);
	return own * (1.0 - gap_factor);
}

void fragment() {
	vec3 cam = (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 ray_dir = normalize(v_world_pos - cam);

	vec3 safe_dir = ray_dir + vec3(1e-6);
	vec3 inv_dir = 1.0 / safe_dir;
	vec3 t1 = (box_min_world - cam) * inv_dir;
	vec3 t2 = (box_max_world - cam) * inv_dir;
	vec3 t_mn = min(t1, t2);
	vec3 t_mx = max(t1, t2);
	float t_enter = max(max(t_mn.x, t_mn.y), t_mn.z);
	float t_exit = min(min(t_mx.x, t_mx.y), t_mx.z);
	t_enter = max(t_enter, 0.0);

	if (t_enter >= t_exit) discard;

	float step_size = (t_exit - t_enter) / 20.0;
	vec3 hit_pos = vec3(0.0);
	bool found = false;

	float hit_rival = 0.0;
	for (int s = 0; s < 20; s++) {
		float t = t_enter + (float(s) + 0.5) * step_size;
		vec3 p = cam + ray_dir * t;
		float own = eval_own_field(p);
		// Skip rival eval when own field is too weak to ever reach threshold
		float rival = 0.0;
		if (own >= iso_threshold * 0.5) {
			rival = eval_rival_field(p);
		}
		// Suppress proportional to rival/own ratio — strong at borders, zero at cores
		float ratio = rival / max(own, 0.001);
		float gap_factor = gap_strength * smoothstep(0.3, 1.0, ratio);
		float net = own * (1.0 - gap_factor);
		if (net >= iso_threshold) {
			found = true;
			hit_pos = p;
			hit_rival = rival;
			break;
		}
	}

	if (!found) discard;

	float e = step_size * 0.4;
	vec3 n = normalize(vec3(
		eval_net_field(hit_pos + vec3(e, 0.0, 0.0)) - eval_net_field(hit_pos - vec3(e, 0.0, 0.0)),
		eval_net_field(hit_pos + vec3(0.0, e, 0.0)) - eval_net_field(hit_pos - vec3(0.0, e, 0.0)),
		eval_net_field(hit_pos + vec3(0.0, 0.0, e)) - eval_net_field(hit_pos - vec3(0.0, 0.0, e))
	));

	float rim = 1.0 - abs(dot(n, -ray_dir));
	rim = rim * rim;

	// Border glow: reuse cached rival field from raymarch hit
	float border_intensity = smoothstep(0.15, 0.5, hit_rival);
	vec3 glow_color = mix(shell_color, vec3(1.0), 0.6);

	float final_alpha = shell_opacity * (0.4 + rim * 1.5);
	// Boost alpha at border seams so the glow is visible
	final_alpha = mix(final_alpha, shell_opacity * 2.5, border_intensity);

	ALBEDO = mix(shell_color, glow_color, border_intensity * 0.7);
	EMISSION = mix(
		shell_color * (0.3 + rim * 0.7),
		glow_color * 2.0,
		border_intensity
	);
	ALPHA = final_alpha;

	// Write depth at the isosurface hit point for occlusion at overview
	if (shell_opacity > 0.3) {
		vec4 view_hit = VIEW_MATRIX * vec4(hit_pos, 1.0);
		vec4 clip_hit = PROJECTION_MATRIX * view_hit;
		DEPTH = clip_hit.z / clip_hit.w;
	}
}
