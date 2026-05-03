# Draft FairnessTargetProfile Values — 6 Non-Prototype Archetypes

Each profile follows the `(target_ratio, tolerance)` format per metric.
Ratio = player_value / enemy_value. Higher ratio = player advantage.

Reference: prototype profiles (unchanged)
- defensive_stand: path=(0.60, 0.15), travel=(1.00, 0.15), vantage=(1.15, 0.15), hazard=(0.75, 0.15)
- assault: path=(1.70, 0.20), travel=(1.00, 0.15), vantage=(0.85, 0.15), hazard=(1.30, 0.20)
- multi_front_defense: all symmetric (1.00, 0.15)
- counterinsurgency: path=(1.00, 0.25), travel=(1.00, 0.20), vantage=(1.20, 0.20), hazard=(0.60, 0.20)

---

## 1. siege_breaking

**Bible:** Player starts inside besieged region, pushes outward. Enemy rings the perimeter with fortified forward positions. Balanced offensive/defensive — player attacks but also holds.

- **path_balance:** (1.20, 0.25) — player_advantage, loose. Relief force needs route options to break through; not as many as pure assault. Bible: "multiple enemy positions that can be tackled in any order."
- **travel_time:** (0.85, 0.20) — enemy_advantage, loose. Siege has geometric advantage; enemy positions are closer to chokepoints. Bible: "enemy positions ring the perimeter."
- **vantage_balance:** (0.90, 0.20) — slight enemy_advantage, loose. Besiegers have had time to take the high ground. Bible: "fortified forward bases."
- **hazard_balance:** (0.85, 0.20) — enemy_advantage, loose. Siege has had time to fortify and create interference. Bible: "supply interdiction points."

```python
"siege_breaking": FairnessTargetProfile(
    path_balance        = (1.20, 0.25),
    travel_time_balance = (0.85, 0.20),
    vantage_balance     = (0.90, 0.20),
    hazard_balance      = (0.85, 0.20),
    archetype           = "siege_breaking",
),
```

## 2. reconquest

**Bible:** Former friendly territory, occupier partially set up. Offensive-heavy player force. Enemy garrison is thinner than fully entrenched defender. Population partially sympathetic.

- **path_balance:** (1.10, 0.20) — slight player_advantage, loose. Former infrastructure gives some route familiarity; not a massive edge. Bible: "infrastructure that the occupier is repurposing."
- **travel_time:** (1.00, 0.20) — symmetric, loose. Neither side has a decisive distance advantage; the occupier isn't fully dug in. Bible: "partially set up."
- **vantage_balance:** (1.00, 0.20) — symmetric, loose. Territory is transitional; neither side fully controls observation.
- **hazard_balance:** (0.85, 0.20) — slight enemy_advantage, loose. Occupier has begun fortifying; hazards lean toward them. Bible: "defensive positions exist but the enemy is partially set up."

```python
"reconquest": FairnessTargetProfile(
    path_balance        = (1.10, 0.20),
    travel_time_balance = (1.00, 0.20),
    vantage_balance     = (1.00, 0.20),
    hazard_balance      = (0.85, 0.20),
    archetype           = "reconquest",
),
```

## 3. suppression

**Bible:** Quick decisive strike against a newly formed breakaway. Enemy is dispersed — multiple small positions. Sensor interference present. Rewards aggressive pursuit.

- **path_balance:** (1.00, 0.25) — symmetric, loose. Dispersed enemy means path balance varies by encounter; no strong directional lean. Bible: "multiple small positions rather than one fortified base."
- **travel_time:** (1.00, 0.25) — symmetric, loose. Both sides scattered; no consistent distance advantage. Bible: "scattered rebel forces."
- **vantage_balance:** (1.10, 0.25) — slight player_advantage, very loose. Player is the organized force with sensor capability. Bible: "use sensor coverage to locate them" (from counterinsurgency, similar dynamic).
- **hazard_balance:** (1.00, 0.25) — symmetric, very loose. Hazards are environmental, not fortified. Bible: "sensor interference may be present."

```python
"suppression": FairnessTargetProfile(
    path_balance        = (1.00, 0.25),
    travel_time_balance = (1.00, 0.25),
    vantage_balance     = (1.10, 0.25),
    hazard_balance      = (1.00, 0.25),
    archetype           = "suppression",
),
```

