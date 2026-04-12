from dataclasses import dataclass, field
import config
import world as world_mod
import faction as faction_mod
import events as _events
import drift as _drift
import technology as _tech
import tick as _tick
import diplomacy as _diplomacy
import generational as _gen
import json
import os
import random
import naming_system as _naming_mod
import coherence_ledger as _ledger_mod
import time_jump as _time_jump
import mission_generator as _mission_gen
import outcome_resolver as _outcome_res
import character_selector as _char_sel
from force_allocator import allocate_forces as _allocate_forces, BUDGET_ARCHETYPES as _BUDGET_ARCHETYPES
from mission_contracts import MissionResult


@dataclass
class TickSnapshot:
    tick: int
    regions: dict          # {region_id: {fields: {...}, faction_id, tier, composites: {...}}}
    factions: dict         # {faction_id: {budget, tech_level, archetype, owned_region_count,
                           #               avg_fields: {field: float}, total_economy, total_military,
                           #               diplomatic_stance: dict}}
    events_fired: list     # [{template_id, region_id, name, field_deltas}]
    faction_actions: list  # [{faction_id, action, target_region, budget_committed, budget_spent,
                           #   outcome_band, conquest: bool}]
    conquests: list        # [{region_id, old_faction_id, new_faction_id}]
    colonizations: list    # [{region_id, faction_id}]
    collisions: list       # [collision log dicts]
    diplomatic_events: list  # [{event_type, tick, factions, result, ...}]
    betrayals: list          # [{event_type, tick, betrayer, victim, ...}]
    player_faction_id: str | None = None


@dataclass
class TrajectoryLog:
    seed: int
    scenario_name: str
    template: str
    total_ticks: int
    features: dict
    config_snapshot: dict
    snapshots: list = field(default_factory=list)
    player_deaths: list = field(default_factory=list)  # [{tick, old_faction_id, new_faction_id}]
    coherence_ledger: object = None
    naming_system: object = None
    time_jump_results: list = field(default_factory=list)  # [run_time_jump() return dicts]
    mission_reviews: list = field(default_factory=list)    # [_run_mission_reviews() entries]

    # ── Query helpers ────────────────────────────────────────────────────────

    def faction_ids(self) -> list[str]:
        if not self.snapshots:
            return []
        return list(self.snapshots[0].factions.keys())

    def field_series(self, faction_id: str, f: str) -> list[float]:
        out = []
        for snap in self.snapshots:
            fac = snap.factions.get(faction_id)
            if fac and fac["avg_fields"].get(f) is not None:
                out.append(fac["avg_fields"][f])
            else:
                out.append(0.0)
        return out

    def region_field_series(self, region_id: str, f: str) -> list[float]:
        out = []
        for snap in self.snapshots:
            rdata = snap.regions.get(region_id)
            if rdata and rdata["fields"].get(f) is not None:
                out.append(rdata["fields"][f])
            else:
                out.append(0.0)
        return out

    def budget_series(self, faction_id: str) -> list[float]:
        return [snap.factions.get(faction_id, {}).get("budget", 0.0) for snap in self.snapshots]

    def action_log(self, faction_id: str) -> list[dict]:
        out = []
        for snap in self.snapshots:
            for a in snap.faction_actions:
                if a.get("faction_id") == faction_id:
                    out.append({**a, "tick": snap.tick})
        return out

    def attacks_by(self, faction_id: str) -> list[dict]:
        return [a for a in self.action_log(faction_id) if a.get("action") == "attack"]

    def conquests_by(self, faction_id: str) -> list[dict]:
        out = []
        for snap in self.snapshots:
            for c in snap.conquests:
                if c.get("new_faction_id") == faction_id:
                    out.append({**c, "tick": snap.tick})
        return out

    def region_ownership_at(self, tick: int) -> dict:
        if tick < 0 or tick >= len(self.snapshots):
            return {}
        snap = self.snapshots[tick]
        return {rid: rdata["faction_id"] for rid, rdata in snap.regions.items()}

    def owned_region_count_series(self, faction_id: str) -> list[int]:
        return [
            snap.factions.get(faction_id, {}).get("owned_region_count", 0)
            for snap in self.snapshots
        ]

    def events_in_range(self, tick_start: int, tick_end: int) -> list[dict]:
        out = []
        for snap in self.snapshots:
            if tick_start <= snap.tick <= tick_end:
                for evt in snap.events_fired:
                    out.append({**evt, "tick": snap.tick})
        return out

    def field_at(self, faction_id: str, f: str, tick: int) -> float:
        if tick < 0 or tick >= len(self.snapshots):
            return 0.0
        fac = self.snapshots[tick].factions.get(faction_id)
        if fac:
            return fac["avg_fields"].get(f, 0.0)
        return 0.0

    def field_delta_series(self, faction_id: str, f: str) -> list[float]:
        series = self.field_series(faction_id, f)
        return [series[i] - series[i - 1] for i in range(1, len(series))]

    def ticks_where(self, faction_id: str, f: str, predicate) -> list[int]:
        series = self.field_series(faction_id, f)
        return [i for i, v in enumerate(series) if predicate(v)]

    def region_ids(self) -> list[str]:
        if not self.snapshots:
            return []
        return list(self.snapshots[0].regions.keys())

    def region_tier(self, region_id: str) -> str:
        if not self.snapshots:
            return "unknown"
        rdata = self.snapshots[0].regions.get(region_id)
        return rdata["tier"] if rdata else "unknown"

    def region_faction_at(self, region_id: str, tick: int) -> str | None:
        if tick < 0 or tick >= len(self.snapshots):
            return None
        rdata = self.snapshots[tick].regions.get(region_id)
        return rdata["faction_id"] if rdata else None


