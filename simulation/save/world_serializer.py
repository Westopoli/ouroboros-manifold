import random

from world import World
from region import Region
from faction import Faction
from chronicle_assembler import ScrollEntry
from naming_system import NamingSystem
from coherence_ledger import CoherenceLedger, CharacterRecord
from generational import GenerationalState
from events import PendingQueue

SAVE_VERSION = 3


class SaveVersionError(ValueError):
    pass


def serialize_world(world: World, factions: dict, chronicle_entries: list,
                    tick: int, era_id: str,
                    stances: dict | None = None,
                    naming_system=None, ledger=None,
                    gen_state=None, pending_queue=None,
                    player_lineage_id=None,
                    trigger_state: dict | None = None,
                    noise_offsets: dict | None = None) -> dict:
    return {
        "save_version": SAVE_VERSION,
        "tick": tick,
        "era_id": era_id,
        "world": _world_to_dict(world),
        "factions": [_faction_to_dict(f) for f in factions.values()],
        "chronicle_entries": [_entry_to_dict(e) for e in chronicle_entries],
        "stances": _stances_to_list(stances or {}),
        "naming_system": _naming_to_dict(naming_system) if naming_system is not None else None,
        "ledger": _ledger_to_dict(ledger) if ledger is not None else None,
        "gen_state": _gen_state_to_dict(gen_state) if gen_state is not None else None,
        "pending_queue": _pending_queue_to_dict(pending_queue) if pending_queue is not None else None,
        "player_lineage_id": player_lineage_id,
        "trigger_state": _trigger_state_to_dict(trigger_state or {}),
        "noise_offsets": _noise_offsets_to_dict(noise_offsets or {}),
    }


def deserialize_world(payload: dict) -> dict:
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

    ns_data = payload.get("naming_system")
    ns = _naming_from_dict(ns_data) if ns_data is not None else NamingSystem()

    ledger_data = payload.get("ledger")
    ledger = _ledger_from_dict(ledger_data, ns) if ledger_data is not None else CoherenceLedger(ns)

    gs_data = payload.get("gen_state")
    gen_state = _gen_state_from_dict(gs_data) if gs_data is not None else None

    pq_data = payload.get("pending_queue")
    pending_queue = _pending_queue_from_dict(pq_data) if pq_data is not None else PendingQueue()

    player_lineage_id = payload.get("player_lineage_id")

    trigger_state = _trigger_state_from_dict(payload.get("trigger_state", {}) or {})
    noise_offsets = _noise_offsets_from_dict(payload.get("noise_offsets", {}) or {})

    return {
        "world": world,
        "factions": factions,
        "chronicle_entries": chronicle_entries,
        "tick": tick,
        "era_id": era_id,
        "stances": stances,
        "naming_system": ns,
        "ledger": ledger,
        "gen_state": gen_state,
        "pending_queue": pending_queue,
        "player_lineage_id": player_lineage_id,
        "trigger_state": trigger_state,
        "noise_offsets": noise_offsets,
    }


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


# ── NamingSystem ──────────────────────────────────────────────────────────────

def _naming_to_dict(ns: NamingSystem) -> dict:
    # Tuple keys (faction_id, category) → list of 3-element rows for JSON safety
    pools = [[fid, cat, list(names)] for (fid, cat), names in ns._pools.items()]
    return {
        "pools": pools,
        "in_use": dict(ns._in_use),
        "cooldowns": dict(ns._cooldowns),
        "subsets": {fid: dict(subset) for fid, subset in ns._subsets.items()},
        "schism_parents": dict(ns._schism_parents),
    }


def _naming_from_dict(d: dict) -> NamingSystem:
    ns = NamingSystem()
    for fid, cat, names in d.get("pools", []):
        ns._pools[(fid, cat)] = list(names)
    ns._in_use = dict(d.get("in_use", {}))
    ns._cooldowns = {name: int(tick) for name, tick in d.get("cooldowns", {}).items()}
    ns._subsets = {fid: dict(subset) for fid, subset in d.get("subsets", {}).items()}
    ns._schism_parents = dict(d.get("schism_parents", {}))
    return ns


# ── CoherenceLedger ───────────────────────────────────────────────────────────

def _char_to_dict(rec: CharacterRecord) -> dict:
    return {
        "id": rec.id,
        "name": rec.name,
        "faction_id": rec.faction_id,
        "region_id": rec.region_id,
        "rank": rec.rank,
        "born_tick": rec.born_tick,
        "death_tick": rec.death_tick,
        "lifespan_ticks": rec.lifespan_ticks,
        "lineage_id": rec.lineage_id,
        "status": rec.status,
        "event_history": list(rec.event_history),
        "parent_id": rec.parent_id,
        "children_ids": list(rec.children_ids),
        "generation": rec.generation,
        "rival_of": list(rec.rival_of),
    }


