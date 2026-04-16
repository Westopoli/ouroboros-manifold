#!/usr/bin/env python3
"""Stage 7.5 Checkpoint A — ConditionLanguage tests.

Verifies: every supported primitive parses and evaluates correctly; every
adversarial input is rejected at parse time without raising uncaught exceptions;
the parse cache returns the cached AST on repeated calls; validate() catches
undeclared bus flags.

Output format: tabular per-expression rows so failures are immediately obvious.
"""
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from trigger_bus import TriggerBus
from condition_language import (
    EvaluationContext, ValidationError,
    evaluate, validate, cache_size, _parse, _parse_cache,
)

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_ctx(
    hp_frac: float = 0.75,
    unit_count: int = 8,
    elapsed_sec: float = 90.0,
    expired: bool = False,
    bus_flags: dict | None = None,
    bus_values: dict | None = None,
    enemy_in_range_fn=None,
    player_frac_in_zone_fn=None,
    structure_owner_fn=None,
) -> EvaluationContext:
    bus = TriggerBus()
    for k in (bus_flags or {}):
        if (bus_flags or {})[k]:
            bus.set_flag(k)
    for k, v in (bus_values or {}).items():
        bus.set_value(k, v)
    return EvaluationContext(
        force_hp_fraction=hp_frac,
        force_unit_count=unit_count,
        timer_elapsed_sec=elapsed_sec,
        timer_expired=expired,
        bus=bus,
        enemy_unit_in_range_fn=enemy_in_range_fn,
        player_force_hp_in_zone_fn=player_frac_in_zone_fn,
        structure_owner_fn=structure_owner_fn,
    )


def _section(title: str) -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  {title}")
    print(f"  {'─'*72}")
    print(f"  {'Expression':<50}  {'Expected':<9}  {'Actual':<9}  Status")
    print(f"  {'─'*50}  {'─'*9}  {'─'*9}  ──────")


def _row(expr: str, expected, ctx: EvaluationContext) -> None:
    global _failures
    try:
        actual = evaluate(expr, ctx)
        ok = (actual == expected)
        status = PASS if ok else FAIL
        if not ok:
            _failures += 1
    except Exception as e:
        actual = f"ERROR: {e}"
        ok = False
        status = FAIL
        _failures += 1

    exp_s = str(expected)
    act_s = str(actual)
    print(f"  {expr:<50}  {exp_s:<9}  {act_s:<9}  {status}")


def _adv_section() -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  ADVERSARIAL REJECTION TABLE")
    print(f"  {'─'*72}")
    print(f"  {'Input':<52}  {'Rejection type':<24}  Status")
    print(f"  {'─'*52}  {'─'*24}  ──────")


def _adv_row(expr: str, expect_rejection_contains: str, declared_flags: set | None = None) -> None:
    """Verify that the input is rejected (parse error, validation error, or eval TypeError)."""
    global _failures
    rejection_type = None
    was_rejected = False

    # Try parse-level rejection
    try:
        _parse(expr)
    except SyntaxError as e:
        rejection_type = f"SyntaxError: {str(e)[:22]}"
        was_rejected = True

    # If it parsed, try validation-level rejection
    if not was_rejected and declared_flags is not None:
        errs = validate(expr, declared_flags)
        if errs:
            rejection_type = f"ValidationError: {str(errs[0])[:20]}"
            was_rejected = True

    # If it passed parse + validation, try evaluate-level rejection
    if not was_rejected:
        try:
            ctx = _make_ctx()
            evaluate(expr, ctx)
            rejection_type = "NOT REJECTED"
        except (TypeError, RuntimeError, Exception) as e:
            rejection_type = f"{type(e).__name__}: {str(e)[:18]}"
            was_rejected = True

    ok = was_rejected
    status = PASS if ok else FAIL
    if not ok:
        _failures += 1

    rtype_s = (rejection_type or "NOT REJECTED")[:26]
    print(f"  {expr:<52}  {rtype_s:<26}  {status}")


# ── Test sections ─────────────────────────────────────────────────────────────

