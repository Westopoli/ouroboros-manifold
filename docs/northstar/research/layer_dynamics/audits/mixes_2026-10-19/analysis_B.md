# Roster mixes for the skill lab: analyst B

Analyst B (Opus), 2026-10-19. Read-only on the repository. Code is cited at `origin/push/labrev2-lab` = `4c638fc0` (detached worktree `~/Projects/om-push/wt/mixB`). Docs are cited at `origin/main`. Every run is in section E, with its command. Raw output is in `runs/` beside this file. "Measured" means I ran it. "Reasoning" means I did not.

---

## A. The six types

Stats come from E-11 R-082-01 and match the engine (`csrc/unit.c:491-532`; read back through `Engine.type_stats`). Reach comes from E-01 R-164-01, and the lab writes it in `scripts/skilllab/plays_space.py:48`. The engine's built-in reach is (0, 0) for every type, so the lab must set reach itself (measured: `profile_reach` returns (0, 0) for all six).

| Type | Role | Category | Range wu | Sensor wu | Reach up / down | Speed | HP | Special as the lab runs it | In mixes (spec) | In the batch that actually runs |
|---|---|---|---|---|---|---|---|---|---|---|
| Raider | flanker | Strike | 200 | 800 | 1 / 1 | 150 | 250 | Surge: off (abilities disabled) | M1, M3b (one unit) | yes (M1: s3_layer_above, s3_dark_striker) |
| Interceptor | screen | Strike | 250 | 1000 | 2 / 1 | 130 | 325 | Intercept: off | M2 | yes (M2: s3_types_by_reach) |
| Vanguard | frontliner | Line | 300 | 700 | 0 / 0 | 80 | 500 | Brace: off | M0 to M4 | yes |
| Warden | support | Line | 350 | 800 | 0 / 0 | 70 | 375 | **Aura stays ON**: 10 % damage reduction (diminishing) and 1.5 HP/s regen per Warden in 300 wu, stacking linearly | **none** | **no** |
| Bombard | artillery | Siege | 1200 | 300 | 0 / 2 | 50 | 400 | 150 wu area disc (a stat, so it stays on); Barrage off | M3, M3b | **no** |
| Bastion | anchor | Siege | 800 | 300 | 0 / 2 | 40 | 1050 | Fortify: off | M4 | **no** |

Notes on the table:
- Abilities are off in every lab fight. `Setup.abilities` defaults to False (`contract.py:85`), and the auto-trigger is skipped when they are off (`unit.c:1646`).
- The Warden aura is not an ability. Neither its regen (`unit.c:2301` calls `om_tactical_apply_aura_regen` every tick) nor its reduction (`unit.c:1057`) checks that switch. The Warden is therefore the only type besides the Bombard whose special is live in the lab.
- A Warden must stay a built-in type to keep its aura. The aura is keyed on type id 3 (`unit.c:974`). A lab-registered copy (`fight.py:42`, ids from 100) would lose it. Line reach is (0, 0) anyway, so the Warden needs no `unit_types` entry.

**The unused types.** As the spec writes the mixes (M0 to M4, M3b), only the **Warden** is missing. In the batch that actually runs, `sweep.PLAYS_BY_FAMILY` (`sweep.py:28-30`) uses only s3_layer_above, s3_types_by_reach and s3_dark_striker (M1, M2) plus s2_concave and s2_mass_one_end (M0). The smoke run uses only the two vision plays. So the **Bombard and the Bastion** never fight in a sweep either: they appear only in plays no family runs (s2_screen, s3_over_the_choke, s1_outrange). On either reading, at least two types go untuned.

What they would have shown (measured, section E):
- **Warden.** Its aura makes elimination impossible at density. 16 Wardens a side capped in 20 of 20 fights. 8 Wardens with 8 Vanguards capped in 6 of 20. 8 Raiders with 8 Wardens capped in 11 of 20. 2 or 4 Wardens in 16 capped in 0 of 16. So the Warden can enter the lab now at 2 to 4 per 16. At higher density it collides with ruling 1.
- **Bombard and Bastion.** They are the only types that fire two layers down. They give the largest formation gain I measured: Bastions screening Bombards beat 21 against a naive break-even of 13, which is +8 units. With Siege two layers up and a type below that can fire up two layers, the up-2 penalty moves the break-even from 18 to 38. That is a crossing inside the ruled band, and it sits on a knob the current sweep cannot move.

## B. What a "line crossing" is here

