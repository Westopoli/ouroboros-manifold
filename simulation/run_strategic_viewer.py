#!/usr/bin/env python3
import sys
import os
import json
import datetime
import argparse

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sys
import config
import world as world_mod
import faction as faction_mod
import events as _events
import tick as _tick
import sim_tuner
from strategic_logger import StrategicLogger

DUMPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer_dumps")
os.makedirs(DUMPS_DIR, exist_ok=True)


def run(scenario_name, ticks_override, seed_override, launch):
    scenario = sim_tuner.SCENARIOS[scenario_name]
    sim_tuner._apply_features(scenario["features"])
    sim_tuner._apply_overrides(scenario.get("overrides", {}))

    seed = seed_override if seed_override is not None else scenario["seed"]
    ticks = ticks_override if ticks_override is not None else scenario["ticks"]

    w = world_mod.generate(scenario["template"], seed=seed)

    try:
        factions = faction_mod.generate_starting_factions(scenario["template"], rng=w.rng, world=w)
        registry = faction_mod.make_registry(*factions)
    except ValueError:
        registry = {}
        for fid in {r.faction_id for r in w.regions.values() if r.faction_id}:
            registry[fid] = faction_mod.Faction(
                fid, fid.title(), "player_civilization", budget=0.0, rng=w.rng,
            )

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()
    pending_telegraphs = []

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_path = os.path.join(DUMPS_DIR, f"{scenario_name}_{timestamp}.jsonl")

    logger = StrategicLogger(dump_path, scenario_name, w, registry, template=scenario["template"])
    logger.log_tick(0, w, registry, [], {})

    for t in range(1, ticks + 1):
        tick_log = _tick.run_tick(
            w, t,
            pending_queue=pending_queue,
            noise_offsets=noise_offsets,
            trigger_state=trigger_state,
            registry=registry if config.ENABLE_FACTIONS else None,
            pending_telegraphs=pending_telegraphs,
        )
        logger.log_tick(
            t, w, registry,
            tick_log.get("events", []),
            tick_log.get("border_friction", {}),
        )

    logger.close(registry=registry)

    file_size = os.path.getsize(dump_path)
    print(f"\nDump: {dump_path}")
    print(f"Size: {file_size:,} bytes  |  Ticks logged: {ticks + 1} (0–{ticks})")

    with open(dump_path) as f:
        lines = f.readlines()

    header = json.loads(lines[0])
    print("\n── Header ──────────────────────────────────────────────────")
    print(json.dumps(header, indent=2))

    last_tick = json.loads(lines[-1])
    print(f"\n── Tick {last_tick['tick']} (last) ───────────────────────────────────────")
    print(json.dumps(last_tick, indent=2))

    if launch:
        viewer = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strategic_viewer.py")
        os.execv(sys.executable, [sys.executable, viewer, dump_path])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record a strategic sim run to a JSONL dump.")
    parser.add_argument("scenario", nargs="?", default="01_solo_drift",
                        help="Scenario name from sim_tuner.SCENARIOS (default: 01_solo_drift)")
    parser.add_argument("--ticks", type=int, default=None,
                        help="Override tick count")
    parser.add_argument("--seed", type=int, default=None,
                        help="Override random seed")
    parser.add_argument("--no-launch", action="store_true",
                        help="Write dump only; do not launch viewer")
    args = parser.parse_args()

    run(args.scenario, args.ticks, args.seed, launch=not args.no_launch)
