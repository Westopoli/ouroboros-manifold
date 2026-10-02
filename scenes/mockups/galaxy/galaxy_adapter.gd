class_name GalaxyAdapter
extends RefCounted

# Thin adapter: galaxy_gen.gd's Galaxy (systems/factions/edges) into the
# regions/connections/territories shape legacy_world_view_data.gd carries,
# so legacy_constellation_renderer.gd (copied from scenes/shared/world_view/renderers/)
# changes as little as possible and shell_renderer.gd (a rewrite) reads the same shape.
# See also: scenes/mockups/galaxy/galaxy_view.gd — owner_color()/TRADE_DIM,
# the single source of truth for point/filament/shell colour this mirrors.


static func _faction_key(owner_id: int) -> String:
	return "neutral" if owner_id == -1 else "faction_%d" % owner_id


static func populate(wv: Node, galaxy: Galaxy, owner_color_fn: Callable, region_size_fn: Callable, trade_color: Color, skip_connections: bool) -> void:
	wv.clear_all()
	for sys in galaxy.systems:
		var color: Color = owner_color_fn.call(sys.owner, galaxy)
		wv.add_region(str(sys.id), sys.pos, region_size_fn.call(sys.significance), color, _faction_key(sys.owner))
		if sys.owner != -1:
			wv.set_territory(str(sys.id), sys.pos, sys.significance, color)
	if skip_connections:
		return
	for e in galaxy.edges:
		var is_border: bool = e.kind == "border"
		var color: Color = owner_color_fn.call(galaxy.systems[e.a].owner, galaxy) if is_border else trade_color
		wv.add_connection(str(e.a), str(e.b), e.kind, color)


static func sync_system(wv: Node, galaxy: Galaxy, system_id: int, owner_color_fn: Callable, region_size_fn: Callable, trade_color: Color) -> void:
	var sys: Dictionary = galaxy.systems[system_id]
	var color: Color = owner_color_fn.call(sys.owner, galaxy)
	wv.add_region(str(system_id), sys.pos, region_size_fn.call(sys.significance), color, _faction_key(sys.owner))
	if sys.owner == -1:
		wv.remove_territory(str(system_id))
	else:
		wv.set_territory(str(system_id), sys.pos, sys.significance, color)
	for e in galaxy.edges:
		if e.a != system_id and e.b != system_id:
			continue
		var oa: int = galaxy.systems[e.a].owner
		var ob: int = galaxy.systems[e.b].owner
		var is_border: bool = oa == ob and oa != -1
		e.kind = "border" if is_border else "trade"
		var edge_color: Color = owner_color_fn.call(oa, galaxy) if is_border else trade_color
		wv.add_connection(str(e.a), str(e.b), e.kind, edge_color)
