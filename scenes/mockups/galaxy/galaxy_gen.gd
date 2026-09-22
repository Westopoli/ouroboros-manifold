class_name GalaxyGen
extends RefCounted


func generate(p_seed: int) -> Galaxy:
	var g := Galaxy.new()
	g.seed_used = p_seed
	g.systems = [
		{"id": 0, "pos": Vector3.ZERO, "significance": 1.0, "owner": 0, "name": "Stub"},
		{"id": 1, "pos": Vector3(10, 0, 0), "significance": 0.5, "owner": -1, "name": "Stub2"},
		{"id": 2, "pos": Vector3(-10, 0, 0), "significance": 0.5, "owner": -1, "name": "Stub3"},
	]
	g.factions = [{"id": 0, "name": "Stub Faction", "capital": 0, "hue": 0.0}]
	g.edges = []
	return g
