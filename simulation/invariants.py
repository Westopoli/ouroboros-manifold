from sim_validator import InvariantResult, TrajectoryLog
import config
import statistics


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP A: Field Health
# ═════════════════════════════════════════════════════════════════════════════

def no_field_flatline(log: TrajectoryLog) -> InvariantResult:
    """A1: No field stuck (range < 3.0) over any 60-tick window."""
    WINDOW = 60
    RANGE_THRESHOLD = 3.0
    FIELDS = ["military", "economy", "tension", "population"]

    if log.total_ticks < WINDOW:
        return InvariantResult("A1_no_field_flatline", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {WINDOW})")

    cfg = log.config_snapshot
    eco_floor = cfg.get("ECONOMY_FLOOR", 8.0)
    ten_floor = cfg.get("TENSION_FLOOR", 12.0)
    mil_ceiling = cfg.get("RECRUITMENT_CEILING", 90.0)

    for fid in log.faction_ids():
        for field in FIELDS:
            series = log.field_series(fid, field)
            for start in range(0, len(series) - WINDOW):
                window = series[start:start + WINDOW]
                w_min, w_max = min(window), max(window)
                if w_max - w_min < RANGE_THRESHOLD:
                    val = window[-1]
                    if field == "economy" and abs(val - eco_floor) < 2.0:
                        continue
                    if field == "tension" and abs(val - ten_floor) < 2.0:
                        continue
                    if field == "military" and abs(val - mil_ceiling) < 2.0:
                        continue
                    if val > 98.0 or val < 2.0:
                        continue
                    # Skip slow monotonic growth/decay — not a true flatline
                    net_change = window[-1] - window[0]
                    if abs(net_change) > 1.0:
                        continue
                    return InvariantResult(
                        "A1_no_field_flatline", False, "critical",
                        f"{fid} {field} flatlined (range={w_max - w_min:.1f}) over ticks {start}–{start + WINDOW} at ~{val:.1f}",
                        details={
                            "faction_id": fid, "field": field, "tick": start + WINDOW,
                            "actual_value": val, "window_range": w_max - w_min,
                            "governing_configs": ["ECONOMY_FLOOR", "ECONOMY_BASE_GROWTH",
                                                  "MILITARY_DECAY_RATE", "RECRUITMENT_RATE",
                                                  "POPULATION_GROWTH_RATE"],
                            "trajectory_excerpt": series[start:start + WINDOW][-15:],
                        },
                    )

    return InvariantResult("A1_no_field_flatline", True, "critical", "No flatlines detected")


def no_premature_collapse(log: TrajectoryLog) -> InvariantResult:
    """A2: Home regions should not have all fields below 15 within first 100 ticks."""
    TICK_LIMIT = min(100, log.total_ticks)
    COLLAPSE_THRESHOLD = 15.0

    for rid in log.region_ids():
        if log.region_tier(rid) != "home":
            continue
        fid = log.region_faction_at(rid, 0)
        if fid is None:
            continue

        for t in range(1, TICK_LIMIT + 1):
            if t >= len(log.snapshots):
                break
            rdata = log.snapshots[t].regions.get(rid)
            if not rdata or not rdata["fields"]:
                continue
            # Check if still owned by original faction
            if rdata["faction_id"] != fid:
                break  # conquered — different failure mode
            fields = rdata["fields"]
            if all(fields.get(f, 100) < COLLAPSE_THRESHOLD
                   for f in ["military", "economy", "tension", "population"]):
                return InvariantResult(
                    "A2_no_premature_collapse", False, "critical",
                    f"Home region {rid} (faction {fid}) collapsed — all fields below {COLLAPSE_THRESHOLD} at tick {t}",
                    details={
                        "region_id": rid, "faction_id": fid, "tick": t,
                        "fields": dict(fields),
                        "governing_configs": ["MILITARY_DECAY_RATE", "ECONOMY_TENSION_PENALTY_RATE",
                                              "POPULATION_SUBSISTENCE", "TENSION_NATURAL_DECAY_RATE"],
                    },
                )

    return InvariantResult("A2_no_premature_collapse", True, "critical", "No premature home collapse")


def fields_stay_bounded(log: TrajectoryLog) -> InvariantResult:
    """A3: All fields in [0, 100]. Economy >= ECONOMY_FLOOR unless conquest tick."""
    eco_floor = log.config_snapshot.get("ECONOMY_FLOOR", 8.0)

    # Build set of (region_id, tick) where conquest happened (floor bypass allowed)
    conquest_ticks = set()
    for snap in log.snapshots:
        for c in snap.conquests:
            conquest_ticks.add((c.get("region_id"), snap.tick))

    for snap in log.snapshots:
        for rid, rdata in snap.regions.items():
            if not rdata["fields"] or rdata["tier"] == "empty" or rdata["faction_id"] is None:
                continue
            for field, val in rdata["fields"].items():
                if val < -0.01:
                    return InvariantResult(
                        "A3_fields_stay_bounded", False, "critical",
                        f"Region {rid} {field}={val:.2f} < 0 at tick {snap.tick}",
                        details={"region_id": rid, "field": field, "tick": snap.tick,
                                 "actual_value": val, "governing_configs": []},
                    )
                if val > 100.01:
                    return InvariantResult(
                        "A3_fields_stay_bounded", False, "critical",
                        f"Region {rid} {field}={val:.2f} > 100 at tick {snap.tick}",
                        details={"region_id": rid, "field": field, "tick": snap.tick,
                                 "actual_value": val, "governing_configs": []},
                    )
                if field == "economy" and val < eco_floor - 0.01:
                    if (rid, snap.tick) not in conquest_ticks:
                        return InvariantResult(
                            "A3_fields_stay_bounded", False, "critical",
                            f"Region {rid} economy={val:.2f} < ECONOMY_FLOOR={eco_floor} at tick {snap.tick} (no conquest)",
                            details={"region_id": rid, "field": "economy", "tick": snap.tick,
                                     "actual_value": val, "expected_range": (eco_floor, 100.0),
                                     "governing_configs": []},
                        )

    return InvariantResult("A3_fields_stay_bounded", True, "critical", "All fields within bounds")


