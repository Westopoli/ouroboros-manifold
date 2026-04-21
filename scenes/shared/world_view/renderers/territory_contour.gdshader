shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;

uniform sampler2D faction_map : filter_linear;
uniform float contour_threshold : hint_range(0.0, 0.5) = 0.08;
uniform float line_thickness : hint_range(0.5, 5.0) = 1.5;
uniform float brightness : hint_range(0.5, 3.0) = 1.4;
uniform vec4 contour_color : source_color = vec4(0.788, 0.659, 0.298, 1.0);

void fragment() {
    vec2 tex_size = vec2(textureSize(faction_map, 0));
    vec2 texel = line_thickness / tex_size;
    vec4 center = texture(faction_map, UV);

    if (center.a < 0.01) {
        ALPHA = 0.0;
    } else {
        float max_diff = 0.0;
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                if (dx == 0 && dy == 0) continue;
                vec4 neighbor = texture(faction_map, UV + vec2(float(dx), float(dy)) * texel);
                float diff = length(center.rgb - neighbor.rgb);
                if (neighbor.a < 0.01) diff = max(diff, center.a * 0.5);
                max_diff = max(max_diff, diff);
            }
        }
        float edge = smoothstep(contour_threshold, contour_threshold + 0.05, max_diff);
        ALBEDO = contour_color.rgb * brightness;
        ALPHA = edge * contour_color.a;
    }
}
