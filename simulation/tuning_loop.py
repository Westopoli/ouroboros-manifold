from dataclasses import dataclass, field as dc_field
import config
from sim_validator import run_recorded_scenario, InvariantResult
from invariants import run_invariants


@dataclass
class ConfigChange:
    config_key: str
    old_value: float
    proposed_value: float
    direction: str
    triggered_by: list = dc_field(default_factory=list)
    confidence: str = "medium"


@dataclass
class TuningReport:
    scenario: str
    seed: int
    total_invariants: int
    passed: int
    failed: int
    failures: list = dc_field(default_factory=list)
    proposed_changes: list = dc_field(default_factory=list)
    conflicts: list = dc_field(default_factory=list)
    escalations: list = dc_field(default_factory=list)
    retest_passed: bool | None = None
    regressions: list = dc_field(default_factory=list)


# ── Config-Invariant Mapping ────────────────────────────────────────────────
# config_key → {invariant_name: "increase" | "decrease" | "either"}

CONFIG_EFFECTS = {
    "ECONOMY_BASE_GROWTH": {
        "B1_economy_recovers": "increase",
        "B2_eco_pop_coupling": "either",
        "A1_no_field_flatline": "either",
    },
    "MILITARY_DECAY_RATE": {
        "A2_no_premature_collapse": "decrease",
        "C1_mil_decays_no_eco": "increase",
        "C2_recruitment_floors_mil": "decrease",
    },
    "RECRUITMENT_RATE": {
        "C2_recruitment_floors_mil": "increase",
        "C3_mil_ceiling": "decrease",
    },
    "RECRUITMENT_BASELINE": {
        "C2_recruitment_floors_mil": "increase",
    },
    "RECRUITMENT_CEILING": {
        "C3_mil_ceiling": "increase",
    },
    "BUDGET_GROWTH_RATE": {
        "D1_budget_monotonic": "increase",
        "D2_conqueror_attacks": "increase",
        "D4_no_hoarding": "either",
    },
    "REGION_MAINTENANCE_COST": {
        "D1_budget_monotonic": "decrease",
    },
    "BORDER_FRICTION_TENSION": {
        "F1_border_tension": "increase",
    },
    "BORDER_FRICTION_ECONOMY": {
        "F2_border_economy": "increase",
    },
    "TENSION_NATURAL_DECAY_RATE": {
        "A2_no_premature_collapse": "increase",
        "B3_tension_economy": "decrease",
    },
    "TENSION_ECONOMY_RATE": {
        "B3_tension_economy": "increase",
    },
    "TENSION_ECONOMY_MIDPOINT": {
        "B3_tension_economy": "either",
    },
    "POPULATION_GROWTH_RATE": {
        "A1_no_field_flatline": "either",
        "B2_eco_pop_coupling": "either",
    },
    "ECONOMY_TENSION_PENALTY_RATE": {
        "A2_no_premature_collapse": "decrease",
        "B1_economy_recovers": "decrease",
    },
    "ECO_POP_RATIO": {
        "B2_eco_pop_coupling": "either",
    },
    "ECO_OVERCAPACITY_DECAY": {
        "B2_eco_pop_coupling": "either",
    },
    "ECONOMY_FLOOR": {
        "A1_no_field_flatline": "either",
    },
    "ATTACK_CONFIDENCE_RANGE": {
        "D2_conqueror_attacks": "decrease",
        "D3_player_conservative": "increase",
    },
    "BUDGET_PRESSURE_THRESHOLD": {
        "D4_no_hoarding": "decrease",
    },
    "CONQUEST_TENSION_SPIKE": {
        "E3_conquest_disruption": "increase",
    },
    "CONQUEST_ECONOMY_DISRUPTION": {
        "E3_conquest_disruption": "increase",
    },
    "RESISTANCE_FACTOR": {
        "E4_no_early_elimination": "increase",
    },
    "ATTACK_EFFICIENCY": {
        "E4_no_early_elimination": "decrease",
    },
    "COLONIZE_COST": {
        "G1_colonization_happens": "decrease",
    },
    "COLONY_START_MILITARY": {
        "G2_colonies_start_weak": "decrease",
    },
    "COLONY_START_ECONOMY": {
        "G2_colonies_start_weak": "decrease",
    },
    "ECON_OSCILLATION_AMPLITUDE": {
        "H1_oscillation": "increase",
    },
    "ECON_OSCILLATION_PERIOD": {
        "H1_oscillation": "either",
    },
    "TENSION_OSCILLATION_AMPLITUDE": {
        "H1_oscillation": "increase",
    },
    "BASE_TECH_RATE": {
        "I1_tech_economy": "increase",
    },
    "TECH_POPULATION_FLOOR": {
        "I1_tech_economy": "either",
    },
    "MIN_ACTION_THRESHOLD": {
        "G1_colonization_happens": "decrease",
        "D2_conqueror_attacks": "decrease",
    },
}


