import config
from force_allocator import allocate_forces
from mission_contracts import MissionSetup, ObjectiveSpec
from mission_briefing import assemble_briefing


REVOLT_EVENT_IDS = {
    "evt_regional_revolt", "evt_revolt_entrenched", "evt_resistance_movement",
    "evt_admin_separatist", "evt_admin_political_crisis",
    "evt_admin_popular_support", "evt_admin_military_defection", "evt_admin_breakaway",
}

ATTACK_ACTIONS = {"attack", "attack_skirmish"}


def _player_region_ids(world, player_faction_id):
    return [r.id for r in world.regions.values() if r.faction_id == player_faction_id]


def _hostile_neighbors(world, region, registry):
    results = []
    faction = registry.get(region.faction_id)
    if not faction:
        return results
    for nid in world.get_neighbors(region.id):
        neighbor = world.regions.get(nid)
        if not neighbor or not neighbor.faction_id:
            continue
        if neighbor.faction_id == region.faction_id:
            continue
        stance = faction.diplomatic_stance.get(neighbor.faction_id, "hostile")
        if stance == "hostile":
            results.append(neighbor)
    return results


def _recent_events(event_log, region_id=None, template_ids=None, ticks_back=None, current_tick=None):
    results = []
    for evt in event_log:
        if region_id and evt.get("region_id") != region_id:
            continue
        if template_ids and evt.get("template_id") not in template_ids:
            continue
        if ticks_back is not None and current_tick is not None:
            evt_tick = evt.get("tick", 0)
            if current_tick - evt_tick > ticks_back:
                continue
        results.append(evt)
    return results


def _recent_conquests(conquest_log, region_id=None, faction_id=None):
    results = []
    for c in conquest_log:
        if region_id and c.get("region_id") != region_id:
            continue
        if faction_id and c.get("old_faction_id") != faction_id:
            continue
        results.append(c)
    return results


def _recent_actions(action_log, target_region=None, action_types=None):
    results = []
    for a in action_log:
        if target_region and a.get("target_region") != target_region:
            continue
        if action_types and a.get("action") not in action_types:
            continue
        results.append(a)
    return results


# ── Trigger conditions ────────────────────────────────────────────────────────
# Each returns True/False + a context dict with trigger-specific data.
# Signature: (region, world, registry, player_faction_id, event_log, action_log,
#             conquest_log, current_tick) → (bool, dict)


