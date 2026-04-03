# Input:  World, optional PendingQueue + noise_offsets (required when ENABLE_EVENTS=True)
#         registry: {faction_id: Faction} when ENABLE_FACTIONS=True
#         antagonist: Antagonist when ENABLE_FACTIONS=False (backward compat)
# Output: mutates world in place each tick; returns tick log dict
#
# 7-step tick resolution sequence (Stage 0 revision):
#   1. Resolve pending events
#   2. Evaluate fresh threshold triggers
#   3. Run all faction agents  (was: single antagonist)
#   4. Apply border friction   (new)
#   5. Apply passive drift     (military now includes recruitment term)
#   6. Recompute composites    (happens inside apply_drift)
#   7. Log everything

import config
import drift as _drift
import events as _events
import intent_resolver as _intent_resolver
import technology as _technology

_SHORT_NAMES = {
    "player": "pl", "conqueror": "conq", "fortifier": "fort", "opportunist": "opp",
}

def _short(fid):
    for key, val in _SHORT_NAMES.items():
        if key in fid:
            return val
    return fid[:8]


def run_tick(world, tick_num: int, ledger=None,
             pending_queue=None, noise_offsets=None, trigger_state=None,
             registry=None, antagonist=None) -> dict:
    log = {
        "tick":            tick_num,
        "events":          [],
        "faction_actions": [],
        "antagonist":      None,
        "border_friction": {},
        "tech_growth":     {},
        "drift":           {},
        "revolts":         [],
        "conquests":       [],
        "colonizations":   [],
        "collisions":      [],
    }

    rng = world.rng

    # ── Steps 1–2: Event system ──────────────────────────────────────────────
    if config.ENABLE_EVENTS:
        # Step 1: resolve pending events
        fired = _events.resolve_pending(pending_queue, world, tick_num, rng)
        log["events"].extend(fired)

        # Step 2: evaluate fresh threshold triggers
        for region in world.inhabited_regions():
            triggered_ids = _events.evaluate_triggers(region, noise_offsets, trigger_state, tick=tick_num)
            for tid in triggered_ids:
                chain_tag = f"{tid}_{region.id}_t{tick_num}"
                result    = _events.fire_event(tid, region, tick_num, chain_tag, rng)
                spawn_dicts = result["spawns"]
                for spawn in spawn_dicts:
                    pending_queue.enqueue(spawn)
                result["spawns"] = [
                    f"{s['template_id']}@tick_{s['due_tick']}" for s in spawn_dicts
                ]
                log["events"].append(result)

        # L4: handle revolt faction creation from any fired event
        if registry is not None:
            for evt in log["events"]:
                if evt.get("creates_faction"):
                    revolt_log = _handle_revolt_faction_creation(
                        evt, world, registry, rng, tick_num
                    )
                    if revolt_log:
                        log["revolts"].append(revolt_log)
                        if ledger is not None:
                            ledger.log_revolt(tick_num, revolt_log)

    # ── Step 3: Faction agents — snapshot-based intent-resolution ────────────
    if registry is not None and config.ENABLE_FACTIONS:
        # 3a: Snapshot (before any mutations this tick)
        snapshot = _build_snapshot(world)
        # 3b: Accumulate budget, then decide against snapshot
        for faction in list(registry.values()):
            faction.accumulate_budget(world)
        intents = []
        for faction in list(registry.values()):
            intent = faction.decide(snapshot, world.adjacency, registry, rng, tick_num)
            intents.append(intent)
        # 3c: Resolve
        resolved = _intent_resolver.resolve(intents, snapshot, registry, rng, tick=tick_num)
        # 3d: Apply
        for action in resolved:
            log["faction_actions"].append(action)
            _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num)
            if action.get("conquest"):
                log["conquests"].append(action["conquest"])
            if action.get("colonization"):
                log["colonizations"].append(action["colonization"])
            if action.get("significance") == "collision" and action.get("outcome_band") == "collision":
                log["collisions"].append(action["log"])

        if config.DIAGNOSTIC_PRINTS:
            # ── DIAGNOSTIC — windowed snapshots + all significant events ─────
            in_window   = tick_num <= 5 or (248 <= tick_num <= 252) or tick_num >= 496
            is_round    = tick_num in (5, 252, 500)

            sig_factions = [
                faction.id for faction in registry.values()
                if next((i for i in intents if i["faction_id"] == faction.id), {}).get("action")
                   in ("attack", "colonize")
            ]
            any_significant = bool(sig_factions) or bool(log.get("conquests")) or bool(log.get("revolts"))

            if in_window or any_significant or is_round:
                print(f"\n── t={tick_num} ──")

                for faction in list(registry.values()):
                    mi = next((i for i in intents if i["faction_id"] == faction.id), None)
                    mr = next((a for a in resolved if a["faction_id"] == faction.id), None)
                    if not mi or not mr:
                        continue
                    if not in_window and faction.id not in sig_factions:
                        continue

                    act = mi["action"]
                    tgt_rid = mi.get("target_region")
                    tgt = tgt_rid.replace("region_", "") if tgt_rid else "—"

                    suffix = ""
                    if act == "attack":
                        band = mr.get("outcome_band", "")
                        suffix = f" <<< {band}"
                        if mr.get("conquest"):
                            suffix += " CONQUEST!"
                        tgt_mil = snapshot[tgt_rid]["fields"]["military"] if tgt_rid and tgt_rid in snapshot else None
                        if tgt_mil is not None:
                            suffix += f"  def_mil={tgt_mil:.1f}"
                    elif act == "colonize":
                        suffix = " <<<"

                    print(
                        f"  t={tick_num:>4} {_short(faction.id):<5}"
                        f"  b={faction.budget + mr['budget_spent']:>6.1f}"
                        f"  {act:<10}"
                        f"  spent={mr['budget_spent']:>5.1f}"
                        f"  rem={faction.budget:>6.1f}"
                        f"  {tgt}{suffix}"
                    )

                if is_round:
                    ownership = {}
                    for rid, r in world.regions.items():
                        fid = r.faction_id or "—"
                        ownership.setdefault(fid, []).append(rid.replace("region_", ""))
                    for fid, rids in sorted(ownership.items()):
                        print(f"    {_short(fid):<5} [{len(rids)}]: {', '.join(sorted(rids))}")

    elif config.ENABLE_ANTAGONIST and antagonist is not None:
        # Backward-compat path for Groups A–E tests
        ant_log = antagonist.act(world.inhabited_regions())
        log["antagonist"] = ant_log
        if ledger is not None:
            ledger.log_antagonist(
                tick_num, ant_log["budget"],
                ant_log["allocation"], ant_log["applied"]
            )

    # ── Step 4: Border friction ──────────────────────────────────────────────
    if config.ENABLE_BORDER_FRICTION and registry is not None:
        friction_log = _apply_border_friction(world, registry)
        log["border_friction"] = friction_log

    # ── Step 4.5: Technology growth ──────────────────────────────────────────
    if config.ENABLE_TECHNOLOGY and registry is not None:
        for faction in registry.values():
            entry = _technology.grow_tech(faction, world)
            if entry is not None:
                log["tech_growth"][faction.id] = entry

    # ── Step 5: Passive drift (with optional faction modifiers) ──────────────
    for region in world.inhabited_regions():
        modifier = {}
        if registry is not None and region.faction_id in registry:
            modifier = registry[region.faction_id].modifiers
        deltas = _drift.apply_drift(region, faction_modifier=modifier)
        log["drift"][region.id] = deltas

    # ── Step 7: Log ──────────────────────────────────────────────────────────
    if ledger is not None:
        for evt in log["events"]:
            ledger.log_event(
                tick_num, evt["region_id"], evt["template_id"],
                evt["name"], evt["field_deltas"],
                evt["chain_tag"], evt["spawns"]
            )
        ledger.log_snapshot(tick_num, world)

    return log


