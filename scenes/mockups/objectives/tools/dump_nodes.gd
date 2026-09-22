extends SceneTree

const SEEDS := [11, 12, 13]
const CANVAS := 24000.0
const STABILITY := 60.0
const OUT_DIR := "res://scenes/mockups/objectives/fixtures/"


func _initialize() -> void:
	for s in SEEDS:
		var fm := FieldMap.new()
		fm.generate(s, CANVAS, STABILITY)
		var nodes := []
		for n in fm.nodes:
			nodes.append({"type": n.type, "pos": [n.pos.x, n.pos.y]})
		var data := {"canvas": CANVAS, "seed": s, "nodes": nodes}
		var f := FileAccess.open(OUT_DIR + "nodes_seed%d.json" % s, FileAccess.WRITE)
		f.store_string(JSON.stringify(data, "  "))
		f.close()
		print("wrote nodes_seed%d.json (%d nodes)" % [s, nodes.size()])
	quit(0)
