# Bible Diagnostic Fix Spec — Sequential Implementation

> **For Claude Code.** This document specifies a sequence of fixes to bring the simulation
> in line with the game bible's designed experience. Fixes are **strictly ordered** — each
> fix depends on the previous one being verified before moving on.
>
> **Workflow for every fix:**
> 1. Read the fix spec (what to change and why)
> 2. Implement the change
> 3. Run the verification test specified in the fix
> 4. If the test passes → move to the next fix
> 5. If the test fails → **STOP and escalate to Westley** with: what you changed, what the test expected, what it produced, and your best guess at root cause
>
> **Do not skip ahead.** Do not combine fixes. Do not tune config values for a later fix
> while implementing an earlier one. Each fix is isolated so we can identify which change
> produced which effect.
>
> **Bible references:** Read `bible_simulation.md` sections "Uninhabited Region Mechanics",
> "Multi-Faction Agent Decision Model", "Simulation Pacing Targets", and "Per-Tick Update Model"
> before starting. Read `bible_world.md` section "World Generation — Tiered Templates" and
> "Civilizational Lifecycle — Mechanical Drivers".

---

## Fix 1: Starting Template — Add Empty Regions

### Problem

The `full_stack` / `05_full_stack` template generates 10 regions with only 2 empty (20%).
The bible specifies the isolated start template as "1 home, 2 frontier, 4–6 empty regions"
per faction cluster — meaning the world should have significantly more empty space than
inhabited territory at tick 0. With 4 factions each starting with 2 regions, the 8 inhabited
regions leave only 2 empties. Factions border each other immediately with no expansion buffer.

The bible's Phase 1 (Expansion) requires empty space: "Factions start with few regions and
low budgets. Empty regions adjacent to faction territory are cheap to colonize... Budget is
too low for confident attacks against defended regions. Result: factions expand into empty
space rather than fighting each other." This phase cannot exist if there's no empty space.

### What to Change

Modify the `full_stack` starting template (wherever templates are defined — likely in
world generation code or a template config):

- **Total regions:** Increase from 10 to at least 14–16
- **Empty regions:** At least 6 (targeting ~40% empty at start)
- **Layout rule:** Each faction must have at least 1 empty region adjacent to its territory
  that is NOT adjacent to another faction's starting territory. This creates the expansion
  buffer the bible requires — factions can colonize without immediately colliding.
- **Keep faction starting regions the same:** Each faction still starts with 2 regions
  (1 home + 1 frontier, or 2 frontiers — whatever the current template uses). Do not change
  starting field values.

The exact topology is up to you as long as the layout rule is satisfied. A simple approach:
each faction's frontier connects to 1–2 dedicated empty regions in a chain, and some empty
regions sit between faction clusters as contested middle ground.

### Verification Test

Run `bible_diagnostic.py` (or equivalent 500-tick run, seed 1) and check Section 2:

```
PASS if:
  - Empty regions at start >= 6
  - Empty fraction >= 35%
  - Each original faction's frontier is adjacent to at least 1 empty region
    (verify by inspecting the adjacency graph or the #Col column in Section 9 —
    factions should see colonization candidates from tick 1)
```

**Do not proceed to Fix 2 until Fix 1 passes.**

---

## Fix 2: Colonization Scoring — Empty Regions Must Enter the Colonize Pool

### Problem

The diagnostic's Section 9 shows `#Col = 0` and `ColScore = None` for every faction on
almost every tick in the first 50 ticks. This means empty regions are either not entering
the colonization candidate pool, or the colonization scoring function is not producing a
score.

At tick 10, the Fortifier "attacks" `region_e0` (military 6.5) — an empty region being
treated as an attack target instead of a colonization opportunity. The bible says:
"The colonize and attack decisions share a single candidate pool — the agent scores all
eligible targets (enemy-owned and uninhabited), picks the best one, and the target type
determines whether it's an attack or a colonization."

An uninhabited region should NEVER be an attack target. It has no defending faction.
If a region has no `faction_id`, it must enter the pool as a colonization candidate only.

### What to Change

In the agent decision logic (likely in `faction.py` or wherever `decide()` is implemented):

1. **Verify that uninhabited regions adjacent to the faction's territory are added to the
   colonization candidate list.** Check whatever filter determines "eligible targets" —
   uninhabited regions must pass it.

2. **Verify that uninhabited regions are NOT added to the attack candidate list.** A region
   with `faction_id = None` (or equivalent) should be excluded from attack evaluation.
   The Fortifier attacking `region_e0` at tick 10 is a bug if `region_e0` is unowned.

