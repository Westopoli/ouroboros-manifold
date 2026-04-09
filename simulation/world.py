# Input:  template name string, optional int seed
# Output: World object with .regions dict, .adjacency dict, .get_neighbors(region_id)

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


def generate(template: str = "isolated_start", seed: int | None = None) -> World:
    rng = random.Random(seed)

    if template == "isolated_start":
        return _isolated_start(rng)
    elif template == "s1_isolated":
        return _s1_isolated_start(rng)
    elif template == "twin_colony":
        return _twin_colony(rng)
    elif template == "archipelago":
        return _archipelago(rng)
    elif template == "contested_border":
        return _contested_border(rng)
    elif template == "four_way":
        return _four_way(rng)
    elif template == "full_game_50":
        return _full_game_50(rng)
    else:
        raise ValueError(f"Unknown world template: {template}")


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



def _isolated_start(rng: random.Random) -> World:
    # ── Player civilization (faction_id="player") ────────────────────────────
    home = _make_region("region_home", rng.choice(theme.REGION_NAMES["home"]), "home", rng,
                        faction_id="player")

    f_names = rng.sample(theme.REGION_NAMES["frontier"], 2)
    f0 = _make_region("region_f0", f_names[0], "frontier", rng, faction_id="player")
    f1 = _make_region("region_f1", f_names[1], "frontier", rng, faction_id="player")

    # ── Neutral buffer (empty regions, no owner) ─────────────────────────────
    empty_count = rng.randint(*config.ISOLATED_START_EMPTY_REGION_COUNT)
    empty_regions = {}
    for i in range(empty_count):
        rid  = f"region_e{i}"
        name = rng.choice(theme.REGION_NAMES["empty"]).replace("{n}", str(i + 1))
        empty_regions[rid] = Region(rid, name, "empty")

    empty_ids = list(empty_regions.keys())

    # ── Conqueror faction (faction_id="conqueror") ───────────────────────────
    c_names = rng.sample(theme.FACTION_NAMES["conqueror"], 2)
    cf0 = _make_region("region_cf0", c_names[0], "frontier", rng, faction_id="conqueror")
    cf1 = _make_region("region_cf1", c_names[1], "frontier", rng, faction_id="conqueror")

    regions = {"region_home": home, "region_f0": f0, "region_f1": f1}
    regions.update(empty_regions)
    regions["region_cf0"] = cf0
    regions["region_cf1"] = cf1

    # ── Topology ──────────────────────────────────────────────────────────────
    # home ↔ both player frontiers
    # each player frontier ↔ its half of the empty buffer
    # conqueror cf0 ↔ last empty in f0's bucket; cf1 ↔ last empty in f1's bucket
    mid = len(empty_ids) // 2
    f0_empties = empty_ids[:mid] if mid > 0 else []
    f1_empties = empty_ids[mid:] if empty_ids[mid:] else []

    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    link("region_home", "region_f0")
    link("region_home", "region_f1")
    for eid in f0_empties:
        link("region_f0", eid)
    for eid in f1_empties:
        link("region_f1", eid)

    # Conqueror regions sit beyond the far edge of the empty buffer
    far_e0 = f0_empties[-1] if f0_empties else "region_f0"
    far_e1 = f1_empties[-1] if f1_empties else "region_f1"
    link("region_cf0", far_e0)
    link("region_cf1", far_e1)

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _s1_isolated_start(rng: random.Random) -> World:
    s1_ranges = {
        "home": {
            "military":   config.S1_HOME_MILITARY_RANGE,
            "economy":    config.S1_HOME_ECONOMY_RANGE,
            "tension":    config.S1_HOME_TENSION_RANGE,
            "population": config.S1_HOME_POPULATION_RANGE,
        },
        "frontier": {
            "military":   config.S1_FRONTIER_MILITARY_RANGE,
            "economy":    config.S1_FRONTIER_ECONOMY_RANGE,
            "tension":    config.S1_FRONTIER_TENSION_RANGE,
            "population": config.S1_FRONTIER_POPULATION_RANGE,
        },
    }

    def make(rid, name, tier, faction_id="player"):
        ranges = s1_ranges[tier]
        fields = {f: rng.uniform(*r) for f, r in ranges.items()}
        r = Region(rid, name, tier, fields, faction_id=faction_id)
        r.econ_phase_offset = rng.uniform(0, 2 * math.pi)
        r.tension_phase_offset = rng.uniform(0, 2 * math.pi)
        return r

    home = make("home_1", rng.choice(theme.REGION_NAMES["home"]), "home")
    f_names = rng.sample(theme.REGION_NAMES["frontier"], 2)
    f1 = make("frontier_1", f_names[0], "frontier")
    f2 = make("frontier_2", f_names[1], "frontier")

    empty_count = rng.randint(*config.S1_EMPTY_REGION_COUNT)
    empties = []
    for i in range(empty_count):
        name = rng.choice(theme.REGION_NAMES["empty"]).replace("{n}", str(i + 1))
        empties.append(Region(f"empty_{i + 1}", name, "empty"))

    all_regions = [home, f1, f2] + empties
    regions = {r.id: r for r in all_regions}
    adjacency = {r.id: [] for r in all_regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    link("home_1", "frontier_1")
    link("home_1", "frontier_2")

    # Split empties between the two frontiers
    empty_ids = [e.id for e in empties]
    mid = len(empty_ids) // 2
    f1_empties = empty_ids[:max(1, mid)]
    f2_empties = empty_ids[max(1, mid):]

    for eid in f1_empties:
        link("frontier_1", eid)
    for eid in f2_empties:
        link("frontier_2", eid)

    # Expansion corridors: connect adjacent empties within each frontier's set
    for group in (f1_empties, f2_empties):
        for i in range(len(group) - 1):
            link(group[i], group[i + 1])

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _twin_colony(rng: random.Random) -> World:
    names = rng.sample(theme.REGION_NAMES["home"], 2)
    home_a = _make_region("region_home_a", names[0], "home", rng)
    home_b = _make_region("region_home_b", names[1], "home", rng)

    f_names = rng.sample(theme.REGION_NAMES["frontier"], 4)
    fa0 = _make_region("region_fa0", f_names[0], "frontier", rng)
    fa1 = _make_region("region_fa1", f_names[1], "frontier", rng)
    fb0 = _make_region("region_fb0", f_names[2], "frontier", rng)
    fb1 = _make_region("region_fb1", f_names[3], "frontier", rng)

    regions = {
        "region_home_a": home_a, "region_home_b": home_b,
        "region_fa0": fa0, "region_fa1": fa1,
        "region_fb0": fb0, "region_fb1": fb1,
    }
    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    link("region_home_a", "region_fa0")
    link("region_home_a", "region_fa1")
    link("region_home_b", "region_fb0")
    link("region_home_b", "region_fb1")
    # Shared frontier connecting the two cores
    link("region_fa1", "region_fb0")

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _contested_border(rng: random.Random) -> World:
    p_home = _make_region("region_p_home", rng.choice(theme.REGION_NAMES["home"]),
                           "home", rng, faction_id="player")

    f_names = rng.sample(theme.REGION_NAMES["frontier"], 5)
    p_f0   = _make_region("region_p_f0",   f_names[0], "frontier", rng, faction_id="player")
    p_f1   = _make_region("region_p_f1",   f_names[1], "frontier", rng, faction_id="player")
    c_f0   = _make_region("region_c_f0",   f_names[2], "frontier", rng, faction_id="conqueror")
    c_f1   = _make_region("region_c_f1",   f_names[3], "frontier", rng, faction_id="conqueror")
    c_home = _make_region("region_c_home", f_names[4], "frontier", rng, faction_id="conqueror")

    e0_name = rng.choice(theme.REGION_NAMES["empty"]).replace("{n}", "1")
    e1_name = rng.choice(theme.REGION_NAMES["empty"]).replace("{n}", "2")
    e0 = Region("region_e0", e0_name, "empty")
    e1 = Region("region_e1", e1_name, "empty")

    regions = {
        "region_p_home": p_home,
        "region_p_f0":   p_f0,
        "region_p_f1":   p_f1,
        "region_c_f0":   c_f0,
        "region_c_f1":   c_f1,
        "region_c_home": c_home,
        "region_e0":     e0,
        "region_e1":     e1,
    }
    adjacency  = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    link("region_p_home", "region_p_f0")
    link("region_p_home", "region_p_f1")
    link("region_p_f0",   "region_c_f0")   # PRIMARY CONTESTED BORDER
    link("region_p_f1",   "region_c_f1")   # SECONDARY CONTESTED BORDER
    link("region_c_f0",   "region_c_home")
    link("region_c_f1",   "region_c_home")
    link("region_p_f1",   "region_e0")
    link("region_c_f1",   "region_e1")

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _four_way(rng: random.Random) -> World:
    p_home  = _make_region("region_p_home",  rng.choice(theme.REGION_NAMES["home"]),
                            "home", rng, faction_id="player")

    f_names = rng.sample(theme.REGION_NAMES["frontier"], 6)
    p_f0   = _make_region("region_p_f0",   f_names[0], "frontier", rng, faction_id="player")
    c_home = _make_region("region_c_home", f_names[1], "frontier", rng, faction_id="conqueror")
    c_f0   = _make_region("region_c_f0",   f_names[2], "frontier", rng, faction_id="conqueror")
    f_home = _make_region("region_f_home", f_names[3], "frontier", rng, faction_id="fortifier")
    f_f0   = _make_region("region_f_f0",   f_names[4], "frontier", rng, faction_id="fortifier")
    o_home = _make_region("region_o_home", f_names[5], "frontier", rng, faction_id="opportunist")
    o_f0   = _make_region("region_o_f0",   "Wayward Post", "frontier", rng, faction_id="opportunist")

    e_pool = theme.REGION_NAMES["empty"]
    e0  = Region("region_e0",  rng.choice(e_pool).replace("{n}", "1"), "empty")
    e1  = Region("region_e1",  rng.choice(e_pool).replace("{n}", "2"), "empty")
    pe0 = Region("region_pe0", rng.choice(e_pool).replace("{n}", "3"), "empty")
    ce0 = Region("region_ce0", rng.choice(e_pool).replace("{n}", "4"), "empty")
    fe0 = Region("region_fe0", rng.choice(e_pool).replace("{n}", "5"), "empty")
    oe0 = Region("region_oe0", rng.choice(e_pool).replace("{n}", "6"), "empty")

    regions = {
        "region_p_home":  p_home,
        "region_p_f0":    p_f0,
        "region_c_home":  c_home,
        "region_c_f0":    c_f0,
        "region_f_home":  f_home,
        "region_f_f0":    f_f0,
        "region_o_home":  o_home,
        "region_o_f0":    o_f0,
        "region_e0":      e0,
        "region_e1":      e1,
        "region_pe0":     pe0,
        "region_ce0":     ce0,
        "region_fe0":     fe0,
        "region_oe0":     oe0,
    }
    adjacency  = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    link("region_p_home", "region_p_f0")
    link("region_c_home", "region_c_f0")
    link("region_f_home", "region_f_f0")
    link("region_o_home", "region_o_f0")

    link("region_p_f0", "region_c_f0")   # player ↔ conqueror
    link("region_p_f0", "region_f_f0")   # player ↔ fortifier
    link("region_c_f0", "region_o_f0")   # conqueror ↔ opportunist
    link("region_f_f0", "region_o_f0")   # fortifier ↔ opportunist

    link("region_p_f0", "region_e0")
    link("region_f_f0", "region_e0")
    link("region_c_f0", "region_e1")
    link("region_o_f0", "region_e1")

    link("region_p_f0", "region_pe0")   # player exclusive empty
    link("region_c_f0", "region_ce0")   # conqueror exclusive empty
    link("region_f_f0", "region_fe0")   # fortifier exclusive empty
    link("region_o_f0", "region_oe0")   # opportunist exclusive empty

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _archipelago(rng: random.Random) -> World:
    home = _make_region("region_home", rng.choice(theme.REGION_NAMES["home"]), "home", rng)

    f_names = rng.sample(theme.REGION_NAMES["frontier"], 3)
    frontiers = {
        f"region_f{i}": _make_region(f"region_f{i}", f_names[i], "frontier", rng)
        for i in range(3)
    }

    regions = {"region_home": home}
    regions.update(frontiers)
    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    # Home connects to all three frontiers; frontiers are sparse (only f0 ↔ f1)
    for fid in frontiers:
        link("region_home", fid)
    link("region_f0", "region_f1")

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))