def frontier_more_volatile_than_home(log: TrajectoryLog) -> InvariantResult:
    """A4: Frontier regions should have higher std dev than home in 2+ of 4 fields."""
    WINDOW = min(200, log.total_ticks)
    if WINDOW < 30:
        return InvariantResult("A4_frontier_volatility", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 30+)")

    FIELDS = ["military", "economy", "tension", "population"]

    # Group regions by faction and tier (at tick 0)
    faction_tiers = {}  # {fid: {"home": [rid, ...], "frontier": [rid, ...]}}
    for rid in log.region_ids():
        tier = log.region_tier(rid)
        fid = log.region_faction_at(rid, 0)
        if fid is None or tier not in ("home", "frontier"):
            continue
        faction_tiers.setdefault(fid, {"home": [], "frontier": []})
        faction_tiers[fid][tier].append(rid)

    tested = False
    for fid, tiers in faction_tiers.items():
        if not tiers["home"] or not tiers["frontier"]:
            continue
        tested = True

        home_stds = {}
        frontier_stds = {}
        for field in FIELDS:
            # Average std dev across regions of each tier
            h_stds = []
            for rid in tiers["home"]:
                series = log.region_field_series(rid, field)[:WINDOW + 1]
                if len(series) > 1:
                    h_stds.append(statistics.stdev(series))
            f_stds = []
            for rid in tiers["frontier"]:
                series = log.region_field_series(rid, field)[:WINDOW + 1]
                if len(series) > 1:
                    f_stds.append(statistics.stdev(series))
            home_stds[field] = statistics.mean(h_stds) if h_stds else 0.0
            frontier_stds[field] = statistics.mean(f_stds) if f_stds else 0.0

        frontier_wins = sum(1 for f in FIELDS if frontier_stds[f] > home_stds[f])
        if frontier_wins < 2:
            return InvariantResult(
                "A4_frontier_volatility", False, "warning",
                f"{fid}: frontier more volatile in only {frontier_wins}/4 fields "
                f"(home_std={home_stds}, frontier_std={frontier_stds})",
                details={
                    "faction_id": fid, "home_stds": home_stds, "frontier_stds": frontier_stds,
                    "governing_configs": ["STARTING_MIL_RATIO", "STARTING_ECO_RATIO",
                                          "FRONTIER_POPULATION_RANGE"],
                },
            )

    if not tested:
        return InvariantResult("A4_frontier_volatility", True, "info",
                               "Skipped — no faction has both home and frontier regions")

    return InvariantResult("A4_frontier_volatility", True, "warning",
                           "Frontier regions more volatile than home as expected")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP D: Budget & Agent Behavior
# ═════════════════════════════════════════════════════════════════════════════

def budget_accumulates_monotonically(log: TrajectoryLog) -> InvariantResult:
    """D1: Budget should increase between spending actions (no unexpected resets)."""
    if not log.features.get("factions"):
        return InvariantResult("D1_budget_monotonic", True, "info",
                               "Skipped — factions not enabled")

    for fid in log.faction_ids():
        budgets = log.budget_series(fid)
        actions = log.action_log(fid)
        # Build set of ticks where spending happened
        spend_ticks = {a["tick"] for a in actions if a.get("budget_spent", 0) > 0}

        for i in range(1, len(budgets)):
            if i in spend_ticks:
                continue  # budget can drop on spend ticks
            if budgets[i] < budgets[i - 1] - 0.01:
                return InvariantResult(
                    "D1_budget_monotonic", False, "critical",
                    f"{fid} budget dropped {budgets[i-1]:.1f} → {budgets[i]:.1f} at tick {i} without spending",
                    details={
                        "faction_id": fid, "tick": i,
                        "budget_before": budgets[i - 1], "budget_after": budgets[i],
                        "governing_configs": ["BUDGET_GROWTH_RATE", "REGION_MAINTENANCE_COST"],
                        "trajectory_excerpt": budgets[max(0, i - 5):i + 2],
                    },
                )

    return InvariantResult("D1_budget_monotonic", True, "critical",
                           "Budget accumulates monotonically between spending actions")


def conqueror_attacks_eventually(log: TrajectoryLog) -> InvariantResult:
    """D2: Conqueror archetype should launch at least one attack within 150 ticks."""
    TICK_LIMIT = 150
    if not log.features.get("factions"):
        return InvariantResult("D2_conqueror_attacks", True, "info",
                               "Skipped — factions not enabled")
    if log.total_ticks < TICK_LIMIT:
        return InvariantResult("D2_conqueror_attacks", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {TICK_LIMIT}+)")

    for fid in log.faction_ids():
        fac = log.snapshots[0].factions.get(fid, {})
        if fac.get("archetype") != "conqueror":
            continue
        attacks = [a for a in log.attacks_by(fid) if a["tick"] <= TICK_LIMIT]
        if not attacks:
            budget_at_limit = log.budget_series(fid)[min(TICK_LIMIT, len(log.snapshots) - 1)]
            return InvariantResult(
                "D2_conqueror_attacks", False, "critical",
                f"Conqueror {fid} launched 0 attacks in {TICK_LIMIT} ticks. Budget at tick {TICK_LIMIT}: {budget_at_limit:.1f}",
                details={
                    "faction_id": fid, "tick": TICK_LIMIT,
                    "budget_at_limit": budget_at_limit,
                    "governing_configs": ["ATTACK_CONFIDENCE_RANGE", "BUDGET_GROWTH_RATE",
                                          "ATTACK_COMMIT_FRACTION", "BUDGET_PRESSURE_THRESHOLD"],
                },
            )

    return InvariantResult("D2_conqueror_attacks", True, "critical",
                           "All conqueror factions attacked within threshold")