3. **Verify that the colonization scoring function runs and returns a numeric score** for
   each colonization candidate. The bible's scoring formula for uninhabited regions:
   - Weakness = 1.0 (maximum — no resistance)
   - Current value = 0 (uninhabited — nothing there yet)
   - Strategic position = based on what the empty region borders (neighboring factions,
     neighboring owned territory, other empty regions)
   - Final score = attractiveness × archetype_expand_weight

4. **Verify that colonization has a budget check:** The bible says colonization costs
   `COLONIZE_COST` (currently 20.0). The agent should only consider colonization if
   `budget >= COLONIZE_COST`. With `BUDGET_GROWTH_RATE = 0.025` and starting economies
   around 35–59, factions should reach budget 20 within roughly 10–20 ticks.

5. **Verify the scoring normalization:** The config shows `COLONIZE_NORM_RANGE = (0.0, 1.0)`
   and `ATTACK_NORM_RANGE = (0.0, 40.0)`. After normalization and archetype weight
   application, colonization must be able to outscore attacks against defended targets in
   the early game (when attack expected_net is negative). If colonize scores are normalized
   to 0–1 but attack scores are normalized from a range of 0–40, the scales may not be
   comparable. Check that the normalization produces scores on the same effective scale
   before archetype weights are applied.

### Verification Test

Run `bible_diagnostic.py` (500 ticks, seed 1) and check Section 9:

```
PASS if:
  - #Col > 0 for at least one faction on tick 1 (factions see colonization candidates)
  - ColScore is a numeric value (not None) when #Col > 0
  - Colonizations in Section 3 window 0-50 >= 4 (most factions colonize at least once
    in the first 50 ticks)
  - No attacks target uninhabited regions (AtkRID should never be a region with
    faction_id = None in the Section 9 output)
```

**Escalation triggers:**
- If `#Col` is still 0 after the template fix (Fix 1), the issue is in candidate pool
  filtering, not the template. Escalate with: the candidate pool filter code, the adjacency
  check, and which regions each faction sees as neighbors.
- If `ColScore` is numeric but always lower than `AtkScore`, the issue is normalization.
  Escalate with: the raw scores before and after normalization, the archetype weights, and
  the final compared values.

**Do not proceed to Fix 3 until Fix 2 passes.**

---

## Fix 3: Tension Equilibrium — Border Friction Overwhelms Decay

### Problem

The diagnostic's Section 6 shows mean tension of 94–99 across most regions in the last
200 ticks. Half the world is permanently at near-civil-war levels. The bible's proportional
tension decay is designed to prevent "permanent runaway spirals," but the current config
produces exactly that.

The math: `BORDER_FRICTION_TENSION = 0.5` per hostile neighbor per tick. A region with 2
hostile neighbors gets +1.0 tension/tick from friction. `TENSION_NATURAL_DECAY_RATE = 0.2`
is proportional, so at tension 80 it removes `0.2 * (80/100) = 0.16` per tick. The friction
input (1.0) is 6x the decay output (0.16). Tension can only equilibrate at very high
values where proportional decay catches up — which is near the ceiling.

The bible says regions should experience "background stress of contested borders" from
friction, not permanent maximum tension. The designed experience for an established faction
is "strategic depth," not perpetual crisis. Tension equilibrium for contested border regions
should be in the 40–60 range, with spikes to 70–80 during active conflict, and 90+ only
during acute crises (active conquest, revolt chains).

### What to Change

**Option A (preferred — smaller change):** Reduce `BORDER_FRICTION_TENSION` from 0.5 to
0.15. This makes friction a slow background stress (as the bible describes) rather than a
dominant force. With 2 hostile neighbors, friction adds +0.3/tick, and proportional decay
at tension 50 removes `0.2 * 0.5 = 0.1`, giving equilibrium around 50–60 for a region
with sustained hostile borders. Spikes from conquest events and revolt chains still push
tension higher.

**Option B (alternative):** Keep friction at 0.5 but increase `TENSION_NATURAL_DECAY_RATE`
to 0.5 or higher. This makes decay strong enough to counteract friction. Downside: faster
decay also means tension from conquest events and revolts dissipates faster, potentially
reducing the impact of those systems.

**Westley: if you have a preference for A vs B, tell Claude Code. If not, use Option A.**

**Important:** Do NOT change both friction and decay simultaneously. Change one value,
verify, and then adjust the other only if needed.

### Verification Test

Run `bible_diagnostic.py` (500 ticks, seed 1) and check Section 6:

```
PASS if:
  - No region has mean tension > 80 over the last 200 ticks
  - At least half the regions have mean tension in the 35–65 range
  - Regions that were recently conquered (check Section 4 for timing) show
    tension spikes to 70+ that decay back below 60 within 30–50 ticks
  - The tension floor is above 15 for border regions (friction should still matter,
    not be eliminated)
```

**Escalation triggers:**
- If tension is still above 80 after the friction reduction, the problem may be
  cumulative — friction + economic_tension + stress_pressure + subsistence_crisis all
  stacking. Escalate with: a per-region breakdown of tension sources for one high-tension
  region over 50 ticks (how much comes from friction, how much from economic_tension term,
  how much from stress_pressure, how much from natural decay).
- If tension drops below 20 everywhere, friction was overcorrected. Escalate with the
  same per-region breakdown.

**Do not proceed to Fix 4 until Fix 3 passes.**

---

## Fix 4: Attack Success Rate — 68% Repelled Is Too High

### Problem

Section 8 shows 68% of attacks are repelled, 20% contested, and only 6% produce territory
changes (collisions). The bible's pacing targets say "at least one conquest or territory
change is typical" per 20–30 tick window. With 85 conquests in 500 ticks, conquests do
happen — but the attack-to-conquest ratio (531 attacks → 85 conquests = 16% conversion)
means most military investment is wasted.

The bible says the simulation should be "dynamic, WorldBox-inspired" with "territory
changing hands regularly." A 68% repelled rate produces a grinding attrition simulation
where factions repeatedly throw budget at walls. The designed experience is that attacks
are meaningful decisions with consequences — some fail, but a well-timed attack against a
weakened target should succeed more often than not.

**Important:** This fix depends on Fix 3 (tension reduction) being complete first, because
lower tension → higher economy → faster budget growth → larger committed budgets → different
attack outcomes. The attack success rate may improve on its own once tension equilibrium
is fixed. Run the diagnostic AFTER Fix 3 and only proceed with Fix 4 if repelled rate is
still above 50%.

### What to Change (only if repelled > 50% after Fix 3)

The attack resolution formula is:
```
effective_attack = attack_strength * ATTACK_EFFICIENCY * tech_attack_mult * surprise_mult
effective_defense = defender_military * RESISTANCE_FACTOR * tech_defense_mult * entrenchment
net_force = effective_attack - effective_defense
```

The current values: `ATTACK_EFFICIENCY = 1.0`, `RESISTANCE_FACTOR = 0.65`,
`ENTRENCHMENT_MAX = 2.0`, `ENTRENCHMENT_RAMP_TICKS = 3`.

`ENTRENCHMENT_RAMP_TICKS = 3` means a region reaches maximum entrenchment (2.0x defense)
in only 3 ticks. Combined with `RESISTANCE_FACTOR = 0.65`, an entrenched defender has
effective defense of `military * 0.65 * 2.0 = military * 1.3`. To break through, the
attacker needs `committed * 1.0 > military * 1.3 + BREAKTHROUGH_THRESHOLD(15.0)`. That's
a very high bar.

**Recommended change:** Increase `ENTRENCHMENT_RAMP_TICKS` from 3 to 50–100. This means
freshly conquered regions are vulnerable for a meaningful period (as the bible intends —
"freshly conquered/colonized regions reset to base entrenchment"). Currently they become
fully entrenched in 3 ticks, which is essentially instant. The bible's narrative of
"opportunistic recapture of freshly conquered territory" can't happen if entrenchment maxes
out before the next faction even gets a turn.

If the repelled rate is still too high after entrenchment fix, consider reducing
`RESISTANCE_FACTOR` from 0.65 to 0.55, making defenders slightly less effective across
the board.

### Verification Test

Run `bible_diagnostic.py` (500 ticks, seed 1) and check Section 8:

```
PASS if:
  - Repelled rate < 50%
  - Contested rate > 20%
  - At least 1 conquest per 20-tick window on average (conquests / ticks >= 0.05)
  - Attacks still fail sometimes (repelled rate > 20% — we don't want automatic wins)
```

**Escalation triggers:**
- If repelled rate drops below 20%, attackers are too strong. Territory will churn too
  fast and no faction can hold anything. Escalate with the new attack outcome distribution.
- If conquests per tick exceed 0.3 (more than 1 every 3 ticks), the world is too violent
  for chronicle material to have weight. Escalate.

**Do not proceed to Fix 5 until Fix 4 passes.**

---

## Fix 5: Breakaway Faction Passivity — 100% Accumulate

### Problem

