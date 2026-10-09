class_name GroundMesh
extends RefCounted

const CELL_WU := 100.0
const GroundBands := preload("res://scenes/ground3d/ground_bands.gd")


# Vertices sit at cell centres (i + 0.5) * CELL_WU, matching the sim's sampling (csrc/terrain.c ts_height_q);
# heights are int32 cm, 100 cm = 1 wu. Colour is stage 3's band ramp, steep tint where not walkable.
static func build(terrain: Dictionary) -> MeshInstance3D:
	var w: int = terrain["cells_w"]
	var h: int = terrain["cells_h"]
	var heights: PackedInt32Array = terrain["heights"]
	var bands: PackedByteArray = terrain["bands"]
	var walk: PackedByteArray = terrain["walkable"]
	var cols := PackedColorArray()
	cols.resize(w * h)
	for k in w * h:
		cols[k] = GroundBands.colour(bands[k], walk[k] != 0)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in h - 1:
		for i in w - 1:
			var k00 := j * w + i
			var k10 := k00 + 1
			var k01 := k00 + w
			var k11 := k01 + 1
			for k in [k00, k10, k11, k00, k11, k01]:
				st.set_color(cols[k])
				st.add_vertex(Vector3((k % w + 0.5) * CELL_WU, heights[k] / 100.0, (k / w + 0.5) * CELL_WU))
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.vertex_color_is_srgb = true
	mat.roughness = 0.9
	mi.material_override = mat
	return mi