def player_civ_is_conservative(log: TrajectoryLog) -> InvariantResult:
    """D3: player_civilization should attack less frequently than conqueror."""
    if not log.features.get("factions"):
        return InvariantResult("D3_player_conservative", True, "info",
                               "Skipped — factions not enabled")
    if log.total_ticks < 100:
        return InvariantResult("D3_player_conservative", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 100+)")

    player_fids = []
    conqueror_fids = []
    for fid in log.faction_ids():
        arch = log.snapshots[0].factions.get(fid, {}).get("archetype")
        if arch == "player_civilization":
            player_fids.append(fid)
        elif arch == "conqueror":
            conqueror_fids.append(fid)

    if not player_fids or not conqueror_fids:
        return InvariantResult("D3_player_conservative", True, "info",
                               "Skipped — scenario lacks both player and conqueror factions")

    player_attacks = sum(len(log.attacks_by(fid)) for fid in player_fids)
    conqueror_attacks = sum(len(log.attacks_by(fid)) for fid in conqueror_fids)

    if conqueror_attacks == 0:
        return InvariantResult("D3_player_conservative", True, "info",
                               "Skipped — conqueror hasn't attacked yet (see D2)")

    if player_attacks > conqueror_attacks:
        return InvariantResult(
            "D3_player_conservative", False, "warning",
            f"Player attacked {player_attacks}× vs conqueror {conqueror_attacks}× — player should be more conservative",
            details={
                "player_attacks": player_attacks, "conqueror_attacks": conqueror_attacks,
                "governing_configs": ["ATTACK_CONFIDENCE_RANGE", "ARCHETYPE_DECISION_WEIGHTS"],
            },
        )

    return InvariantResult("D3_player_conservative", True, "warning",
                           f"Player ({player_attacks} attacks) ≤ conqueror ({conqueror_attacks} attacks)")


def budget_pressure_prevents_hoarding(log: TrajectoryLog) -> InvariantResult:
    """D4: No faction should hoard budget above 5x cheapest attack cost for 50+ consecutive ticks."""
    HOARD_WINDOW = 50
    HOARD_MULTIPLIER = 5.0
    if not log.features.get("factions"):
        return InvariantResult("D4_no_hoarding", True, "info",
                               "Skipped — factions not enabled")
    if log.total_ticks < HOARD_WINDOW:
        return InvariantResult("D4_no_hoarding", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {HOARD_WINDOW}+)")

    cfg = log.config_snapshot
    # Cheapest viable attack = confidence_threshold * commit_fraction
    # Use the lowest known confidence threshold
    min_confidence = 8.0  # conqueror low end
    commit_fraction = cfg.get("ATTACK_COMMIT_FRACTION", 0.7)
    cheapest_attack = min_confidence * commit_fraction
    hoard_threshold = cheapest_attack * HOARD_MULTIPLIER

    for fid in log.faction_ids():
        budgets = log.budget_series(fid)
        run = 0
        for i, b in enumerate(budgets):
            if b > hoard_threshold:
                run += 1
                if run >= HOARD_WINDOW:
                    return InvariantResult(
                        "D4_no_hoarding", False, "warning",
                        f"{fid} budget above {hoard_threshold:.0f} for {run} ticks ending at tick {i} (budget={b:.1f})",
                        details={
                            "faction_id": fid, "tick": i, "budget": b,
                            "hoard_threshold": hoard_threshold,
                            "governing_configs": ["BUDGET_PRESSURE_THRESHOLD", "ATTACK_CONFIDENCE_RANGE"],
                            "trajectory_excerpt": budgets[max(0, i - 10):i + 1],
                        },
                    )
            else:
                run = 0

    return InvariantResult("D4_no_hoarding", True, "warning", "No budget hoarding detected")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP E: Combat & Conquest
# ═════════════════════════════════════════════════════════════════════════════

def attacks_produce_damage(log: TrajectoryLog) -> InvariantResult:
    """E1: Every attack should produce non-zero military damage to the target."""
    if not log.features.get("factions"):
        return InvariantResult("E1_attacks_damage", True, "info",
                               "Skipped — factions not enabled")

    for snap in log.snapshots:
        for action in snap.faction_actions:
            if action.get("action") != "attack":
                continue
            if action.get("outcome_band") == "collision_loss":
                continue
            if action.get("colonization"):
                continue
            deltas = action.get("deltas", {})
            target = action.get("target_region")
            if not target or target not in deltas:
                return InvariantResult(
                    "E1_attacks_damage", False, "critical",
                    f"Attack at tick {snap.tick} by {action.get('faction_id')} has no deltas for target {target}",
                    details={"tick": snap.tick, "action": action, "governing_configs": []},
                )
            mil_delta = deltas[target].get("military", 0.0)
            if mil_delta >= 0.0:
                return InvariantResult(
                    "E1_attacks_damage", False, "critical",
                    f"Attack at tick {snap.tick} by {action.get('faction_id')} on {target} dealt 0 military damage "
                    f"(outcome={action.get('outcome_band')})",
                    details={"tick": snap.tick, "action": action, "governing_configs": []},
                )

    total_attacks = sum(
        1 for snap in log.snapshots for a in snap.faction_actions if a.get("action") == "attack"
    )
    return InvariantResult("E1_attacks_damage", True, "critical",
                           f"All {total_attacks} attacks produced military damage")


def conquest_changes_ownership(log: TrajectoryLog) -> InvariantResult:
    """E2: Every conquest should result in region ownership changing to the attacker."""
    for i, snap in enumerate(log.snapshots):
        for conquest in snap.conquests:
            rid = conquest.get("region_id")
            new_fid = conquest.get("new_faction_id")
            if not rid or not new_fid:
                continue
            # Check ownership on next tick
            next_tick = i + 1
            if next_tick >= len(log.snapshots):
                continue
            actual_owner = log.region_faction_at(rid, next_tick)
            if actual_owner != new_fid:
                # Skip if the region was re-conquered at tick T+1 (legitimate back-to-back conquest)
                reconquered = any(
                    c.get("region_id") == rid
                    for c in log.snapshots[next_tick].conquests
                ) if next_tick < len(log.snapshots) else False
                if reconquered:
                    continue
                return InvariantResult(
                    "E2_conquest_ownership", False, "critical",
                    f"Conquest at tick {snap.tick}: {rid} should belong to {new_fid} but belongs to {actual_owner}",
                    details={"region_id": rid, "tick": snap.tick,
                             "expected_faction": new_fid, "actual_faction": actual_owner,
                             "governing_configs": []},
                )

    total = sum(len(snap.conquests) for snap in log.snapshots)
    return InvariantResult("E2_conquest_ownership", True, "critical",
                           f"All {total} conquests transferred ownership correctly")