A fight is 16 units against N enemies, N from 8 to 48. Both sides field the same unit mix (ruling 2) and fight to elimination (ruling 1). The **break-even** is the largest N the 16 still beat in every fight of a cell. A skilled arrangement is worth its break-even minus the naive arrangement's.

**The measure (ruling 5).**
- The result is who was left standing.
- The firing count predicts who should have won. Every 5 ticks it counts the units on each side able to fire: the target is seen, is in reach and range at that layer offset, the line is clear, and (later) it is inside the firing arc.
- Two predictions are made per fight, over the first 40 ticks after contact. One counts able units. The other weights each able unit by the ALG-60 category multiplier against its target of record.
- The agreement column records whether each prediction matched the survivor. A miss is a finding: "there's a number that's off".

**A line** is the edge, in settings space, of where one condition holds. **A crossing** is where all the conditions hold at once. A knob value where a play's break-even flips from below 16 to above it, or from no gain to gain, marks a line. More than one region can qualify, and each is a candidate Climate of War.

**The conditions.**
- **C0, control.** In a mirrored fight the larger force wins, and the break-even sits at equal numbers.
- **C1, skill wins the firing count.** The skilled side's firing advantage beats the noise of the mirror control. It is checked against both naive baselines (ruling 3).
- **C2, the result follows the firing count.** Rank agreement is at least 0.8, and no more than one fight in five is more than 25 % off the trend.

## C. The gap

### C1. The ALG-60 category matrix: which cells any mix exercises

A mix of categories {A, B} produces every attacker-to-target cell among A and B. The sweep column shows whether the batch that runs today reaches that cell.

| Attacker → target | Multiplier | Mixes with this cell | Swept today |
|---|---|---|---|
| Strike → Strike | 1.0 | M1, M2 | yes |
| Strike → Line | 0.75 | M1, M2 | yes |
| Strike → Siege | **1.5** | only M3b (one Raider) | **no** |
| Line → Strike | 1.5 | M1, M2 | yes |
| Line → Line | 1.0 | all | yes |
| Line → Siege | 0.75 | M3, M4 | **no** |
| Siege → Strike | **0.20** (Q-081-01: 0.75 in the bible) | only M3b (one Raider) | **no** |
| Siege → Line | 1.5 | M3, M4 | **no** |
| Siege → Siege | 1.0 | M3, M4 (Bombard to Bombard, Bastion to Bastion only) | **no** |

- The sweep reaches 4 of 9 cells.
- The two most extreme cells are never measured with weight: 1.5 and 0.20, the Strike-Siege pair. The 0.20 is the number register row Q-081-01 says is disputed.
- The type-weighted prediction can only differ from the count-only one where the cells differ. On Line and Strike mixes the weights span only 0.75 to 1.5.

### C2. Reach pairings: which layer offsets ever occur

The offset is the target's layer minus the shooter's layer.

| Offset | Types that can fire | Return fire possible from | Plays with it | Knobs that act there | Swept today |
|---|---|---|---|---|---|
| +1 (fire up one) | Raider, Interceptor | the target, if it can fire down one: Raider, Interceptor, Siege | s3_layer_above, s3_types_by_reach (the naive side fires up) | RANGE_UP_1, DAMAGE_UP_1, VISION_*_1 | yes |
| −1 (fire down one) | Raider, Interceptor, Bombard, Bastion | Raider, Interceptor | the same two plays (the skilled side fires down) | RANGE_DOWN_1 (held at 1.0) | yes |
| +2 (fire up two) | **Interceptor only** | Siege (fires down two) | **none** | RANGE_UP_2, DAMAGE_UP_2, VISION_*_2 | **no: these knobs are inert** |
| −2 (fire down two) | **Bombard, Bastion** | Interceptor only | s3_over_the_choke (not swept) | RANGE_DOWN_2, VISION_*_2 | **no** |

**The two-layer knobs are dead in the current batch (measured, E3c).** The sweep sets RANGE_UP_2 and DAMAGE_UP_2 together with the one-layer values (`sweep.py:76-82`). No swept play ever puts two layers between a shooter and its target. I set RANGE_UP_2 and DAMAGE_UP_2 to 0.25 and VISION_*_2 to 0.05 on s3_types_by_reach and s3_layer_above at 16 against 20. The outcome, ticks, survivors and margin were identical to base in every fight. The one-layer knobs at 0.25 changed every result. Half the vision, range and damage parameter space is swept and cannot move a result.

### C3. Arrangements and families

