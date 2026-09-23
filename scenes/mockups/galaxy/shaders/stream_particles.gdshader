shader_type particles;

uniform float outer_radius = 45.0;
uniform float inner_radius = 5.0;
uniform float flow_speed = 0.06;
uniform float stream_width = 1.5;
uniform float y_scatter = 1.5;
uniform int num_streams = 6;
uniform vec4 stream_color : source_color = vec4(1.0, 0.92, 0.65, 0.7);

float hash(uint n) {
	n = (n << 13u) ^ n;
	n = n * (n * n * 15731u + 789221u) + 1376312589u;
	return float(n & 0x7fffffffu) / float(0x7fffffff);
}

void start() {
	uint id = uint(INDEX);
	int stream_id = int(uint(INDEX) % uint(num_streams));
	float stream_angle = float(stream_id) / float(num_streams) * TAU;

	float progress = fract(TIME * flow_speed + hash(id) * 1.0);
	float radius = mix(outer_radius, inner_radius, progress);

	float scatter = (hash(id + 5000u) - 0.5) * stream_width * 2.0;
	float y_off = (hash(id + 6000u) - 0.5) * y_scatter * 2.0;

	vec3 stream_dir = vec3(cos(stream_angle), 0.0, sin(stream_angle));
	vec3 perp = vec3(-stream_dir.z, 0.0, stream_dir.x);

	TRANSFORM[3].xyz = stream_dir * radius + perp * scatter + vec3(0.0, y_off, 0.0);

	float fade = 1.0;
	if (progress > 0.8) {
		fade = 1.0 - (progress - 0.8) / 0.2;
	}
	if (progress < 0.1) {
		fade = progress / 0.1;
	}
	COLOR = vec4(stream_color.rgb, stream_color.a * fade);
}

void process() {
	uint id = uint(INDEX);
	int stream_id = int(uint(INDEX) % uint(num_streams));
	float stream_angle = float(stream_id) / float(num_streams) * TAU;

	float progress = fract(TIME * flow_speed + hash(id) * 1.0);
	float radius = mix(outer_radius, inner_radius, progress);

	float scatter = (hash(id + 5000u) - 0.5) * stream_width * 2.0;
	float y_off = (hash(id + 6000u) - 0.5) * y_scatter * 2.0;

	vec3 stream_dir = vec3(cos(stream_angle), 0.0, sin(stream_angle));
	vec3 perp = vec3(-stream_dir.z, 0.0, stream_dir.x);

	TRANSFORM[3].xyz = stream_dir * radius + perp * scatter + vec3(0.0, y_off, 0.0);

	float fade = 1.0;
	if (progress > 0.8) {
		fade = 1.0 - (progress - 0.8) / 0.2;
	}
	if (progress < 0.1) {
		fade = progress / 0.1;
	}
	COLOR = vec4(stream_color.rgb, stream_color.a * fade);
}
