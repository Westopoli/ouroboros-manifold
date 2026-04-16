#!/usr/bin/env python3
"""Stage 7.5 Checkpoint B — Script Schema + Loader tests.

Verifies:
  - _stub_default.json loads and validates clean (0 errors)
  - 6 deliberately broken scripts each produce exactly the expected error
    from the right validator (dead state, missing initial state, undeclared bus
    flag, undefined predicate, unreachable state, non-terminal trap)
  - load_script() returns the stub for non-prototype archetypes
  - Error messages are specific enough for a script author to fix the file

Output is formatted so each test case is immediately readable.
"""
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from script_schema import validate_script
from script_loader import load_script

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0

# ── Helpers ───────────────────────────────────────────────────────────────────

def _prow(label: str, ok: bool, detail: str = "") -> None:
    global _failures
    if not ok:
        _failures += 1
    status = PASS if ok else FAIL
    suffix = f"  [{detail}]" if detail else ""
    print(f"    {label:<58}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*70}")
    print(f"  {title}")
    print(f"  {'─'*70}")


def _broken_case(
    label: str,
    script: dict,
    expect_min_errors: int,
    keyword: str,
) -> None:
    """Run validate_script on a broken script and verify the expected error appears."""
    global _failures
    errors = validate_script(script)
    got_count = len(errors)
    messages = [str(e) for e in errors]
    keyword_found = any(keyword.lower() in m.lower() for m in messages)
    ok_count = got_count >= expect_min_errors
    ok_keyword = keyword_found

    if not ok_count or not ok_keyword:
        _failures += 1

    status = PASS if (ok_count and ok_keyword) else FAIL
    print(f"    {label}")
    print(f"      errors returned : {got_count}  (expected ≥{expect_min_errors})  "
          f"{'✓' if ok_count else '✗ FAIL'}")
    print(f"      keyword {keyword!r:<30} found in errors: "
          f"{'✓' if ok_keyword else '✗ FAIL — NOT FOUND'}")
    if messages:
        for m in messages:
            print(f"      → {m}")
    print(f"      {status}")
    print()


# ── Stub script fixture ───────────────────────────────────────────────────────

def _make_valid_stub() -> dict:
    """Minimal valid two-state advance script (mirrors _stub_default.json)."""
    return {
        "script_id": "stub_default_v1",
        "archetype": "_stub_default",
        "trigger_bus_vocabulary": [],
        "terminal_states": ["destroyed"],
        "forces": [{
            "force_id": "force_main",
            "composition_template": "default",
            "power_share": 1.0,
            "initial_state": "advance_cautious",
            "states": {
                "advance_cautious": {
                    "behavior": "advance",
                    "modifier": "cautious",
                    "transitions": [
                        {"condition": "timer.elapsed_sec >= 120",
                         "to_state": "advance_aggressive", "noise_pct": 0.20},
                        {"condition": "force_hp_fraction < 0.30",
                         "to_state": "retreat_cautious",  "noise_pct": 0.10},
                    ],
                },
                "advance_aggressive": {
                    "behavior": "advance",
                    "modifier": "aggressive",
                    "transitions": [
                        {"condition": "force_hp_fraction < 0.25",
                         "to_state": "retreat_cautious", "noise_pct": 0.10},
                    ],
                },
                "retreat_cautious": {
                    "behavior": "retreat",
                    "modifier": "cautious",
                    "transitions": [
                        {"condition": "force_unit_count == 0", "to_state": "destroyed"},
                    ],
                },
                "destroyed": {
                    "behavior": "defend",
                    "modifier": "cautious",
                    "transitions": [],
                },
            },
        }],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_valid_stub_from_file() -> None:
    _section("VALID SCRIPT — _stub_default.json (loaded from disk)")
    global _failures

    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "_stub_default.json")
    with open(path, encoding="utf-8") as fh:
        script = json.load(fh)
    errors = validate_script(script)
    ok = len(errors) == 0
    if not ok:
        _failures += 1
        for e in errors:
            print(f"    UNEXPECTED ERROR: {e}")
    _prow("_stub_default.json: 0 validation errors", ok)
    _prow(f"script_id present:  {script.get('script_id')!r}", "script_id" in script)
    _prow(f"forces count:       {len(script.get('forces', []))}", len(script.get("forces", [])) >= 1)


def test_valid_stub_inline() -> None:
    _section("VALID SCRIPT — inline fixture (sanity check for broken-script comparisons)")
    global _failures

    script = _make_valid_stub()
    errors = validate_script(script)
    ok = len(errors) == 0
    if not ok:
        _failures += 1
        for e in errors:
            print(f"    UNEXPECTED ERROR: {e}")
    _prow("inline stub: 0 validation errors", ok)