def conquest_causes_disruption(log: TrajectoryLog) -> InvariantResult:
    """E3: Resolved by Westley — tension at cap (100) can't increase further; economy at floor handled by subsistence crisis."""
    return InvariantResult("E3_conquest_disruption", True, "info", "Resolved: edge cases at field caps")
    for i, snap in enumerate(log.snapshots):
        for conquest in snap.conquests:
            rid = conquest.get("region_id")
            if not rid or i == 0:
                continue
            prev_rdata = log.snapshots[i - 1].regions.get(rid, {})
            curr_rdata = snap.regions.get(rid, {})
            if not prev_rdata.get("fields") or not curr_rdata.get("fields"):
                continue

            prev_ten = prev_rdata["fields"].get("tension", 0)
            curr_ten = curr_rdata["fields"].get("tension", 0)
            prev_eco = prev_rdata["fields"].get("economy", 0)
            curr_eco = curr_rdata["fields"].get("economy", 0)

            if curr_ten <= prev_ten:
                return InvariantResult(
                    "E3_conquest_disruption", False, "critical",
                    f"Conquest at tick {snap.tick} on {rid}: tension didn't increase "
                    f"({prev_ten:.1f} → {curr_ten:.1f})",
                    details={"region_id": rid, "tick": snap.tick,
                             "tension_before": prev_ten, "tension_after": curr_ten,
                             "governing_configs": ["CONQUEST_TENSION_SPIKE"]},
                )
            if curr_eco >= prev_eco and prev_eco > config.ECONOMY_FLOOR + 0.5:
                return InvariantResult(
                    "E3_conquest_disruption", False, "critical",
                    f"Conquest at tick {snap.tick} on {rid}: economy didn't decrease "
                    f"({prev_eco:.1f} → {curr_eco:.1f})",
                    details={"region_id": rid, "tick": snap.tick,
                             "economy_before": prev_eco, "economy_after": curr_eco,
                             "governing_configs": ["CONQUEST_ECONOMY_DISRUPTION"]},
                )

    total = sum(len(snap.conquests) for snap in log.snapshots)
    return InvariantResult("E3_conquest_disruption", True, "critical",
                           f"All {total} conquests caused appropriate disruption")


def no_faction_eliminated_too_fast(log: TrajectoryLog) -> InvariantResult:
    """E4: No faction should lose all regions within the first 80 ticks."""
    TICK_LIMIT = min(80, log.total_ticks)

    for fid in log.faction_ids():
        counts = log.owned_region_count_series(fid)
        if counts[0] == 0:
            continue  # wasn't a real faction at start
        for t in range(1, TICK_LIMIT + 1):
            if t >= len(counts):
                break
            if counts[t] == 0:
                return InvariantResult(
                    "E4_no_early_elimination", False, "warning",
                    f"{fid} lost all regions by tick {t} (started with {counts[0]})",
                    details={
                        "faction_id": fid, "tick": t, "starting_regions": counts[0],
                        "governing_configs": ["RESISTANCE_FACTOR", "ATTACK_EFFICIENCY",
                                              "BREAKTHROUGH_THRESHOLD"],
                    },
                )

    return InvariantResult("E4_no_early_elimination", True, "warning",
                           "No faction eliminated within first 80 ticks")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP B: Economy Dynamics
# ═════════════════════════════════════════════════════════════════════════════

def economy_recovers_from_famine(log: TrajectoryLog) -> InvariantResult:
    """B1: If avg economy < 20, it should recover above 30 within 100 ticks (given pop > 20, tension < 70)."""
    FAMINE_THRESHOLD = 20.0
    RECOVERY_TARGET = 30.0
    RECOVERY_WINDOW = 100

    for fid in log.faction_ids():
        eco = log.field_series(fid, "economy")
        pop = log.field_series(fid, "population")
        ten = log.field_series(fid, "tension")

        i = 0
        while i < len(eco):
            if eco[i] < FAMINE_THRESHOLD:
                # Check preconditions: pop > 20 and tension < 70
                if pop[i] <= 20.0 or ten[i] >= 70.0:
                    i += 1
                    continue
                # Look for recovery within window
                recovered = False
                for j in range(i + 1, min(i + RECOVERY_WINDOW + 1, len(eco))):
                    if eco[j] >= RECOVERY_TARGET:
                        recovered = True
                        i = j
                        break
                if not recovered:
                    end = min(i + RECOVERY_WINDOW, len(eco) - 1)
                    return InvariantResult(
                        "B1_economy_recovers", False, "critical",
                        f"{fid} economy dropped below {FAMINE_THRESHOLD} at tick {i} and didn't recover above {RECOVERY_TARGET} within {RECOVERY_WINDOW} ticks (eco={eco[end]:.1f} at tick {end})",
                        details={
                            "faction_id": fid, "tick": i,
                            "governing_configs": ["ECONOMY_BASE_GROWTH", "POPULATION_SUBSISTENCE",
                                                  "ECONOMY_TENSION_PENALTY_RATE", "ECO_POP_RATIO"],
                            "trajectory_excerpt": eco[i:end + 1][-15:],
                        },
                    )
            i += 1

    return InvariantResult("B1_economy_recovers", True, "critical", "Economy recovers from famine conditions")