@dataclass
class InvariantResult:
    name: str
    passed: bool
    severity: str          # "critical" | "warning" | "info"
    message: str
    details: dict | None = None


# ── Config snapshot ──────────────────────────────────────────────────────────

def _snapshot_config() -> dict:
    out = {}
    for key in dir(config):
        if key.startswith("_"):
            continue
        val = getattr(config, key)
        if isinstance(val, (int, float, bool, str, tuple, list)):
            out[key] = val
        elif isinstance(val, dict):
            out[key] = dict(val)
    return out


# ── Snapshot capture ─────────────────────────────────────────────────────────

def _capture_snapshot(tick: int, world, registry: dict, tick_log: dict | None,
                      player_faction_id: str | None = None) -> TickSnapshot:
    regions = {}
    for rid, r in world.regions.items():
        regions[rid] = {
            "fields": dict(r.fields) if r.fields else {},
            "faction_id": r.faction_id,
            "tier": r.tier,
            "composites": dict(r.composites) if r.composites else {},
            "held_since_tick": r.held_since_tick,
            "previous_faction_id": r.previous_faction_id,
        }

    factions = {}
    for fid, fac in registry.items():
        owned = [r for r in world.regions.values() if r.faction_id == fid]
        avg_fields = {}
        total_economy = 0.0
        total_military = 0.0
        if owned:
            for f in ["military", "economy", "tension", "population"]:
                avg_fields[f] = sum(r.fields[f] for r in owned) / len(owned)
            total_economy = sum(r.fields["economy"] for r in owned)
            total_military = sum(r.fields["military"] for r in owned)
        else:
            for f in ["military", "economy", "tension", "population"]:
                avg_fields[f] = 0.0

        factions[fid] = {
            "budget": fac.budget,
            "tech_level": getattr(fac, "tech_level", 0.0),
            "archetype": fac.archetype,
            "owned_region_count": len(owned),
            "avg_fields": avg_fields,
            "total_economy": total_economy,
            "total_military": total_military,
            "diplomatic_stance": dict(fac.diplomatic_stance) if hasattr(fac, "diplomatic_stance") else {},
        }

    events_fired = []
    faction_actions = []
    conquests = []
    colonizations = []
    collisions = []
    diplomatic_events = []
    betrayals = []

    if tick_log:
        events_fired = tick_log.get("events", [])
        faction_actions = tick_log.get("faction_actions", [])
        conquests = tick_log.get("conquests", [])
        colonizations = tick_log.get("colonizations", [])
        collisions = tick_log.get("collisions", [])
        diplomatic_events = tick_log.get("diplomatic_events", [])
        betrayals = tick_log.get("betrayals", [])

    return TickSnapshot(
        tick=tick,
        regions=regions,
        factions=factions,
        events_fired=events_fired,
        faction_actions=faction_actions,
        conquests=conquests,
        colonizations=colonizations,
        collisions=collisions,
        diplomatic_events=diplomatic_events,
        betrayals=betrayals,
        player_faction_id=player_faction_id,
    )


# ── Recorded scenario runner ────────────────────────────────────────────────

def _apply_features(features: dict):
    config.ENABLE_EVENTS          = features.get("events", False)
    config.ENABLE_FACTIONS        = features.get("factions", False)
    config.ENABLE_BORDER_FRICTION = features.get("border_friction", False)
    config.ENABLE_RECRUITMENT     = features.get("recruitment", True)
    config.ENABLE_ADJACENCY_BONUS = features.get("adjacency_bonus", True)
    config.ENABLE_OSCILLATION     = features.get("oscillation", True)
    config.ENABLE_EVENTS_STAGE2   = features.get("events", False)
    config.ENABLE_TECHNOLOGY      = features.get("technology", False)
    config.ENABLE_DIPLOMACY       = features.get("diplomacy", False)
    config.ENABLE_ADMIN_REVOLTS   = features.get("admin_revolts", False)
    config.DIAGNOSTIC_PRINTS      = False


