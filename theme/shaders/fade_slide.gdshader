shader_type canvas_item;

uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float slide_offset : hint_range(0.0, 32.0) = 8.0;

void vertex() {
	VERTEX.y += slide_offset * (1.0 - progress);
}

void fragment() {
	COLOR.a *= progress;
}
