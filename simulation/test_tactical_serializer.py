"""Round-trip + forward-tick equivalence tests for TacticalEngine save/resume.

Backstop for BLOCKER B6 (tactical mid-mission save/resume). The apex E2E test
exercises this path end-to-end; this fast pytest catches regressions in
export_full_state() / restore_from_state() in seconds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from command import Command
from tactical_engine import TacticalEngine
from test_maps import open_field


FACTION_A = 0
FACTION_B = 1
SEED = 42

# Minimal unit roster — two factions, a couple units each. Goal is RNG +
# state-shape coverage, not balance.
UNIT_TYPES_A = ["Raider", "Vanguard"]
UNIT_TYPES_B = ["Raider", "Vanguard"]


def _build_engine(seed=SEED):
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=seed)
    engine.player_faction = FACTION_A

    for i, ut in enumerate(UNIT_TYPES_A):
        engine.store.spawn(ut, FACTION_A, 400.0 + i * 150.0, 500.0)
    for i, ut in enumerate(UNIT_TYPES_B):
        engine.store.spawn(ut, FACTION_B, 400.0 + i * 150.0, 3500.0)

    # Issue attack-moves so the command queue, movement, targeting, and damage
    # subsystems all get exercised within 50-100 ticks.
    a_ids = engine.store.active_ids_for_faction(FACTION_A)
    engine.command_queue.add(Command(
        tick=0, type="attack_move", unit_ids=a_ids,
        params={"target_x": 2000.0, "target_y": 3500.0}))
    b_ids = engine.store.active_ids_for_faction(FACTION_B)
    engine.command_queue.add(Command(
        tick=0, type="attack_move", unit_ids=b_ids,
        params={"target_x": 2000.0, "target_y": 500.0}))
    return engine


def _fresh_restored_engine(state):
    """Build a fresh engine on the same map and restore the given state into it."""
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=0)  # seed irrelevant; rng is restored
    engine.restore_from_state(state)
    return engine


def _diff_summary(a, b, path="root", out=None, limit=10):
    """Collect a small list of (path, a_val, b_val) tuples where dicts differ.

    Used only when an assertion fails — gives a tractable failure message
    instead of dumping two full state dicts.
    """
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if type(a) is not type(b):
        out.append((path, f"<type {type(a).__name__}>", f"<type {type(b).__name__}>"))
        return out
    if isinstance(a, dict):
        keys = set(a.keys()) | set(b.keys())
        for k in sorted(keys, key=str):
            if k not in a:
                out.append((f"{path}.{k}", "<missing>", b[k]))
            elif k not in b:
                out.append((f"{path}.{k}", a[k], "<missing>"))
            else:
                _diff_summary(a[k], b[k], f"{path}.{k}", out, limit)
                if len(out) >= limit:
                    return out
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((f"{path}.len", len(a), len(b)))
        for i, (xa, xb) in enumerate(zip(a, b)):
            _diff_summary(xa, xb, f"{path}[{i}]", out, limit)
            if len(out) >= limit:
                return out
    else:
        if a != b:
            out.append((path, a, b))
    return out


# ── Test 1: byte-identical round trip ─────────────────────────────────────────

def test_round_trip_byte_identical():
    engine = _build_engine()
    for _ in range(80):
        engine.step()

    state_a = engine.export_full_state()
    engine_b = _fresh_restored_engine(state_a)
    state_b = engine_b.export_full_state()

    if state_a != state_b:
        diff = _diff_summary(state_a, state_b)
        msg = "round-trip not byte-identical; first diffs:\n" + "\n".join(
            f"  {p}: {av!r} != {bv!r}" for p, av, bv in diff)
        raise AssertionError(msg)


# ── Test 2: forward-tick equivalence after restore ────────────────────────────

def test_forward_tick_equivalence_after_restore():
    engine_a = _build_engine()
    for _ in range(50):
        engine_a.step()

    state_at_50 = engine_a.export_full_state()
    engine_b = _fresh_restored_engine(state_at_50)

    # Sanity: both engines start the forward-tick phase with identical state.
    assert engine_a.export_full_state() == engine_b.export_full_state(), (
        "engines not equal immediately after restore (before any forward tick)")

    for i in range(1, 11):
        engine_a.step()
        engine_b.step()
        sa = engine_a.export_full_state()
        sb = engine_b.export_full_state()
        if sa != sb:
            diff = _diff_summary(sa, sb)
            msg = (f"divergence at forward tick {i}; first diffs:\n"
                   + "\n".join(f"  {p}: {av!r} != {bv!r}" for p, av, bv in diff))
            raise AssertionError(msg)
