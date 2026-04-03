#!/usr/bin/env python3
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from sim_validator import run_recorded_scenario
from sim_tuner import SCENARIOS
from invariants import run_invariants, GROUP_MAP


def print_report(scenario_name: str, tlog, results: list):
    fids = tlog.faction_ids()
    n_ticks = len(tlog.snapshots) - 1
    from collections import Counter

    print(f"\n{'═'*70}")
    print(f"  Simulation Validator — Ouroboros Manifold")
    print(f"  Scenario: {scenario_name}  |  Seed: {tlog.seed}  |  Ticks: {n_ticks}")
    print(f"  Template: {tlog.template}")
    print(f"  Features: {', '.join(k for k,v in tlog.features.items() if v)}")
    print(f"{'═'*70}")

    # Faction summary
    final = tlog.snapshots[-1]
    print(f"\n  {'Faction':<20} {'Arch':<18} {'Rgn':>3} {'Mil':>6} {'Eco':>6} {'Ten':>6} {'Pop':>6}")
    print(f"  {'─'*20} {'─'*18} {'─'*3} {'─'*6} {'─'*6} {'─'*6} {'─'*6}")
    for fid in fids:
        fac = final.factions.get(fid, {})
        avg = fac.get("avg_fields", {})
        print(f"  {fid:<20} {fac.get('archetype','?'):<18} "
              f"{fac.get('owned_region_count',0):>3} "
              f"{avg.get('military',0):>6.1f} {avg.get('economy',0):>6.1f} "
              f"{avg.get('tension',0):>6.1f} {avg.get('population',0):>6.1f}")

    all_events = []
    total_conquests = 0
    for snap in tlog.snapshots:
        for evt in snap.events_fired:
            all_events.append(evt.get("name", evt.get("template_id", "?")))
        total_conquests += len(snap.conquests)
    print(f"\n  Events: {len(all_events)}  |  Conquests: {total_conquests}")

    # Invariant results
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    skipped = [r for r in results if r.severity == "info"]

    print(f"\n{'─'*70}")
    print(f"  INVARIANT RESULTS")
    print(f"{'─'*70}\n")

    for r in results:
        if r.severity == "info":
            icon = " ·"
        elif r.passed:
            icon = " +"
        else:
            icon = " X"
        severity_tag = ""
        if not r.passed and r.severity != "info":
            severity_tag = f" [{r.severity.upper()}]"
        print(f"  {icon} {r.name}{severity_tag}")
        if not r.passed and r.severity != "info":
            print(f"      {r.message}")
            if r.details and r.details.get("governing_configs"):
                configs = ", ".join(r.details["governing_configs"])
                print(f"      Governing: {configs}")
            if r.details and r.details.get("trajectory_excerpt"):
                excerpt = [f"{v:.1f}" for v in r.details["trajectory_excerpt"]]
                print(f"      Excerpt: [{', '.join(excerpt)}]")

    # Summary
    real_results = [r for r in results if r.severity != "info"]
    real_passed = [r for r in real_results if r.passed]
    real_failed = [r for r in real_results if not r.passed]
    crit_failed = [r for r in real_failed if r.severity == "critical"]
    warn_failed = [r for r in real_failed if r.severity == "warning"]

    print(f"\n{'─'*70}")
    print(f"  SUMMARY: {len(real_passed)}/{len(real_results)} passed", end="")
    if crit_failed:
        print(f"  |  {len(crit_failed)} critical", end="")
    if warn_failed:
        print(f"  |  {len(warn_failed)} warning", end="")
    if skipped:
        print(f"  |  {len(skipped)} skipped", end="")
    print()
    print(f"{'═'*70}\n")


def main():
    args = sys.argv[1:]

    # Parse flags
    groups = None
    scenario_names = []
    list_mode = False

    for arg in args:
        if arg == "--list-invariants":
            list_mode = True
        elif arg.startswith("--groups="):
            groups = arg.split("=")[1].split(",")
        elif arg == "--all":
            scenario_names = list(SCENARIOS.keys())
        else:
            scenario_names.append(arg)

    if list_mode:
        print("\nAvailable invariants:")
        for group_key in sorted(GROUP_MAP.keys()):
            for fn in GROUP_MAP[group_key]:
                result = fn.__doc__.split(":")[0] if fn.__doc__ else fn.__name__
                print(f"  {group_key}  {fn.__name__:<40} {result}")
        return

    if not scenario_names:
        scenario_names = ["03_contested"]

    for scenario_name in scenario_names:
        if scenario_name not in SCENARIOS:
            print(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")
            continue

        scenario = SCENARIOS[scenario_name]
        if scenario.get("variants"):
            scenario = dict(scenario)
            del scenario["variants"]

        tlog = run_recorded_scenario(scenario_name, scenario)
        results = run_invariants(tlog, groups=groups)
        print_report(scenario_name, tlog, results)


if __name__ == "__main__":
    main()