def test_numeric_predicates() -> None:
    _section("NUMERIC PREDICATES")

    ctx_hi  = _make_ctx(hp_frac=0.80, unit_count=8)
    ctx_lo  = _make_ctx(hp_frac=0.25, unit_count=0)

    _row("force_hp_fraction < 0.40",    False, ctx_hi)
    _row("force_hp_fraction < 0.40",    True,  ctx_lo)
    _row("force_hp_fraction <= 0.25",   True,  ctx_lo)
    _row("force_hp_fraction >= 0.80",   True,  ctx_hi)
    _row("force_hp_fraction > 0.79",    True,  ctx_hi)
    _row("force_unit_count == 0",       True,  ctx_lo)
    _row("force_unit_count == 8",       True,  ctx_hi)
    _row("force_unit_count > 5",        True,  ctx_hi)
    _row("force_unit_count > 5",        False, ctx_lo)


def test_timer_predicates() -> None:
    _section("TIMER PREDICATES")

    ctx_early   = _make_ctx(elapsed_sec=45.0,  expired=False)
    ctx_late    = _make_ctx(elapsed_sec=200.0, expired=True)

    _row("timer.elapsed_sec >= 180",    False, ctx_early)
    _row("timer.elapsed_sec >= 180",    True,  ctx_late)
    _row("timer.elapsed_sec >= 45",     True,  ctx_early)
    _row("timer.expired",               False, ctx_early)
    _row("timer.expired",               True,  ctx_late)
    _row("timer.elapsed_sec < 100",     True,  ctx_early)


def test_bus_predicates() -> None:
    _section("BUS FLAG PREDICATES")

    ctx_none = _make_ctx(bus_flags={})
    ctx_b    = _make_ctx(bus_flags={"force_b_broken": True, "objective_reached": True})

    _row("bus.force_b_broken",                        False, ctx_none)
    _row("bus.force_b_broken",                        True,  ctx_b)
    _row("bus.objective_reached",                     True,  ctx_b)
    _row("bus.primary_chokepoint_contested",          False, ctx_b)   # not set
    _row("not bus.force_b_broken",                    True,  ctx_none)
    _row("not bus.force_b_broken",                    False, ctx_b)


def test_boolean_logic() -> None:
    _section("BOOLEAN LOGIC — and / or / not")

    ctx = _make_ctx(
        hp_frac=0.25,
        unit_count=3,
        elapsed_sec=200.0,
        expired=True,
        bus_flags={"force_b_broken": True},
    )

    _row("force_hp_fraction < 0.30 and bus.force_b_broken",     True,  ctx)
    _row("force_hp_fraction < 0.30 and not bus.force_b_broken", False, ctx)
    _row("force_hp_fraction > 0.80 or bus.force_b_broken",      True,  ctx)
    _row("force_hp_fraction > 0.80 or force_unit_count > 10",   False, ctx)
    _row("not force_hp_fraction < 0.30",                        False, ctx)
    _row("timer.elapsed_sec >= 180 and not timer.expired",      False, ctx)
    _row("timer.elapsed_sec >= 180 and timer.expired",          True,  ctx)
    # Short-circuit: False and <anything> should not raise
    _row("force_hp_fraction > 0.90 and bus.force_b_broken",     False, ctx)


def test_callable_predicates() -> None:
    _section("CALLABLE PREDICATES — enemy_unit_in_range / player_frac_in_zone / structure_owner")

    ctx_with_fns = _make_ctx(
        enemy_in_range_fn=lambda zone, radius: (zone == "chokepoint_primary" and radius <= 800),
        player_frac_in_zone_fn=lambda zone: 0.20 if zone == "chokepoint_primary" else 0.80,
        structure_owner_fn=lambda sid: "enemy" if sid == "fort_alpha" else "player",
    )

    _row("enemy_unit_in_range('chokepoint_primary', 800)",       True,  ctx_with_fns)
    _row("enemy_unit_in_range('chokepoint_primary', 900)",       False, ctx_with_fns)
    _row("enemy_unit_in_range('flank_south', 800)",              False, ctx_with_fns)
    _row("player_force_hp_fraction_in_zone('chokepoint_primary') < 0.30",
                                                                  True,  ctx_with_fns)
    _row("player_force_hp_fraction_in_zone('staging') < 0.30",  False, ctx_with_fns)
    _row("structure_owner('fort_alpha') == 'enemy'",             True,  ctx_with_fns)
    _row("structure_owner('fort_alpha') == 'player'",            False, ctx_with_fns)
    _row("structure_owner('garrison_b') == 'player'",            True,  ctx_with_fns)

    # None-fn fallbacks (no fns provided)
    ctx_no_fns = _make_ctx()
    _row("enemy_unit_in_range('zone_x', 500)",                   False, ctx_no_fns)
    _row("player_force_hp_fraction_in_zone('zone_x') < 0.5",    True,  ctx_no_fns)  # 0.0 < 0.5


