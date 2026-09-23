# leaf-02-Q1 — test_R_083_03 conflicts with test_R_081_01 on om_unit_deal_damage's category multiplier

Not a small choice. Genuine conflict between two fenced tests, both "must
stay green" / "must go green" for this leaf. Cannot satisfy both with one
consistent `om_unit_deal_damage`. Proceeded under best-guess below; did not
edit either test.

## The conflict

`om_unit_deal_damage(w, p1, p2, p3)` (B10-1, already landed, frozen) applies
`p3 * category_multiplier(attacker->category, target->category)`.
`tests/csim/test_E11_S081_three_categories_a_soft_triangle.py::test_R_081_01`
tests this directly and exhaustively over all 9 category pairs, e.g.
(Strike, Line): spawns attacker category Strike, target category Line,
calls `om_unit_deal_damage(w, atk, tgt, 20.0)`, asserts damage dealt ==
`20.0 * 0.75` == 15.0. This test is fenced, already green, mandatory
regression gate for this leaf ("must stay green", "not optional").

`test_E11_S083_stats_traits_ability.py::test_R_083_03` spawns a Raider
(category Strike, per the B10-1 roster) attacking a Vanguard (category
Line), calls `om_unit_deal_damage(w, enemy, friendly_in, 50.0)`, and
asserts the damage dealt == exactly `50.0 * 0.90` == 45.0 (10% Warden aura
reduction, comment says "takes 50.0 * 0.9 = 45.0"). It also asserts a
second Vanguard *outside* aura range takes exactly `50.0` (zero reduction).

Both assertions require the Strike-vs-Line category multiplier (0.75, per
`docs/bible/algorithms.md` ALG-60 and the S-081 contract) to be 1.0 for
this call. It is not — 0.75 is required by S-081, is the bible's own
number, and is unconditionally baked into the already-frozen
`om_unit_deal_damage`. `base_hit * mult * (1 - reduction)` cannot equal
both `50*0.75*(1-0.10)=33.75` (correct per ALG-60) and `50*0.90=45.0`
(what the test hardcodes) for the same call. Confirmed empirically:
implementing the ALG-60-correct formula (category mult times aura
reduction, exactly what `om_unit_deal_damage` already does for S-081)
gives `dmg_in == 33.75`, not 45.0 — pytest run attached below.

```
FAILED tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_03_that_unit_takes_10_percent
assert 33.75 == 45.0 ± 1.0e-06
```

The same test's very next assertion (friendly_out, no aura in range) would
independently fail too: it expects exactly `50.0` (zero reduction), but
Strike-vs-Line at 0.75 gives `37.5` even with zero aura reduction. Both
failures trace to the same root cause: the test's author appears to have
picked a Strike-attacks-Line matchup without accounting for the 0.75
category multiplier that S-081 already requires `om_unit_deal_damage` to
apply unconditionally. Likely fix on the test side: use a same-category
attacker/target pair (mult 1.0) for the aura-isolation assertions, or spawn
the enemy pre-multiplied. Not mine to make — do not edit test files.

## What I did

Implemented `om_unit_deal_damage` per ALG-60 (category mult × Warden aura
reduction), matching the already-frozen, S-081-verified behavior, and
extended it with the aura reduction exactly as instructed. This keeps
S-081/S-082 green (13/13 there) and gets 12/13 assertions in
`test_E11_S083_stats_traits_ability.py` green, including both aura-regen
checks (0.075 for one Warden, 0.150 for two Wardens — the numbers the spec
says are actually load-bearing). The one failure is
`test_R_083_03_that_unit_takes_10_percent`, on the `dmg_in`/`dmg_out`
assertions described above.

I did not weaken, special-case, or bypass the category multiplier to force
this number — that would silently break the S-081 contract for every other
matchup a caller might use, or require an unprincipled "skip category math
when a Warden aura is present" carve-out invented for this one test, with
no basis in the bible or ALG-60.

## Best-guess I proceeded under

Prioritized S-081/S-082 (explicit, repeated "mandatory regression check,
not optional" instruction) over this one test's exact number. Reported the
resulting single test failure honestly rather than claim full green.
