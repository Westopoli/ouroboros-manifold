import math
import random
import config
import theme_scifi as theme
from region import Region


class World:
    def __init__(self, regions: dict, adjacency: dict,
                 edge_types: dict | None = None,
                 seed: int | None = None) -> None:
        self.regions = regions      # {region_id: Region}
        self.adjacency = adjacency  # {region_id: [neighbor_id, ...]}
        self.edge_types = edge_types or {}  # {(a, b): "both"|"border"|"trade"}
        self.rng = random.Random(seed)

    def get_neighbors(self, region_id: str, edge_type: str | None = None) -> list:
        neighbors = self.adjacency.get(region_id, [])
        if edge_type is None or not self.edge_types:
            return neighbors
        return [n for n in neighbors
                if self.edge_types.get((region_id, n)) in (edge_type, "both")]

    def allied_inhabited_neighbors(self, region_id: str, edge_type: str | None = None) -> list:
        region = self.regions[region_id]
        if region.faction_id is None:
            return []
        return [self.regions[nid] for nid in self.get_neighbors(region_id, edge_type=edge_type)
                if self.regions[nid].tier != "empty"
                and self.regions[nid].faction_id == region.faction_id]

    def set_edge_type(self, a: str, b: str, edge_type: str) -> None:
        self.edge_types[(a, b)] = edge_type
        self.edge_types[(b, a)] = edge_type

    def update_faction_pair_edges(self, fid_a: str, fid_b: str, edge_type: str) -> int:
        count = 0
        for region in self.regions.values():
            if region.faction_id != fid_a:
                continue
            for nid in self.adjacency.get(region.id, []):
                nr = self.regions.get(nid)
                if nr and nr.faction_id == fid_b:
                    self.set_edge_type(region.id, nid, edge_type)
                    count += 1
        return count

    def inhabited_regions(self) -> list:
        return [r for r in self.regions.values() if r.tier != "empty"]

    # ── I2: Faction-aware queries ─────────────────────────────────────────────

    def regions_by_faction(self, faction_id: str) -> list:
        return [r for r in self.regions.values() if r.faction_id == faction_id]

    def bordering_factions(self, faction_id: str) -> set:
        owned_ids = {r.id for r in self.regions_by_faction(faction_id)}
        bordering = set()
        for rid in owned_ids:
            for neighbor_id in self.get_neighbors(rid):
                nf = self.regions[neighbor_id].faction_id
                if nf is not None and nf != faction_id:
                    bordering.add(nf)
        return bordering


def _assign_edge_types(regions: dict, edge_types: dict) -> None:
    for (a, b) in edge_types:
        ra, rb = regions.get(a), regions.get(b)
        if (ra and rb and ra.faction_id and rb.faction_id
                and ra.faction_id == rb.faction_id):
            edge_types[(a, b)] = "both"
        else:
            edge_types[(a, b)] = "border"


def _make_region(region_id: str, name: str, tier: str, rng: random.Random,
                 faction_id: str | None = None) -> Region:
    if tier == "home":
        pop_range = config.HOME_POPULATION_RANGE
    elif tier == "frontier":
        pop_range = config.FRONTIER_POPULATION_RANGE
    else:
        return Region(region_id, name, tier, None, faction_id=faction_id)

    jitter = config.STARTING_FIELD_JITTER
    population = rng.uniform(*pop_range)
    economy    = max(0.0, min(100.0, population * config.STARTING_ECO_RATIO     + rng.uniform(-jitter, jitter)))
    military   = max(0.0, min(100.0, population * config.STARTING_MIL_RATIO     + rng.uniform(-jitter, jitter)))
    tension    = max(0.0, min(100.0, population * config.STARTING_TENSION_RATIO  + rng.uniform(-jitter, jitter)))
    fields = {"military": military, "economy": economy, "tension": tension, "population": population}
    region = Region(region_id, name, tier, fields, faction_id=faction_id)
    region.econ_phase_offset = rng.uniform(0, 2 * math.pi)
    region.tension_phase_offset = rng.uniform(0, 2 * math.pi)
    return region


