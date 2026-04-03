from dataclasses import dataclass, field
import config
import world as world_mod
import faction as faction_mod
import events as _events
import drift as _drift
import technology as _tech
import tick as _tick


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


@dataclass
class TrajectoryLog:
    seed: int
    scenario_name: str
    template: str
    total_ticks: int
    features: dict
    config_snapshot: dict
    snapshots: list = field(default_factory=list)

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

def _capture_snapshot(tick: int, world, registry: dict, tick_log: dict | None) -> TickSnapshot:
    regions = {}
    for rid, r in world.regions.items():
        regions[rid] = {
            "fields": dict(r.fields) if r.fields else {},
            "faction_id": r.faction_id,
            "tier": r.tier,
            "composites": dict(r.composites) if r.composites else {},
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

    if tick_log:
        events_fired = tick_log.get("events", [])
        faction_actions = tick_log.get("faction_actions", [])
        conquests = tick_log.get("conquests", [])
        colonizations = tick_log.get("colonizations", [])
        collisions = tick_log.get("collisions", [])

    return TickSnapshot(
        tick=tick,
        regions=regions,
        factions=factions,
        events_fired=events_fired,
        faction_actions=faction_actions,
        conquests=conquests,
        colonizations=colonizations,
        collisions=collisions,
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

    # Tick 0 snapshot (initial state, no tick_log)
    tlog.snapshots.append(_capture_snapshot(0, w, registry, None))

    if scenario.get("use_tick_engine", False):
        for t in range(1, ticks + 1):
            tick_log = _tick.run_tick(
                w, t,
                pending_queue=pending_queue,
                noise_offsets=noise_offsets,
                trigger_state=trigger_state,
                registry=registry if config.ENABLE_FACTIONS else None,
            )
            tlog.snapshots.append(_capture_snapshot(t, w, registry, tick_log))
    else:
        for t in range(1, ticks + 1):
            manual_log = {"events": [], "faction_actions": [], "conquests": [],
                          "colonizations": [], "collisions": []}

            if config.ENABLE_EVENTS:
                fired = _events.resolve_pending(pending_queue, w, t, w.rng)
                manual_log["events"].extend(fired)
                for region in w.inhabited_regions():
                    triggered_ids = _events.evaluate_triggers(region, noise_offsets, trigger_state, tick=t)
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
                    for neighbor_id in w.get_neighbors(region.id):
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

            for region in w.inhabited_regions():
                modifier = {}
                if region.faction_id in registry:
                    modifier = registry[region.faction_id].modifiers
                adj_bonus = 0.0
                if config.ENABLE_ADJACENCY_BONUS:
                    for nr in w.allied_inhabited_neighbors(region.id):
                        adj_bonus += config.NEIGHBOR_ECONOMY_BONUS * (nr.fields["economy"] / 100.0)
                    if config.ENABLE_DIPLOMACY and region.faction_id:
                        for nid in w.get_neighbors(region.id):
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

            tlog.snapshots.append(_capture_snapshot(t, w, registry, manual_log))

    return tlog