def run_recorded_scenario(name: str, scenario: dict,
                          seed_override: int | None = None) -> TrajectoryLog:
    seed_used = seed_override if seed_override is not None else scenario["seed"]

    _apply_features(scenario["features"])
    for key, val in scenario.get("overrides", {}).items():
        setattr(config, key, val)

    cfg_snap = _snapshot_config()

    template = scenario["template"]
    ticks = scenario["ticks"]
    w = world_mod.generate(template, seed=seed_used)

    try:
        factions = faction_mod.generate_starting_factions(template, rng=w.rng, world=w)
        registry = faction_mod.make_registry(*factions)
    except ValueError:
        registry = {}
        faction_ids_in_world = {r.faction_id for r in w.regions.values() if r.faction_id}
        for fid in faction_ids_in_world:
            registry[fid] = faction_mod.Faction(
                fid, fid.title(), "player_civilization",
                budget=0.0, rng=w.rng,
            )

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()

    tlog = TrajectoryLog(
        seed=seed_used,
        scenario_name=name,
        template=template,
        total_ticks=ticks,
        features=dict(scenario["features"]),
        config_snapshot=cfg_snap,
    )

    stances = _diplomacy.init_stances(registry) if config.ENABLE_DIPLOMACY and registry else {}

    # ── Coherence ledger + naming system (Stage 5) ──────────────────────────
    coherence_ledger = None
    ns = None
    if scenario["features"].get("coherence_ledger"):
        ns = _naming_mod.NamingSystem()
        if scenario["features"].get("real_naming_pools"):
            _load_real_naming_pools(ns)
        else:
            _load_test_naming_pools(ns, registry, w)
        coherence_ledger = _ledger_mod.CoherenceLedger(ns)
        for fid, fac in registry.items():
            home_regions = [r for r in w.regions.values() if r.faction_id == fid]
            home_rid = home_regions[0].id if home_regions else None
            if home_rid:
                coherence_ledger.assign_faction_leader(fid, home_rid, 0, w.rng)
        if scenario["features"].get("real_naming_pools"):
            for fid, fac in registry.items():
                fname = ns.get_name(fid, "factions", current_tick=0, rng=w.rng)
                if fname:
                    fac.name = fname

    player_fid = None
    for fid, fac in registry.items():
        if fac.archetype == "player_civilization":
            player_fid = fid
            break
    gen_state = _gen.GenerationalState(player_fid, start_tick=0) if player_fid else None

    # Tick 0 snapshot (initial state, no tick_log)
    tlog.snapshots.append(_capture_snapshot(0, w, registry, None,
                                           player_faction_id=player_fid))

    if scenario.get("use_tick_engine", False):
        pending_telegraphs = []
        for t in range(1, ticks + 1):
            tick_log = _tick.run_tick(
                w, t,
                pending_queue=pending_queue,
                noise_offsets=noise_offsets,
                trigger_state=trigger_state,
                registry=registry if config.ENABLE_FACTIONS else None,
                stances=stances if config.ENABLE_DIPLOMACY else None,
                pending_telegraphs=pending_telegraphs,
                coherence_ledger=coherence_ledger,
            )
            if gen_state and _gen.check_player_collapse(gen_state, w, registry):
                result = _gen.reassign_player(gen_state, w, registry, w.rng, t)
                if result and result["type"] == "reassignment":
                    tlog.player_deaths.append({
                        "tick": t,
                        "old_faction_id": result["old_faction"],
                        "new_faction_id": result["new_faction"],
                    })
            tlog.snapshots.append(_capture_snapshot(t, w, registry, tick_log,
                                                    player_faction_id=gen_state.player_faction_id if gen_state else None))
    else:
        for t in range(1, ticks + 1):
            manual_log = {"events": [], "faction_actions": [], "conquests": [],
                          "colonizations": [], "collisions": []}

            if config.ENABLE_EVENTS:
                fired = _events.resolve_pending(pending_queue, w, t, w.rng)
                manual_log["events"].extend(fired)
                for region in w.inhabited_regions():
                    triggered_ids = _events.evaluate_triggers(region, noise_offsets, trigger_state, tick=t, rng=w.rng)
                    for tid in triggered_ids:
                        chain_tag = f"{tid}_{region.id}_t{t}"
                        result = _events.fire_event(tid, region, t, chain_tag, w.rng)
                        manual_log["events"].append(result)
                        for spawn in result["spawns"]:
                            pending_queue.enqueue(spawn)

            for fac in registry.values():
                fac.accumulate_budget(w)

            if config.ENABLE_BORDER_FRICTION:
                for region in w.inhabited_regions():
                    if region.faction_id is None:
                        continue
                    for neighbor_id in w.get_neighbors(region.id, edge_type="border"):
                        neighbor = w.regions[neighbor_id]
                        if neighbor.faction_id is None or neighbor.faction_id == region.faction_id:
                            continue
                        our_fac = registry.get(region.faction_id)
                        their_fac = registry.get(neighbor.faction_id)
                        our_stance = our_fac.diplomatic_stance.get(neighbor.faction_id, "hostile") if our_fac else "hostile"
                        their_stance = their_fac.diplomatic_stance.get(region.faction_id, "hostile") if their_fac else "hostile"
                        if our_stance == "hostile" or their_stance == "hostile":
                            region.fields["tension"] = min(100.0, region.fields["tension"] + config.BORDER_FRICTION_TENSION)
                            region.fields["economy"] = max(config.ECONOMY_FLOOR, region.fields["economy"] - config.BORDER_FRICTION_ECONOMY)
                            region.recompute_composites()

            if config.ENABLE_DIPLOMACY and registry and stances:
                betrayals = _diplomacy.check_betrayals(stances, registry, w, w.rng, t)
                manual_log["betrayals"] = betrayals
                _diplomacy.update_timers(stances, registry, w, manual_log)
                diplo_events = _diplomacy.check_peace_formation(
                    stances, registry, w, w.rng, t, manual_log
                )
                manual_log["diplomatic_events"] = diplo_events

            for region in w.inhabited_regions():
                modifier = {}
                if region.faction_id in registry:
                    modifier = registry[region.faction_id].modifiers
                adj_bonus = 0.0
                if config.ENABLE_ADJACENCY_BONUS:
                    for nr in w.allied_inhabited_neighbors(region.id, edge_type="trade"):
                        adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
                    if config.ENABLE_DIPLOMACY and region.faction_id:
                        for nid in w.get_neighbors(region.id, edge_type="trade"):
                            nr = w.regions.get(nid)
                            if (nr and nr.tier != "empty" and nr.faction_id
                                    and nr.faction_id != region.faction_id):
                                our_stance = registry[region.faction_id].diplomatic_stance.get(nr.faction_id, "hostile")
                                if our_stance == "cooperative":
                                    adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
                deltas = _drift.compute_drift_deltas(
                    region, tick=t,
                    faction_modifier=modifier,
                    adjacency_bonus=adj_bonus,
                )
                _drift.apply_drift_deltas(region, deltas)

            if config.ENABLE_TECHNOLOGY:
                for fac in registry.values():
                    _tech.grow_tech(fac, w)
                if config.ENABLE_DIPLOMACY and stances:
                    for fac in registry.values():
                        _tech.apply_convergence(fac, registry, stances)

            if gen_state and _gen.check_player_collapse(gen_state, w, registry):
                result = _gen.reassign_player(gen_state, w, registry, w.rng, t)
                if result and result["type"] == "reassignment":
                    tlog.player_deaths.append({
                        "tick": t,
                        "old_faction_id": result["old_faction"],
                        "new_faction_id": result["new_faction"],
                    })
            tlog.snapshots.append(_capture_snapshot(t, w, registry, manual_log,
                                                    player_faction_id=gen_state.player_faction_id if gen_state else None))

    # ── Time jumps (Stage 5 chronicle) ──────────────────────────────────────
    chronicle_reviews = scenario["features"].get("chronicle_reviews", [])
    if chronicle_reviews and coherence_ledger:
        player_lineage_id = None
        if player_fid:
            for cid, char in coherence_ledger._characters.items():
                if char.faction_id == player_fid and char.lineage_id:
                    player_lineage_id = char.lineage_id
                    break
            if not player_lineage_id:
                leader = coherence_ledger.assign_faction_leader(
                    player_fid, None, 0, w.rng)
                if leader:
                    player_lineage_id = coherence_ledger.create_lineage(leader.id)

        player_regions = w.regions_by_faction(player_fid) if player_fid else []
        last_mission_region = player_regions[0].id if player_regions else None

        jump_duration = scenario["features"].get("chronicle_jump_duration", 100)
        for jump_tick in chronicle_reviews:
            result = _time_jump.run_time_jump(
                world=w,
                n_ticks=jump_duration,
                registry=registry,
                pending_queue=pending_queue,
                noise_offsets=noise_offsets,
                trigger_state=trigger_state,
                stances=stances if config.ENABLE_DIPLOMACY else None,
                pending_telegraphs=pending_telegraphs if scenario.get("use_tick_engine") else [],
                rng=w.rng,
                start_tick=jump_tick,
                coherence_ledger=coherence_ledger,
                naming_system=ns,
                player_lineage_id=player_lineage_id,
                last_mission_region=last_mission_region,
                last_mission_outcome="mixed",
                mission_info={
                    "outcome": "a hard-won engagement whose costs became clear only afterward",
                    "archetype": "defensive_stand",
                    "region": last_mission_region or "unknown",
                },
            )
            result["jump_tick"] = jump_tick
            tlog.time_jump_results.append(result)

            player_regions = w.regions_by_faction(player_fid) if player_fid else []
            last_mission_region = player_regions[0].id if player_regions else last_mission_region

    tlog.coherence_ledger = coherence_ledger
    tlog.naming_system = ns

    # ── Mission reviews (Checkpoint H) ──────────────────────────────────────
    if scenario["features"].get("missions") and coherence_ledger and player_fid:
        _run_mission_reviews(
            tlog, scenario, w, registry, player_fid, coherence_ledger, ns,
            pending_queue, noise_offsets, trigger_state, stances, gen_state,
        )

    return tlog