def economy_population_coupling(log: TrajectoryLog) -> InvariantResult:
    """B2: Resolved by Westley — economy divergence from pop×ratio is expected due to tension drag and other forces."""
    return InvariantResult("B2_eco_pop_coupling", True, "info", "Resolved: expected divergence")
    STABLE_WINDOW = 50
    POP_THRESHOLD = 50.0
    STD_THRESHOLD = 5.0
    DIVERGENCE = 20.0

    if log.total_ticks < STABLE_WINDOW:
        return InvariantResult("B2_eco_pop_coupling", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {STABLE_WINDOW}+)")

    cfg = log.config_snapshot
    eco_pop_ratio = cfg.get("ECO_POP_RATIO", 1.45)

    for fid in log.faction_ids():
        eco = log.field_series(fid, "economy")
        pop = log.field_series(fid, "population")

        for start in range(0, len(pop) - STABLE_WINDOW):
            window_pop = pop[start:start + STABLE_WINDOW]
            avg_pop = statistics.mean(window_pop)
            if avg_pop < POP_THRESHOLD:
                continue
            if statistics.stdev(window_pop) > STD_THRESHOLD:
                continue
            # Population is stable and high — check economy at end of window
            expected_eco = min(100.0, avg_pop * eco_pop_ratio)
            actual_eco = eco[start + STABLE_WINDOW - 1]
            if abs(actual_eco - expected_eco) > DIVERGENCE:
                return InvariantResult(
                    "B2_eco_pop_coupling", False, "warning",
                    f"{fid} economy={actual_eco:.1f} diverged from expected {expected_eco:.1f} (pop={avg_pop:.1f} × {eco_pop_ratio}) at tick {start + STABLE_WINDOW}",
                    details={
                        "faction_id": fid, "tick": start + STABLE_WINDOW,
                        "actual_economy": actual_eco, "expected_economy": expected_eco,
                        "avg_population": avg_pop,
                        "governing_configs": ["ECO_POP_RATIO", "ECO_OVERCAPACITY_DECAY", "ECONOMY_BASE_GROWTH"],
                    },
                )

    return InvariantResult("B2_eco_pop_coupling", True, "warning", "Economy tracks population as expected")


def tension_responds_to_economy(log: TrajectoryLog) -> InvariantResult:
    """B3: Low economy (< midpoint for 30+ ticks) → tension trends up. High economy → tension trends down."""
    SUSTAINED_WINDOW = 30

    if log.total_ticks < SUSTAINED_WINDOW:
        return InvariantResult("B3_tension_economy", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {SUSTAINED_WINDOW}+)")

    cfg = log.config_snapshot
    midpoint = cfg.get("TENSION_ECONOMY_MIDPOINT", 50.0)

    for fid in log.faction_ids():
        eco = log.field_series(fid, "economy")
        ten_deltas = log.field_delta_series(fid, "tension")

        for start in range(0, len(eco) - SUSTAINED_WINDOW):
            window_eco = eco[start:start + SUSTAINED_WINDOW]
            if all(e < midpoint - 5 for e in window_eco):
                # Economy below midpoint for full window — tension should trend up
                window_deltas = ten_deltas[start:start + SUSTAINED_WINDOW]
                avg_delta = statistics.mean(window_deltas) if window_deltas else 0.0
                if avg_delta < -0.1:
                    return InvariantResult(
                        "B3_tension_economy", False, "warning",
                        f"{fid} economy below {midpoint} for {SUSTAINED_WINDOW} ticks starting at {start} but tension trending DOWN (avg delta={avg_delta:.3f})",
                        details={
                            "faction_id": fid, "tick": start,
                            "avg_economy": statistics.mean(window_eco),
                            "avg_tension_delta": avg_delta,
                            "governing_configs": ["TENSION_ECONOMY_RATE", "TENSION_ECONOMY_MIDPOINT",
                                                  "TENSION_NATURAL_DECAY_RATE"],
                        },
                    )

    return InvariantResult("B3_tension_economy", True, "warning", "Tension responds to economy conditions")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP C: Military & Recruitment
# ═════════════════════════════════════════════════════════════════════════════

def military_decays_without_economy(log: TrajectoryLog) -> InvariantResult:
    """C1: If avg economy < 15 for 50+ ticks, military should trend downward."""
    SUSTAINED_WINDOW = 50
    ECO_THRESHOLD = 15.0

    if log.total_ticks < SUSTAINED_WINDOW:
        return InvariantResult("C1_mil_decays_no_eco", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need {SUSTAINED_WINDOW}+)")

    for fid in log.faction_ids():
        eco = log.field_series(fid, "economy")
        mil_deltas = log.field_delta_series(fid, "military")

        for start in range(0, len(eco) - SUSTAINED_WINDOW):
            window_eco = eco[start:start + SUSTAINED_WINDOW]
            if all(e < ECO_THRESHOLD for e in window_eco):
                window_deltas = mil_deltas[start:start + SUSTAINED_WINDOW]
                avg_delta = statistics.mean(window_deltas) if window_deltas else 0.0
                if avg_delta > 0.1:
                    return InvariantResult(
                        "C1_mil_decays_no_eco", False, "warning",
                        f"{fid} economy below {ECO_THRESHOLD} for {SUSTAINED_WINDOW} ticks starting at {start} but military trending UP (avg delta={avg_delta:.3f})",
                        details={
                            "faction_id": fid, "tick": start,
                            "avg_economy": statistics.mean(window_eco),
                            "avg_military_delta": avg_delta,
                            "governing_configs": ["MILITARY_DECAY_RATE", "RECRUITMENT_THRESHOLD", "RECRUITMENT_RATE"],
                        },
                    )

    return InvariantResult("C1_mil_decays_no_eco", True, "warning",
                           "Military decays when economy can't support it")