def run_ticks(world, n: int, ledger=None,
              pending_queue=None, noise_offsets=None, trigger_state=None,
              registry=None, antagonist=None) -> list:
    return [
        run_tick(world, t + 1, ledger, pending_queue, noise_offsets, trigger_state,
                 registry, antagonist)
        for t in range(n)
    ]


# ── F3: Snapshot builder ─────────────────────────────────────────────────────

def _build_snapshot(world) -> dict:
    return {
        rid: {
            "fields":     dict(r.fields),
            "faction_id": r.faction_id,
            "tier":       r.tier,
        }
        for rid, r in world.regions.items()
    }


# ── F3: Apply a single resolved action to live world state ───────────────────

def _apply_resolved_action(world, registry, action, pending_queue, ledger, tick_num):
    fid     = action["faction_id"]
    faction = registry.get(fid)

    if faction and action["budget_spent"] > 0:
        faction.budget = max(0.0, faction.budget - action["budget_spent"])

    if action.get("colonization"):
        col    = action["colonization"]
        region = world.regions[col["region_id"]]
        region.faction_id = col["faction_id"]
        region.tier       = "frontier"

    if action.get("conquest"):
        con    = action["conquest"]
        region = world.regions[con["region_id"]]
        region.faction_id = con["new_faction_id"]

    bypass_floor = action.get("log", {}).get("bypass_floor", False)
    for rid, deltas in action["deltas"].items():
        region = world.regions.get(rid)
        if region is None:
            continue
        for field, delta in deltas.items():
            old_val = region.fields.get(field, 0.0)
            new_val = old_val + delta
            if field == "economy":
                floor = 0.0 if bypass_floor else config.ECONOMY_FLOOR
                new_val = max(floor, min(100.0, new_val))
            else:
                new_val = max(0.0, min(100.0, new_val))
            region.fields[field] = new_val
        region.recompute_composites()

    # Apply garrison military after battle damage is resolved
    if action.get("conquest") and action["conquest"].get("garrison"):
        con_region = world.regions[action["conquest"]["region_id"]]
        garrison = action["conquest"]["garrison"]
        con_region.fields["military"] = min(100.0, con_region.fields["military"] + garrison)
        con_region.recompute_composites()

    if pending_queue is not None:
        for spawn in action.get("chain_spawns", []):
            pending_queue.enqueue(spawn)