## 4. evacuation

**Bible:** Not trying to win. Protecting evacuation while delaying enemy. Force is undersized. Collapsing perimeter. Enemy approaching from front, extraction at rear.

- **path_balance:** (1.30, 0.25) — player_advantage, loose. Multiple extraction routes is the design intent; one route is a death trap. Bible: "extraction points at the rear" + "multiple things to protect."
- **travel_time:** (0.75, 0.20) — enemy_advantage. Enemy spawns close to the fight; player must fall back. Bible: "enemy forces approaching from the front."
- **vantage_balance:** (1.00, 0.25) — symmetric, very loose. Collapsing perimeter means vantage shifts over time; no strong initial lean.
- **hazard_balance:** (1.00, 0.25) — symmetric, very loose. Hazards are situational in a retreat scenario.

```python
"evacuation": FairnessTargetProfile(
    path_balance        = (1.30, 0.25),
    travel_time_balance = (0.75, 0.20),
    vantage_balance     = (1.00, 0.25),
    hazard_balance      = (1.00, 0.25),
    archetype           = "evacuation",
),
```

## 5. raid

**Bible:** Not in the archetype list — "raid" is in archetype_filters but not in bible_missions.md. It appears to be a non-bible archetype used as a stub filter. No bible-grounded tactical character exists.

**Proposed approach:** Use loose symmetric defaults since there's no bible authority for directional intent. Wider than `_SYMMETRIC_DEFAULT` to avoid false rejections.

- **path_balance:** (1.00, 0.30) — symmetric, very loose.
- **travel_time:** (1.00, 0.30) — symmetric, very loose.
- **vantage_balance:** (1.00, 0.30) — symmetric, very loose.
- **hazard_balance:** (1.00, 0.30) — symmetric, very loose.

```python
"raid": FairnessTargetProfile(
    path_balance        = (1.00, 0.30),
    travel_time_balance = (1.00, 0.30),
    vantage_balance     = (1.00, 0.30),
    hazard_balance      = (1.00, 0.30),
    archetype           = "raid",
),
```

## 6. rear_guard

**Bible:** Not explicitly separate from evacuation in the bible — bible §8 is titled "Rear Guard / Evacuation" and describes them as one archetype. However, `archetype_filters.py` has them as separate entries. Like `raid`, `rear_guard` has no independent bible prose.

**Proposed approach:** Mirror evacuation's directional intent but shift vantage toward player (rear guard chooses defensive ground). Loose tolerances.

- **path_balance:** (0.80, 0.25) — enemy_advantage, loose. Attacker has multiple approaches; rear guard holds a narrow line. Inverse of evacuation's extraction-route advantage.
- **travel_time:** (1.00, 0.25) — symmetric, loose. Meeting engagement; neither side has decisive distance advantage.
- **vantage_balance:** (1.20, 0.25) — player_advantage, loose. Defender chooses ground. Bible: "defensive position with evacuation points behind them."
- **hazard_balance:** (1.10, 0.25) — slight player_advantage, loose. Defender prepared the field.

```python
"rear_guard": FairnessTargetProfile(
    path_balance        = (0.80, 0.25),
    travel_time_balance = (1.00, 0.25),
    vantage_balance     = (1.20, 0.25),
    hazard_balance      = (1.10, 0.25),
    archetype           = "rear_guard",
),
```

---

## Notes for approval

1. **`raid` and `rear_guard`** have no independent bible prose — they exist only as stub entries in `archetype_filters.py`. Profiles above are best-guess; if these archetypes are deprecated or meant to merge with others, say the word.

2. **Tolerances are deliberately wider** (±0.20 to ±0.30) than the prototype profiles (±0.15 to ±0.20). This reflects the spec's D2 rationale: these archetypes haven't been playtested, and tight tolerances on unplaytested profiles will reject valid maps.

3. **All targets are chosen to be achievable** given the observed ratio ranges from the baseline diagnostic. E.g., travel_time ratios of 0.50 are common, so profiles with travel=(1.00, 0.15) would reject most layouts — but travel=(0.85, 0.20) or travel=(1.00, 0.25) can accommodate 0.50 in some cases.
