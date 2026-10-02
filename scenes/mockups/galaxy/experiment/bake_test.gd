extends Node
const FieldBake := preload("res://scenes/mockups/galaxy/experiment/field_bake.gd")
func _sum(fb, N) -> Array:
	var s := 0.0
	var ids := 0.0
	for z in range(0, N, 3):
		var d: PackedByteArray = fb.last_images[z].get_data()
		for i in range(0, N * N, 7):
			s += d.decode_half(i * 8)
			ids += d.decode_half(i * 8 + 4)
	return [s, ids]
func _ready() -> void:
	var g := GalaxyGen.new().generate(11)
	var d := FieldBake.system_data(g)
	var d2 := FieldBake.system_data(g)
	for i in d2.fid.size():
		if d2.fid[i] == 0:
			d2.fid[i] = 1
	var N := 96
	var fb := FieldBake.new()
	add_child(fb)
	fb.setup(N)
	await get_tree().process_frame
	await get_tree().process_frame
	await fb.bake(d)
	print("bake d  ", _sum(fb, N))
	await fb.bake(d2)
	print("bake d2 ", _sum(fb, N))
	await fb.bake(d)
	print("bake d  ", _sum(fb, N))
	# time with N full-frame gpu: how long does one draw take if forced to wait?
	var t0 := Time.get_ticks_usec()
	for k in 20:
		fb._vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		fb._vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		RenderingServer.force_draw(false, 0.0)
		var im := fb._vp.get_texture().get_image()
	print("20x draw+readback ms each ", (Time.get_ticks_usec() - t0) / 20000.0)
	get_tree().quit()