def _run_mission_reviews(tlog, scenario, w, registry, player_fid, coherence_ledger, ns,
                         pending_queue, noise_offsets, trigger_state, stances, gen_state):
    jump_indices    = scenario.get("mission_review_jumps", [])
    mock_bands      = scenario.get("mock_outcome_bands", [])
    difficulty      = scenario.get("difficulty", "medium")
    player_prefs    = scenario.get("player_preferences")
    test_all_arches = scenario.get("test_all_archetypes", False)
    test_diffs      = scenario.get("test_difficulties")
    jump_duration   = scenario["features"].get("chronicle_jump_duration", 100)

    # Flatten event / action / conquest logs from all recorded snapshots.
    event_log   = []
    action_log  = []
    conquest_log = []
    for snap in tlog.snapshots:
        for evt in snap.events_fired:
            event_log.append({**evt, "tick": snap.tick})
        for act in snap.faction_actions:
            action_log.append({**act, "tick": snap.tick})
        for con in snap.conquests:
            conquest_log.append({**con, "tick": snap.tick})

    current_tick = tlog.total_ticks
    current_lineage_id = None
    if gen_state:
        char_id = gen_state.current_chapter.get("character_id")
        if char_id:
            rec = coherence_ledger.get_character_by_id(char_id)
            if rec:
                current_lineage_id = rec.lineage_id

    pending_telegraphs = []
    review_rng = random.Random(tlog.seed + 9000)  # deterministic, separate from world rng

    for jump_idx, _ in enumerate(jump_indices):
        mock_band = mock_bands[jump_idx] if jump_idx < len(mock_bands) else "partial_success"

        mission_raw = _mission_gen.generate_mission(
            world=w,
            registry=registry,
            player_faction_id=player_fid,
            event_log=event_log,
            action_log=action_log,
            conquest_log=conquest_log,
            current_tick=current_tick,
            difficulty=difficulty,
            rng=review_rng,
            ledger=coherence_ledger,
            current_lineage_id=current_lineage_id,
            player_preferences=player_prefs,
        )

        setup             = mission_raw["setup"] if mission_raw else None
        scored_candidates = mission_raw["scored_candidates"] if mission_raw else []

        # Commander selection
        cmdr_sel           = None
        chapter_count_at_sel = None
        if setup and gen_state:
            if current_lineage_id:
                chapter_count_at_sel = coherence_ledger.get_chapter_count(current_lineage_id)
            cmdr_sel = _char_sel.run_selection(
                gen_state, coherence_ledger, w, setup.region_id,
                review_rng, current_tick,
                current_lineage_id=current_lineage_id,
            )
            if cmdr_sel and cmdr_sel.lineage_id:
                current_lineage_id = cmdr_sel.lineage_id
                gen_state.current_chapter["character_id"] = cmdr_sel.character_id

        # Outcome resolution — apply to world so next jump inherits consequences,
        # but record the deltas.
        outcome_result = None
        if setup:
            mock_result = MissionResult(
                mission_id=setup.mission_id,
                outcome_band=mock_band,
                objective_score=0.7,
                force_retention=0.8,
                per_objective=[],
                commander_survived=True,
                ticks_elapsed=200,
            )
            commander_id = cmdr_sel.character_id if cmdr_sel else None
            outcome_result = _outcome_res.resolve_outcome(
                mock_result, setup.archetype, setup.region_id,
                w, player_fid, ledger=coherence_ledger, commander_id=commander_id,
            )

        # Scenario 15: non-mutating all-bands preview for M9 / M10
        all_bands_preview = _build_all_bands_preview(w, player_fid) if test_all_arches else None

        # Scenario 16: fixed-snapshot difficulty variants for M8
        difficulty_variants = None
        if test_diffs and setup:
            difficulty_variants = _build_difficulty_variants(
                setup, w, player_fid, test_diffs)

        tlog.mission_reviews.append({
            "jump_index":            jump_idx,
            "setup":                 setup,
            "scored_candidates":     scored_candidates,
            "outcome_band":          mock_band,
            "outcome_result":        outcome_result,
            "commander_selection":   cmdr_sel,
            "chapter_count_at_sel":  chapter_count_at_sel,
            "all_bands_preview":     all_bands_preview,
            "difficulty_variants":   difficulty_variants,
        })

        # Advance world via time jump before next mission generation
        tj_result = _time_jump.run_time_jump(
            world=w,
            n_ticks=jump_duration,
            registry=registry,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            stances=stances if config.ENABLE_DIPLOMACY else None,
            pending_telegraphs=pending_telegraphs,
            rng=w.rng,
            start_tick=current_tick,
            coherence_ledger=coherence_ledger,
            naming_system=ns,
            player_lineage_id=current_lineage_id,
            last_mission_region=setup.region_id if setup else None,
            last_mission_outcome=mock_band,
            mission_info={
                "outcome": mock_band,
                "archetype": setup.archetype if setup else "unknown",
                "region": setup.region_id if setup else "unknown",
            },
        )
        tlog.time_jump_results.append({**tj_result, "jump_tick": current_tick})
        current_tick += jump_duration


