import json

class StrategicLogger:
    def __init__(self, path, scenario_name, world, registry, template=None):
        self._path = path
        self._tick_count = 0
        self._f = open(path, "w")
        layout_map = {}

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
