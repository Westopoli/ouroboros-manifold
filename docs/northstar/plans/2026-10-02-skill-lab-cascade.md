# Build brief: the skill lab and the engine cascade

Written 2026-10-02 by the design chat (ouroboros-b1) for the chat that conducts the build. Read `docs/northstar/research/layer_dynamics/README.md` first: it says what this is for. This file says what to build, in what order, and what "done" means. Where this file and the record disagree, stop and report; do not guess.

## 0. Who does what

- **Design chat (ouroboros-b1):** owns this brief, the bible text, the provisional numbers, and runs the experiments. It does not build.
- **Conducting chat:** runs the cascades below and reports to the design chat after each. (Westley asked for the engine gaps as one cascade; building the harness as its own, earlier cascade is the design chat's split.) It decides nothing about game behaviour. A rule this brief leaves unclear comes back as a question, not as a choice.
- **Westley:** owns every threshold and tolerance, and anything marked "ask".

## 1. Method: manager-mode-lite

Westley, 2026-10-01: "Use manager-mode-lite (sonnet subagents for everything, shard test writers and auditors)." That is his definition. The bullets below add this repo's rules (CLAUDE.md, PLAN.md) and the design chat's sequencing.

- Every sub-agent is Sonnet. Name the model on every spawn (CLAUDE.md).
- Tests first. A shard test writer writes the failing tests for a part; an auditor, a different agent, checks them against this brief before any code; an implementer writes only code and never edits a test. Nobody grades their own tests.
- A test that cannot fail is a defect: every new detector ships with a positive control.
- Sub-agents never spawn sub-agents.
- Prose in agent reports and commit messages: caveman style. Code, tests and config: normal.

Repo rules that bind the engine cascade (CLAUDE.md, `docs/northstar/PLAN.md` "The Factory"):

- **Contract first.** `csrc/ouroboros_sim.h` and `docs/northstar/spec_factory/signatures.toml` change in their own step, before any implementation, and the ABI version is bumped once for the whole cascade.
- **One owner per file.** Register the files this cascade touches in `docs/northstar/plans/push/pieces.toml` before starting, so the Linux side does not edit them at the same time. Remove the registration when the cascade lands.
- **Wired, not just tested.** New behaviour must be reached from `om_tactical_step` (or a command it serves), not only from tests. `scripts/specfactory/reach_lint.py` checks this.
- **Engine tests live in `tests/csim/`**, named for the story and rule they prove (`test_E01_S162_...`). Thresholds and tolerances are Westley's; none is loosened to make a build pass.
- **Determinism.** No random draw, no libm transcendental, nothing hash-ordered or wall-clock in the tactical path. O0 and O2 builds agree.
- **Tick delta and pipe frames are not touched by this cascade.** The Godot client and `csrc/pipe/` stay as they are. Anything that would change a frame is out of scope and comes back as a note.

## 2. Two machines

The Mac (arm64) and the Linux machine (x86_64) work on this repo at once.

- No machine paths in code or tests. Find the repo root from the file's own location.
- Scripts guard their entry point (`if __name__ == "__main__":`) and pass plain data to worker processes. macOS starts workers by spawn; do not rely on fork on either machine.
- Work lands on `main` in small units. Merge, never rebase. Pull before editing a shared file. Cascade branches and worktrees stay local and are removed at the end; only the result is pushed.
- Nothing generated is committed: libraries, result tables, pictures, Godot `.import` and `.uid` files. The one exception is the control hash file of section 3.3.
- Before starting on the Mac: the cascade tooling needs a clean working tree (the design chat's rule). Westley decided to discard the stray `project.godot` change; the guard blocks agents from discarding files, so he runs `git restore project.godot`. 34 old agent worktrees sit under `.claude/worktrees/`; ask Westley before removing any.

## 3. Cascade A: the skill lab harness

A Python package that only calls the production library. No engine edits. It does not wait for the engine cascade.

**Where:** `scripts/skilllab/` (package), `tests/skilllab/` (pytest). Not under `tests/csim/`.

**Reuse, by copying the engine-independent logic, not importing the toy:** the whole-unit scan and non-increasing fit in `toys/layerlab/layerlab/skill/rstar.py`; headcount shares in `toys/layerlab/layerlab/skill/cost.py`; formation geometry in `toys/layerlab/layerlab/formations.py`; grid and seeded random sampling in `toys/layerlab/layerlab/sample.py`; CSV rows in `toys/layerlab/layerlab/batch.py`. The chart page: the template behind https://claude.ai/artifact/WtQDNnNZTR8hqx6LpxBaJ2 is described in section 3.4; ask the design chat for the source if wanted.

### 3.1 Contract

```python
@dataclass(frozen=True)
class Group:
    side: int                 # 0 or 1
    unit: str                 # a built-in type name or a key of Setup.unit_types
    count: int
    formation: str            # "line" | "blob" | "concave" | "column" | "points"
    x: float; y: float        # anchor
    facing_deg: float
    layer: int                # as the engine numbers layers; see 3.5
    order: str                # "attack_move" | "move" | "idle"
    goal: tuple[float, float] | None
    params: dict              # spacing, cols, arc_deg, radius, points=[(x, y), ...]

@dataclass(frozen=True)
class Setup:
    groups: tuple[Group, ...]
    unit_types: dict          # name -> stats, registered with om_roster_register_custom_unit
    abilities: bool = False   # False calls om_tactical_disable_abilities
    max_ticks: int = 6000
    stalemate_ticks: int = 400
    sample_every: int = 5     # ticks between firing-count samples

@dataclass
class FightResult:
    outcome: str              # "side0" | "side1" | "stalemate" | "cap"
    margin: float             # share of side 0's starting strength left, minus side 1's
    strength_left: tuple[float, float]
    survivors: tuple[int, int]
    heads: tuple[int, int]
    ticks: int
    first_contact_tick: int   # first sample at which any unit could fire; -1 if never
    firing: list              # [(tick, able0, able1), ...], one per sample
    firing_unit_seconds: tuple[float, float]

def fight(setup: Setup, seed: int = 0, swap: bool = False) -> FightResult: ...
def cell(build, enemy_heads: int, replicates: int) -> CellResult: ...
def scan(build, size: int, enemy_from: int, enemy_to: int, replicates: int = 10) -> ScanResult: ...
def write_rows(rows, path): ...
def report(batch, out_dir) -> str: ...      # path of the HTML page
```

- `build(enemy_heads, swap) -> Setup` is supplied by a play.
- `swap=True` spawns side 1's units before side 0's. The engine acts in unit-id order, so the first-spawned side shoots first; every cell runs both orders.
- `seed` drives only the harness's own small position shifts (default up to 10 world units per unit, from `random.Random(seed)`). The engine has no randomness; these shifts are the replicates.
- **Able to fire**, at a sample: the unit is alive, and some living enemy is on a layer it may fire at, within its attack range, and `om_combat_can_shoot` is true for the pair. After engine step G3 also: the enemy is seen by the unit's side. Until G5 "a layer it may fire at" is its own layer.
- **Strength** of a side: the sum over its living units of hp over starting hp, divided by its starting headcount.
- `ScanResult` reports `beats` and `loses_to` as whole enemy headcounts taken from the rows, so "beats N, loses to N+1" is literally what the table shows; a cell is won when the mean margin over its fights exceeds the win margin (default 0.05, a parameter; Westley's to set).
- A stalemate is not a win.

### 3.2 Parts

`engine.py` (build the library into a scratch directory with flags chosen by architecture, load it, bind the calls used; after G0, plain `make` output is used), `fight.py`, `formations.py`, `plays.py` (the naive ladder: blob and line abreast; a control play with a reach advantage), `scan.py`, `sample.py`, `rows.py`, `report.py`, `__main__.py` (`python3 -m scripts.skilllab controls`).

### 3.3 Tests that must exist and pass (`tests/skilllab/`)

1. Mirror control: identical sides, flat ground, 16 against 16. Over both spawn orders and 10 replicates, the mean margin is within 0.05 of zero. Positive control for the detector: with the swap disabled the same test shows the first-spawned side ahead.
2. Numbers control: 16 against 8 of the same type: the 16 win every fight.
3. Planted advantage: 16 units with 20 percent more reach (a custom type) beat a larger enemy than 16 identical units do, by at least one unit.
4. Firing count, hand-built: three units of side 0 in a row and one enemy placed so exactly two are within reach: the sample reads 2 and 1. A second case with an obstacle between one pair reads one fewer.
5. Determinism: the same setup and seed give byte-identical rows twice.
6. Cross-machine: the rows for the three controls hash to the values in `tests/skilllab/golden_hashes.json`. The file is written on the first machine and must match on the second. A mismatch is reported to the design chat as a determinism finding, not patched.
7. Scan honesty: on a synthetic margin series with a known sign change the scan returns the right `beats` and `loses_to`; on a flat series it returns none.
8. Speed gate: a scan of 16 units against 12 to 24 enemies, 10 replicates, both orders, finishes in under 30 seconds on either machine.

Umbrella test (red until the cascade is done): `python3 -m scripts.skilllab controls` writes one rows file and one HTML page for the three controls, and exits 0.

### 3.4 The page

One self-contained HTML file per batch, light and dark, no external scripts beyond fonts. The form is that of the sample Westley called "much better" on 2026-10-01; he named only the top graphic. The bullets describe that sample; a different chart form is allowed when the kind of data changes:

- The heading of each figure states the finding in soldiers ("With longer reach, 16 units beat 17. Identical sides beat 15.").
- A line of fights by enemy size: one dot per cell, coloured won or lost, the break-even marked and labelled "beats N, loses to N+1".
- Units able to fire through one fight: one line per side, labelled on the chart, the gap shaded.
- A table with a plain-words column in place of any scatter plot.
- A table view under each chart.

### 3.5 Things to find out and report, not decide

- How the engine numbers layers (the bible numbers them 1 to 5 from the bottom; the harness spawned on layer 0 without complaint).
- Whether `om_tactical_run_until_eliminated`'s own stalemate rule (1800 ticks) interferes with stepping by `om_tactical_step`.
- The measured fights per second on each machine.

## 4. Between the cascades

The design chat runs the controls batch on today's engine and reads it with Westley. The engine cascade starts after that.

## 5. Cascade B: the engine, G0 to G7 in one cascade

Westley, 2026-10-01: "Every G doesn't need it's own cascade, it can be done all in one." Waves inside it run in dependency order: W0 the contract (header, `signatures.toml`, the ABI bump) and G0; W1 G1; W2 G2 and G3; W3 G4; W4 G5, G6, G7. If a wave decomposes into more than 16 parts, split the wave.

**The invariant across the steps that add new mechanisms (G1, G4, G5, G6, G7):** with no new call made and every setting at its default, the engine behaves exactly as it does today. Record, before touching `csrc/`, a file of hashes over the unit states of a fixed set of fights (the three skill-lab controls plus `tests/csim` tactical fixtures of the conducting chat's choice); assert the same hashes after every wave, with the two switches below off. The existing `tests/csim` suite does not regress.

**Two steps change default behaviour on purpose, because the engine is behind its own bible there.** G3 (targeting by sight) changes every fight in which a side cannot see an enemy that is within reach. G2 changes fights on maps with blocked cells. Each gets a setting so the old behaviour stays available as a control: `OM_TP_TARGET_BY_SIGHT` and `OM_TP_ROUTE_AROUND_TERRAIN`, both default 1 (the bible's rule), 0 for today's behaviour. The hash invariant is asserted with both at 0. With both at 1, re-hash the three open-ground controls and report any difference to the design chat; do not explain it away. A `tests/csim` test that encodes the old behaviour is not edited by an implementer: list it in the report, and the design chat rules on it under the change protocol.

Signatures below are proposals in the header's style. The conducting chat may adjust names to match `signatures.toml` conventions; it may not change behaviour.

### G0. A build that works on both machines

- `Makefile`: `-msse2 -mfpmath=sse` only when the target is x86. On x86 the flags, and so the output, are unchanged.
- `.gdignore` files in `toys/` and in `scripts/skilllab/`'s output directory, so Godot stops writing `.import` files for charts.
- Test: `make` succeeds on the Mac; on Linux the built library is byte-identical to before.

### G1. Rule numbers settable at run time

Today every tactical rule number is a `#define` generated into `csrc/om_constants.h`. The lab has to move them without recompiling.

```c
typedef enum om_tac_param { OM_TP_CONE_LAYER_1 = 0, OM_TP_CONE_LAYER_2, /* ... */ OM_TP__COUNT } om_tac_param;
double om_tactical_get_param(const om_world *w, om_tac_param p);
int    om_tactical_set_param(om_world *w, om_tac_param p, double value);   /* 0 ok; -1 unknown or out of range */
```

- Parameters to expose: the two cross-layer vision factors; the vantage multiplier; the attack-move leash; the return-fire flee distance; the unit collision radius; the nine category multipliers; the area-damage cap; the targeting cohort count; and every provisional number in section 6.
- Defaults are the `om_constants.h` values. A parameter set before any unit is spawned applies to the whole fight; setting one mid-fight is allowed and takes effect on the next tick.
- Each parameter has a documented valid range; out of range is refused and changes nothing.
- Tests: default equals the constant for every parameter; setting the leash to 0 makes an attack-moving unit drop a target that steps 1 unit from its anchor, and the default does not; setting a category multiplier changes damage by exactly that factor; an out-of-range value is refused.

### G2. Solid terrain, and routing around it

Bible: E-13 S-097 (R-097-01, R-097-02, R-097-06), E-01 S-001 (R-001-01 to R-001-04), E-01 S-007.

- The route grid is 100-unit cells per layer; a cell is blocked on a layer where its obstacle density there exceeds 0.7. Today movement and fire sample layer 0 only (`csrc/tactical_move.c`); they must sample the unit's own layer.
- A unit never enters a blocked cell on its layer. A move order to a point routes by the shortest path on the grid, straightened where the straight line is clear, computed once per shared destination (R-097-02). With no blocked cell on the straight line the path is the straight line and behaviour is as today.
- A sight line and a line of fire between two units are blocked by a blocked cell on the layers involved (both units on layer L: a cell blocked on L blocks). This is in addition to cover discs. Cross-layer lines: the same interpolation the cover rule uses.
- `om_map_sample_layer_accessibility` stops being a stub and reads this grid (R-001-04).
- A convenience call to block a rectangle on a range of layers:

```c
int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi);
```

- Tests: two masses with a 200-unit gap; a unit ordered to the far side goes through the gap and never occupies a blocked cell; the trip is longer than the straight line by the detour; two units either side of a mass cannot see or fire at each other and can when moved to face the gap; a unit on a layer above the blocked range crosses straight over (R-001-02); a destination with no route leaves the unit stopped at the nearest reachable point, not frozen inside a cell.

### G3. Units act on what their side can see

Bible: E-12 S-093 (R-093-02), R-089-02, E-01 R-008-04.

- A side's visible set is the union of what its living units see (`om_unit_can_see`: sensor radius, interference, cross-layer factor, cover, and now blocked cells).
- A unit acquires, keeps and fires only at targets in its side's visible set. An attack-moving unit steps toward the nearest **visible** enemy within sensor radius (today it steps toward any enemy, through anything).
- A target that leaves the visible set, or whose line of fire becomes blocked, is dropped at the next acquisition; a unit never sits holding a target it cannot fire at.
- R-093-01 stays true: the result of a battle does not depend on which faction is "the player".
- Tests: two forces separated by more than sensor radius do not react to each other; a hidden target behind a mass is not acquired; a third unit with sight of it makes it acquirable by the others (shared sight); a unit whose target moves behind a mass retargets.
- Reading to confirm with Westley through the design chat: sight is shared across a side, as R-089-02 has it for the player. If he wants per-unit sight for firing, only the last filter changes.

### G4. Changing layer

Bible: E-01 S-002, S-004 (R-004-01 to R-004-05), R-001-05, R-001-07; register Q-004-02, Q-004-05, Q-001-05.

- A hard transfer order:

```c
int    om_command_set_layer(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t layer);
double om_unit_transition_progress(const om_world *w, uint32_t unit);    /* 0 when settled, else in (0, 1) */
uint32_t om_unit_get_target_layer(const om_world *w, uint32_t unit);     /* the layer it is moving to, or its own */
```

- The transfer takes the unit type's `layer_transition_time` (already in the roster, unused today). It begins on the tick the target layer is open at the unit's position, and stays pending otherwise (R-002-02).
- The cross-over is halfway through. Before it the unit is on the layer it is leaving, for sensing, for attacking and for being attacked; from it on, the layer it is moving to. `om_unit_get_layer` returns this effective layer. A transitioning unit attacks, under the same rules as any unit on its effective layer (register Q-004-05).
- Shortest route across layers (R-001-05): the router of G2 works over cells and layers together. Changing layer in a cell where both layers are open costs the transfer time. A unit takes the quickest route by travel time and ends on the layer it was ordered on. With `OM_TP_ROUTE_ACROSS_LAYERS` at 0 the router stays on the unit's layer (the control).
- Every Settled Reach unit type flies (R-001-07): it may change layer wherever nothing blocks. Walking units and slopes are out of this cascade.
- Tests: a Raider ordered up a layer is on it 20 ticks later (1.0 s) and a Bastion 100 ticks later (R-004-01, R-004-03); before tick 10 an attacker on the old layer may target the Raider and one on the new layer may not, and the reverse from tick 10 (R-004-02); a unit ordered to a point behind a mass blocked on its layer and open above goes over when that is quicker and around when that is quicker, and ends on its own layer; with the switch off it goes around or stops; same seed, same ticks (R-004-05).

### G5. Reach by unit type

Bible: E-01 S-164, S-008.

```c
int om_roster_set_reach(om_world *w, int unit_type, uint32_t layers_up, uint32_t layers_down);
int om_unit_profile_reach(om_world *w, int unit_type, uint32_t *up, uint32_t *down);
```

- A unit may acquire and fire at a target whose layer is within its type's reach above or below its own effective layer, and at no other (R-164-02).
- Range and damage at an offset are multiplied by per-offset settings (G1): one value for each of 1 to 4 layers up and 1 to 4 down, default 1.0.
- **The built-in roster's default reach is 0 up, 0 down**, which is today's same-layer rule, so nothing changes until a caller sets reach. The provisional reach table in section 6 is applied by the lab, and later by the era pack.
- The area attack and the return-fire rule follow the same reach test. The attack-target order's missing layer check (`csrc/unit.c`, the drop check gated on the order kind) is closed: reach applies to it too.
- Tests: reach 1 up, target one layer above in range: engaged; two above: not; reach 0: today's behaviour, by the hash invariant; a range multiplier of 0.5 one layer up halves the distance at which it engages; a damage multiplier applies exactly.

### G6. Going dark

Bible: E-01 S-163.

```c
typedef enum om_emission { OM_EMIT_SILENT = 0, OM_EMIT_ACTIVE = 1 } om_emission;
int om_command_set_emission(om_world *w, const uint32_t *unit_ids, uint32_t n_units, om_emission mode);
int om_unit_get_emission(const om_world *w, uint32_t unit);
```

- A unit is silent or emitting. **Silent is the default and is exactly today's behaviour.** Switching costs nothing and takes effect on the next tick.
- An emitting observer's cross-layer vision factors are multiplied by `OM_TP_EMIT_SIGHT_MULT`; the result is capped at 1.0.
- An emitting unit is seen from other layers as if the observer's cross-layer factor were multiplied by `OM_TP_EMIT_SEEN_MULT`, capped at 1.0. Same-layer sight is unchanged in both directions.
- Tests, on E-01 R-005's numbers (observer sensor 1000): silent, an enemy one layer up is seen at 400 and not at 600 (today); the observer emitting sees it at 600; a silent observer sees an **emitting** enemy one layer up at 600; both silent, unchanged.

### G7. The targeted ping

Bible: E-01 S-162.

```c
int om_command_ping(om_world *w, uint32_t caster, uint32_t layer, double x, double y);  /* 0 ok; nonzero reason */
typedef struct om_ping_alert { uint64_t tick; int32_t faction; int32_t sector; } om_ping_alert;
uint32_t om_ping_alert_count(const om_world *w, int32_t faction);
int      om_ping_alert_get(const om_world *w, int32_t faction, uint32_t index, om_ping_alert *out);
```

- The caster must be alive and the point within `OM_TP_PING_REACH` of it. Each unit has its own cooldown, `OM_TP_PING_COOLDOWN_TICKS`. A refused ping changes nothing and reports why (dead, out of reach, on cooldown, bad layer).
- For `OM_TP_PING_REVEAL_TICKS` ticks, every enemy unit on the named layer within `OM_TP_PING_RADIUS` of the point is in the caster's side's visible set. When it ends they are hidden again unless seen some other way (R-162-05).
- It costs no resource (R-162-02).
- Every side with at least one unit inside the pinged disc gets an alert: the tick, and a sector. The sector is the 60-degree slice, numbered 0 to 5 counter-clockwise from the +x axis, that contains the bearing from the centroid of that side's pinged units to the caster. Nothing more precise is exposed (R-162-03).
- Scouts for eras without the technology (R-162-04) are a proposal, not decided, and are out of this cascade.
- Tests: a ping on layer 5 from a unit on layer 1 reveals an enemy there for exactly the reveal ticks and then not; an enemy on another layer inside the disc is not revealed; a second ping inside the cooldown is refused; a ping beyond reach is refused; the pinged side's alert sector contains the true bearing, and a caster moved 30 degrees within the same slice gives the same sector; the casting side gets no alert.

## 6. Provisional numbers

Westley, 2026-10-01, accepted the recommended starting values (`Q-005-04` and `Q-001-05`, option a) as provisional so the stories can be built. That option named kinds of value, not numbers. **The numbers in the right-hand column were chosen by the design chat**, from existing constants where one exists and by judgement otherwise; he has not set or confirmed them. Every one is a runtime setting (G1), tuned by the lab. Engine defaults keep today's behaviour; the lab applies the right-hand column.

| Setting | Engine default | Lab starting value | Source |
|---|---|---|---|
| Cross-layer vision, 1 and 2 layers away | 0.50, 0.20 | same | `om_constants.h`; Q-005-02 |
| Emitting: sight multiplier | 1.0 (no effect until set) | 2.0 | design chat proposal, by analogy with the vantage multiplier of 2.0 |
| Emitting: seen-from multiplier | 1.0 | 2.0 | design chat proposal |
| Ping radius | 500 | 500 | the unused pulse radius |
| Ping reveal | 40 ticks (2 s) | same | the unused pulse reveal |
| Ping cooldown, per unit | 400 ticks (20 s) | same | the unused pulse cooldown |
| Ping reach from the caster | 2,000 | 2,000 | design chat proposal; his words are "a much longer range" than passive sight (at most 500) |
| Reach: Vanguard, Warden (Line) | 0 up, 0 down | 0, 0 | Q-005-04 |
| Reach: Raider (Strike) | 0, 0 | 1, 1 | Q-005-04 |
| Reach: Interceptor (Strike) | 0, 0 | 2 up, 1 down | design chat proposal for the type that fires upward well |
| Reach: Bombard, Bastion (Siege) | 0, 0 | 0 up, 2 down | design chat proposal; Q-005-04 says downward only |
| Range and damage multiplier per layer of offset | 1.0 | 1.0 | Q-008-03, swept by the lab |
| Route across layers | on | on | Q-001-04 |
| Route cost | travel time, transfer time included | same | Q-001-05 |

The sensor pulse of E-01 S-006 is not built: the ping takes its place (provisional).

## 7. Out of scope

The Godot client; pipe frames and `docs/architecture.md`; land eras (walking units, slopes, land flags); abilities; the layer preference (E-01 S-003); the map generator (E-17); the toy (`toys/layerlab/`, frozen); the alert's display.

## 8. Reporting back

After each cascade, one message to the design chat (ouroboros-b1), plain words, under 300 words: what landed and at which commit; the test counts, red before and green after; the hash invariant's result; anything in this brief that was unclear, wrong, or changed on the way; what was left out and why; measured speed. Then stop and wait.