def trigger_defensive_stand(region, world, registry, player_faction_id,
                            event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    attacks = _recent_actions(action_log, target_region=region.id,
                              action_types=ATTACK_ACTIONS)
    # Exclude stale log entries where the player attacked this region when it was
    # enemy-owned — after territory flips those entries name the player as attacker.
    attacks = [a for a in attacks if a.get("faction_id") != player_faction_id]
    if not attacks:
        return False, {}
    top = max(attacks, key=lambda a: a.get("budget_committed", 0))
    return True, {
        "attacker_faction": top.get("faction_id"),
        "budget_committed": top.get("budget_committed", 0),
    }


def trigger_siege_breaking(region, world, registry, player_faction_id,
                           event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    hostiles = _hostile_neighbors(world, region, registry)
    high_mil_hostiles = [h for h in hostiles if h.fields["military"] > 50]
    if not high_mil_hostiles:
        return False, {}
    mil = region.fields["military"]
    eco = region.fields["economy"]
    held = region.held_since_tick or 0
    ticks_held = current_tick - held
    if ticks_held < config.SIEGE_BREAKING_MIN_TICKS:
        return False, {}
    if mil > 40 and eco > 40:
        return False, {}
    return True, {
        "hostile_neighbors": [h.id for h in high_mil_hostiles],
        "ticks_under_pressure": ticks_held,
    }


def trigger_reconquest(region, world, registry, player_faction_id,
                       event_log, action_log, conquest_log, current_tick):
    if region.faction_id == player_faction_id:
        return False, {}
    conquests = _recent_conquests(conquest_log, region_id=region.id,
                                  faction_id=player_faction_id)
    if not conquests:
        return False, {}
    return True, {
        "conquering_faction": region.faction_id,
        "previous_faction": player_faction_id,
    }


def trigger_assault(region, world, registry, player_faction_id,
                    event_log, action_log, conquest_log, current_tick):
    if region.faction_id == player_faction_id:
        return False, {}
    player_faction = registry.get(player_faction_id)
    if not player_faction:
        return False, {}
    stance = player_faction.diplomatic_stance.get(region.faction_id, "hostile")
    if stance != "hostile":
        return False, {}
    player_regions = _player_region_ids(world, player_faction_id)
    adjacent_to_player = False
    for pr_id in player_regions:
        if region.id in world.get_neighbors(pr_id):
            adjacent_to_player = True
            break
    if not adjacent_to_player:
        return False, {}
    mil = region.fields["military"]
    stability = region.composites.get("stability", 50)
    if mil > 60 and stability > 50:
        return False, {}
    return True, {
        "target_faction": region.faction_id,
        "target_military": mil,
        "target_stability": stability,
    }


def trigger_suppression(region, world, registry, player_faction_id,
                        event_log, action_log, conquest_log, current_tick):
    if region.faction_id == player_faction_id:
        return False, {}
    owner = registry.get(region.faction_id)
    if not owner or not owner.archetype.startswith("breakaway"):
        return False, {}
    held = region.held_since_tick or 0
    age = current_tick - held
    if age > config.SUPPRESSION_MAX_AGE:
        return False, {}
    player_regions = _player_region_ids(world, player_faction_id)
    adjacent = any(region.id in world.get_neighbors(pr_id) for pr_id in player_regions)
    if not adjacent:
        return False, {}
    return True, {
        "breakaway_faction": region.faction_id,
        "breakaway_age": age,
    }


def trigger_multi_front_defense(region, world, registry, player_faction_id,
                                event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    attacks = [a for a in _recent_actions(action_log, target_region=region.id,
               action_types=ATTACK_ACTIONS) if a.get("faction_id") != player_faction_id]
    hostiles = _hostile_neighbors(world, region, registry)
    high_mil_hostiles = [h for h in hostiles if h.fields["military"] > 50]
    attacking_factions = {a.get("faction_id") for a in attacks}
    hostile_faction_ids = {h.faction_id for h in high_mil_hostiles}
    threat_sources = attacking_factions | hostile_faction_ids
    if len(threat_sources) < 2:
        return False, {}
    return True, {
        "threat_factions": list(threat_sources),
        "attack_count": len(attacks),
    }


def trigger_interception(region, world, registry, player_faction_id,
                         event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    attacks = [a for a in _recent_actions(action_log, target_region=region.id,
               action_types=ATTACK_ACTIONS) if a.get("faction_id") != player_faction_id]
    if not attacks:
        return False, {}
    for attack in attacks:
        attacker_fid = attack.get("faction_id")
        if not attacker_fid:
            continue
        attacker_regions = [r.id for r in world.regions.values()
                           if r.faction_id == attacker_fid]
        adjacent_to_target = any(
            region.id in world.get_neighbors(ar_id) for ar_id in attacker_regions
        )
        if not adjacent_to_target:
            return True, {
                "attacker_faction": attacker_fid,
                "budget_committed": attack.get("budget_committed", 0),
            }
    return False, {}


def trigger_evacuation(region, world, registry, player_faction_id,
                       event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    mil = region.fields["military"]
    eco = region.fields["economy"]
    stab = region.composites.get("stability", 50)
    if (mil >= config.EVAC_MILITARY_THRESHOLD or
            eco >= config.EVAC_ECONOMY_THRESHOLD or
            stab >= config.EVAC_STABILITY_THRESHOLD):
        return False, {}
    hostiles = _hostile_neighbors(world, region, registry)
    high_mil_hostiles = [h for h in hostiles if h.fields["military"] > 50]
    if not high_mil_hostiles:
        return False, {}
    return True, {
        "region_military": mil,
        "region_economy": eco,
        "region_stability": stab,
        "hostile_neighbors": [h.id for h in high_mil_hostiles],
    }


def trigger_containment(region, world, registry, player_faction_id,
                        event_log, action_log, conquest_log, current_tick):
    if region.faction_id == player_faction_id:
        return False, {}
    owner = registry.get(region.faction_id)
    if not owner:
        return False, {}
    faction_conquests = _recent_conquests(conquest_log, faction_id=None)
    regions_gained = [c for c in faction_conquests
                      if c.get("new_faction_id") == region.faction_id]
    if len(regions_gained) < config.CONTAINMENT_EXPANSION_THRESHOLD:
        return False, {}
    player_regions = _player_region_ids(world, player_faction_id)
    adjacent = any(region.id in world.get_neighbors(pr_id) for pr_id in player_regions)
    if not adjacent:
        return False, {}
    return True, {
        "expanding_faction": region.faction_id,
        "regions_gained": len(regions_gained),
    }


def trigger_counterinsurgency(region, world, registry, player_faction_id,
                              event_log, action_log, conquest_log, current_tick):
    if region.faction_id != player_faction_id:
        return False, {}
    revolt_events = _recent_events(event_log, region_id=region.id,
                                    template_ids=REVOLT_EVENT_IDS)
    if not revolt_events:
        return False, {}
    return True, {
        "revolt_events": [e.get("template_id") for e in revolt_events],
    }


TRIGGER_FUNCTIONS = {
    "defensive_stand":     trigger_defensive_stand,
    "siege_breaking":      trigger_siege_breaking,
    "reconquest":          trigger_reconquest,
    "assault":             trigger_assault,
    "suppression":         trigger_suppression,
    "multi_front_defense": trigger_multi_front_defense,
    "interception":        trigger_interception,
    "evacuation":          trigger_evacuation,
    "containment":         trigger_containment,
    "counterinsurgency":   trigger_counterinsurgency,
}


# ── Scoring ───────────────────────────────────────────────────────────────────


def _clamp(lo, hi, val):
    return max(lo, min(hi, val))


def compute_urgency(region, world, registry, event_log, action_log,
                    conquest_log, current_tick):
    mil = region.fields["military"]
    eco = region.fields["economy"]
    stab = region.composites.get("stability", 50)
    field_deficit = ((100 - mil) / 100 + (100 - eco) / 100 + (100 - stab) / 100) / 3.0

    # Conflict intensity: three sub-signals per spec
    # 1. Hostile forces at borders — strongest hostile neighbor's military
    hostiles = _hostile_neighbors(world, region, registry)
    max_hostile_mil = max((h.fields["military"] for h in hostiles), default=0)
    border_threat = min(1.0, max_hostile_mil / 70.0)

    # 2. Recent attacks — count + committed budget strength
    attacks = _recent_actions(action_log, target_region=region.id,
                              action_types=ATTACK_ACTIONS)
    total_budget = sum(a.get("budget_committed", 0) for a in attacks)
    attack_pressure = min(1.0, len(attacks) * 0.5 + total_budget / 600.0)

    # 3. Territory recently lost — nearby regions conquered from this faction
    owner_fid = region.faction_id
    neighbors = set(world.get_neighbors(region.id))
    nearby_losses = sum(1 for c in conquest_log
                        if c.get("old_faction_id") == owner_fid
                        and c.get("region_id") in neighbors)
    territory_loss = min(1.0, nearby_losses * 0.5)

    # Additive stacking, clamped — multiple active threats compound
    conflict_intensity = _clamp(0, 1,
        border_threat + attack_pressure * 0.5 + territory_loss * 0.3)

    revolt_events = _recent_events(event_log, region_id=region.id,
                                    template_ids=REVOLT_EVENT_IDS)
    chain_criticality = _clamp(0, 1, len(revolt_events) * 0.3)

    return _clamp(0, 1,
        config.URGENCY_FIELD_WEIGHT * field_deficit +
        config.URGENCY_CONFLICT_WEIGHT * conflict_intensity +
        config.URGENCY_CHAIN_WEIGHT * chain_criticality
    )


def _shortest_path_hops(world, start_region, end_region):
    if start_region == end_region:
        return 0
    visited = {start_region}
    frontier = [start_region]
    hops = 0
    max_hops = config.RELEVANCE_MAX_HOPS
    while frontier and hops < max_hops:
        hops += 1
        next_frontier = []
        for rid in frontier:
            for nid in world.get_neighbors(rid):
                if nid == end_region:
                    return hops
                if nid not in visited:
                    visited.add(nid)
                    next_frontier.append(nid)
        frontier = next_frontier
    return max_hops


def compute_relevance(region, archetype, world, ledger, current_lineage_id):
    if not ledger or not current_lineage_id:
        return 0.0

    lineage_regions = ledger.get_lineage_history(current_lineage_id)
    if ledger.lineage_in_region(current_lineage_id, region.id):
        lineage_connection = 1.0
    elif region.id in lineage_regions:
        lineage_connection = 0.5
    else:
        lineage_connection = 0.0

    home_region = lineage_regions[0] if lineage_regions else None
    if home_region:
        hops = _shortest_path_hops(world, home_region, region.id)
        proximity = 1.0 - (hops / config.RELEVANCE_MAX_HOPS)
    else:
        proximity = 0.0

    archetype_history = {}
    if hasattr(ledger, 'get_lineage_archetype_history'):
        archetype_history = ledger.get_lineage_archetype_history(current_lineage_id)
    count = archetype_history.get(archetype, 0)
    archetype_fit = min(1.0, count / config.RELEVANCE_ARCHETYPE_FIT_THRESHOLD)

    return _clamp(0, 1,
        config.RELEVANCE_LINEAGE_WEIGHT * lineage_connection +
        config.RELEVANCE_PROXIMITY_WEIGHT * proximity +
        config.RELEVANCE_ARCHETYPE_WEIGHT * archetype_fit
    )


def compute_preference(archetype, player_preferences):
    if not player_preferences:
        return config.GENERATOR_DEFAULT_PREFERENCE
    pref = player_preferences.get(archetype)
    if pref is None:
        return config.GENERATOR_DEFAULT_PREFERENCE
    if pref == "rare":
        return config.GENERATOR_RARE_PREFERENCE
    return float(pref)


def build_candidate_pool(world, registry, player_faction_id, event_log,
                         action_log, conquest_log, current_tick):
    candidates = []
    all_region_ids = set()
    player_regions = _player_region_ids(world, player_faction_id)
    all_region_ids.update(player_regions)
    for pr_id in player_regions:
        for nid in world.get_neighbors(pr_id):
            all_region_ids.add(nid)

    for rid in all_region_ids:
        region = world.regions.get(rid)
        if not region or region.tier == "empty" if hasattr(region, 'tier') else False:
            continue
        for archetype, fn in TRIGGER_FUNCTIONS.items():
            fired, ctx = fn(region, world, registry, player_faction_id,
                            event_log, action_log, conquest_log, current_tick)
            if fired:
                candidates.append({
                    "region_id": rid,
                    "archetype": archetype,
                    "trigger_context": ctx,
                })
    return candidates


def score_candidates(candidates, world, registry, player_faction_id,
                     event_log, action_log, conquest_log, current_tick,
                     ledger=None, current_lineage_id=None,
                     player_preferences=None):
    scored = []
    for c in candidates:
        region = world.regions[c["region_id"]]
        urgency = compute_urgency(region, world, registry, event_log,
                                   action_log, conquest_log, current_tick)
        relevance = compute_relevance(region, c["archetype"], world,
                                       ledger, current_lineage_id)
        preference = compute_preference(c["archetype"], player_preferences)

        score = (config.GENERATOR_URGENCY_WEIGHT * urgency +
                 config.GENERATOR_RELEVANCE_WEIGHT * relevance +
                 config.GENERATOR_PREFERENCE_WEIGHT * preference)

        scored.append({
            **c,
            "urgency": urgency,
            "relevance": relevance,
            "preference": preference,
            "score": score,
        })

    scored.sort(key=lambda x: -x["score"])
    return scored


def select_mission(scored_candidates, rng):
    top_n = config.GENERATOR_TOP_N_CANDIDATES
    pool = scored_candidates[:top_n]
    if not pool:
        return None
    weights = [c["score"] for c in pool]
    total = sum(weights)
    if total <= 0:
        return rng.choice(pool)
    r = rng.random() * total
    cumulative = 0.0
    for c in pool:
        cumulative += c["score"]
        if r <= cumulative:
            return c
    return pool[-1]


ARCHETYPE_OBJECTIVES = {
    "defensive_stand":     [("defend_region", 0.6, True), ("destroy_attackers", 0.4, False)],
    "siege_breaking":      [("destroy_positions", 0.5, True), ("reopen_supply", 0.3, False), ("hold_ground", 0.2, False)],
    "reconquest":          [("destroy_garrison", 0.5, True), ("secure_region", 0.3, False), ("preserve_infrastructure", 0.2, False)],
    "assault":             [("destroy_defenders", 0.5, True), ("capture_region", 0.3, True), ("breach_fortifications", 0.2, False)],
    "suppression":         [("destroy_rebels", 0.6, True), ("secure_region", 0.4, False)],
    "multi_front_defense": [("hold_all_fronts", 0.4, True), ("destroy_primary_threat", 0.3, False), ("minimize_losses", 0.3, False)],
    "interception":        [("destroy_enemy_force", 0.6, True), ("prevent_breakthrough", 0.4, False)],
    "evacuation":          [("extract_assets", 0.5, True), ("delay_enemy", 0.3, False), ("protect_convoys", 0.2, False)],
    "containment":         [("hold_boundary", 0.5, True), ("prevent_expansion", 0.3, False), ("maintain_positions", 0.2, False)],
    "counterinsurgency":   [("eliminate_insurgents", 0.5, True), ("minimize_collateral", 0.3, False), ("restore_order", 0.2, False)],
}


def _build_objectives(archetype):
    specs = ARCHETYPE_OBJECTIVES.get(archetype, [("generic_objective", 1.0, True)])
    objectives = []
    for i, (obj_type, weight, is_primary) in enumerate(specs):
        objectives.append(ObjectiveSpec(
            id=f"obj_{archetype}_{i}",
            type=obj_type,
            weight=weight,
            params={},
            is_primary=is_primary,
        ))
    return objectives


def _field_descriptor(value):
    if value < 20:
        return "critically low"
    elif value < 35:
        return "dangerously low"
    elif value < 50:
        return "weakened"
    elif value < 65:
        return "moderate"
    elif value < 80:
        return "strong"
    return "robust"


def _build_variable_slots(candidate, region, world, registry, player_faction_id):
    slots = {
        "region_name": getattr(region, 'display_name', region.id),
        "region_id": region.id,
        "archetype": candidate["archetype"],
        "military_desc": _field_descriptor(region.fields.get("military", 50)),
        "economy_desc": _field_descriptor(region.fields.get("economy", 50)),
        "tension_desc": _field_descriptor(region.fields.get("tension", 50)),
        "military_value": region.fields.get("military", 50),
        "economy_value": region.fields.get("economy", 50),
        "tension_value": region.fields.get("tension", 50),
        "player_faction": player_faction_id,
    }
    player_faction = registry.get(player_faction_id)
    if player_faction:
        slots["player_faction_name"] = getattr(player_faction, 'display_name',
                                                getattr(player_faction, 'id', player_faction_id))

    ctx = candidate.get("trigger_context", {})
    enemy_fid = ctx.get("attacker_faction") or ctx.get("target_faction") or \
                ctx.get("conquering_faction") or ctx.get("breakaway_faction") or \
                ctx.get("expanding_faction")
    if enemy_fid:
        enemy_faction = registry.get(enemy_fid)
        slots["enemy_faction_name"] = getattr(enemy_faction, 'display_name',
                                               enemy_fid) if enemy_faction else enemy_fid
        slots["enemy_faction_id"] = enemy_fid

    for k, v in ctx.items():
        if k not in slots:
            slots[k] = v

    return slots


def generate_mission(world, registry, player_faction_id, event_log, action_log,
                     conquest_log, current_tick, difficulty, rng,
                     ledger=None, current_lineage_id=None,
                     player_preferences=None):
    candidates = build_candidate_pool(
        world, registry, player_faction_id, event_log, action_log,
        conquest_log, current_tick)
    if not candidates:
        return None

    scored = score_candidates(
        candidates, world, registry, player_faction_id,
        event_log, action_log, conquest_log, current_tick,
        ledger=ledger, current_lineage_id=current_lineage_id,
        player_preferences=player_preferences)

    selected = select_mission(scored, rng)
    if not selected:
        return None

    region = world.regions[selected["region_id"]]
    archetype = selected["archetype"]
    trigger_ctx = selected.get("trigger_context", {})

    capacity = region.composites.get("capacity", 0.5) if hasattr(region, 'composites') else 0.5
    capacity_norm = capacity / 100.0 if capacity > 1.0 else capacity

    enemy_fid = trigger_ctx.get("attacker_faction") or \
                trigger_ctx.get("target_faction") or \
                trigger_ctx.get("conquering_faction") or \
                trigger_ctx.get("breakaway_faction") or \
                trigger_ctx.get("expanding_faction") or \
                "enemy_faction"

    allocation = allocate_forces(
        archetype, trigger_ctx, region, capacity_norm,
        difficulty, player_faction_id, enemy_fid, rng)

    objectives = _build_objectives(archetype)
    variable_slots = _build_variable_slots(
        selected, region, world, registry, player_faction_id)

    variable_slots["player_units"] = len(allocation["player_force"].units)
    variable_slots["enemy_units"] = len(allocation["enemy_force"].units)
    variable_slots["player_power"] = allocation["player_force"].total_power
    variable_slots["enemy_power"] = allocation["enemy_force"].total_power
    variable_slots["parity_ratio"] = allocation["parity_ratio"]
    variable_slots["shortfall_types"] = allocation["shortfall_types"]
    variable_slots["reinforcements"] = allocation["reinforcements"]

    briefing = assemble_briefing(archetype, variable_slots)

    mission_id = f"mission_{archetype}_{selected['region_id']}_{current_tick}"

    setup = MissionSetup(
        mission_id=mission_id,
        archetype=archetype,
        region_id=selected["region_id"],
        map_params={},
        player_force=allocation["player_force"],
        enemy_forces=[allocation["enemy_force"]],
        objectives=objectives,
        reinforcements=allocation["reinforcements"],
        time_limit_ticks=config.ARCHETYPE_TIME_LIMITS.get(archetype, 300),
        behavior_script_id=f"behavior_{archetype}",
        briefing=briefing,
        difficulty=difficulty,
        metadata={
            "score": selected["score"],
            "urgency": selected["urgency"],
            "relevance": selected["relevance"],
            "preference": selected["preference"],
            "trigger_context": trigger_ctx,
            "parity_ratio": allocation["parity_ratio"],
        },
    )

    return {
        "setup": setup,
        "scored_candidates": scored,
        "selected": selected,
        "allocation": allocation,
    }
