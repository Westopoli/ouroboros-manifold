# Spec 03: the mission clock tests move to 30 to 60 minutes (tests only)

You are a Claude Sonnet 4.6 worker chat acting as the **test writer**. You execute this spec directly. You do not spawn agents, redesign, or widen scope. You edit tests only; you never edit `csrc/`. The tests you produce must be **red** against current main: that is the point. A builder (spec 04) makes them green afterwards.

## Why

The bible now says a mission's base clock is 30 to 60 minutes of battle time, by archetype (E-10 R-076-02, closed by Q-076-01 and Q-076-02, Westley 2026-09-29). The tests still pin the retired 3 to 4.5 minute table, so they pass against wrong code. Tests are the spec: they change first.

## Where

Your own clone of the repo, never `~/Projects/ouroboros-manifold`:
```
git clone --branch main "$(git -C ~/Projects/ouroboros-manifold remote get-url origin)" ~/Projects/relay-03
cd ~/Projects/relay-03 && git checkout -b relay/03-clock-tests
```
Build the library once so the tests can load it: `make -j8` (produces `libouroboros.so` and `libouroboros_dbg.so`). Run tests with `~/Projects/ouroboros-manifold/.venv/bin/pytest`.

## Files you may edit

- `tests/csim/test_E10_S076_the_clock.py`
- `tests/csim/test_E15_S126_most_of_my_force_is_out_there.py` (only if step 3 finds it asserts on the base-time table)

Nothing else.

## The rule the tests prove

E-10 S-076, R-076-02: base time B by archetype, in minutes of battle time; ticks = minutes × 60 × `TACTICAL_TICK_RATE` (20).

| id | archetype | minutes | ticks |
|---|---|---|---|
| 0 | DEFENSIVE_STAND | 37.5 | 45000 |
| 1 | SIEGE_BREAKING | 60 | 72000 |
| 2 | RECONQUEST | 45 | 54000 |
| 3 | ASSAULT | 52.5 | 63000 |
| 4 | SUPPRESSION | 30 | 36000 |
| 5 | MULTI_FRONT_DEFENSE | 60 | 72000 |
| 6 | INTERCEPTION | 37.5 | 45000 |
| 7 | EVACUATION | 30 | 36000 |
| 8 | CONTAINMENT | 52.5 | 63000 |
| 9 | COUNTERINSURGENCY | 37.5 | 45000 |

R-076-01 is unchanged: `limit = max(B · (1 − 0.2 · u), 0.6 · B)`. The floor stays 0.6·B, so the shortest possible mission is 18 minutes (21600 ticks) and that is by design.

## Steps

1. Read `tests/csim/test_E10_S076_the_clock.py`. `test_R_076_02_they_minutes_in_table_q` holds an `expected_minutes` dict of the old values and a docstring that still mentions Q-076-01's old wording. Replace the dict with the table above and rewrite the docstring to: `Given base times, When read, Then each archetype's base time is the minutes in the R-076-02 table (30 to 60 minutes of battle time; Q-076-01 and Q-076-02, Westley 2026-09-29).` Keep the test's shape (`lib.om_archetype_base_time_ticks(archetype_id)` compared with `int(minutes * 60 * 20)`); do not change how it calls the library.
2. `test_R_076_01_limit_max_b_1_0` uses `base_ticks = 3600` as an example input to `om_mission_compute_time_limit`. That is a formula test and stays valid; change the example to a real base (45000, defensive stand) and recompute its expected values (u = 0 → 45000; u = 1.0 → 36000; u = 1.5 → 31500, which is 0.7·B and still above the 0.6 floor of 27000). Add one case at u = 2.5 where the candidate 0.5·B is below the floor, expecting 27000. Keep the R-076-01 docstring; update the comments.
3. Read `tests/csim/test_E15_S126_most_of_my_force_is_out_there.py`. It passes `3600` as `time_limit_ticks` to `om_mission_compute_reinforcement_capacity`. If that value is only an input to a formula, leave the file alone. If any assertion depends on the base-time table itself, update it to the table above and say so in the report.
4. Run `~/Projects/ouroboros-manifold/.venv/bin/pytest tests/csim/test_E10_S076_the_clock.py -q`. Expect `test_R_076_02_they_minutes_in_table_q` to **fail** (the library still holds the old table) and `test_R_076_01_limit_max_b_1_0` to **pass** (pure formula). If R-076-02 passes, you have not changed the values; stop and re-read step 1.
5. Run `~/Projects/ouroboros-manifold/.venv/bin/pytest tests/csim -q -x --deselect tests/csim/test_E10_S076_the_clock.py::test_R_076_02_they_minutes_in_table_q` and confirm nothing else broke.
6. Commit the edited test file(s) by name, message in plain prose ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, and `git push origin relay/03-clock-tests`. Stop.

## Report (your last message, nothing after it)

```
Branch: relay/03-clock-tests (commit <hash>)
Files: <list>
Red on main: <name of the failing test and its one-line assertion message>
Rest of tests/csim: <pass count / fail count>
S126: <"unchanged, input only" or what you changed>
Open: <anything, or "none">
```
