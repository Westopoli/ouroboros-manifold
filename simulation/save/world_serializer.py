import random

from world import World
from region import Region
from faction import Faction
from chronicle_assembler import ScrollEntry

SAVE_VERSION = 1


class SaveVersionError(ValueError):
    pass


def serialize_world(world: World, factions: dict, chronicle_entries: list,
                    tick: int, era_id: str,
                    stances: dict | None = None) -> dict:
    return {
        "save_version": SAVE_VERSION,
        "tick": tick,
        "era_id": era_id,
        "world": _world_to_dict(world),
        "factions": [_faction_to_dict(f) for f in factions.values()],
        "chronicle_entries": [_entry_to_dict(e) for e in chronicle_entries],
        "stances": _stances_to_list(stances or {}),
    }


def deserialize_world(payload: dict) -> tuple:
    ver = payload.get("save_version")
    if ver != SAVE_VERSION:
        raise SaveVersionError(
            f"unknown save_version {ver!r}; expected {SAVE_VERSION}")
    world = _world_from_dict(payload["world"])
    factions = {
        f["id"]: _faction_from_dict(f)
        for f in payload.get("factions", [])
    }
    chronicle_entries = [_entry_from_dict(e)
                         for e in payload.get("chronicle_entries", [])]
    tick = int(payload.get("tick", 0))
    era_id = str(payload.get("era_id", ""))
    stances = _stances_from_list(payload.get("stances", []))
    return world, factions, chronicle_entries, tick, era_id, stances


# ── World ─────────────────────────────────────────────────────────────────────

def _world_to_dict(world: World) -> dict:
    edges = [[a, b, etype] for (a, b), etype in world.edge_types.items()]
    return {
        "regions": [_region_to_dict(r) for r in world.regions.values()],
        "adjacency": {rid: list(nbrs) for rid, nbrs in world.adjacency.items()},
        "edge_types": edges,
        "rng_state": _encode_rng_state(world.rng.getstate()),
    }


def _world_from_dict(data: dict) -> World:
    regions = {r["id"]: _region_from_dict(r) for r in data.get("regions", [])}
    adjacency = {rid: list(nbrs) for rid, nbrs in data.get("adjacency", {}).items()}
    edge_types = {(a, b): etype for a, b, etype in data.get("edge_types", [])}
    world = World(regions=regions, adjacency=adjacency, edge_types=edge_types)
    rng_state = data.get("rng_state")
    if rng_state is not None:
        world.rng.setstate(_decode_rng_state(rng_state))
    return world


# ── Region ────────────────────────────────────────────────────────────────────

def _region_to_dict(r: Region) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "tier": r.tier,
        "faction_id": r.faction_id,
        "previous_faction_id": r.previous_faction_id,
        "fields": dict(r.fields),
        "econ_phase_offset": r.econ_phase_offset,
        "tension_phase_offset": r.tension_phase_offset,
        "held_since_tick": r.held_since_tick,
    }


def _region_from_dict(d: dict) -> Region:
    fields = d.get("fields")
    region = Region(
        d["id"], d["name"], d["tier"],
        fields=fields if d["tier"] != "empty" else None,
        faction_id=d.get("faction_id"),
    )
    region.econ_phase_offset = float(d.get("econ_phase_offset", 0.0))
    region.tension_phase_offset = float(d.get("tension_phase_offset", 0.0))
    region.held_since_tick = d.get("held_since_tick")
    region.previous_faction_id = d.get("previous_faction_id")
    if region.tier != "empty":
        region.recompute_composites()
    return region


# ── Faction ───────────────────────────────────────────────────────────────────

def _faction_to_dict(f: Faction) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "archetype": f.archetype,
        "color": f.color,
        "budget": f.budget,
        "budget_growth_rate": f.budget_growth_rate,
        "modifiers": dict(f.modifiers),
        "diplomatic_stance": dict(f.diplomatic_stance),
        "attack_confidence": f.attack_confidence,
        "tech_level": f.tech_level,
    }


def _faction_from_dict(d: dict) -> Faction:
    f = Faction(
        d["id"], d["name"], d["archetype"],
        budget=d.get("budget", 0.0),
        budget_growth_rate=d.get("budget_growth_rate"),
        modifiers=dict(d.get("modifiers", {})),
        diplomatic_stance=dict(d.get("diplomatic_stance", {})),
        color=d.get("color"),
        rng=random.Random(0),
    )
    # __init__ rolls these from rng; overwrite with persisted values.
    f.attack_confidence = float(d["attack_confidence"])
    f.tech_level = float(d["tech_level"])
    return f


# ── ScrollEntry ───────────────────────────────────────────────────────────────

def _entry_to_dict(e: ScrollEntry) -> dict:
    return {
        "base_text": e.base_text,
        "expanded_text": e.expanded_text,
        "cluster_type": e.cluster_type,
        "category": e.category,
        "fragment_ids": list(e.fragment_ids),
        "resolved_slots": dict(e.resolved_slots),
        "source_events": list(e.source_events),
        "region_id": e.region_id,
        "tick_range": list(e.tick_range),
        "mentions": list(e.mentions),
        "expanded_mentions": list(e.expanded_mentions),
    }


def _entry_from_dict(d: dict) -> ScrollEntry:
    tick_range = d.get("tick_range", [0, 0])
    return ScrollEntry(
        base_text=d.get("base_text", ""),
        expanded_text=d.get("expanded_text", ""),
        cluster_type=d.get("cluster_type", ""),
        category=d.get("category", ""),
        fragment_ids=list(d.get("fragment_ids", [])),
        resolved_slots=dict(d.get("resolved_slots", {})),
        source_events=list(d.get("source_events", [])),
        region_id=d.get("region_id", ""),
        tick_range=tuple(tick_range),
        mentions=list(d.get("mentions", [])),
        expanded_mentions=list(d.get("expanded_mentions", [])),
    )


# ── Stances ───────────────────────────────────────────────────────────────────

# Canonical source: diplomacy.py stances dict, pair-keyed by (fid_a, fid_b)
# with three fields per pair: stance, non_aggression_ticks, cooperative_since_tick.
# Faction.diplomatic_stance is a derived mirror — restore stances first, then
# diplomacy.sync_to_factions(stances, registry) repopulates the mirror.

def _stances_to_list(stances: dict) -> list:
    out = []
    for (a, b), entry in stances.items():
        out.append([
            a, b,
            entry.get("stance", "neutral"),
            int(entry.get("non_aggression_ticks", 0)),
            entry.get("cooperative_since_tick"),
        ])
    return out


def _stances_from_list(data: list) -> dict:
    result = {}
    for row in data:
        a, b, stance, nat, csince = row
        result[(a, b)] = {
            "stance": stance,
            "non_aggression_ticks": int(nat),
            "cooperative_since_tick": csince,
        }
    return result


# ── RNG state ─────────────────────────────────────────────────────────────────

def _encode_rng_state(state: tuple) -> list:
    # random.Random.getstate() = (version_int, tuple_of_625_ints, gauss_next | None)
    version, internal, gauss = state
    return [int(version), list(int(x) for x in internal), gauss]


def _decode_rng_state(encoded: list) -> tuple:
    version, internal, gauss = encoded
    return (int(version), tuple(int(x) for x in internal), gauss)