- **Cone.** The cone family attaches its cone to the Vanguard only (`sweep.py:95-96`), on two all-Vanguard plays. So the cone is measured only Line against Line. It is never measured on the Bombard, where it replaces the disc (R-084-03), and never on a mixed target set, where the multiplier changes per victim.
- **Arc.** The arc runs only on M0 (all Vanguard), so turn rates per category (ALG-69: Strike 6.0, Line 4.0, Siege 2.5 rad/s) never differ inside a fight. Arc is the family where Siege's slow turn should matter most. (Reasoning.)
- **One baseline has the wrong mix (measured, E3b).** The `naive_attacker` baseline is built from `scenes._groups_and_timeline`'s naive branch (`scenes.py:133-136`), which fields 16 Vanguards against Vanguards whatever the play's mix. On layout 81, s3_layer_above and s3_types_by_reach read `naive_attacker side0 {Vanguard@L0: 16} side1 {Vanguard@L0: 16}`, while the play itself is 8 Raiders or Interceptors and 8 Vanguards. Ruling 2 still holds inside that one fight. But C1 "against a naive attacker" compares an M1 or M2 play with an M0 fight. The other two baselines do keep the mix (`sweep.py:290-310`).

### C4. Per type

| Type | What is never measured today |
|---|---|
| Warden | Everything. Its aura is the only live special besides the Bombard disc. |
| Bombard | The −2 offset, the disc against mixed targets, the cone on a Siege type, and Siege → Strike 0.20 |
| Bastion | Its tank role (1050 HP) in any swept play; −2 fire |
| Interceptor | Its unique +2 reach. It is used only as a +1 type, which a Raider also covers. |
| Raider | Against Siege: the S5 flank matchup "Strike beats Siege" |
| Vanguard | Covered |

## D. Proposed layouts

Design rules I kept:
- Same mix on both sides.
- Two types per mix, so a crossing can be pinned on one pairing.
- One six-type mix, kept as a robustness check only.
- Every play is a skilled arrangement against the existing naive baselines.
- Bands as ruled (rulings 10 and 11): coarse first, refine only at a sign change.

The mixes:
- Keep M0 to M4 and M3b, and add **M5 to M10**.
- Run M3, M3b and M4 under families. Today they are written but never swept.
- **Step 0 for every new mix:** a 30-fight naive mirror (C0) before any sweep. It rejects a mix that caps. My E1 is exactly that step, and it is what rejected the Warden-heavy mixes.

### D1. Mixes and plays