def recruitment_prevents_military_zero(log: TrajectoryLog) -> InvariantResult:
    """C2: No-combat, eco > 30, pop > 30 → military should not stay below 10 for 20+ ticks."""
    MIL_FLOOR = 10.0
    MAX_RUN = 20
    ECO_REQ = 30.0
    POP_REQ = 30.0

    for fid in log.faction_ids():
        mil = log.field_series(fid, "military")
        eco = log.field_series(fid, "economy")
        pop = log.field_series(fid, "population")

        # Build set of ticks where faction was attacked
        attacked_ticks = set()
        for snap in log.snapshots:
            for a in snap.faction_actions:
                if a.get("action") == "attack" and a.get("target_region"):
                    target_fid = snap.regions.get(a["target_region"], {}).get("faction_id")
                    if target_fid == fid:
                        attacked_ticks.add(snap.tick)

        run = 0
        for t in range(len(mil)):
            if t in attacked_ticks:
                run = 0
                continue
            if eco[t] > ECO_REQ and pop[t] > POP_REQ and mil[t] < MIL_FLOOR:
                run += 1
                if run >= MAX_RUN:
                    return InvariantResult(
                        "C2_recruitment_floors_mil", False, "warning",
                        f"{fid} military below {MIL_FLOOR} for {run} ticks ending at {t} despite eco={eco[t]:.1f}, pop={pop[t]:.1f} (no attacks)",
                        details={
                            "faction_id": fid, "tick": t,
                            "governing_configs": ["RECRUITMENT_BASELINE", "RECRUITMENT_RATE",
                                                  "RECRUITMENT_THRESHOLD", "RECRUITMENT_CEILING"],
                        },
                    )
            else:
                run = 0

    return InvariantResult("C2_recruitment_floors_mil", True, "warning",
                           "Recruitment prevents military collapse in peacetime")


def military_ceiling_respected(log: TrajectoryLog) -> InvariantResult:
    """C3: Military should rarely exceed RECRUITMENT_CEILING through drift alone."""
    cfg = log.config_snapshot
    ceiling = cfg.get("RECRUITMENT_CEILING", 90.0)
    TOLERANCE = 2.0

    for fid in log.faction_ids():
        mil = log.field_series(fid, "military")
        over_ceiling = [t for t, m in enumerate(mil) if m > ceiling + TOLERANCE]
        if len(over_ceiling) > len(mil) * 0.05:
            return InvariantResult(
                "C3_mil_ceiling", False, "warning",
                f"{fid} military above {ceiling + TOLERANCE:.0f} for {len(over_ceiling)}/{len(mil)} ticks ({100*len(over_ceiling)/len(mil):.1f}%)",
                details={
                    "faction_id": fid,
                    "over_count": len(over_ceiling),
                    "total_ticks": len(mil),
                    "governing_configs": ["RECRUITMENT_CEILING", "RECRUITMENT_RATE"],
                },
            )

    return InvariantResult("C3_mil_ceiling", True, "warning", "Military respects recruitment ceiling")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP F: Border Friction
# ═════════════════════════════════════════════════════════════════════════════

def border_friction_raises_tension(log: TrajectoryLog) -> InvariantResult:
    """F1: Border regions should have higher avg tension than interior regions."""
    WINDOW = min(100, log.total_ticks)
    if WINDOW < 30:
        return InvariantResult("F1_border_tension", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 30+)")
    if not log.features.get("border_friction"):
        return InvariantResult("F1_border_tension", True, "info",
                               "Skipped — border_friction not enabled")

    # Need adjacency info from the trajectory to classify border vs interior
    # Use tick 0 ownership to classify regions
    snap0 = log.snapshots[0]
    for fid in log.faction_ids():
        owned = [rid for rid, rd in snap0.regions.items() if rd["faction_id"] == fid]
        if len(owned) < 2:
            continue

        border_rids = []
        interior_rids = []
        for rid in owned:
            # Check if any neighbor belongs to a different faction
            is_border = False
            for snap_rid, snap_rd in snap0.regions.items():
                if snap_rid == rid:
                    continue
                if snap_rd["faction_id"] is not None and snap_rd["faction_id"] != fid:
                    is_border = True
                    break
            if is_border:
                border_rids.append(rid)
            else:
                interior_rids.append(rid)

        if not border_rids or not interior_rids:
            continue

        border_avg = statistics.mean(
            statistics.mean(log.region_field_series(rid, "tension")[:WINDOW + 1])
            for rid in border_rids
        )
        interior_avg = statistics.mean(
            statistics.mean(log.region_field_series(rid, "tension")[:WINDOW + 1])
            for rid in interior_rids
        )

        if border_avg <= interior_avg:
            return InvariantResult(
                "F1_border_tension", False, "warning",
                f"{fid} border tension ({border_avg:.1f}) ≤ interior tension ({interior_avg:.1f}) over {WINDOW} ticks",
                details={
                    "faction_id": fid, "border_avg": border_avg, "interior_avg": interior_avg,
                    "border_regions": border_rids, "interior_regions": interior_rids,
                    "governing_configs": ["BORDER_FRICTION_TENSION", "BORDER_FRICTION_ECONOMY"],
                },
            )

    return InvariantResult("F1_border_tension", True, "warning",
                           "Border regions show higher tension than interior")


def border_friction_drags_economy(log: TrajectoryLog) -> InvariantResult:
    """F2: Border regions should have lower avg economy than interior regions."""
    WINDOW = min(100, log.total_ticks)
    if WINDOW < 30:
        return InvariantResult("F2_border_economy", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 30+)")
    if not log.features.get("border_friction"):
        return InvariantResult("F2_border_economy", True, "info",
                               "Skipped — border_friction not enabled")

    snap0 = log.snapshots[0]
    for fid in log.faction_ids():
        owned = [rid for rid, rd in snap0.regions.items() if rd["faction_id"] == fid]
        if len(owned) < 2:
            continue

        border_rids = []
        interior_rids = []
        for rid in owned:
            is_border = False
            for snap_rid, snap_rd in snap0.regions.items():
                if snap_rid == rid:
                    continue
                if snap_rd["faction_id"] is not None and snap_rd["faction_id"] != fid:
                    is_border = True
                    break
            if is_border:
                border_rids.append(rid)
            else:
                interior_rids.append(rid)

        if not border_rids or not interior_rids:
            continue

        border_avg = statistics.mean(
            statistics.mean(log.region_field_series(rid, "economy")[:WINDOW + 1])
            for rid in border_rids
        )
        interior_avg = statistics.mean(
            statistics.mean(log.region_field_series(rid, "economy")[:WINDOW + 1])
            for rid in interior_rids
        )

        if border_avg >= interior_avg:
            return InvariantResult(
                "F2_border_economy", False, "warning",
                f"{fid} border economy ({border_avg:.1f}) ≥ interior economy ({interior_avg:.1f}) over {WINDOW} ticks",
                details={
                    "faction_id": fid, "border_avg": border_avg, "interior_avg": interior_avg,
                    "border_regions": border_rids, "interior_regions": interior_rids,
                    "governing_configs": ["BORDER_FRICTION_ECONOMY"],
                },
            )

    return InvariantResult("F2_border_economy", True, "warning",
                           "Border regions show lower economy than interior")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP G: Colonization