def generate_random(seed: int | None = None) -> World:
    rng = random.Random(seed)
    n_regions = rng.randint(*config.WORLD_REGION_COUNT_RANGE)
    min_sep = config.WORLD_MIN_FACTION_SEPARATION

    faction_ids = ["player", "conqueror", "fortifier", "opportunist"]
    faction_archetypes = {
        "player": "home",
        "conqueror": "frontier",
        "fortifier": "frontier",
        "opportunist": "frontier",
    }

    regions = {}
    adjacency = {}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    # Create faction regions: 1 home + 1 frontier per faction = 8 total
    faction_regions = {}
    for fid in faction_ids:
        home_name = rng.choice(theme.REGION_NAMES["home"])
        home_id = f"region_{fid}_home"
        home = _make_region(home_id, home_name, "home", rng, faction_id=fid)
        regions[home_id] = home
        adjacency[home_id] = []

        f_name = rng.choice(theme.REGION_NAMES["frontier"])
        f_id = f"region_{fid}_f0"
        frontier = _make_region(f_id, f_name, "frontier", rng, faction_id=fid)
        regions[f_id] = frontier
        adjacency[f_id] = []

        link(home_id, f_id)
        faction_regions[fid] = (home_id, f_id)

    # Create empty regions
    n_empty = n_regions - len(regions)
    e_pool = theme.REGION_NAMES["empty"]
    empty_ids = []
    for i in range(n_empty):
        rid = f"region_e{i:03d}"
        name = rng.choice(e_pool).replace("{n}", str(i + 1))
        regions[rid] = Region(rid, name, "empty")
        adjacency[rid] = []
        empty_ids.append(rid)

    # Build connected graph with faction separation
    # Strategy: build corridors outward from each faction frontier through empty regions,
    # then connect the remaining empties into a spanning tree, then add extra edges.

    rng.shuffle(empty_ids)

    # Assign each faction a corridor of min_sep empties extending from its frontier
    corridor_ends = {}
    assigned = set()
    ei = 0
    for fid in faction_ids:
        _, frontier_id = faction_regions[fid]
        corridor_len = min(min_sep, len(empty_ids) - ei)
        prev = frontier_id
        for j in range(corridor_len):
            eid = empty_ids[ei]
            link(prev, eid)
            prev = eid
            assigned.add(eid)
            ei += 1
        corridor_ends[fid] = prev

    # Connect the 4 faction components via their corridor ends
    component_nodes = list(corridor_ends.values())
    for i in range(1, len(component_nodes)):
        link(component_nodes[i], component_nodes[i - 1])

    # Remaining empties: attach to the graph via spanning tree
    # Start connected set from the first faction and grow outward
    first_home = faction_regions[faction_ids[0]][0]
    connected = set()
    queue = [first_home]
    while queue:
        rid = queue.pop()
        if rid in connected:
            continue
        connected.add(rid)
        queue.extend(adjacency[rid])
    connected_list = list(connected)

    unassigned = [eid for eid in empty_ids if eid not in assigned]
    rng.shuffle(unassigned)

    for eid in unassigned:
        target = rng.choice(connected_list)
        attempts = 0
        while target.endswith("_home") and attempts < 20:
            target = rng.choice(connected_list)
            attempts += 1
        link(eid, target)
        connected.add(eid)
        connected_list.append(eid)

    # Add extra edges for loops/alternate paths
    all_ids = list(regions.keys())
    faction_home_ids = {f"region_{fid}_home" for fid in faction_ids}
    n_extra = max(1, int(len(all_ids) * config.WORLD_EXTRA_EDGE_RATIO))
    added = 0
    attempts = 0
    while added < n_extra and attempts < n_extra * 10:
        attempts += 1
        a = rng.choice(all_ids)
        b = rng.choice(all_ids)
        if a == b:
            continue
        if b in adjacency[a]:
            continue
        # Don't create direct links between different factions' homes
        if a in faction_home_ids and b in faction_home_ids:
            continue
        link(a, b)
        added += 1

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))
