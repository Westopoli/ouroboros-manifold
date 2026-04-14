import json

TEMPLATE_LAYOUTS = {
    "s1_isolated": {
        "home_1":     [500, 500],
        "frontier_1": [300, 350],
        "frontier_2": [700, 350],
        "empty_1":    [150, 200],
        "empty_2":    [350, 200],
        "empty_3":    [650, 200],
        "empty_4":    [850, 200],
        "empty_5":    [500, 100],
    },
    "contested_border": {
        "region_p_home": [150, 500],
        "region_p_f0":   [350, 350],
        "region_p_f1":   [350, 650],
        "region_c_f0":   [650, 350],
        "region_c_f1":   [650, 650],
        "region_c_home": [850, 500],
        "region_e0":     [250, 800],
        "region_e1":     [750, 800],
    },
    "four_way": {
        "region_p_home": [250, 800],
        "region_p_f0":   [350, 600],
        "region_c_home": [250, 200],
        "region_c_f0":   [350, 400],
        "region_f_home": [750, 800],
        "region_f_f0":   [650, 600],
        "region_o_home": [750, 200],
        "region_o_f0":   [650, 400],
        "region_e0":     [500, 650],
        "region_e1":     [500, 350],
        "region_pe0":    [180, 600],
        "region_ce0":    [180, 400],
        "region_fe0":    [820, 600],
        "region_oe0":    [820, 400],
    },
}


class StrategicLogger:
    def __init__(self, path, scenario_name, world, registry, template=None):
        self._path = path
        self._tick_count = 0
        self._f = open(path, "w")
        layout_map = TEMPLATE_LAYOUTS.get(template, {})

        seen = set()
        adjacency = []
        for a_id, neighbors in world.adjacency.items():
            for b_id in neighbors:
                key = (min(a_id, b_id), max(a_id, b_id))
                if key not in seen:
                    seen.add(key)
                    edge_type = world.edge_types.get((a_id, b_id), "border")
                    adjacency.append([a_id, b_id, edge_type])

        header = {
            "type": "header",
            "version": 1,
            "scenario": scenario_name,
            "factions": {
                fid: {"name": f.name, "color": f.color}
                for fid, f in registry.items()
            },
            "regions": [
                {"id": r.id, "name": r.name, "tier": r.tier, "layout": layout_map.get(r.id)}
                for r in world.regions.values()
            ],
            "adjacency": adjacency,
            "tick_count": None,
        }
        self._f.write(json.dumps(header) + "\n")
        self._all_factions = {
            fid: {"name": f.name, "color": f.color}
            for fid, f in registry.items()
        }

    def log_tick(self, tick, world, registry, events_this_tick, friction):
        self._tick_count += 1
        for fid, f in registry.items():
            if fid not in self._all_factions:
                self._all_factions[fid] = {"name": f.name, "color": f.color}

        regions = {
            rid: {
                "faction_id": r.faction_id,
                "fields": {k: round(v, 2) for k, v in r.fields.items()},
                "composites": dict(r.composites),
            }
            for rid, r in world.regions.items()
        }

        factions = {}
        for fid, f in registry.items():
            owned = [r for r in world.regions.values() if r.faction_id == fid]
            if owned:
                totals = {
                    field: round(sum(r.fields[field] for r in owned), 2)
                    for field in ("military", "economy", "population")
                }
            else:
                totals = {"military": 0.0, "economy": 0.0, "population": 0.0}
            factions[fid] = {
                "region_count": len(owned),
                "tech_level": round(f.tech_level, 4),
                "budget": round(f.budget, 2),
                "totals": totals,
                "stances": dict(f.diplomatic_stance),
            }

        events = [
            {
                "region_id": e.get("region_id"),
                "type": e.get("template_id", e.get("name", "?")),
                "chain_tag": e.get("chain_tag"),
            }
            for e in events_this_tick
        ]

        line = {
            "type": "tick",
            "tick": tick,
            "regions": regions,
            "factions": factions,
            "events": events,
            "friction": friction,
        }
        self._f.write(json.dumps(line) + "\n")

    def close(self, registry=None):
        self._f.flush()
        self._f.close()
        with open(self._path) as f:
            lines = f.readlines()
        header = json.loads(lines[0])
        header["tick_count"] = self._tick_count
        for fid, meta in self._all_factions.items():
            if fid not in header["factions"]:
                header["factions"][fid] = meta
        lines[0] = json.dumps(header) + "\n"
        with open(self._path, "w") as f:
            f.writelines(lines)