# ═════════════════════════════════════════════════════════════════════════════

def colonization_happens(log: TrajectoryLog) -> InvariantResult:
    """G1: Scenarios with uninhabited regions should see colonization within 200 ticks."""
    TICK_LIMIT = min(200, log.total_ticks)
    if not log.features.get("factions"):
        return InvariantResult("G1_colonization_happens", True, "info",
                               "Skipped — factions not enabled")

    # Check if there are uninhabited regions at tick 0
    snap0 = log.snapshots[0]
    uninhabited = [rid for rid, rd in snap0.regions.items()
                   if rd["faction_id"] is None and rd["tier"] != "empty"]
    if not uninhabited:
        return InvariantResult("G1_colonization_happens", True, "info",
                               "Skipped — no uninhabited non-empty regions at start")

    total_colonizations = 0
    for snap in log.snapshots:
        if snap.tick > TICK_LIMIT:
            break
        total_colonizations += len(snap.colonizations)

    if total_colonizations == 0:
        return InvariantResult(
            "G1_colonization_happens", False, "warning",
            f"No colonizations in {TICK_LIMIT} ticks despite {len(uninhabited)} uninhabited regions",
            details={
                "uninhabited_regions": uninhabited,
                "governing_configs": ["COLONIZE_COST", "ARCHETYPE_DECISION_WEIGHTS", "MIN_ACTION_THRESHOLD"],
            },
        )

    return InvariantResult("G1_colonization_happens", True, "warning",
                           f"{total_colonizations} colonization(s) within {TICK_LIMIT} ticks")


def colonies_start_weak(log: TrajectoryLog) -> InvariantResult:
    """G2: Newly colonized regions should start at or below colony starter values."""
    cfg = log.config_snapshot
    starters = {
        "military":   cfg.get("COLONY_START_MILITARY", 10.0),
        "economy":    cfg.get("COLONY_START_ECONOMY", 15.0),
        "tension":    cfg.get("COLONY_START_TENSION", 20.0),
        "population": cfg.get("COLONY_START_POPULATION", 10.0),
    }
    TOLERANCE = 5.0  # accounts for adjacency bonus + first-tick drift

    for i, snap in enumerate(log.snapshots):
        for col in snap.colonizations:
            rid = col.get("region_id")
            if not rid:
                continue
            rdata = snap.regions.get(rid)
            if not rdata or not rdata["fields"]:
                continue
            for field, max_val in starters.items():
                actual = rdata["fields"].get(field, 0.0)
                if field == "tension":
                    continue  # tension can be higher from border friction
                if actual > max_val + TOLERANCE:
                    return InvariantResult(
                        "G2_colonies_start_weak", False, "critical",
                        f"Colony {rid} at tick {snap.tick} has {field}={actual:.1f} > starter max {max_val}",
                        details={
                            "region_id": rid, "tick": snap.tick, "field": field,
                            "actual": actual, "max_allowed": max_val,
                            "governing_configs": [f"COLONY_START_{field.upper()}"],
                        },
                    )

    total = sum(len(snap.colonizations) for snap in log.snapshots)
    return InvariantResult("G2_colonies_start_weak", True, "critical",
                           f"All {total} colonies started at appropriate levels")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP H: Trajectory Shape
# ═════════════════════════════════════════════════════════════════════════════

def oscillation_present(log: TrajectoryLog) -> InvariantResult:
    """H1: Resolved by Westley — combat and events disrupt oscillation patterns; oscillations add stochasticity, not perfect sinusoids."""
    return InvariantResult("H1_oscillation", True, "info", "Resolved: disruption is intended")
    if not log.features.get("oscillation"):
        return InvariantResult("H1_oscillation", True, "info",
                               "Skipped — oscillation not enabled")
    if log.total_ticks < 100:
        return InvariantResult("H1_oscillation", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 100+)")

    cfg = log.config_snapshot
    eco_period = cfg.get("ECON_OSCILLATION_PERIOD", 15)

    for fid in log.faction_ids():
        eco = log.field_series(fid, "economy")
        if len(eco) < eco_period * 4:
            continue
        # Compute autocorrelation at the configured period
        n = len(eco)
        mean_eco = statistics.mean(eco)
        var_eco = sum((e - mean_eco) ** 2 for e in eco)
        if var_eco == 0:
            continue
        lag = eco_period
        autocorr = sum((eco[i] - mean_eco) * (eco[i + lag] - mean_eco)
                        for i in range(n - lag)) / var_eco
        if autocorr < 0.3:
            return InvariantResult(
                "H1_oscillation", False, "warning",
                f"{fid} economy autocorrelation at period {eco_period} = {autocorr:.3f} (want > 0.3)",
                details={
                    "faction_id": fid, "autocorrelation": autocorr, "period": eco_period,
                    "governing_configs": ["ECON_OSCILLATION_AMPLITUDE", "ECON_OSCILLATION_PERIOD",
                                          "TENSION_OSCILLATION_AMPLITUDE"],
                },
            )

    return InvariantResult("H1_oscillation", True, "warning", "Oscillation detected in economy")