def _build_all_bands_preview(w, player_fid):
    """Non-mutating sweep: for each archetype × band, compute deltas on a low- and
    high-stat player region. Returns None if no contrasting pair exists (min 10 mil gap)."""
    BANDS = ["total_success", "strong_success", "partial_success",
             "partial_failure", "total_failure"]

    player_regions = [r for r in w.regions.values()
                      if r.faction_id == player_fid and r.tier != "empty"]
    if not player_regions:
        return None

    low_r  = min(player_regions, key=lambda r: r.fields.get("military", 50))
    high_r = max(player_regions, key=lambda r: r.fields.get("military", 50))
    if low_r.id == high_r.id or high_r.fields.get("military", 50) - low_r.fields.get("military", 50) < 10:
        return None

    def _adj_player(base_region):
        """Return a player-owned neighbor of base_region, or base_region if none exists."""
        for nid in w.get_neighbors(base_region.id):
            nr = w.regions.get(nid)
            if nr and nr.faction_id == player_fid:
                return nr
        return base_region

    result = []
    for archetype, table in config.CONSEQUENCE_TABLES.items():
        entry = {
            "archetype":     archetype,
            "low_region_id": low_r.id,
            "high_region_id": high_r.id,
            "bands": {},
            "deficit_check": {},
        }
        for band in BANDS:
            low_deltas  = {}
            high_deltas = {}
            for delta_spec in table.get(band, []):
                target = delta_spec["target"]
                if target not in ("mission", "home", "exposed", "adjacent_player"):
                    continue
                f    = delta_spec["field"]
                form = delta_spec["form"]
                pct  = delta_spec["pct"]
                if target == "adjacent_player":
                    eff_low  = _adj_player(low_r)
                    eff_high = _adj_player(high_r)
                else:
                    eff_low  = low_r
                    eff_high = high_r
                # Floor field values at 1.0 so "current"-form deltas are never all-zero
                # (prevents degenerate band signatures when a region has field=0).
                low_val  = max(eff_low.fields.get(f, 50),  1.0)
                high_val = max(eff_high.fields.get(f, 50), 1.0)
                low_deltas[f]  = _outcome_res.compute_delta(low_val,  form, pct)
                high_deltas[f] = _outcome_res.compute_delta(high_val, form, pct)
            entry["bands"][band] = {"low": low_deltas, "high": high_deltas}

            # Per-field deficit pairs for M9: find the actual low/high region per field
            fc = {}
            for delta_spec in table.get(band, []):
                if delta_spec["form"] != "deficit" or delta_spec["pct"] <= 0:
                    continue
                f   = delta_spec["field"]
                pct = delta_spec["pct"]
                fvals  = [(r.fields.get(f, 50), r) for r in player_regions]
                fl_r   = min(fvals, key=lambda x: x[0])[1]
                fh_r   = max(fvals, key=lambda x: x[0])[1]
                if abs(fl_r.fields.get(f, 50) - fh_r.fields.get(f, 50)) < 5:
                    continue
                fc[f] = {
                    "low_delta":  _outcome_res.compute_delta(fl_r.fields.get(f, 50),  "deficit", pct),
                    "high_delta": _outcome_res.compute_delta(fh_r.fields.get(f, 50), "deficit", pct),
                    "low_val":    fl_r.fields.get(f, 50),
                    "high_val":   fh_r.fields.get(f, 50),
                }
            entry["deficit_check"][band] = fc

        result.append(entry)
    return result