CONFIG_BOUNDS = {
    "ECONOMY_BASE_GROWTH":          (0.5, 8.0),
    "MILITARY_DECAY_RATE":          (0.001, 0.05),
    "RECRUITMENT_RATE":             (0.5, 10.0),
    "RECRUITMENT_BASELINE":         (0.01, 0.5),
    "RECRUITMENT_CEILING":          (60.0, 100.0),
    "BUDGET_GROWTH_RATE":           (0.005, 0.05),
    "REGION_MAINTENANCE_COST":      (2.0, 20.0),
    "BORDER_FRICTION_TENSION":      (0.01, 0.5),
    "BORDER_FRICTION_ECONOMY":      (0.001, 0.05),
    "TENSION_NATURAL_DECAY_RATE":   (0.05, 0.5),
    "TENSION_ECONOMY_RATE":         (0.1, 1.5),
    "TENSION_ECONOMY_MIDPOINT":     (20.0, 80.0),
    "POPULATION_GROWTH_RATE":       (0.5, 8.0),
    "ECONOMY_TENSION_PENALTY_RATE": (0.1, 1.5),
    "ECO_POP_RATIO":                (1.0, 2.5),
    "ECO_OVERCAPACITY_DECAY":       (0.1, 1.0),
    "ECONOMY_FLOOR":                (2.0, 15.0),
    "BUDGET_PRESSURE_THRESHOLD":    (0.5, 5.0),
    "CONQUEST_TENSION_SPIKE":       (2.0, 20.0),
    "CONQUEST_ECONOMY_DISRUPTION":  (2.0, 15.0),
    "RESISTANCE_FACTOR":            (0.3, 1.0),
    "ATTACK_EFFICIENCY":            (0.5, 2.0),
    "COLONIZE_COST":                (5.0, 50.0),
    "COLONY_START_MILITARY":        (3.0, 25.0),
    "COLONY_START_ECONOMY":         (5.0, 30.0),
    "ECON_OSCILLATION_AMPLITUDE":   (1.0, 15.0),
    "ECON_OSCILLATION_PERIOD":      (8, 30),
    "TENSION_OSCILLATION_AMPLITUDE": (0.5, 8.0),
    "BASE_TECH_RATE":               (0.01, 0.5),
    "TECH_POPULATION_FLOOR":        (0.1, 0.8),
    "MIN_ACTION_THRESHOLD":         (0.01, 0.2),
}

STEP_FRACTION = 0.15


def _governing_configs_for(result: InvariantResult) -> list[str]:
    declared = result.details.get("governing_configs", []) if result.details else []
    # Also include configs from CONFIG_EFFECTS that map to this invariant
    from_effects = [ck for ck, inv_map in CONFIG_EFFECTS.items() if result.name in inv_map]
    combined = list(dict.fromkeys(declared + from_effects))
    return combined


def _classify_failure(result: InvariantResult) -> str:
    governing = _governing_configs_for(result)
    if not governing:
        return "escalate"
    tunable = [g for g in governing if g in CONFIG_BOUNDS]
    if not tunable:
        return "escalate"
    return "tunable"


def _find_direction(config_key: str, invariant_name: str) -> str | None:
    effects = CONFIG_EFFECTS.get(config_key, {})
    return effects.get(invariant_name)


def _propose_change(config_key: str, direction: str, triggered_by: list) -> ConfigChange | None:
    current = getattr(config, config_key, None)
    if current is None:
        return None
    bounds = CONFIG_BOUNDS.get(config_key)
    if bounds is None:
        return None

    step = abs(current) * STEP_FRACTION
    if step < 0.001:
        step = 0.001

    if direction == "increase":
        proposed = current + step
    elif direction == "decrease":
        proposed = current - step
    else:
        return None

    lo, hi = bounds
    proposed = max(lo, min(hi, proposed))

    if isinstance(current, int) and isinstance(lo, int) and isinstance(hi, int):
        proposed = round(proposed)

    if proposed == current:
        return None

    confidence = "high" if len(triggered_by) == 1 else "medium"

    return ConfigChange(
        config_key=config_key,
        old_value=current,
        proposed_value=proposed,
        direction=direction,
        triggered_by=triggered_by,
        confidence=confidence,
    )


