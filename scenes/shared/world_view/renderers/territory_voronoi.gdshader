shader_type canvas_item;

uniform sampler2D system_data : filter_nearest;
uniform sampler2D faction_colors : filter_nearest;
uniform int system_count = 0;
uniform float fill_alpha : hint_range(0.0, 1.0) = 0.25;
uniform float fill_falloff : hint_range(0.01, 0.5) = 0.15;
uniform float edge_softness : hint_range(0.001, 0.1) = 0.02;
uniform float outline_width : hint_range(0.001, 0.05) = 0.01;
uniform float outline_alpha : hint_range(0.0, 1.0) = 0.8;
uniform float border_width : hint_range(0.001, 0.05) = 0.012;
uniform float border_alpha : hint_range(0.0, 1.0) = 0.9;

void fragment() {
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
		float sys_significance = sys.a;

		float d = distance(UV, sys_pos);

		if (d < nearest_dist) {
			second_dist = nearest_dist;
			second_faction = nearest_faction;
			nearest_dist = d;
			nearest_faction = sys_faction;
			nearest_significance = sys_significance;
		} else if (d < second_dist) {
			second_dist = d;
			second_faction = sys_faction;
		}
	}

	if (nearest_faction < 0.001) {
		COLOR = vec4(0.0);
	} else {
		int faction_idx = int(round(nearest_faction * 8.0)) - 1;
		float fc_u = (float(faction_idx) + 0.5) / 8.0;
		vec3 color = texture(faction_colors, vec2(fc_u, 0.5)).rgb;

		// Territory fill — fades with distance from nearest system
		float effective_falloff = fill_falloff * (0.5 + nearest_significance * 0.5);
		float fill_factor = 1.0 - smoothstep(effective_falloff - edge_softness, effective_falloff, nearest_dist);
		float alpha = fill_alpha * fill_factor;

		// Territory perimeter outline — bright ring at the edge of influence
		float outline_center = effective_falloff - edge_softness * 0.5;
		float outline_dist = abs(nearest_dist - outline_center);
		float outline_factor = (1.0 - smoothstep(0.0, outline_width, outline_dist)) * fill_factor;
		alpha = max(alpha, outline_factor * outline_alpha);

		// Faction border — where two different factions meet
		if (nearest_faction != second_faction && second_faction > 0.001) {
			float border_factor = second_dist - nearest_dist;
			if (border_factor < border_width) {
				float border_intensity = 1.0 - border_factor / border_width;
				border_intensity = border_intensity * border_intensity;
				alpha = max(alpha, border_intensity * border_alpha);
			}
		}

		COLOR = vec4(color, alpha);
	}
}
