"""CLI tool for inspecting bug report ZIPs.

Usage:
    python3 report_loader.py info <zip_path>
    python3 report_loader.py load <zip_path> [--snapshot <tick>]
    python3 report_loader.py replay <zip_path> [--snapshot <tick>]
    python3 report_loader.py serve <zip_path> [--snapshot <tick>] [--port <port>]
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path


def _read_zip(zip_path: Path) -> dict[str, bytes]:
    contents = {}
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        for name in zf.namelist():
            contents[name] = zf.read(name)
    return contents


def _parse_json(raw: bytes) -> dict | list:
    return json.loads(raw.decode("utf-8"))


def _get_snapshots(contents: dict[str, bytes]) -> dict[int, dict]:
    snaps = {}
    for name, data in contents.items():
        if name.startswith("tactical_snapshots/") and name.endswith(".json"):
            snap = _parse_json(data)
            tick = snap.get("tick", 0)
            snaps[tick] = snap
    return dict(sorted(snaps.items()))


def cmd_info(zip_path: Path) -> None:
    contents = _read_zip(zip_path)

    if "metadata.json" in contents:
        meta = _parse_json(contents["metadata.json"])
        print("=== METADATA ===")
        for k, v in meta.items():
            print(f"  {k}: {v}")
    else:
        print("  (no metadata.json)")

    snapshots = _get_snapshots(contents)
    print(f"\n=== TACTICAL SNAPSHOTS ({len(snapshots)}) ===")
    for tick, snap in snapshots.items():
        unit_count = snap.get("unit_count", len(snap.get("units", {})))
        struct_count = len(snap.get("structures", {}))
        print(f"  tick {tick:>6d}  units={unit_count}  structures={struct_count}")

    if "command_log.json" in contents:
        cmds = _parse_json(contents["command_log.json"])
        print(f"\n=== COMMAND LOG ({len(cmds)} entries) ===")
        for cmd in cmds[:10]:
            print(f"  tick {cmd.get('tick', '?'):>6}  {cmd.get('command', {}).get('kind', '?')}")
        if len(cmds) > 10:
            print(f"  ... and {len(cmds) - 10} more")
    else:
        print("\n  (no command_log.json)")

    if "mission_metrics.json" in contents:
        metrics = _parse_json(contents["mission_metrics.json"])
        samples = metrics.get("samples", [])
        print(f"\n=== MISSION METRICS ({len(samples)} samples) ===")
        if samples:
            first = samples[0]
            last = samples[-1]
            print(f"  first: tick={first.get('tick', '?')}  player_hp={first.get('player_force_hp', '?')}  enemy_hp={first.get('enemy_force_hp', '?')}")
            print(f"  last:  tick={last.get('tick', '?')}  player_hp={last.get('player_force_hp', '?')}  enemy_hp={last.get('enemy_force_hp', '?')}")

    has_screenshot = "screenshot.png" in contents
    has_crash = "crash_log.txt" in contents
    print(f"\n=== OTHER FILES ===")
    print(f"  screenshot.png: {'yes (%d bytes)' % len(contents['screenshot.png']) if has_screenshot else 'no'}")
    print(f"  crash_log.txt:  {'yes (%d bytes)' % len(contents['crash_log.txt']) if has_crash else 'no'}")
    if "sim_state.json" in contents:
        print(f"  sim_state.json: yes ({len(contents['sim_state.json'])} bytes)")


def cmd_load(zip_path: Path, snapshot_tick: int | None) -> None:
    contents = _read_zip(zip_path)
    snapshots = _get_snapshots(contents)

    if not snapshots:
        print("No tactical snapshots in this report.")
        return

    if snapshot_tick is not None:
        if snapshot_tick not in snapshots:
            print(f"Snapshot at tick {snapshot_tick} not found. Available: {list(snapshots.keys())}")
            return
        snap = snapshots[snapshot_tick]
    else:
        tick = max(snapshots.keys())
        snap = snapshots[tick]
        print(f"Loading latest snapshot (tick {tick})")

    units = snap.get("units", {})
    structures = snap.get("structures", {})
    objectives = snap.get("objectives", [])

    factions = {}
    for uid, u in units.items():
        f = u.get("faction", -1)
        factions.setdefault(f, {"count": 0, "total_hp": 0, "types": {}})
        factions[f]["count"] += 1
        factions[f]["total_hp"] += u.get("hp", 0)
        t = u.get("type", "?")
        factions[f]["types"][t] = factions[f]["types"].get(t, 0) + 1

    print(f"\n=== SNAPSHOT TICK {snap.get('tick', '?')} ===")
    for fid, info in sorted(factions.items()):
        print(f"  Faction {fid}: {info['count']} units, {info['total_hp']} total HP")
        for t, n in sorted(info["types"].items()):
            print(f"    {t}: {n}")

    print(f"\n  Structures: {len(structures)}")
    for sid, s in structures.items():
        print(f"    [{sid}] owner={s.get('owner', '?')} hp={s.get('hp', '?')}/{s.get('max_hp', '?')}")

    print(f"\n  Objectives: {len(objectives)}")
    for obj in objectives:
        print(f"    {obj.get('id', '?')}: {obj.get('progress', 0):.0%} [{obj.get('status', '?')}]")


def cmd_replay(zip_path: Path, snapshot_tick: int | None) -> None:
    contents = _read_zip(zip_path)
    snapshots = _get_snapshots(contents)

    if not snapshots:
        print("No tactical snapshots in this report.")
        return

    if "command_log.json" not in contents:
        print("No command log in this report.")
        return

    cmds = _parse_json(contents["command_log.json"])

    start_tick = snapshot_tick if snapshot_tick is not None else min(snapshots.keys())
    if start_tick not in snapshots:
        print(f"Snapshot at tick {start_tick} not found. Available: {list(snapshots.keys())}")
        return

    print(f"=== REPLAY from tick {start_tick} ===")
    print(f"  Snapshots: {list(snapshots.keys())}")
    print(f"  Commands: {len(cmds)}")

    relevant_cmds = [c for c in cmds if c.get("tick", 0) >= start_tick]
    print(f"  Commands from tick {start_tick}+: {len(relevant_cmds)}")

    for snap_tick in sorted(snapshots.keys()):
        if snap_tick < start_tick:
            continue
        snap = snapshots[snap_tick]
        units = snap.get("units", {})
        player_hp = sum(u.get("hp", 0) for u in units.values() if u.get("faction") == 0)
        enemy_hp = sum(u.get("hp", 0) for u in units.values() if u.get("faction") == 1)
        player_n = sum(1 for u in units.values() if u.get("faction") == 0)
        enemy_n = sum(1 for u in units.values() if u.get("faction") == 1)

        tick_cmds = [c for c in relevant_cmds if c.get("tick") == snap_tick]
        cmd_str = ""
        if tick_cmds:
            kinds = [c.get("command", {}).get("kind", "?") for c in tick_cmds]
            cmd_str = f"  cmds: {', '.join(kinds)}"

        print(f"  tick {snap_tick:>6d}  player={player_n} ({player_hp}hp)  enemy={enemy_n} ({enemy_hp}hp){cmd_str}")


def cmd_serve(zip_path: Path, snapshot_tick: int | None, port: int) -> None:
    print("serve mode requires the tactical engine and socket server.")
    print("This is a placeholder — full implementation needs engine restore wiring.")
    print(f"Would serve on port {port} from snapshot tick {snapshot_tick or 'latest'}")
    cmd_load(zip_path, snapshot_tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bug report loader")
    parser.add_argument("mode", choices=["info", "load", "replay", "serve"])
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--snapshot", type=int, default=None, help="Snapshot tick to load")
    parser.add_argument("--port", type=int, default=8765, help="Port for serve mode")
    args = parser.parse_args()

    if not args.zip_path.exists():
        print(f"File not found: {args.zip_path}")
        sys.exit(1)

    match args.mode:
        case "info":
            cmd_info(args.zip_path)
        case "load":
            cmd_load(args.zip_path, args.snapshot)
        case "replay":
            cmd_replay(args.zip_path, args.snapshot)
        case "serve":
            cmd_serve(args.zip_path, args.snapshot, args.port)


if __name__ == "__main__":
    main()