def _build_difficulty_variants(setup, w, player_fid, test_difficulties):
    """Run allocate_forces at each difficulty from a frozen field snapshot.
    Uses a fixed seed per call so enemy forces are comparable across difficulties (M8)."""
    region = w.regions.get(setup.region_id)
    if not region:
        return None

    archetype   = setup.archetype
    trigger_ctx = dict(setup.metadata.get("trigger_context", {}))
    capacity    = region.composites.get("capacity", 0.5) if hasattr(region, "composites") else 0.5
    cap_norm    = capacity / 100.0 if capacity > 1.0 else capacity
    enemy_fid   = setup.enemy_forces[0].faction_id if setup.enemy_forces else "enemy_faction"
    frozen      = dict(region.fields)

    # Budget archetypes derive enemy power from budget_committed, which is missing from
    # the snapshot trigger_context. Inject a synthetic value representative of a mid-game
    # attack commit (faction budget ~200 * ATTACK_COMMIT_FRACTION=0.70 ≈ 140, rounded to 150).
    synthetic_budget = None
    if archetype in _BUDGET_ARCHETYPES and not trigger_ctx.get("budget_committed"):
        synthetic_budget = region.fields.get("military", 50) * config.MILITARY_TO_POWER_SCALE / config.BUDGET_TO_POWER_SCALE
        trigger_ctx = dict(trigger_ctx)
        trigger_ctx["budget_committed"] = synthetic_budget

    variants = []
    for diff in test_difficulties:
        region.fields.update(frozen)          # same field state for every call
        call_rng = random.Random(42)          # same rng state for every call → M8 comparable
        alloc = _allocate_forces(archetype, trigger_ctx, region, cap_norm,
                                 diff, player_fid, enemy_fid, call_rng)
        variants.append({
            "difficulty":         diff,
            "player_force":       alloc["player_force"],
            "enemy_force":        alloc["enemy_force"],
            "parity_ratio":       alloc["parity_ratio"],
            "synthetic_budget":   synthetic_budget,
        })

    region.fields.update(frozen)              # final restore
    return variants