def test_broken_scripts() -> None:
    _section("BROKEN SCRIPTS — each must be caught by the right validator")
    print()

    # ── [1] Dead state ────────────────────────────────────────────────────────
    # A transition points to "phantom_state" which does not exist in states.
    s = _make_valid_stub()
    s["forces"][0]["states"]["advance_cautious"]["transitions"].append(
        {"condition": "timer.elapsed_sec >= 300", "to_state": "phantom_state"}
    )
    _broken_case(
        "[1] Dead state — to_state 'phantom_state' not in states{}",
        s,
        expect_min_errors=1,
        keyword="dead state",
    )

    # ── [2] Missing initial state ─────────────────────────────────────────────
    # initial_state references a name that doesn't exist in states.
    s = _make_valid_stub()
    s["forces"][0]["initial_state"] = "missing_state"
    _broken_case(
        "[2] Missing initial state — 'missing_state' not defined in states{}",
        s,
        expect_min_errors=1,
        keyword="initial_state",
    )

    # ── [3] Undeclared bus flag ───────────────────────────────────────────────
    # trigger_bus_vocabulary = [] but a condition uses bus.stale_flag.
    s = _make_valid_stub()
    s["forces"][0]["states"]["advance_cautious"]["reactive_hooks"] = [
        {"when": "bus.stale_flag", "to_state": "advance_aggressive"}
    ]
    _broken_case(
        "[3] Undeclared bus flag — bus.stale_flag not in trigger_bus_vocabulary",
        s,
        expect_min_errors=1,
        keyword="undeclared bus flag",
    )

    # ── [4] Undefined predicate (condition language level) ────────────────────
    # A condition string uses an unknown function; caught by condition_language
    # tokenizer and surfaced as a schema ValidationError.
    s = _make_valid_stub()
    s["forces"][0]["states"]["advance_cautious"]["transitions"][0]["condition"] = (
        "unknown_predicate() < 0.5"
    )
    _broken_case(
        "[4] Undefined predicate — 'unknown_predicate()' rejected by condition parser",
        s,
        expect_min_errors=1,
        keyword="Unknown identifier",
    )

    # ── [5] Unreachable state ─────────────────────────────────────────────────
    # A state 'orphan_state' is defined but no transition ever leads to it.
    s = _make_valid_stub()
    s["terminal_states"].append("orphan_state")
    s["forces"][0]["states"]["orphan_state"] = {
        "behavior": "defend",
        "modifier": "cautious",
        "transitions": [],
    }
    _broken_case(
        "[5] Unreachable state — 'orphan_state' defined but no transition leads to it",
        s,
        expect_min_errors=1,
        keyword="unreachable",
    )

    # ── [6] Non-terminal trap — no outgoing transitions ───────────────────────
    # 'advance_aggressive' is not in terminal_states but has an empty transitions list.
    s = _make_valid_stub()
    s["forces"][0]["states"]["advance_aggressive"]["transitions"] = []
    _broken_case(
        "[6] Non-terminal trap — 'advance_aggressive' has no transitions and is not terminal",
        s,
        expect_min_errors=1,
        keyword="no transitions",
    )


def test_loader_stub_fallback() -> None:
    _section("LOADER — non-prototype archetypes fall back to stub")
    global _failures

    non_prototypes = ["siege_breaking", "reconquest", "suppression", "evacuation", "raid", "rear_guard"]
    print(f"  {'Archetype':<22}  {'script_id':<22}  Errors  Status")
    print(f"  {'─'*22}  {'─'*22}  ──────  ──────")
    for archetype in non_prototypes:
        script = load_script(archetype)
        errors = validate_script(script)
        sid = script.get("script_id", "?")
        is_stub = sid == "stub_default_v1"
        ok = is_stub and len(errors) == 0
        if not ok:
            _failures += 1
        status = PASS if ok else FAIL
        print(f"  {archetype:<22}  {sid:<22}  {len(errors):>6}  {status}")


def test_missing_fields() -> None:
    _section("MISSING TOP-LEVEL FIELDS — each missing field caught individually")
    global _failures

    required = ("script_id", "archetype", "forces", "trigger_bus_vocabulary", "terminal_states")
    print(f"  {'Removed field':<28}  {'Errors':>6}  {'Contains field name':>20}  Status")
    print(f"  {'─'*28}  {'─'*6}  {'─'*20}  ──────")
    for field in required:
        s = _make_valid_stub()
        del s[field]
        errors = validate_script(s)
        count = len(errors)
        keyword_ok = any(field in str(e) for e in errors)
        ok = count >= 1 and keyword_ok
        if not ok:
            _failures += 1
        status = PASS if ok else FAIL
        print(f"  {field:<28}  {count:>6}  {str(keyword_ok):>20}  {status}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 72)
    print("  STAGE 7.5 CHECKPOINT B — Script Schema + Loader")
    print("=" * 72)

    test_valid_stub_from_file()
    test_valid_stub_inline()
    test_broken_scripts()
    test_loader_stub_fallback()
    test_missing_fields()

    print()
    print("=" * 72)
    if _failures == 0:
        print(f"  {PASS}  All schema tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 72)
    sys.exit(0 if _failures == 0 else 1)
