shader_type canvas_item;

// Data textures — updated by GDScript when territory changes
uniform sampler2D system_data : filter_nearest;   // Nx1: RG=normalized XZ pos, B=faction index/8, A=significance
uniform sampler2D faction_colors : filter_nearest; // 8x1: RGB=faction color
uniform int system_count = 0;

// Fill controls
uniform float fill_opacity : hint_range(0.0, 1.0) = 0.15;       // max alpha inside faction territory
uniform float fill_falloff : hint_range(0.01, 0.5) = 0.18;       // UV-space radius of territory around each system
uniform float edge_softness : hint_range(0.001, 0.1) = 0.04;     // smoothstep band at territory outer edge

// Faction border controls
uniform float border_width : hint_range(0.001, 0.08) = 0.02;     // UV-space width of glow where factions meet
uniform float border_brightness : hint_range(0.5, 3.0) = 1.6;    // color brightness boost at faction borders
uniform float border_alpha : hint_range(0.0, 1.0) = 0.7;         // max alpha of the border glow

void fragment() {
	float nearest_dist = 1e10;
	float nearest_faction = 0.0;
	float nearest_significance = 0.0;
	float second_dist = 1e10;
	float second_faction = 0.0;

	// Find nearest and second-nearest system
	for (int i = 0; i < system_count; i++) {
		float u = (float(i) + 0.5) / 128.0;
		vec4 sys = texture(system_data, vec2(u, 0.5));
		vec2 sys_pos = sys.rg;
		float sys_faction = sys.b;

		float d = distance(UV, sys_pos);

		if (d < nearest_dist) {
			second_dist = nearest_dist;
			second_faction = nearest_faction;
			nearest_dist = d;
			nearest_faction = sys_faction;
			nearest_significance = sys.a;
		} else if (d < second_dist) {
			second_dist = d;
			second_faction = sys_faction;
		}
	}

	// Unowned cell — fully transparent
	if (nearest_faction < 0.001) {
		COLOR = vec4(0.0);
		return;
	}

	// Look up faction color
	int faction_idx = int(round(nearest_faction * 8.0)) - 1;
	float fc_u = (float(faction_idx) + 0.5) / 8.0;
	vec3 fcolor = texture(faction_colors, vec2(fc_u, 0.5)).rgb;

	// --- Territory fill ---
	// Each system's territory fades with distance. Significance scales the reach.
	float effective_falloff = fill_falloff * (0.6 + nearest_significance * 0.4);
	float fill_factor = 1.0 - smoothstep(effective_falloff - edge_softness, effective_falloff, nearest_dist);

	// Inside same-faction territory: continuous fill, no internal cell edges
	float alpha = fill_opacity * fill_factor;
	vec3 out_color = fcolor;

	// --- Faction border glow ---
	// Where two DIFFERENT factions meet, draw a soft luminous edge
	bool is_faction_border = (nearest_faction != second_faction) && (second_faction > 0.001);
	if (is_faction_border) {
		float border_dist = second_dist - nearest_dist;
		if (border_dist < border_width) {
			float t = 1.0 - (border_dist / border_width);
			float glow = t * t; // quadratic for soft falloff
			// Brighten the faction color and boost alpha at the border
			out_color = mix(fcolor, fcolor * border_brightness, glow);
			alpha = max(alpha, glow * border_alpha);
		}
	}

	COLOR = vec4(out_color, alpha);
}
