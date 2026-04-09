#!/usr/bin/env python3
import sys
import os
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from sim_validator import run_recorded_scenario
from sim_tuner import SCENARIOS
from invariants import run_invariants, GROUP_MAP
import tuning_loop


def print_chronicle_review(scenario_name: str, tlog):
    if not tlog.time_jump_results:
        print(f"  No time jumps in scenario {scenario_name} — nothing to review.")
        return

    print(f"\n{'═'*70}")
    print(f"  Chronicle Review Report — {scenario_name}")
    print(f"  Seed: {tlog.seed}")
    print(f"{'═'*70}")

    for tj in tlog.time_jump_results:
        start = tj.get("start_tick", 0)
        end = tj.get("end_tick", 0)
        n_ticks = tj.get("ticks_run", 0)
        events = tj.get("events", [])
        scroll_entries = tj.get("scroll_entries", [])
        warnings = tj.get("chronicle_warnings", [])
        factions_alive = len([f for f, info in tj.get("post_jump_snapshot", {}).get("factions", {}).items()
                              if info.get("owned_region_count", 0) > 0])

        print(f"\n{'═'*70}")
        print(f"  TIME JUMP: Tick {start} \u2192 {end} ({n_ticks} ticks)")
        print(f"  Factions alive: {factions_alive}  |  Events fired: {len(events)}")
        print(f"{'═'*70}")

        # Event log summary
        type_counts = Counter()
        chains_completed = set()
        chars_attached = 0
        for e in events:
            tid = e.get("template_id", e.get("name", "unknown"))
            type_counts[tid] += 1
            if e.get("chain_tag"):
                chains_completed.add(e["chain_tag"])
            if e.get("character_id"):
                chars_attached += 1

        print(f"\n  \u2500\u2500 Event Log Summary \u2500\u2500")
        print(f"  Total events: {len(events)}")
        if type_counts:
            sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
            type_strs = [f"{name} ({count})" for name, count in sorted_types[:10]]
            print(f"  By type: {', '.join(type_strs)}")
        print(f"  Chain tags seen: {len(chains_completed)}")
        print(f"  Characters attached: {chars_attached}")

        # Top significance scores
        scored = [(e, e.get("significance_score", 0)) for e in events if e.get("significance_score", 0) > 0]
        scored.sort(key=lambda x: -x[1])
        if scored:
            print(f"\n  \u2500\u2500 Top Significance Scores \u2500\u2500")
            for i, (e, score) in enumerate(scored[:10]):
                tid = e.get("template_id", e.get("name", "?"))
                region = e.get("region_id", "?")
                tick = e.get("tick", "?")
                char_name = e.get("character_name", "")
                char_str = f" \u2014 char: {char_name}" if char_name else ""
                lineage_str = " (lineage)" if e.get("lineage_member") else ""
                print(f"  {i+1:>3}. [Score {score:>5.1f}] {tid} in {region} (tick {tick}){char_str}{lineage_str}")

        # Clusters formed
        if scroll_entries:
            cluster_types = Counter(entry.cluster_type for entry in scroll_entries)
            print(f"\n  \u2500\u2500 Clusters Selected for Scroll \u2500\u2500")
            for ct, count in cluster_types.items():
                cats = [e.category for e in scroll_entries if e.cluster_type == ct]
                cat_str = ", ".join(cats)
                print(f"  {ct}: {count} ({cat_str})")
            print(f"  Total entries: {len(scroll_entries)}")

        # Scroll entries
        for idx, entry in enumerate(scroll_entries):
            base_wc = len(entry.base_text.split())
            expanded_wc = len(entry.expanded_text.split())
            print(f"\n  \u2500\u2500 SCROLL ENTRY {idx+1} of {len(scroll_entries)} \u2500\u2500")
            print(f"  Type: {entry.cluster_type}")
            print(f"  Category: {entry.category}")
            print(f"  Fragments: {entry.fragment_ids}")
            if entry.resolved_slots:
                slots_str = ", ".join(f"{k}: \"{v}\"" for k, v in entry.resolved_slots.items())
                print(f"  Slots: {{{slots_str}}}")
            print()
            print(f"  BASE TEXT:")
            for line in _wrap(entry.base_text, 66):
                print(f"  \"{line}\"" if line == _wrap(entry.base_text, 66)[0] else f"   {line}\"" if line == _wrap(entry.base_text, 66)[-1] else f"   {line}")
            print()
            print(f"  EXPANDED TEXT:")
            for line in _wrap(entry.expanded_text, 66):
                print(f"  \"{line}\"" if line == _wrap(entry.expanded_text, 66)[0] else f"   {line}\"" if line == _wrap(entry.expanded_text, 66)[-1] else f"   {line}")
            print()
            print(f"  Word count: base {base_wc}, expanded {expanded_wc}")

        if warnings:
            print(f"\n  \u2500\u2500 Warnings \u2500\u2500")
            for w in warnings:
                print(f"  \u26a0 {w}")

    print(f"\n{'═'*70}")
    print(f"  End of Chronicle Review — {scenario_name} (seed {tlog.seed})")
    print(f"{'═'*70}\n")


def _wrap(text, width):
    words = text.split()
    lines = []
    current = []
    length = 0
    for word in words:
        if length + len(word) + (1 if current else 0) > width:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + (1 if len(current) > 1 else 0)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def print_report(scenario_name: str, tlog, results: list):
    fids = tlog.faction_ids()
    n_ticks = len(tlog.snapshots) - 1

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
    mode = None  # None = normal validator, "report_only" or "propose_and_test"
    seed_override = None

    for arg in args:
        if arg == "--list-invariants":
            list_mode = True
        elif arg.startswith("--groups="):
            groups = arg.split("=")[1].split(",")
        elif arg.startswith("--mode="):
            mode = arg.split("=")[1]
        elif arg.startswith("--seed="):
            seed_override = int(arg.split("=")[1])
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

        if mode == "report_only":
            report = tuning_loop.diagnose(scenario_name, scenario)
            tuning_loop.print_report(report)
        elif mode == "propose_and_test":
            report = tuning_loop.propose_and_test(scenario_name, scenario)
            tuning_loop.print_report(report)
        elif mode == "chronicle_review":
            tlog = run_recorded_scenario(scenario_name, scenario, seed_override=seed_override)
            print_chronicle_review(scenario_name, tlog)
        else:
            tlog = run_recorded_scenario(scenario_name, scenario, seed_override=seed_override)
            results = run_invariants(tlog, groups=groups)
            print_report(scenario_name, tlog, results)


if __name__ == "__main__":
    main()
