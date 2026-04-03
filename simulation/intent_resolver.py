import config
import events as _events
import technology as _tech


def resolve(intents: list, snapshot: dict, registry: dict,
            rng, tick: int = 0) -> list:
    """Resolve intents against snapshot. Detects collisions (2+ intents targeting the same
    region) and routes them to _resolve_collision(). Non-colliding intents resolve normally.
    Does not mutate snapshot, registry, or any region."""

    # Group intents by target_region (None targets like accumulate are never collisions)
    by_target = {}
    for intent in intents:
        tgt = intent.get("target_region")
        if tgt is not None:
            by_target.setdefault(tgt, []).append(intent)

    collision_targets = {tgt for tgt, group in by_target.items() if len(group) >= 2}

    resolved = []
    for intent in intents:
        tgt = intent.get("target_region")
        if tgt in collision_targets:
            continue  # handled below as a group
        action = intent["action"]
        if action == "accumulate":
            resolved.append(_resolve_accumulate(intent))
        elif action == "reinforce":
            resolved.append(_resolve_reinforce(intent, snapshot, rng))
        elif action == "attack":
            resolved.append(_resolve_attack(intent, snapshot, registry, rng, tick))
        elif action == "colonize":
            resolved.append(_resolve_colonize(intent, snapshot))

    for tgt in collision_targets:
        resolved.extend(_resolve_collision(by_target[tgt], snapshot, registry, rng, tick))

    return resolved