def _char_from_dict(d: dict) -> CharacterRecord:
    rec = CharacterRecord(
        d["id"], d["name"], d["faction_id"], d["region_id"], d["rank"],
        born_tick=d["born_tick"], lifespan_ticks=d["lifespan_ticks"],
        lineage_id=d.get("lineage_id"), parent_id=d.get("parent_id"),
        generation=d.get("generation", 0),
    )
    rec.death_tick = d.get("death_tick")
    rec.status = d.get("status", "active")
    rec.event_history = list(d.get("event_history", []))
    rec.children_ids = list(d.get("children_ids", []))
    rec.rival_of = list(d.get("rival_of", []))
    return rec


def _ledger_to_dict(ledger: CoherenceLedger) -> dict:
    return {
        "characters": [_char_to_dict(c) for c in ledger._characters.values()],
        "lineages": {lid: dict(lin) for lid, lin in ledger._lineages.items()},
        "next_char_id": ledger._next_char_id,
        "next_lineage_id": ledger._next_lineage_id,
        "archetype_history": {lid: dict(h) for lid, h in ledger._archetype_history.items()},
        "chapter_counts": dict(ledger._chapter_counts),
        "main_character_ids": list(ledger._main_character_ids),
    }


def _ledger_from_dict(d: dict, naming_system: NamingSystem) -> CoherenceLedger:
    ledger = CoherenceLedger(naming_system)
    ledger._characters = {c["id"]: _char_from_dict(c) for c in d.get("characters", [])}
    ledger._lineages = {
        lid: {"root_id": lin["root_id"], "member_ids": list(lin["member_ids"])}
        for lid, lin in d.get("lineages", {}).items()
    }
    ledger._next_char_id = int(d.get("next_char_id", 0))
    ledger._next_lineage_id = int(d.get("next_lineage_id", 0))
    ledger._archetype_history = {lid: dict(h) for lid, h in d.get("archetype_history", {}).items()}
    ledger._chapter_counts = dict(d.get("chapter_counts", {}))
    ledger._main_character_ids = set(d.get("main_character_ids", []))
    return ledger


# ── GenerationalState ─────────────────────────────────────────────────────────

def _gen_state_to_dict(gs: GenerationalState) -> dict:
    return {
        "player_faction_id": gs.player_faction_id,
        "chapters": [dict(ch) for ch in gs.chapters],
        "current_chapter_index": gs.current_chapter_index,
    }


def _gen_state_from_dict(d: dict) -> GenerationalState:
    fid = d.get("player_faction_id", "player")
    # __init__ auto-creates a default chapter; we overwrite everything.
    gs = GenerationalState(fid, start_tick=0)
    gs.chapters = [dict(ch) for ch in d.get("chapters", [])]
    gs.current_chapter_index = int(d.get("current_chapter_index", 0))
    gs.player_faction_id = fid
    return gs


# ── PendingQueue ──────────────────────────────────────────────────────────────

def _pending_queue_to_dict(pq: PendingQueue) -> dict:
    return {"queue": [dict(e) for e in pq._queue]}


def _pending_queue_from_dict(d: dict) -> PendingQueue:
    pq = PendingQueue()
    for entry in d.get("queue", []):
        pq.enqueue(dict(entry))
    return pq


# ── Event trigger_state + noise_offsets (D1) ──────────────────────────────────
# trigger_state: {region_id: {template_id: bool | "<tid>_cooldown": int}} — dedupe
# edge-state plus revolt cooldowns. Mutated in place across ticks by
# events.evaluate_triggers; persist as-is so resume continues without re-firing.
# noise_offsets: {region_id: {template_id: float}} — per-region threshold jitter,
# rolled once at sim_env init. Persist to honor current init-time-only behavior.

def _trigger_state_to_dict(ts: dict) -> dict:
    return {rid: dict(states) for rid, states in ts.items()}


def _trigger_state_from_dict(d: dict) -> dict:
    out = {}
    for rid, states in d.items():
        rebuilt = {}
        for key, val in states.items():
            if key.endswith("_cooldown"):
                rebuilt[key] = int(val)
            else:
                rebuilt[key] = bool(val)
        out[rid] = rebuilt
    return out


def _noise_offsets_to_dict(offsets: dict) -> dict:
    return {rid: dict(per_tid) for rid, per_tid in offsets.items()}


def _noise_offsets_from_dict(d: dict) -> dict:
    return {rid: {tid: float(v) for tid, v in per_tid.items()}
            for rid, per_tid in d.items()}