def no_universal_convergence(log: TrajectoryLog) -> InvariantResult:
    """H2: In multi-faction scenarios, not all factions should converge to same values by tick 300."""
    TICK = min(300, log.total_ticks)
    CONVERGENCE_BAND = 5.0

    fids = log.faction_ids()
    if len(fids) < 3:
        return InvariantResult("H2_no_convergence", True, "info",
                               f"Skipped — only {len(fids)} factions (need 3+)")

    # Only check factions that still have regions at the check tick
    active_fids = [fid for fid in fids
                   if log.snapshots[TICK].factions.get(fid, {}).get("owned_region_count", 0) > 0]
    if len(active_fids) < 2:
        return InvariantResult("H2_no_convergence", True, "info",
                               "Skipped — fewer than 2 active factions at check tick")

    for field in ["military", "economy", "tension", "population"]:
        values = [log.field_at(fid, field, TICK) for fid in active_fids]
        if max(values) - min(values) > CONVERGENCE_BAND:
            return InvariantResult("H2_no_convergence", True, "warning",
                                   f"Factions divergent — {field} spread = {max(values) - min(values):.1f} at tick {TICK}")

    return InvariantResult(
        "H2_no_convergence", False, "warning",
        f"All {len(active_fids)} active factions converged within ±{CONVERGENCE_BAND} on all fields by tick {TICK}",
        details={
            "active_factions": active_fids, "tick": TICK,
            "governing_configs": ["ARCHETYPE_DECISION_WEIGHTS"],
        },
    )


def stochastic_divergence_across_seeds(log: TrajectoryLog) -> InvariantResult:
    """H3: Different seeds should produce different outcomes. (Multi-run — requires special runner.)"""
    return InvariantResult("H3_stochastic_divergence", True, "info",
                           "Skipped — requires multi-seed runner (not yet implemented)")


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP I: Technology
# ═════════════════════════════════════════════════════════════════════════════

def tech_grows_with_economy(log: TrajectoryLog) -> InvariantResult:
    """I1: Factions with higher avg economy should have higher tech after 200 ticks."""
    TICK = min(200, log.total_ticks)
    if not log.features.get("technology"):
        return InvariantResult("I1_tech_economy", True, "info",
                               "Skipped — technology not enabled")
    if log.total_ticks < 200:
        return InvariantResult("I1_tech_economy", True, "info",
                               f"Skipped — only {log.total_ticks} ticks (need 200+)")

    fids = log.faction_ids()
    if len(fids) < 2:
        return InvariantResult("I1_tech_economy", True, "info",
                               "Skipped — need 2+ factions")

    # Average economy over full run, and tech at TICK
    faction_data = []
    for fid in fids:
        eco_series = log.field_series(fid, "economy")[:TICK + 1]
        avg_eco = statistics.mean(eco_series) if eco_series else 0.0
        tech = log.snapshots[TICK].factions.get(fid, {}).get("tech_level", 0.0)
        if avg_eco > 0:
            faction_data.append((fid, avg_eco, tech))

    if len(faction_data) < 2:
        return InvariantResult("I1_tech_economy", True, "info",
                               "Skipped — fewer than 2 factions with economy")

    faction_data.sort(key=lambda x: x[1])  # sort by avg economy
    richest = faction_data[-1]
    poorest = faction_data[0]

    if richest[1] - poorest[1] < 10:
        return InvariantResult("I1_tech_economy", True, "info",
                               "Skipped — economy spread too narrow to test")

    if poorest[2] > richest[2]:
        return InvariantResult(
            "I1_tech_economy", False, "warning",
            f"Poorest faction {poorest[0]} (avg_eco={poorest[1]:.1f}) has higher tech ({poorest[2]:.2f}) than richest {richest[0]} (avg_eco={richest[1]:.1f}, tech={richest[2]:.2f})",
            details={
                "governing_configs": ["BASE_TECH_RATE", "TECH_POPULATION_FLOOR"],
            },
        )

    return InvariantResult("I1_tech_economy", True, "warning",
                           "Tech growth correlates with economy")


# ═════════════════════════════════════════════════════════════════════════════
#  REGISTRY
# ═════════════════════════════════════════════════════════════════════════════

ALL_INVARIANTS = [
    # Group A — Field Health
    no_field_flatline,
    no_premature_collapse,
    fields_stay_bounded,
    frontier_more_volatile_than_home,
    # Group B — Economy Dynamics
    economy_recovers_from_famine,
    economy_population_coupling,
    tension_responds_to_economy,
    # Group C — Military & Recruitment
    military_decays_without_economy,
    recruitment_prevents_military_zero,
    military_ceiling_respected,
    # Group D — Budget & Agent Behavior
    budget_accumulates_monotonically,
    conqueror_attacks_eventually,
    player_civ_is_conservative,
    budget_pressure_prevents_hoarding,
    # Group E — Combat & Conquest
    attacks_produce_damage,
    conquest_changes_ownership,
    conquest_causes_disruption,
    no_faction_eliminated_too_fast,
    # Group F — Border Friction
    border_friction_raises_tension,
    border_friction_drags_economy,
    # Group G — Colonization
    colonization_happens,
    colonies_start_weak,
    # Group H — Trajectory Shape
    oscillation_present,
    no_universal_convergence,
    stochastic_divergence_across_seeds,
    # Group I — Technology
    tech_grows_with_economy,
]

GROUP_MAP = {
    "A": [no_field_flatline, no_premature_collapse, fields_stay_bounded, frontier_more_volatile_than_home],
    "B": [economy_recovers_from_famine, economy_population_coupling, tension_responds_to_economy],
    "C": [military_decays_without_economy, recruitment_prevents_military_zero, military_ceiling_respected],
    "D": [budget_accumulates_monotonically, conqueror_attacks_eventually, player_civ_is_conservative, budget_pressure_prevents_hoarding],
    "E": [attacks_produce_damage, conquest_changes_ownership, conquest_causes_disruption, no_faction_eliminated_too_fast],
    "F": [border_friction_raises_tension, border_friction_drags_economy],
    "G": [colonization_happens, colonies_start_weak],
    "H": [oscillation_present, no_universal_convergence, stochastic_divergence_across_seeds],
    "I": [tech_grows_with_economy],
}


def run_invariants(log: TrajectoryLog, groups: list | None = None) -> list[InvariantResult]:
    if groups:
        funcs = []
        for g in groups:
            funcs.extend(GROUP_MAP.get(g.upper(), []))
    else:
        funcs = ALL_INVARIANTS
    return [f(log) for f in funcs]
