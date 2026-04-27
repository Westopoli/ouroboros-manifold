"""
Regression test: large group move/attack_move must NOT be dropped when
some (but not all) units in the group are dead.

Bug was in command_ingest._ingest() — it called _drop() on the first dead uid,
rejecting the entire command even when N-1 units were alive.

TEST 1  Move with 1 dead unit in 20-unit group → accepted, 19 units move
TEST 2  Attack_move with 1 dead unit in 20-unit group → accepted
TEST 3  All-alive group → accepted (sanity check)
TEST 4  All-dead group → rejected (expected)
TEST 5  Only dead units filtered out — command carries only alive uids
"""

import sys
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_engine import TacticalEngine
from test_maps import open_field
from command_ingest import ingest

config.DEBUG_COMMAND_LOG = False


def _banner(label):
    print(f"\n{'─' * 62}")
    print(f"  {label}")
    print('─' * 62)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _make_engine():
    return TacticalEngine(open_field())


def _spawn_group(engine, n, faction=0):
    uids = []
    for i in range(n):
        uid = engine.store.spawn("Raider", faction, 500.0 + i * 10, 500.0)
        uids.append(uid)
    return uids


def test_move_one_dead():
    _banner("TEST 1  Move with 1 dead in 20-unit group → accepted")
    engine = _make_engine()
    uids = _spawn_group(engine, 20)
    engine.store.alive[uids[7]] = False

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": uids,
                    "target": {"pos": [2000.0, 2000.0]}},
    }, engine)

    return _result("move accepted despite 1 dead unit", ok, reason)


def test_attack_move_one_dead():
    _banner("TEST 2  Attack_move with 1 dead in 20-unit group → accepted")
    engine = _make_engine()
    uids = _spawn_group(engine, 20)
    engine.store.alive[uids[0]] = False

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "attack_move", "unit_uids": uids,
                    "target": {"pos": [3000.0, 3000.0]}},
    }, engine)

    return _result("attack_move accepted despite 1 dead unit", ok, reason)


def test_all_alive_sanity():
    _banner("TEST 3  All-alive group accepted (sanity check)")
    engine = _make_engine()
    uids = _spawn_group(engine, 20)

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": uids,
                    "target": {"pos": [2000.0, 2000.0]}},
    }, engine)

    return _result("all-alive 20-unit move accepted", ok, reason)


def test_all_dead():
    _banner("TEST 4  All-dead group rejected (expected)")
    engine = _make_engine()
    uids = _spawn_group(engine, 5)
    for uid in uids:
        engine.store.alive[uid] = False

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": uids,
                    "target": {"pos": [2000.0, 2000.0]}},
    }, engine)

    return _result("all-dead group correctly rejected", not ok, reason)


def test_only_alive_uids_forwarded():
    _banner("TEST 5  Command carries only alive uids, dead filtered out")
    engine = _make_engine()
    uids = _spawn_group(engine, 10)
    dead = [uids[2], uids[5], uids[9]]
    for uid in dead:
        engine.store.alive[uid] = False

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": uids,
                    "target": {"pos": [2000.0, 2000.0]}},
    }, engine)

    results = []
    results.append(_result("command accepted", ok, reason))

    cmds = engine.command_queue.all_commands()
    results.append(_result("exactly 1 command queued", len(cmds) == 1,
                           f"got {len(cmds)}"))

    if cmds:
        queued_uids = cmds[0].unit_ids
        alive_uids = [u for u in uids if u not in dead]
        results.append(_result(
            f"queued {len(queued_uids)} uids (expected {len(alive_uids)})",
            set(queued_uids) == set(alive_uids),
            f"queued={sorted(queued_uids)} expected={sorted(alive_uids)}"
        ))

    return all(results)


if __name__ == "__main__":
    results = [
        test_move_one_dead(),
        test_attack_move_one_dead(),
        test_all_alive_sanity(),
        test_all_dead(),
        test_only_alive_uids_forwarded(),
    ]

    total = len(results)
    n_pass = sum(results)
    print(f"\n{'═' * 62}")
    print(f"  {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