| Mix | Composition (per 16) | Play (side 0 skilled; side 1 naive blob per type) | Covers | Families | Crossing it looks for | Measured so far |
|---|---|---|---|---|---|---|
| M5 Strike-Siege | 8 Raider + 8 Bombard | `s5_vulnerable_away` (Bombards 400 back, Raiders forward); `s2_screen` with Raiders as the screen | S→Si 1.5, Si→S 0.20, Si→Si with the disc | base, cone on **Bombard** (range 150, 300, 600 at 45°), arc 360 to 90 | Where the Bombard's 0.20 against Strike makes the screen order matter. Whether a cone on the Bombard flips it. | screen 14 = naive 14: no gain at base in a meeting |
| M6 Reach duel | 8 Interceptor + 8 Bombard | **new `s3_siege_high`**: Bombards two layers up, Interceptors on the enemy's layer | +2 and −2, the only two-way two-layer pairing | RANGE_UP_2 and DAMAGE_UP_2 swept **on their own** (1.0, 0.75, 0.5, 0.25), VISION_*_2 (0.05 to 0.4) | The up-2 penalty at which Siege up high starts to dominate | **break-even 18 at 1.0, 38 at 0.25; naive 15. The crossing is inside the band.** |
| M7 Fire from below | 8 Raider + 8 Interceptor | **new `s3_fire_from_below`**: enemy two layers up; Interceptors stay low, Raiders meet the enemy on its layer | +2 one-way (the README's S3 counter "bring the type that fires upward") | RANGE_UP_2, DAMAGE_UP_2 on their own | The penalty at which firing up two stops being a ceiling | ceiling at 1.0 (beats 48); 26 at 0.25; caps above 27 |
| M8 Siege pair | 8 Bombard + 8 Bastion | `s2_screen` with Bastions as the screen | Si→Si, the disc against a tank | base, cone on Bombard, arc | Formation gain inside Siege, and whether the cone erases it | **screen beats 21, naive 13: +8, the largest gain measured** |
| M9 Warden support | 12 Vanguard + 4 Warden (never more than 4) | `s2_concave` and `s2_spread_line` with the Wardens at the centre; a "Wardens at one end" variant | the aura (the sixth type's special), L→L | base, arc | Whether a spread line that leaves the aura's 300 wu loses its formation gain | mirror no caps at 2 or 4 Wardens; caps at 8 or more |
| M10 All six | 3 Raider, 3 Interceptor, 3 Vanguard, 2 Warden, 3 Bombard, 2 Bastion | the two layer plays with each type on its best layer; the naive mirror | every cell at once | base only (C8-style robustness) | Whether a crossing found on a pair survives in a full army | mirror: break-even 16, no caps |
| M3 (existing) | 8 Vanguard + 8 Bombard | `s2_screen`; **new `s3_siege_high_line`**: Bombards two up over Vanguards | L↔Si; −2 one-way | cone on Bombard, VISION_DOWN_2 | Siege blind two layers down (sensor 300 × 0.2 = 60 wu) without a spotter | screen 15 = naive 15; Bombards two up hit the ceiling (beats 48): one-way, a control only |
| M3b (existing) | 7 Vanguard + 1 Raider + 8 Bombard | `s3_over_the_choke` | the spotter | VISION_DOWN_2 | how far below the base vision the spotter keeps the Bombards firing | not run |
| M4 (existing) | 8 Vanguard + 8 Bastion | `s1_outrange` | L↔Si, range 800 | base, arc | outrange against the hold | Bastion fights are long: mean 5000 to 10600 ticks; 1 cap at 16 v 16 |

Every pairing covered:
- **ALG-60 cells:**
  - L↔S: M1, M2
  - L↔Si: M3, M4
  - S↔Si: M5, M6
  - Si↔Si: M8
  - S↔S: M7
  - all at once: M10
- **Reach offsets:** ±1 (M1, M2), +2 two-way (M6), +2 one-way (M7), −2 one-way (M3 high, M3b)
- **Specials:** the disc (M5, M6, M8), the cone on Siege (M5, M8), the aura (M9)

**Asymmetric control.** I propose none. The planted 20 % damage control stays the only one. The one-way reach scenes (M3 Bombards two up, M7 at 1.0) behave like ceiling controls: they show the instrument can see a total advantage. They should be labelled as controls, not plays.

### D2. Fights per batch

A scan with bisection at 3 replicates is 6 coarse cells plus about 3 bisection cells, at 6 fights each: about 54 fights. My measured scans at 2 replicates were 24 to 36 fights. Roles per point: s3 plays 4 (play plus 3 baselines), others 3. Layouts: the 3 smoke layouts.

| Row | Points | Plays × roles × layouts | Fights |
|---|---|---|---|
| Step 0: C0 mirror for M5 to M10 (5 headcounts × 6 fights) | 1 | 6 mixes | 180 |
| M6 s3_siege_high: up-2 range 4, up-2 damage 4, vision-2 4 | 12 | 1 × 4 × 3 | 7,776 |
| M7 s3_fire_from_below: up-2 range 4, damage 4 | 8 | 1 × 4 × 3 | 5,184 |
| M5: base + cone 3 + arc 5 | 9 | 2 × 3 × 3 | 8,748 |
| M8 s2_screen: base + cone 3 + arc 5 | 9 | 1 × 3 × 3 | 4,374 |
| M9 concave and spread line: base + arc 5 | 6 | 2 × 3 × 3 | 5,832 |
| M3 s2_screen (cone 3 + base) and s3_siege_high_line (vision-2 4) | 4 + 4 | 3 × 3 and 4 × 3 | 1,944 + 2,592 |
| M3b s3_over_the_choke: vision-2 4 | 4 | 1 × 4 × 3 | 2,592 |
| M4 s1_outrange: base + arc 5 | 6 | 1 × 3 × 3 | 2,916 |
| M10 robustness: two layer plays at base | 1 | 2 × 4 × 3 | 1,296 |
| **Total** | | | **about 43,400** |

- At 0.4 s a fight that is **about 4.8 CPU-hours, or about 24 minutes wall at 12 workers**. That is well under the 4-hour mark of ruling 13.
- **Correction.** 0.4 s is a 16 v 48 Vanguard-scale fight. Fight length varies by mix (E1, mean ticks):
  - Raider and Bombard mixes: 500 to 1,000 ticks
  - Vanguard mixes: 2,300 to 3,600 ticks
  - Bastion mixes: 4,700 to 11,700 ticks
- Weighting the Bastion and Warden rows (M4, M8, M9; about 13,100 fights) at three times the cost gives **about 7.7 CPU-hours, about 39 minutes at 12 workers**.
- Refinement adds at most two rounds of about 54 fights per role, per sign change found.
- Order: Step 0 first, then M6 and M7 (they make dead knobs live), then M5 and M8 (matrix cells), then M9, M3, M3b, M4, and M10 last.

## E. Evidence

Every run used `~/Projects/ouroboros-manifold/.venv/bin/python` and the lab's own `fight()`, `scan.scan()` (bisection, 2 replicates × both spawn orders = 4 fights per cell) and `pool.FightPool`. The library is built by `make` at `4c638fc0`.

The scenes are mine, in `mixlib.py`:
- a meeting: both sides attack-move to (0, 0) from 900 wu apart, with no terrain
- side 0 has 16 units; side 1 is the same mix scaled to N by largest remainder
- reach is set as in `plays_space._types`; the Warden and Vanguard stay built-in

These are **not** the sweep's placed layouts. They show what a mix can reveal, not what the sweep's layouts will measure.

The machine load was about 15 on 16 cores throughout, so wall times are pessimistic. Total lab run time was about 14 minutes. That includes one 10-minute run lost to a missing `__main__` guard in my script (exp3), which re-spawned workers and was killed by `timeout 600`. It produced no data.

**E1. Naive mirror per mix.** Command: `timeout 600 python exp1_mirrors.py 8 runs/exp1.json`. 300 fights in 51 s. Wins for the 16 out of 4 fights, at N = 12 / 15 / 16 / 17 / 20.

| Mix | 12 | 15 | 16 | 17 | 20 | Caps | Mean ticks at 16 |
|---|---|---|---|---|---|---|---|
| M0 V16 | 4 | 4 | 0 | 2 | 0 | 0 | 3,232 |
| M1 V8 R8 | 4 | 3 | 1 | 0 | 0 | 0 | 2,738 |
| M2 V8 I8 | 4 | 3 | 1 | 0 | 0 | 0 | 2,834 |
| M3 V8 B8 | 4 | 4 | 3 | 3 | 0 | 0 | 1,247 |
| M4 V8 Bas8 | 4 | 4 | 1 | 1 | 0 | **1** | 10,600 |
| **W16** | 0 | 0 | 0 | 0 | 0 | **20 of 20** | 12,000 (cap) |
| **V8 W8** | 3 | 1 | 2 | 1 | 0 | **6** | 8,758 |
| **R8 W8** | 4 | 2 | 0 | 0 | 0 | **11** | 12,000 |
| R8 B8 | 4 | 2 | 0 | 0 | 0 | 0 | 1,016 |
| I8 Bas8 | 4 | 2 | 1 | 0 | 0 | 0 | 7,340 |
| R16 / B16 / Bas16 / I16 | C0 holds | | | | | Bas16: 3 caps at 16 | 978 / 936 / 11,722 / 2,262 |
| Six-type mix | 4 | 4 | 2 | 0 | 0 | 0 | 2,138 |

What E1 shows:
- C0 holds on every mix without Wardens, within the noise of 4 fights.
- Warden density above 4 per 16 breaks ruling 1.
- Bastion-heavy mixes run close to the 12,000-tick cap at equal numbers.
- Agreement counts per mix are in `runs/exp1.json`. Siege mixes predicted best: B16 16 of 16 both_right, Bas16 16 of 16. Raider-heavy mixes predicted worst: R16 had 10 both_wrong in 20.

**E2. Skilled against naive, same mix.** Command: `timeout 600 python exp2_skill.py 8 runs/exp2.json`. Break-even for the 16:

| Scene | Beats | Loses to | Fights |
|---|---|---|---|
| R8 B8 naive / Raider screen | 14 / 14 | 15 / 15 | 36 / 36 |
| I8 B8 naive | 15 | 16 | 36 |
| I8 B8, Bombards two up, up-2 = 1.0 | **18** | 19 | 36 |
| I8 B8, Bombards two up, up-2 = 0.25 | **38** | 39 (caps from 39) | 36 |
| V8 B8 naive / Vanguard screen (M3 s2_screen shape) | 15 / 15 | 16 / 16 | 36 / 36 |
| V8 B8, Bombards two up | **48, ceiling** | none | 24 |

**E3b. Baseline rosters.** Command: `python exp3b_rosters.py` (15 s, no fights). It found the all-Vanguard `naive_attacker` described in C3.

**E3c. Dead knobs and Warden density.** Command: `timeout 600 python exp3c_knob_warden.py`. 28 fights in 17 s.
- On s3_types_by_reach at 16 v 20, base and "two-layer knobs 0.25" give identical rows: `(cap, 12000, (2, 7))` and `(side1, 2420, (0, 7))`. "One-layer knobs 0.25" gives `(side0, 5133, (8, 0))` and `(side0, 4215, (8, 0))`.
- On s3_layer_above, base and the two-layer knobs are again identical, and the one-layer knobs change the result.
- Side note: the unplaced (no terrain) builds of these two current plays capped in 1 of 2 fights each at 16 v 20. Whether the placed sweep scenes cap too is not tested here.
- Warden mixes, 4 fights each at N = 16 and 20: V14 W2, V12 W4, R7 V7 W2 and B7 V7 W2 gave **0 caps** in 16 fights.

**E4. More pairs.** Command: `timeout 600 python exp4_more.py 6 runs/exp4.json`.

| Scene | Beats | Loses to | Note |
|---|---|---|---|
| R8 I8 naive, all on layer 2 | 14 | 15 | |
| R8 I8 from below, up-2 = 1.0 | **48, ceiling** | none | |
| R8 I8 from below, up-2 = 0.25 | **26** | 27 | caps at 27 to 48 |
| B8 Bas8 naive | 13 | 14 | |
| B8 Bas8, Bastion screen | **21** | 22 | +8 units |
| R8 B8 flank (Raiders sent behind the Bombards) | none | none | **capped at 8 and 16: my flank scene is a lab defect, not a result** |

**Reasoning only, not measured:**
- the arc and cone effects per category
- the M9 concave-with-Wardens gain
- whether any of these crossings survive on the placed layouts
- the fight counts and CPU in D2, which come from scan arithmetic plus the E1 tick ratios

## F. Risks, and what I would not change

**Binding rules I keep untouched:**
- same mix both sides (ruling 2)
- elimination only, with the cap as a defect (ruling 1)
- scan 8 to 48 against 16, with ceiling hits reported (ruling 4)
- bands from the base value inside 0.25× to 4×, with one labelled sign-flip point (rulings 10 and 11)
- type weight = category multiplier only (ruling 5)

None of my mixes needs a new knob or a new asymmetry. The only change to how knobs are set is that M6 and M7 sweep RANGE_UP_2 and DAMAGE_UP_2 apart from the one-layer values. That is still inside the ruled band.

**Risks, each measured:**
1. **One-way reach scenes cap.**
   - Where it happened: M6 at up-2 0.25 from 39 enemies; M7 at 0.25 from 27; the flank scene.
   - Why: once the side that can reply is dead, what is left cannot see or hit the enemy, so the fight cannot end.
   - The pre-flight `no_reach` check (`scenes.py:258-272`) only looks at holders at the start, so it does not catch this.
   - Whether such a cell is a "defect" or a ceiling needs an Architect ruling. I do not decide it.
2. **Warden density.** More than 4 Wardens per 16 caps (E1). Whether the aura's linear regen stacking (R-083-03, 1.5 HP/s per Warden, `om_constants.h:558`) is intended at that density is a question for Westley, not a lab number. Until then, M9 holds at most 4.
3. **Bastion cost.** Bastion fights run 3 to 10 times longer than Raider fights, and M4 and Bas16 touch the cap at 16 v 16. The cap of 12,000 ticks may be too short for Bastion mixes. That is a number for Westley; I propose no change.
4. **Baseline mismatch.** `naive_attacker` is all Vanguard for every play (C3). Fixing it is a spec matter for the Architect. Until it is fixed, C1 against the naive attacker is not like for like on M1 to M10.
5. **My scenes are meetings without terrain.** The numbers in E show that each mix can reveal a crossing. They are not the sweep's values on the placed layouts.

**What I would not change:** M0 to M4 and M3b as ruled, the families' bands, the smoke run, the planted damage control, and abilities off. The Warden aura stays on because it is passive; that is the engine's rule, not the lab's.

---
Files: `analysis.md`, `mixlib.py`, `exp1_mirrors.py`, `exp2_skill.py`, `exp3b_rosters.py`, `exp3c_knob_warden.py`, `exp4_more.py`, `runs/exp1.json`, `runs/exp2.json`, `runs/exp4.json`, `runs/exp4.log`, `runs/exp3c.json`, `runs/exp3c.log`, all under `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B/`.