# ── J2: Border friction helper ────────────────────────────────────────────────

def _apply_border_friction(world, registry: dict) -> dict:
    friction_log = {}
    for region in world.inhabited_regions():
        if region.faction_id is None:
            continue
        total_ten = 0.0
        total_eco = 0.0
        for neighbor_id in world.get_neighbors(region.id):
            neighbor = world.regions[neighbor_id]
            if neighbor.faction_id is None or neighbor.faction_id == region.faction_id:
                continue
            our_faction  = registry.get(region.faction_id)
            their_faction = registry.get(neighbor.faction_id)
            our_stance   = our_faction.diplomatic_stance.get(neighbor.faction_id, "hostile") if our_faction else "hostile"
            their_stance = their_faction.diplomatic_stance.get(region.faction_id, "hostile") if their_faction else "hostile"
            if our_stance == "hostile" or their_stance == "hostile":
                total_ten += config.BORDER_FRICTION_TENSION
                total_eco += config.BORDER_FRICTION_ECONOMY
        if total_ten > 0.0 or total_eco > 0.0:
            region.fields["tension"] = min(100.0, region.fields["tension"] + total_ten)
            region.fields["economy"] = max(config.ECONOMY_FLOOR, region.fields["economy"] - total_eco)
            region.recompute_composites()
            friction_log[region.id] = {
                "tension": round(total_ten, 3),
                "economy": round(-total_eco, 3),
            }
    return friction_log


# ── L4: Revolt faction creation helper ───────────────────────────────────────

def _handle_revolt_faction_creation(evt: dict, world, registry: dict,
                                     rng, tick: int) -> dict | None:
    from faction import Faction

    region = world.regions.get(evt["region_id"])
    if region is None or region.faction_id is None:
        return None

    # Roll for breakaway formation
    lo, hi = config.REVOLT_SUCCESS_RANGE
    success_rate = rng.uniform(lo, hi)
    if rng.random() > success_rate:
        return None  # revolt didn't produce a lasting faction

    original_faction = region.faction_id
    new_id   = f"breakaway_{tick}_{region.id}"
    new_name = f"Breakaway of {region.name}"

    # Steal resources from the region
    mil_stolen = region.fields["military"] * config.REVOLT_MILITARY_STEAL
    eco_stolen = region.fields["economy"]  * config.REVOLT_ECONOMY_STEAL
    region.fields["military"] = max(0.0, region.fields["military"] - mil_stolen)
    region.fields["economy"]  = max(0.0, region.fields["economy"]  - eco_stolen)
    region.recompute_composites()

    # Transfer ownership
    region.faction_id = new_id

    # Create the new faction (hostile toward all current factions by default)
    new_faction = Faction(
        new_id, new_name, "breakaway",
        budget=0.0,
        diplomatic_stance={fid: "hostile" for fid in registry},
    )
    # Existing factions become hostile toward the breakaway
    for fac in registry.values():
        fac.diplomatic_stance[new_id] = "hostile"

    registry[new_id] = new_faction

    return {
        "type":             "revolt",
        "tick":             tick,
        "region":           region.id,
        "original_faction": original_faction,
        "new_faction":      new_id,
        "success_rate":     round(success_rate, 3),
        "military_stolen":  round(mil_stolen, 2),
        "economy_stolen":   round(eco_stolen, 2),
    }
