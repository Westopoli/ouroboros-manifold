"""
Checkpoint D — Onboarding Store Validation
===========================================
Verifies write/load round-trip and boundary validation for onboarding preferences.

  TEST 1  Valid payloads write and load cleanly for all three difficulty levels
  TEST 2  Rare-mark boundary cases: 0 marks, 9 marks accepted; 10 marks rejected
  TEST 3  Overwrites previous file (last write wins)
  TEST 4  Load returns None for a slot with no onboarding file

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
  [INFO]  informational metric (no pass/fail judgment)
"""

import sys
import tempfile
import os

sys.path.insert(0, ".")

from onboarding_store import write_onboarding, load_onboarding, VALID_DIFFICULTIES

ARCHETYPES = [
    "blitz", "counterinsurgency", "evacuation", "suppression",
    "siege", "raider", "fortify", "escort", "sabotage", "extraction",
]


def _banner(label):
    print(f"\n{'─' * 62}")
    print(f"  {label}")
    print('─' * 62)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _info(label, value):
    print(f"  [INFO]  {label}: {value}")


# ── Test 1 — valid payloads ───────────────────────────────────────────────────

def test_valid_payloads():
    _banner("TEST 1  Valid payloads — all three difficulties write and load cleanly")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        for difficulty in sorted(VALID_DIFFICULTIES):
            prefs = {
                "difficulty": difficulty,
                "rare_marks": ["counterinsurgency", "evacuation"],
                "generational_cycle_id": 1,
            }
            write_onboarding("slot_a", prefs, save_root=tmp)
            loaded = load_onboarding("slot_a", save_root=tmp)

            results.append(_result(
                f"difficulty={difficulty!r} round-trips",
                loaded is not None and loaded["difficulty"] == difficulty,
                f"got {loaded!r}" if loaded is None else "",
            ))
            results.append(_result(
                f"difficulty={difficulty!r} rare_marks preserved",
                loaded is not None and loaded["rare_marks"] == ["counterinsurgency", "evacuation"],
                f"got {loaded.get('rare_marks')!r}" if loaded else "",
            ))
            results.append(_result(
                f"difficulty={difficulty!r} schema_version=1",
                loaded is not None and loaded.get("schema_version") == 1,
            ))

    return all(results)


# ── Test 2 — rare-mark boundary cases ────────────────────────────────────────

def test_rare_mark_boundaries():
    _banner("TEST 2  Rare-mark boundary: 0 and 9 accepted, 10 rejected")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        # 0 rare marks — accepted
        try:
            write_onboarding("slot_a", {
                "difficulty": "medium",
                "rare_marks": [],
            }, save_root=tmp)
            loaded = load_onboarding("slot_a", save_root=tmp)
            results.append(_result("0 rare marks accepted", loaded is not None and loaded["rare_marks"] == []))
        except ValueError as e:
            results.append(_result("0 rare marks accepted", False, str(e)))

        # 9 rare marks — accepted (one archetype left unmarked)
        nine_marks = ARCHETYPES[:9]
        try:
            write_onboarding("slot_a", {
                "difficulty": "hard",
                "rare_marks": nine_marks,
            }, save_root=tmp)
            loaded = load_onboarding("slot_a", save_root=tmp)
            results.append(_result("9 rare marks accepted",
                                   loaded is not None and len(loaded["rare_marks"]) == 9,
                                   f"got {len(loaded['rare_marks']) if loaded else 'None'} marks"))
        except ValueError as e:
            results.append(_result("9 rare marks accepted", False, str(e)))

        # 10 rare marks — must be rejected
        ten_marks = ARCHETYPES[:]
        rejected = False
        rejection_reason = ""
        try:
            write_onboarding("slot_a", {
                "difficulty": "medium",
                "rare_marks": ten_marks,
            }, save_root=tmp)
        except ValueError as e:
            rejected = True
            rejection_reason = str(e)
        results.append(_result("10 rare marks rejected", rejected,
                               rejection_reason if rejected else "no error raised"))
        _info("rejection message", rejection_reason)

    return all(results)


# ── Test 3 — last write wins ──────────────────────────────────────────────────

def test_overwrite():
    _banner("TEST 3  Overwrite: last write wins, no stale data")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        write_onboarding("slot_a", {
            "difficulty": "easy",
            "rare_marks": ["blitz"],
        }, save_root=tmp)
        write_onboarding("slot_a", {
            "difficulty": "hard",
            "rare_marks": ["siege", "escort"],
        }, save_root=tmp)
        loaded = load_onboarding("slot_a", save_root=tmp)

        results.append(_result("difficulty updated to hard",
                               loaded is not None and loaded["difficulty"] == "hard",
                               f"got {loaded.get('difficulty')!r}" if loaded else "None"))
        results.append(_result("rare_marks updated to 2 marks",
                               loaded is not None and len(loaded["rare_marks"]) == 2,
                               f"got {loaded.get('rare_marks')!r}" if loaded else "None"))
        results.append(_result("stale 'blitz' mark absent",
                               loaded is not None and "blitz" not in loaded.get("rare_marks", []),
                               f"marks={loaded.get('rare_marks')!r}" if loaded else "None"))

    return all(results)


# ── Test 4 — missing file returns None ───────────────────────────────────────

def test_missing_returns_none():
    _banner("TEST 4  Load returns None when no onboarding file exists")
    results = []

    with tempfile.TemporaryDirectory() as tmp:
        result = load_onboarding("nonexistent_slot", save_root=tmp)
        results.append(_result("missing slot returns None", result is None,
                               f"got {result!r}"))

    return all(results)


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = [
        test_valid_payloads(),
        test_rare_mark_boundaries(),
        test_overwrite(),
        test_missing_returns_none(),
    ]

    total = len(passed)
    n_pass = sum(passed)
    print(f"\n{'═' * 62}")
    print(f"  Onboarding Store result: {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
