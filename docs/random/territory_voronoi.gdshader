shader_type canvas_item;

// Data textures
uniform sampler2D system_data : filter_nearest;   // Nx1: RG=pos, B=faction/8, A=significance
uniform sampler2D faction_colors : filter_nearest; // 8x1: RGB per faction
uniform int system_count = 0;

// Fill
uniform float fill_opacity : hint_range(0.0, 1.0) = 0.18;
uniform float fill_falloff : hint_range(0.05, 0.6) = 0.22;
uniform float edge_softness : hint_range(0.01, 0.15) = 0.07;

// Faction border glow (where two different factions meet)
uniform float border_width : hint_range(0.002, 0.06) = 0.025;
uniform float border_brightness : hint_range(0.5, 3.0) = 1.8;
uniform float border_alpha : hint_range(0.0, 1.0) = 0.65;

void fragment() {
	// --- Find nearest and second-nearest system ---
	float nearest_dist = 1e10;
	float nearest_faction = 0.0;
	float nearest_significance = 0.0;
	float second_dist = 1e10;
	float second_faction = 0.0;

	for (int i = 0; i < system_count; i++) {
		float u = (float(i) + 0.5) / 128.0;
		vec4 sys = texture(system_data, vec2(u, 0.5));
		vec2 sys_pos = sys.rg;
		float sys_faction = sys.b;
		float sys_sig = sys.a;

		float d = distance(UV, sys_pos);

		if (d < nearest_dist) {
			second_dist = nearest_dist;
			second_faction = nearest_faction;
			nearest_dist = d;
			nearest_faction = sys_faction;
			nearest_significance = sys_sig;
		} else if (d < second_dist) {
			second_dist = d;
			second_faction = sys_faction;
		}
	}

	// Unowned — transparent
	if (nearest_faction < 0.001) {
		COLOR = vec4(0.0);
		return;
	}

	// Faction color lookup
	int faction_idx = int(round(nearest_faction * 8.0)) - 1;
	float fc_u = (float(faction_idx) + 0.5) / 8.0;
	vec3 fcolor = texture(faction_colors, vec2(fc_u, 0.5)).rgb;

	// --- Territory fill ---
	// Significance scales reach: important systems claim more space
	float effective_falloff = fill_falloff * (0.6 + nearest_significance * 0.4);

	// The fill fades smoothly from full opacity near the system to zero at the edge.
	// Wide smoothstep band = organic, flowing boundary (not a hard cutoff).
	float fill_t = 1.0 - smoothstep(
		effective_falloff - edge_softness,   // starts fading here
		effective_falloff + edge_softness,   // fully gone here
		nearest_dist
	);

	float alpha = fill_opacity * fill_t;
	vec3 out_color = fcolor;

	// --- Faction border glow ---
	// Only where two DIFFERENT factions meet. Not between same-faction cells.
	bool is_faction_border = abs(nearest_faction - second_faction) > 0.001
	                         && second_faction > 0.001;

	if (is_faction_border) {
		// border_dist = how much closer we are to our faction than the rival.
		// At the exact Voronoi edge it's 0; deep inside territory it's large.
		float border_dist = second_dist - nearest_dist;
		if (border_dist < border_width) {
			float t = 1.0 - (border_dist / border_width);
			float glow = t * t;  // quadratic falloff for soft glow
			// Brighten faction color at the border and boost alpha
			out_color = mix(fcolor, min(fcolor * border_brightness, vec3(1.0)), glow);
			alpha = max(alpha, glow * border_alpha);
		}
	}

	// --- NO outline rings. NO per-system circles. ---
	// Territory = continuous filled regions with soft edges. That's it.

	COLOR = vec4(out_color, alpha);
}