def test_literal_values() -> None:
    _section("LITERAL VALUES — numbers, strings, booleans")

    ctx = _make_ctx(
        structure_owner_fn=lambda sid: "player",
    )

    _row("true",                                 True,  ctx)
    _row("false",                                False, ctx)
    _row("not true",                             False, ctx)
    _row("not false",                            True,  ctx)
    _row("structure_owner('obj') == 'player'",   True,  ctx)
    _row("structure_owner('obj') == 'enemy'",    False, ctx)


def test_adversarial_inputs() -> None:
    _adv_section()

    declared = {"force_b_broken", "objective_reached", "inner_breach"}

    # Arbitrary Python — rejected at tokenize/parse
    _adv_row("__import__('os').system('rm')",     "SyntaxError")
    _adv_row("eval('1+1')",                       "SyntaxError")
    _adv_row("exec('pass')",                      "SyntaxError")
    _adv_row("open('/etc/passwd').read()",         "SyntaxError")
    _adv_row("lambda x: x",                       "SyntaxError")
    _adv_row("globals()['x']",                    "SyntaxError")

    # Unknown predicates — rejected at tokenize
    _adv_row("unknown_predicate()",               "SyntaxError")
    _adv_row("some_function(42)",                 "SyntaxError")

    # Malformed expressions — rejected at parse
    _adv_row("force_hp_fraction <",              "SyntaxError")   # EOF after op
    _adv_row("and force_hp_fraction < 0.5",      "SyntaxError")   # leading 'and'
    _adv_row("force_hp_fraction < 0.5 and",      "SyntaxError")   # trailing 'and'
    _adv_row("bus.",                              "SyntaxError")   # no flag after .
    _adv_row("timer.unknown_field",              "SyntaxError")   # bad timer field
    _adv_row("'unterminated string",             "SyntaxError")   # unclosed quote

    # Undeclared bus flags — caught by validate(), not tokenizer
    _adv_row("bus.undeclared_flag",              "ValidationError",  declared_flags=declared)
    _adv_row("bus.stale_flag and force_hp_fraction < 0.5",
                                                  "ValidationError", declared_flags=declared)

    # Type mismatch — now caught at validate() time (schema-time), not eval time
    _adv_row("force_hp_fraction < 'text'",       "ValidationError", declared_flags=set())
    _adv_row("bus.force_b_broken < 0.5",         "ValidationError", declared_flags=set())
    _adv_row("structure_owner('x') > 0.5",       "ValidationError", declared_flags=set())


def test_type_inference() -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  TYPE INFERENCE — validate() catches mismatches at schema time")
    print(f"  {'─'*72}")
    global _failures

    # (expression, expected_error_count, note)
    cases = [
        # ── Valid comparisons ──────────────────────────────────────────────
        ("force_hp_fraction < 0.40",               0, "numeric < numeric — ok"),
        ("force_unit_count == 0",                  0, "numeric == numeric — ok"),
        ("timer.elapsed_sec >= 180",               0, "numeric >= numeric — ok"),
        ("timer.expired == true",                  0, "boolean == boolean — ok"),
        ("bus.force_b_broken == false",            0, "boolean == boolean — ok"),
        ("structure_owner('x') == 'player'",       0, "string == string — ok"),
        # ── Type mismatches on == ──────────────────────────────────────────
        ("force_hp_fraction == 'enemy'",           1, "numeric == string — mismatch"),
        ("force_hp_fraction == true",              1, "numeric == boolean — mismatch"),
        ("bus.force_b_broken == 0.5",              1, "boolean == numeric — mismatch"),
        ("structure_owner('x') == 0.5",            1, "string == numeric — mismatch"),
        # ── Ordering ops on non-numeric ────────────────────────────────────
        ("structure_owner('x') < 'b'",            1, "string < string — ordering op invalid"),
        ("bus.force_b_broken < 0.5",               1, "boolean < numeric — both wrong"),
        ("timer.expired > false",                  1, "boolean > boolean — ordering op invalid"),
        # ── Nested: type error inside and/or ──────────────────────────────
        ("force_hp_fraction < 0.4 and structure_owner('x') == 'p'",
                                                   0, "valid and — ok"),
        ("force_hp_fraction < 0.4 and bus.flag == 0.5",
                                                   1, "valid lhs, bad rhs — 1 error"),
    ]

    print(f"  {'Expression':<50}  {'Exp':>4}  {'Got':>4}  Status  Note")
    print(f"  {'─'*50}  {'─':>4}  {'─':>4}  ──────  ────")
    for expr, exp_count, note in cases:
        errs = validate(expr)
        got = len(errs)
        ok = got == exp_count
        if not ok:
            _failures += 1
        status = PASS if ok else FAIL
        detail = f"  [{errs[0]}]" if errs else ""
        print(f"  {expr:<50}  {exp_count:>4}  {got:>4}  {status}  {note}{detail}")