def _detect_conflicts(failures: list[InvariantResult]) -> tuple[list[ConfigChange], list[str]]:
    # Build: config_key → {direction → [invariant_names]}
    direction_map: dict[str, dict[str, list[str]]] = {}
    for f in failures:
        governing = _governing_configs_for(f)
        for ck in governing:
            d = _find_direction(ck, f.name)
            if d is None or d == "either":
                continue
            direction_map.setdefault(ck, {}).setdefault(d, []).append(f.name)

    conflicts = []
    proposals = []
    for ck, dirs in direction_map.items():
        if len(dirs) > 1:
            all_invs = []
            for d_invs in dirs.values():
                all_invs.extend(d_invs)
            conflicts.append(
                f"{ck}: {', '.join(all_invs)} want opposite directions"
            )
        else:
            direction = list(dirs.keys())[0]
            triggered = list(dirs.values())[0]
            change = _propose_change(ck, direction, triggered)
            if change:
                proposals.append(change)

    # Deduplicate proposals by config_key (keep the one with most triggers)
    seen = {}
    for p in proposals:
        if p.config_key not in seen or len(p.triggered_by) > len(seen[p.config_key].triggered_by):
            seen[p.config_key] = p

    # Also handle "either" direction configs — try increasing first
    for f in failures:
        governing = _governing_configs_for(f)
        for ck in governing:
            d = _find_direction(ck, f.name)
            if d != "either":
                continue
            if ck in seen:
                continue
            change = _propose_change(ck, "increase", [f.name])
            if change:
                seen[ck] = change

    return list(seen.values()), conflicts


def diagnose(scenario_name: str, scenario: dict,
             seed_override: int | None = None) -> TuningReport:
    tlog = run_recorded_scenario(scenario_name, scenario, seed_override)
    results = run_invariants(tlog)

    real = [r for r in results if r.severity != "info"]
    passed = [r for r in real if r.passed]
    failed = [r for r in real if not r.passed]

    escalations = []
    tunable_failures = []
    for f in failed:
        cls = _classify_failure(f)
        if cls == "escalate":
            escalations.append(f"{f.name}: {f.message}")
        else:
            tunable_failures.append(f)

    # Sort by severity (critical first), then by governing config count (most shared first)
    tunable_failures.sort(key=lambda f: (
        0 if f.severity == "critical" else 1,
        -len(f.details.get("governing_configs", []) if f.details else []),
    ))

    proposals, conflicts = _detect_conflicts(tunable_failures)

    return TuningReport(
        scenario=scenario_name,
        seed=tlog.seed,
        total_invariants=len(real),
        passed=len(passed),
        failed=len(failed),
        failures=failed,
        proposed_changes=proposals,
        conflicts=conflicts,
        escalations=escalations,
    )


def propose_and_test(scenario_name: str, scenario: dict,
                     seed_override: int | None = None) -> TuningReport:
    report = diagnose(scenario_name, scenario, seed_override)

    if not report.proposed_changes:
        return report

    # Track what passed in the original run
    first_passed_names = set()
    tlog_orig = run_recorded_scenario(scenario_name, scenario, seed_override)
    for r in run_invariants(tlog_orig):
        if r.passed and r.severity != "info":
            first_passed_names.add(r.name)

    # Apply proposals
    originals = {}
    for change in report.proposed_changes:
        originals[change.config_key] = change.old_value
        setattr(config, change.config_key, change.proposed_value)

    # Re-run with proposed changes
    tlog2 = run_recorded_scenario(scenario_name, scenario, seed_override)
    results2 = run_invariants(tlog2)

    # Restore originals
    for ck, val in originals.items():
        setattr(config, ck, val)

    failed2 = [r for r in results2 if not r.passed and r.severity != "info"]
    regressions = [r.name for r in failed2 if r.name in first_passed_names]

    report.retest_passed = len(failed2) < len(report.failures) and not regressions
    report.regressions = regressions

    return report


def print_report(report: TuningReport):
    print(f"\n{'═'*70}")
    print(f"  Tuning Loop Report — {report.scenario}")
    print(f"  Seed: {report.seed}  |  {report.passed}/{report.total_invariants} passed")
    print(f"{'═'*70}")

    if report.failures:
        print(f"\n  FAILURES ({len(report.failures)}):")
        for f in report.failures:
            governing = _governing_configs_for(f)
            cls = _classify_failure(f)
            tag = "TUNABLE" if cls == "tunable" else "ESCALATE"
            print(f"    [{tag}] {f.name} [{f.severity}]")
            print(f"      {f.message}")
            if governing:
                print(f"      Configs: {', '.join(governing)}")

    if report.escalations:
        print(f"\n  ESCALATIONS ({len(report.escalations)}):")
        for e in report.escalations:
            print(f"    ! {e}")

    if report.conflicts:
        print(f"\n  CONFLICTS ({len(report.conflicts)}):")
        for c in report.conflicts:
            print(f"    ! {c}")

    if report.proposed_changes:
        print(f"\n  PROPOSED CHANGES ({len(report.proposed_changes)}):")
        for ch in report.proposed_changes:
            print(f"    {ch.config_key}: {ch.old_value} → {ch.proposed_value}"
                  f"  ({ch.direction}, {ch.confidence})")
            print(f"      Triggered by: {', '.join(ch.triggered_by)}")

    if report.retest_passed is not None:
        status = "PASSED" if report.retest_passed else "FAILED"
        print(f"\n  RETEST: {status}")
        if report.regressions:
            print(f"    Regressions: {', '.join(report.regressions)}")

    print(f"{'═'*70}\n")