Section 11 shows that most breakaway factions spend 100% of their ticks accumulating and
never attack or colonize. Examples: `breakaway_130_region_o_f0` accumulate=371 (100%),
`breakaway_276_region_e0` accumulate=225 (100%), `breakaway_366_region_c_f0` accumulate=135
(100%). These factions exist but do nothing — they contribute no chronicle material and
create no strategic pressure.

The bible says breakaway factions "operate as independent agents — they can be attacked,
they can attack, they can be allied with or absorbed." A breakaway that never acts is
narratively inert.

**Important:** This fix depends on Fixes 1–4 being complete first. Several upstream issues
contribute to breakaway passivity:
- Low budget (spawning with eco ~19 minus maintenance cost 8 = ~11 net income × 0.025
  growth rate = ~0.28 budget/tick — it takes 70+ ticks to reach colonize cost of 20)
- High tension at spawn (no economy growth → no budget → no actions)
- High confidence thresholds for breakaway archetype (4.0–8.0 range)
- No colonization candidates (Fix 1 + Fix 2 may help if empty regions exist near them)

After Fixes 1–4, re-check Section 11. If breakaway passivity is still a problem:

### What to Change

1. **Check breakaway budget growth.** With the config values shown, a single-region
   breakaway with eco=19 generates `(19 - 8) * 0.025 = 0.275` budget per tick. To reach
   `COLONIZE_COST = 20`, that's 73 ticks. To reach attack viability (budget * 0.7 * 1.0 >
   target_mil * 0.65 * entrenchment + confidence), it's even longer. Breakaways may need
   a **spawn budget** (small starting budget so they can act within their first 20–30 ticks)
   or the maintenance cost needs to scale with economy rather than being flat.

2. **Check breakaway confidence thresholds.** The breakaway range is (4.0, 8.0). Compare
   to the Conqueror at (2.0, 6.0). Breakaways are more cautious than Conquerors by default.
   This makes sense for stability, but combined with low budget, it means they never cross
   the threshold. Consider narrowing to (2.0, 6.0) to match Conqueror aggression.

### Verification Test

Run `bible_diagnostic.py` (500 ticks, seed 1) and check Section 11:

```
PASS if:
  - Breakaway factions that survive > 100 ticks have attack percentage > 5%
  - At least 3 breakaway factions attempt at least one attack or colonization
  - No breakaway faction that survives > 200 ticks is still at 100% accumulate
```

**Escalation triggers:**
- If breakaways are now too aggressive (attacking every few ticks and dying immediately),
  the confidence threshold was lowered too far. Escalate with attack outcomes for breakaway
  factions specifically.
- If breakaways still can't act because budget growth is too slow even after tension fix,
  escalate with: breakaway budget trajectory (budget at tick 0, 50, 100 after spawn).

---

## Fix 6: Re-run Full Diagnostic and Evaluate

After all five fixes are implemented and individually verified, run the full diagnostic
one final time:

```bash
python3 bible_diagnostic.py
```

Paste the complete output (all 13 sections) to Westley. Do not summarize.

### What Westley Will Check

- **Section 2:** Empty regions >= 6, each faction has colonizable neighbors
- **Section 3:** Colonizations > 10 in the first 100 ticks, attack rate builds over time
  (not flat from tick 1)
- **Section 6:** Mean tension 35–65 for most regions, spikes during conflict, decay after
- **Section 8:** Repelled < 50%, conquests at a sustainable rate
- **Section 9:** ColScore is numeric, colonize beats attack in early ticks when empty
  regions are available, attack takes over once empties are claimed
- **Section 11:** Original factions show a mix of accumulate/attack/colonize; breakaways
  that survive show some offensive activity
- **Section 12:** All checklist items pass

### Bible Compliance Targets (for Westley's evaluation)

The diagnostic should show the emergence of the bible's lifecycle phases:

- **Phase 1 (ticks 0–50ish):** Colonizations outnumber attacks. Factions expand into
  empty space. Budget is building.
- **Phase 2 (ticks 50–100ish):** Empty space fills up. Attacks begin as factions contact
  each other. Colonizations taper off.
- **Phase 3 (ticks 100–200):** Regular inter-faction conflict. Territory changes hands.
  Conquests produce chronicle material.
- **Phase 4–5 (ticks 200–500):** Overextended factions fragment through admin revolts
  and tension revolts. Breakaway factions appear and participate. World stabilizes into
  dynamic equilibrium with 4–8 active factions.

If the diagnostic shows this progression, the simulation is producing the designed
experience. If not, Westley will identify which phase is missing and direct further tuning.