def _resolve_collision(collision_intents: list, snapshot: dict, registry: dict,
                       rng, tick: int) -> list:
    # 1. Effective strength per participant
    faction_economies = {}
    for intent in collision_intents:
        fid = intent["faction_id"]
        faction_economies[fid] = sum(
            rd["fields"]["economy"]
            for rd in snapshot.values()
            if rd["faction_id"] == fid
        )

    max_economy = max(faction_economies.values()) if any(v > 0 for v in faction_economies.values()) else 1.0

    effective_strengths = []
    for intent in collision_intents:
        fid     = intent["faction_id"]
        commit  = intent["budget_committed"]
        eco     = faction_economies[fid]
        ratio   = eco / max_economy if max_economy > 0 else 1.0
        factor  = config.COLLISION_ECONOMY_FLOOR + (config.COLLISION_ECONOMY_CEILING - config.COLLISION_ECONOMY_FLOOR) * ratio
        atk_mult = 1.0
        if config.ENABLE_TECHNOLOGY:
            fac = registry.get(fid)
            if fac:
                atk_mult = _tech.get_tech_multipliers(fac.archetype, fac.tech_level)["attack"]
        effective_strengths.append(commit * config.ATTACK_EFFICIENCY * factor * atk_mult)

    # 2. Weighted probability draw
    total_str = sum(effective_strengths)
    weights   = [s / total_str for s in effective_strengths] if total_str > 0 else [1.0 / len(collision_intents)] * len(collision_intents)

    roll, cumulative, winner_index = rng.random(), 0.0, len(collision_intents) - 1
    for i, w in enumerate(weights):
        cumulative += w
        if roll < cumulative:
            winner_index = i
            break

    winner_intent  = collision_intents[winner_index]
    winner_fid     = winner_intent["faction_id"]
    winner_str     = effective_strengths[winner_index]
    winner_commit  = winner_intent["budget_committed"]
    loser_indices  = [i for i in range(len(collision_intents)) if i != winner_index]
    loser_strs     = [effective_strengths[i] for i in loser_indices]

    # 3. Victory margin
    second_best  = max(loser_strs) if loser_strs else 0.0
    margin_ratio = winner_str / (winner_str + second_best) if (winner_str + second_best) > 0 else 1.0

    # 4. Force retention for winner
    opp_ratio        = sum(loser_strs) / winner_str if winner_str > 0 else 0.0
    ret_ceiling      = config.COLLISION_RETENTION_MAX * max(0.0, 1.0 - opp_ratio * config.COLLISION_RETENTION_OPPOSITION_SCALE)
    ret_fraction     = rng.uniform(0.0, ret_ceiling)
    budget_refunded  = winner_commit * ret_fraction
    winner_spent     = winner_commit - budget_refunded

    # 5. Significance metadata
    player_fids = {fid for fid in faction_economies if registry.get(fid) and getattr(registry[fid], "archetype", "") == "player_civilization"}
    player_involved = bool(player_fids)
    player_underdog = False
    if player_involved:
        med = sorted(effective_strengths)[len(effective_strengths) // 2]
        player_idx   = next((i for i, intent in enumerate(collision_intents) if intent["faction_id"] in player_fids), None)
        if player_idx is not None:
            player_underdog = effective_strengths[player_idx] < med

    sig = {
        "significance":       "collision",
        "collision_size":     len(collision_intents),
        "factions_involved":  [i["faction_id"] for i in collision_intents],
        "winner":             winner_fid,
        "margin_ratio":       round(margin_ratio, 4),
        "player_involved":    player_involved,
        "player_was_underdog": player_underdog,
        "mission_candidate":  True,
    }

    # 6. Apply consequences
    tid          = winner_intent["target_region"]
    target_data  = snapshot[tid]
    target_owner = target_data["faction_id"]
    participant_fids = {i["faction_id"] for i in collision_intents}
    has_external_defender = (target_owner is not None and target_owner not in participant_fids)

    resolved = []

    if has_external_defender:
        mil_before = target_data["fields"]["military"]
        def_mult = 1.0
        if config.ENABLE_TECHNOLOGY:
            def_fac = registry.get(target_owner)
            if def_fac:
                def_mult = _tech.get_tech_multipliers(def_fac.archetype, def_fac.tech_level)["defense"]
        total_mil_dmg = total_eco_dmg = total_ten_dmg = total_pop_dmg = 0.0

        for i, intent in enumerate(collision_intents):
            ea  = effective_strengths[i]
            ed  = mil_before * config.RESISTANCE_FACTOR * def_mult
            net = (ea - ed) * rng.uniform(*config.STOCHASTIC_RANGE)
            if net > config.BREAKTHROUGH_THRESHOLD:
                total_mil_dmg += net * 0.8
                total_eco_dmg += net * 0.3
                total_ten_dmg += min(net * 0.5, 30.0)
            elif net > 0.0:
                total_mil_dmg += net * 0.5
                total_eco_dmg += net * 0.2
                total_ten_dmg += net * 0.4
            else:
                total_mil_dmg += ea * 0.10
                total_ten_dmg += 2.0

        mil_after    = max(0.0, mil_before - total_mil_dmg)
        conquest     = None
        chain_spawns = []
        bypass_floor = False

        if mil_after < config.CONQUEST_THRESHOLD:
            conquest = {
                "region_id":      tid,
                "new_faction_id": winner_fid,
                "old_faction_id": target_owner,
                "garrison":       winner_commit * config.CONQUEST_GARRISON_FRACTION,
            }
            total_eco_dmg += config.CONQUEST_ECONOMY_DISRUPTION
            total_ten_dmg += config.CONQUEST_TENSION_SPIKE
            total_pop_dmg += config.CONQUEST_POPULATION_LOSS
            bypass_floor   = True
            chain_tag      = _events._next_chain_tag()
            if rng.random() < 0.60:
                delay = round(rng.triangular(4, 8, 6))
                chain_spawns.append({
                    "template_id": "CONQUEST_UNREST",
                    "region_id":   tid,
                    "due_tick":    tick + delay,
                    "chain_tag":   chain_tag,
                    "probability": 1.0,
                    "conditions":  {},
                })

        deltas = {tid: {"military": -total_mil_dmg, "economy": -total_eco_dmg, "tension": +total_ten_dmg}}
        if total_pop_dmg:
            deltas[tid]["population"] = -total_pop_dmg

        resolved.append(_base(
            winner_intent,
            budget_spent=winner_spent,
            deltas=deltas,
            outcome_band="collision",
            conquest=conquest,
            chain_spawns=chain_spawns,
            significance="collision",
            log={**sig, "effective_strengths": [round(s, 4) for s in effective_strengths],
                 "opposition_ratio": round(opp_ratio, 4), "retention_ceiling": round(ret_ceiling, 4),
                 "retention_fraction": round(ret_fraction, 4), "budget_refunded": round(budget_refunded, 4),
                 "bypass_floor": bypass_floor},
        ))

    elif target_owner is not None:
        # Participant-owned — treat as attack, not colonization
        mil_before = target_data["fields"]["military"]
        def_mult = 1.0
        if config.ENABLE_TECHNOLOGY:
            def_fac = registry.get(target_owner)
            if def_fac:
                def_mult = _tech.get_tech_multipliers(def_fac.archetype, def_fac.tech_level)["defense"]
        total_mil_dmg = total_eco_dmg = total_ten_dmg = total_pop_dmg = 0.0

        for i, intent in enumerate(collision_intents):
            ea  = effective_strengths[i]
            ed  = mil_before * config.RESISTANCE_FACTOR * def_mult
            net = (ea - ed) * rng.uniform(*config.STOCHASTIC_RANGE)
            if net > config.BREAKTHROUGH_THRESHOLD:
                total_mil_dmg += net * 0.8
                total_eco_dmg += net * 0.3
                total_ten_dmg += min(net * 0.5, 30.0)
            elif net > 0.0:
                total_mil_dmg += net * 0.5
                total_eco_dmg += net * 0.2
                total_ten_dmg += net * 0.4
            else:
                total_mil_dmg += ea * 0.10
                total_ten_dmg += 2.0

        mil_after    = max(0.0, mil_before - total_mil_dmg)
        conquest     = None
        chain_spawns = []
        bypass_floor = False

        if mil_after < config.CONQUEST_THRESHOLD:
            conquest = {
                "region_id":      tid,
                "new_faction_id": winner_fid,
                "old_faction_id": target_owner,
                "garrison":       winner_commit * config.CONQUEST_GARRISON_FRACTION,
            }
            total_eco_dmg += config.CONQUEST_ECONOMY_DISRUPTION
            total_ten_dmg += config.CONQUEST_TENSION_SPIKE
            total_pop_dmg += config.CONQUEST_POPULATION_LOSS
            bypass_floor   = True
            chain_tag      = _events._next_chain_tag()
            if rng.random() < 0.60:
                delay = round(rng.triangular(4, 8, 6))
                chain_spawns.append({
                    "template_id": "CONQUEST_UNREST",
                    "region_id":   tid,
                    "due_tick":    tick + delay,
                    "chain_tag":   chain_tag,
                    "probability": 1.0,
                    "conditions":  {},
                })

        deltas = {tid: {"military": -total_mil_dmg, "economy": -total_eco_dmg, "tension": +total_ten_dmg}}
        if total_pop_dmg:
            deltas[tid]["population"] = -total_pop_dmg

        resolved.append(_base(
            winner_intent,
            budget_spent=winner_spent,
            deltas=deltas,
            outcome_band="collision",
            conquest=conquest,
            chain_spawns=chain_spawns,
            significance="collision",
            log={**sig, "effective_strengths": [round(s, 4) for s in effective_strengths],
                 "opposition_ratio": round(opp_ratio, 4), "retention_ceiling": round(ret_ceiling, 4),
                 "retention_fraction": round(ret_fraction, 4), "budget_refunded": round(budget_refunded, 4),
                 "bypass_floor": bypass_floor},
        ))

    else:
        # Uninhabited — colonize with margin modifier
        mil_start = config.COLONY_START_MILITARY
        if margin_ratio < config.COLLISION_NARROW_MARGIN:
            mil_start *= rng.uniform(config.COLLISION_NARROW_MIL_PENALTY, 0.70)

        resolved.append(_base(
            winner_intent,
            budget_spent=winner_spent,
            deltas={tid: {
                "military":   mil_start,
                "economy":    config.COLONY_START_ECONOMY,
                "tension":    config.COLONY_START_TENSION,
                "population": config.COLONY_START_POPULATION,
            }},
            outcome_band="collision",
            colonization={"region_id": tid, "faction_id": winner_fid},
            significance="collision",
            log={**sig, "effective_strengths": [round(s, 4) for s in effective_strengths],
                 "opposition_ratio": round(opp_ratio, 4), "retention_ceiling": round(ret_ceiling, 4),
                 "retention_fraction": round(ret_fraction, 4), "budget_refunded": round(budget_refunded, 4),
                 "mil_start": round(mil_start, 4)},
        ))

    # Losers: full budget spent + home tension hit
    for i in loser_indices:
        loser_intent  = collision_intents[i]
        loser_fid     = loser_intent["faction_id"]
        loser_commit  = loser_intent["budget_committed"]
        loser_faction = registry.get(loser_fid)
        total_budget  = loser_faction.budget if loser_faction else loser_commit
        tension_hit   = config.COLLISION_LOSER_TENSION_BASE * (loser_commit / total_budget) if total_budget > 0 else 0.0

        loser_owned = [(rid, rd) for rid, rd in snapshot.items() if rd["faction_id"] == loser_fid]
        loser_deltas = {}
        if loser_owned:
            home_rid = max(loser_owned, key=lambda x: x[1]["fields"]["military"])[0]
            loser_deltas = {home_rid: {"tension": tension_hit}}

        resolved.append(_base(
            loser_intent,
            budget_spent=loser_commit,
            deltas=loser_deltas,
            outcome_band="collision_loss",
            significance="collision",
            log={"significance": "collision", "winner": winner_fid,
                 "tension_hit": round(tension_hit, 4),
                 "home_region": list(loser_deltas.keys())[0] if loser_deltas else None},
        ))

    return resolved


def _base(intent, budget_spent, deltas, outcome_band=None, net_force=None,
          conquest=None, colonization=None, chain_spawns=None, significance=None,
          log=None):
    return {
        "faction_id":      intent["faction_id"],
        "action":          intent["action"],
        "target_region":   intent.get("target_region"),
        "budget_committed": intent.get("budget_committed", 0.0),
        "budget_spent":    budget_spent,
        "deltas":          deltas,
        "conquest":      conquest,
        "colonization":  colonization,
        "chain_spawns":  chain_spawns or [],
        "outcome_band":  outcome_band,
        "net_force":     net_force,
        "significance":  significance,
        "log":           log or {},
    }


def _resolve_accumulate(intent):
    return _base(intent, budget_spent=0.0, deltas={})


def _resolve_reinforce(intent, snapshot, rng):
    tid   = intent["target_region"]
    td    = snapshot[tid]
    mil   = td["fields"]["military"]
    ten   = td["fields"]["tension"]
    commit = intent["budget_committed"]

    tier_cap = config.REINFORCE_MIL_CAP.get(td["tier"], 100)
    headroom = max(0.0, (tier_cap - mil) / tier_cap)
    base_boost = commit * config.REINFORCE_EFFICIENCY * headroom

    ten_factor = ten / 100.0
    lo = config.REINFORCE_VARIANCE_BASE[0] - ten_factor * config.REINFORCE_VARIANCE_TENSION_SCALE
    hi = config.REINFORCE_VARIANCE_BASE[1] + ten_factor * config.REINFORCE_VARIANCE_TENSION_SCALE
    variance = rng.uniform(lo, hi)
    actual_boost = base_boost * variance

    return _base(
        intent,
        budget_spent=commit,
        deltas={tid: {"military": actual_boost}},
        log={
            "tier_cap": tier_cap, "headroom": round(headroom, 4),
            "base_boost": round(base_boost, 4),
            "variance": round(variance, 4),
            "actual_boost": round(actual_boost, 4),
        },
    )


def _resolve_attack(intent, snapshot, registry, rng, tick):
    tid     = intent["target_region"]
    td      = snapshot[tid]
    commit  = intent["budget_committed"]
    mil_before = td["fields"]["military"]

    atk_mult = def_mult = 1.0
    if config.ENABLE_TECHNOLOGY and registry:
        atk_fac = registry.get(intent["faction_id"])
        if atk_fac:
            atk_mult = _tech.get_tech_multipliers(atk_fac.archetype, atk_fac.tech_level)["attack"]
        def_fid = td["faction_id"]
        def_fac = registry.get(def_fid) if def_fid else None
        if def_fac:
            def_mult = _tech.get_tech_multipliers(def_fac.archetype, def_fac.tech_level)["defense"]

    effective_attack  = commit * config.ATTACK_EFFICIENCY * atk_mult
    effective_defense = mil_before * config.RESISTANCE_FACTOR * def_mult
    raw_net           = effective_attack - effective_defense
    stochastic        = rng.uniform(*config.STOCHASTIC_RANGE)
    net_force         = raw_net * stochastic

    if net_force > config.BREAKTHROUGH_THRESHOLD:
        outcome  = "breakthrough"
        mil_dmg  = net_force * 0.8
        eco_dmg  = net_force * 0.3
        ten_dmg  = min(net_force * 0.5, 30.0)
        pop_dmg  = 0.0
    elif net_force > 0.0:
        outcome  = "contested"
        mil_dmg  = net_force * 0.5
        eco_dmg  = net_force * 0.2
        ten_dmg  = net_force * 0.4
        pop_dmg  = 0.0
    else:
        outcome  = "repelled"
        mil_dmg  = effective_attack * 0.10
        eco_dmg  = 0.0
        ten_dmg  = 2.0
        pop_dmg  = 0.0

    mil_after = max(0.0, mil_before - mil_dmg)
    conquest  = None
    chain_spawns = []
    bypass_floor = False

    if outcome != "repelled" and mil_after < config.CONQUEST_THRESHOLD:
        old_fid = td["faction_id"]
        new_fid = intent["faction_id"]
        conquest = {
            "region_id":      tid,
            "new_faction_id": new_fid,
            "old_faction_id": old_fid,
            "garrison":       commit * config.CONQUEST_GARRISON_FRACTION,
        }
        eco_dmg  += config.CONQUEST_ECONOMY_DISRUPTION
        ten_dmg  += config.CONQUEST_TENSION_SPIKE
        pop_dmg  += config.CONQUEST_POPULATION_LOSS
        bypass_floor = True

        chain_tag = _events._next_chain_tag()
        if rng.random() < 0.60:
            delay = round(rng.triangular(4, 8, 6))
            chain_spawns.append({
                "template_id": "CONQUEST_UNREST",
                "region_id":   tid,
                "due_tick":    tick + delay,
                "chain_tag":   chain_tag,
                "probability": 1.0,
                "conditions":  {},
            })

    deltas = {tid: {
        "military":   -mil_dmg,
        "economy":    -eco_dmg,
        "tension":    +ten_dmg,
    }}
    if pop_dmg:
        deltas[tid]["population"] = -pop_dmg

    return _base(
        intent,
        budget_spent=commit,
        deltas=deltas,
        outcome_band=outcome,
        net_force=round(net_force, 4),
        conquest=conquest,
        chain_spawns=chain_spawns,
        significance=None,
        log={
            "effective_attack":  round(effective_attack, 4),
            "effective_defense": round(effective_defense, 4),
            "raw_net":           round(raw_net, 4),
            "stochastic":        round(stochastic, 4),
            "mil_before":        round(mil_before, 4),
            "mil_after":         round(mil_after, 4),
            "bypass_floor":      bypass_floor,
        },
    )


def _resolve_colonize(intent, snapshot):
    tid = intent["target_region"]
    return _base(
        intent,
        budget_spent=config.COLONIZE_COST,
        deltas={tid: {
            "military":   config.COLONY_START_MILITARY,
            "economy":    config.COLONY_START_ECONOMY,
            "tension":    config.COLONY_START_TENSION,
            "population": config.COLONY_START_POPULATION,
        }},
        colonization={"region_id": tid, "faction_id": intent["faction_id"]},
    )