def _full_game_50(rng: random.Random) -> World:
    # 50 regions: 8 inhabited (4 factions × 2), 42 empty
    # Layout: 4 corners connected by corridors through a central hub
    # Avg degree ~2.2, center degree 5, min 6 empties between any two factions

    # ── Faction regions (same field ranges as four_way) ─────────────────────
    p_home = _make_region("region_p_home", rng.choice(theme.REGION_NAMES["home"]),
                          "home", rng, faction_id="player")
    f_names = rng.sample(theme.REGION_NAMES["frontier"], 6)
    p_f0   = _make_region("region_p_f0",   f_names[0], "frontier", rng, faction_id="player")
    c_home = _make_region("region_c_home", f_names[1], "frontier", rng, faction_id="conqueror")
    c_f0   = _make_region("region_c_f0",   f_names[2], "frontier", rng, faction_id="conqueror")
    f_home = _make_region("region_f_home", f_names[3], "frontier", rng, faction_id="fortifier")
    f_f0   = _make_region("region_f_f0",   f_names[4], "frontier", rng, faction_id="fortifier")
    o_home = _make_region("region_o_home", f_names[5], "frontier", rng, faction_id="opportunist")
    o_f0   = _make_region("region_o_f0",   "Wayward Post", "frontier", rng, faction_id="opportunist")

    # ── 42 empty regions ────────────────────────────────────────────────────
    e_pool = theme.REGION_NAMES["empty"]
    empties = {}
    for i in range(1, 43):
        rid = f"region_e{i:02d}"
        name = rng.choice(e_pool).replace("{n}", str(i))
        empties[rid] = Region(rid, name, "empty")

    def e(n):
        return f"region_e{n:02d}"

    regions = {
        "region_p_home": p_home, "region_p_f0": p_f0,
        "region_c_home": c_home, "region_c_f0": c_f0,
        "region_f_home": f_home, "region_f_f0": f_f0,
        "region_o_home": o_home, "region_o_f0": o_f0,
    }
    regions.update(empties)

    adjacency = {rid: [] for rid in regions}
    edge_types = {}

    def link(a, b, etype="both"):
        adjacency[a].append(b)
        adjacency[b].append(a)
        edge_types[(a, b)] = etype
        edge_types[(b, a)] = etype

    # ── NW corner (Player) ──────────────────────────────────────────────────
    #   p_home ─ p_f0 ─┬─ e01 ─ e03 ─ e05(spur)
    #                   └─ e02 ─ e04
    link("region_p_home", "region_p_f0")
    link("region_p_f0", e(1))
    link("region_p_f0", e(2))
    link(e(1), e(3))
    link(e(2), e(4))
    link(e(3), e(5))    # spur

    # ── NE corner (Conqueror) ───────────────────────────────────────────────
    #   c_home ─ c_f0 ─┬─ e06 ─ e08 ─ e10(spur)
    #                   └─ e07 ─ e09
    link("region_c_home", "region_c_f0")
    link("region_c_f0", e(6))
    link("region_c_f0", e(7))
    link(e(6), e(8))
    link(e(7), e(9))
    link(e(8), e(10))   # spur

    # ── SW corner (Fortifier) ───────────────────────────────────────────────
    #   f_home ─ f_f0 ─┬─ e11 ─ e13 ─ e15(spur)
    #                   └─ e12 ─ e14
    link("region_f_home", "region_f_f0")
    link("region_f_f0", e(11))
    link("region_f_f0", e(12))
    link(e(11), e(13))
    link(e(12), e(14))
    link(e(13), e(15))  # spur

    # ── SE corner (Opportunist) ─────────────────────────────────────────────
    #   o_home ─ o_f0 ─┬─ e16 ─ e18 ─ e20(spur)
    #                   └─ e17 ─ e19
    link("region_o_home", "region_o_f0")
    link("region_o_f0", e(16))
    link("region_o_f0", e(17))
    link(e(16), e(18))
    link(e(17), e(19))
    link(e(18), e(20))  # spur

    # ── North corridor (NW ↔ NE): e03 ─ e21 ─ e22 ─ e08 ───────────────────
    link(e(3), e(21))
    link(e(21), e(22))
    link(e(22), e(8))
    link(e(21), e(37))  # spur off north corridor

    # ── West corridor (NW ↔ SW): e04 ─ e23 ─ e24 ─ e14 ────────────────────
    link(e(4), e(23))
    link(e(23), e(24))
    link(e(24), e(14))
    link(e(23), e(39))  # spur off west corridor

    # ── East corridor (NE ↔ SE): e09 ─ e25 ─ e26 ─ e18 ────────────────────
    link(e(9), e(25))
    link(e(25), e(26))
    link(e(26), e(18))
    link(e(25), e(40))  # spur off east corridor

    # ── South corridor (SW ↔ SE): e13 ─ e27 ─ e28 ─ e19 ───────────────────
    link(e(13), e(27))
    link(e(27), e(28))
    link(e(28), e(19))
    link(e(27), e(38))  # spur off south corridor

    # ── Center hub (most connected area) ────────────────────────────────────
    # e29 (center-NW) and e30 (center-SE) form the core
    link(e(22), e(29))   # north corridor → center
    link(e(24), e(29))   # west corridor → center
    link(e(26), e(30))   # east corridor → center
    link(e(28), e(30))   # south corridor → center
    link(e(29), e(30))   # center core link
    link(e(22), e(35))   # north inland connector
    link(e(35), e(29))   # inland → center
    link(e(28), e(36))   # south inland connector
    link(e(36), e(30))   # inland → center

    # ── Center branches ─────────────────────────────────────────────────────
    link(e(29), e(31))
    link(e(30), e(32))
    link(e(31), e(32))   # cross-link center branches
    link(e(31), e(33))
    link(e(32), e(34))
    link(e(33), e(41))   # deep center spur
    link(e(34), e(42))   # deep center spur

    _assign_edge_types(regions, edge_types)
    return World(regions, adjacency, edge_types, seed=rng.randint(0, 2**31))