def test_parse_cache() -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  PARSE CACHE")
    print(f"  {'─'*72}")
    global _failures

    # Clear cache so we have a controlled baseline
    _parse_cache.clear()
    expr = "force_hp_fraction < 0.40"

    size_before = cache_size()
    node1 = _parse(expr)
    size_after_first = cache_size()
    node2 = _parse(expr)
    size_after_second = cache_size()

    ok1 = size_after_first == size_before + 1
    ok2 = size_after_second == size_after_first
    ok3 = node1 is node2   # same object — cache hit returns exact same AST

    def _prow(label, ok):
        global _failures
        if not ok:
            _failures += 1
        print(f"  {label:<60}  {PASS if ok else FAIL}")

    _prow(f"cache grows by 1 on first parse ({size_before} → {size_after_first})", ok1)
    _prow(f"cache size unchanged on second parse (stays {size_after_first})", ok2)
    _prow("second parse returns identical AST object (cache hit)", ok3)


def test_validate_function() -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  VALIDATE() — schema-time flag checking")
    print(f"  {'─'*72}")
    global _failures

    declared = {"force_b_broken", "objective_reached", "inner_breach"}

    cases = [
        ("force_hp_fraction < 0.40",                       declared,  0,  "valid expr — no errors"),
        ("bus.force_b_broken",                             declared,  0,  "declared flag — no errors"),
        ("bus.undeclared_flag",                            declared,  1,  "undeclared flag — 1 error"),
        ("bus.force_b_broken and bus.stale_ref",          declared,  1,  "one undeclared — 1 error"),
        ("bus.stale_a and bus.stale_b",                   declared,  2,  "two undeclared — 2 errors"),
        ("force_hp_fraction < <",                         declared,  1,  "syntax error — 1 error"),
        ("bus.force_b_broken",                            None,      0,  "None declared set — skip check"),
    ]

    print(f"  {'Expression':<44}  {'Decl':<5}  {'Exp':>4}  {'Got':>4}  Status")
    print(f"  {'─'*44}  {'─'*5}  {'─':>4}  {'─':>4}  ──────")
    for expr, decl, exp_count, note in cases:
        errs = validate(expr, decl)
        got = len(errs)
        ok = got == exp_count
        if not ok:
            _failures += 1
        decl_s = "None" if decl is None else f"{len(decl)}f"
        status = PASS if ok else FAIL
        print(f"  {expr:<44}  {decl_s:<5}  {exp_count:>4}  {got:>4}  {status}  # {note}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 74)
    print("  STAGE 7.5 CHECKPOINT A — Condition Language")
    print("=" * 74)

    test_numeric_predicates()
    test_timer_predicates()
    test_bus_predicates()
    test_boolean_logic()
    test_callable_predicates()
    test_literal_values()
    test_adversarial_inputs()
    test_type_inference()
    test_parse_cache()
    test_validate_function()

    print()
    print("=" * 74)
    if _failures == 0:
        print(f"  {PASS}  All condition language tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 74)
    sys.exit(0 if _failures == 0 else 1)