_TEST_NAME_POOL = [
    "Kaelith Vorn", "Suranna Deshkov", "Toryn Ashemark", "Velan Koss",
    "Mireth Solane", "Draven Thurik", "Olenna Brask", "Fendric Hale",
    "Cassia Vrenn", "Aldric Mourne", "Zhara Okun", "Brin Tasev",
    "Lunara Chelk", "Demaris Vyth", "Korren Sable", "Ithara Goss",
    "Tyven Marsh", "Sariel Donn", "Quillon Pask", "Elanda Rieve",
    "Dareth Kayn", "Solvei Hask", "Orill Vandre", "Maelis Thorn",
    "Kavi Rennic", "Tallis Obren", "Yenara Stross", "Firek Dallow",
    "Jessamine Kael", "Ulric Voss", "Petra Holm", "Neven Drask",
    "Caris Aldune", "Roshan Mevek", "Liri Ashfall", "Gavin Torr",
    "Xandri Pell", "Osen Kraith", "Emira Vael", "Jorik Stenn",
    "Halla Birsk", "Renn Calder", "Savin Oreth", "Devan Falk",
    "Ilya Maren", "Theron Gale", "Anise Drava", "Kellan Ruud",
    "Brynn Solvar", "Ondri Tavish",
    # Extended pool — prevents exhaustion in longer test scenarios (1500+ ticks, many breakaways)
    "Kaelith Vorn II", "Suranna Deshkov II", "Toryn Ashemark II", "Velan Koss II",
    "Mireth Solane II", "Draven Thurik II", "Olenna Brask II", "Fendric Hale II",
    "Cassia Vrenn II", "Aldric Mourne II", "Zhara Okun II", "Brin Tasev II",
    "Lunara Chelk II", "Demaris Vyth II", "Korren Sable II", "Ithara Goss II",
    "Tyven Marsh II", "Sariel Donn II", "Quillon Pask II", "Elanda Rieve II",
    "Dareth Kayn II", "Solvei Hask II", "Orill Vandre II", "Maelis Thorn II",
    "Kavi Rennic II", "Tallis Obren II", "Yenara Stross II", "Firek Dallow II",
    "Jessamine Kael II", "Ulric Voss II", "Petra Holm II", "Neven Drask II",
    "Caris Aldune II", "Roshan Mevek II", "Liri Ashfall II", "Gavin Torr II",
    "Xandri Pell II", "Osen Kraith II", "Emira Vael II", "Jorik Stenn II",
    "Halla Birsk II", "Renn Calder II", "Savin Oreth II", "Devan Falk II",
    "Ilya Maren II", "Theron Gale II", "Anise Drava II", "Kellan Ruud II",
    "Brynn Solvar II", "Ondri Tavish II",
    "Kaelith Vorn III", "Suranna Deshkov III", "Toryn Ashemark III", "Velan Koss III",
    "Mireth Solane III", "Draven Thurik III", "Olenna Brask III", "Fendric Hale III",
    "Cassia Vrenn III", "Aldric Mourne III", "Zhara Okun III", "Brin Tasev III",
    "Lunara Chelk III", "Demaris Vyth III", "Korren Sable III", "Ithara Goss III",
    "Tyven Marsh III", "Sariel Donn III", "Quillon Pask III", "Elanda Rieve III",
    "Dareth Kayn III", "Solvei Hask III", "Orill Vandre III", "Maelis Thorn III",
    "Kavi Rennic III", "Tallis Obren III", "Yenara Stross III", "Firek Dallow III",
    "Jessamine Kael III", "Ulric Voss III", "Petra Holm III", "Neven Drask III",
    "Caris Aldune III", "Roshan Mevek III", "Liri Ashfall III", "Gavin Torr III",
    "Xandri Pell III", "Osen Kraith III", "Emira Vael III", "Jorik Stenn III",
    "Halla Birsk III", "Renn Calder III", "Savin Oreth III", "Devan Falk III",
    "Ilya Maren III", "Theron Gale III", "Anise Drava III", "Kellan Ruud III",
    "Brynn Solvar III", "Ondri Tavish III",
    "Kaelith Vorn IV", "Suranna Deshkov IV", "Toryn Ashemark IV", "Velan Koss IV",
    "Mireth Solane IV", "Draven Thurik IV", "Olenna Brask IV", "Fendric Hale IV",
    "Cassia Vrenn IV", "Aldric Mourne IV", "Zhara Okun IV", "Brin Tasev IV",
    "Lunara Chelk IV", "Demaris Vyth IV", "Korren Sable IV", "Ithara Goss IV",
    "Tyven Marsh IV", "Sariel Donn IV", "Quillon Pask IV", "Elanda Rieve IV",
    "Dareth Kayn IV", "Solvei Hask IV", "Orill Vandre IV", "Maelis Thorn IV",
    "Kavi Rennic IV", "Tallis Obren IV", "Yenara Stross IV", "Firek Dallow IV",
    "Jessamine Kael IV", "Ulric Voss IV", "Petra Holm IV", "Neven Drask IV",
    "Caris Aldune IV", "Roshan Mevek IV", "Liri Ashfall IV", "Gavin Torr IV",
    "Xandri Pell IV", "Osen Kraith IV", "Emira Vael IV", "Jorik Stenn IV",
    "Halla Birsk IV", "Renn Calder IV", "Savin Oreth IV", "Devan Falk IV",
    "Ilya Maren IV", "Theron Gale IV", "Anise Drava IV", "Kellan Ruud IV",
    "Brynn Solvar IV", "Ondri Tavish IV",
]


def _load_test_naming_pools(ns, registry, world):
    for fid in registry:
        shuffled = list(_TEST_NAME_POOL)
        world.rng.shuffle(shuffled)
        ns.load_pool(fid, "people", shuffled)


def _load_real_naming_pools(ns):
    names_path = os.path.join("library", "naming", "names.json")
    if not os.path.exists(names_path):
        return
    with open(names_path) as f:
        all_names = json.load(f)
    for fid, cats in all_names.items():
        for cat, names in cats.items():
            ns.load_pool(fid, cat, names)
    ns.load_pool("player_civilization", "people",
                 all_names.get("player", {}).get("people", []))
    ns.load_pool("player_civilization", "places",
                 all_names.get("player", {}).get("places", []))
    ns.load_pool("player_civilization", "factions",
                 all_names.get("player", {}).get("factions", []))

    subsets_path = os.path.join("prompts", "variable_subsets.json")
    if os.path.exists(subsets_path):
        with open(subsets_path) as f:
            subsets = json.load(f)
        for fid, subset in subsets.items():
            ns.set_variable_subset(fid, subset)
