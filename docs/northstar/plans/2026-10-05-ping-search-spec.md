# Skill lab: the ping search scene (Stage A), spec

For the method and the reasons, read `docs/northstar/research/layer_dynamics/ping_definition_and_measurement.md`. This file fixes what is built first: a search with no fight, on open ground, in the skill lab. Stage B (what knowing is worth) and the "likely places" policy (which needs terrain) are later pieces.

Every number here is a lab draft, provisional, named as a module constant with the comment "provisional (lab draft, 2026-10-05)". None is confirmed by Westley.

## Base and files

Branch from `push/lab-run-3` after `origin/main` (with the ping change of 2026-10-05: the reveal follows the units caught) has been merged into it. New files only; no existing lab file is edited except to register the batch name where batches are listed.

| File | Holds |
|---|---|
| `scripts/skilllab/search.py` | the scene, one run, the measures |
| `scripts/skilllab/search_policies.py` | the ping policies and the hider scripts |
| `scripts/skilllab/search_batch.py` | the batch, the csv, the run file, the page |
| `tests/skilllab/test_search_policies.py`, `tests/skilllab/test_search_measures.py` | unit tests, no engine |
| `tests/skilllab/integration/test_search_real.py` | real engine, with the positive controls |

## The scene

- Open ground, no terrain, canvas 12,000 x 12,000. Two sides. Nobody fires: both sides hold fire by whatever the engine allows without a new engine call (for example a side that is never given an attack order and an attack range parameter of zero, or units of a type that cannot attack); the builder states which was used. If no means exists, stop and report.
- Side 0 (the seeker): `force` Vanguards in a blob on layer 2, starting at (-3000, 0), moving along +x at its own speed.
- Side 1 (the hider): 16 Vanguards in a blob, placed by a `Placement`: an offset from the seeker's start, a layer 0 to 4, a heading, and a script.
- Every unit can ping (R-162-01). The cooldown is per casting unit (R-162-02). The alert is off.
- A run ends at first true-vision contact (any unit of either side sees an enemy by sight, `seen_by_sight`) or at the cap of 2,400 ticks (120 s).

## Interfaces (fixed, so the three files can be built side by side)

```python
# search.py
@dataclass(frozen=True)
class SearchSetting:
    radius: float          # ping radius, wu
    reach: float           # ping reach, wu
    reveal_ticks: int
    cooldown_ticks: int
    force: int             # seeker headcount; every unit casts

@dataclass(frozen=True)
class Placement:
    dx: float; dy: float   # hider centre, relative to the seeker's start
    layer: int             # 0..4
    heading_deg: float
    script: str            # a key of search_policies.HIDER_SCRIPTS

@dataclass(frozen=True)
class SideResult:
    found_before_contact: bool      # a ping revealed an enemy before any true-vision contact
    first_reveal_tick: int | None
    warning_ticks: int | None       # contact tick (or the cap) minus first_reveal_tick
    share_revealed: float           # enemy units revealed at least once before contact / enemy headcount
    layer_learned: bool             # at least one reveal, so the enemy's layer is known
    picture_age_ticks: int | None   # at contact: ticks since the last tick any enemy was revealed
    pings_cast: int
    pings_found: int                # pings that caught at least one unit

@dataclass(frozen=True)
class SearchResult:
    side: tuple[SideResult, SideResult]
    contact_tick: int | None
    ended: str                      # "contact" or "cap"

def placements(seed: int, n: int, sight: float, reach_max: float) -> list[Placement]
def coverage_rate(setting: SearchSetting, layers: int = 5) -> float
def run_search(setting, policy0: str, policy1: str, placement: Placement, seed: int,
               cap_ticks: int = 2400, engine=None) -> SearchResult

# search_policies.py
@dataclass
class PolicyView:                   # what a policy may read; it never sees hidden enemies
    tick: int
    setting: SearchSetting
    centre: tuple[float, float]     # own force centre
    heading_deg: float
    layer: int                      # own layer
    ready: list[int]                # own unit ids whose cooldown has passed, ascending
    unit_pos: dict[int, tuple[float, float]]
    revealed: dict[int, tuple[float, float, int]]   # enemy id -> x, y, layer, visible now by any means
    memory: dict                    # the policy's own notes, kept between calls

POLICIES: dict[str, Callable[[PolicyView], list[tuple[int, int, float, float]]]]
#   returns pings to cast now: (caster id, layer, x, y)
HIDER_SCRIPTS: dict[str, Callable[..., list]]       # movement orders for the hider by tick
```

- `placements`: seeded, deterministic. The hider's centre is drawn in the half-plane ahead of the seeker (bearing within 75 degrees of +x), at a distance from just beyond `sight` to `reach_max` + 2,000; the layer uniform over 0 to 4; the heading uniform; the script cycled through the keys of `HIDER_SCRIPTS` so each appears equally often. No placement starts inside true vision.
- `coverage_rate` = (force x pi x radius^2) / (cooldown in seconds x pi x reach^2 x layers).
- `run_search` steps the engine; every `DECIDE_EVERY` = 10 ticks it builds a `PolicyView` for each side and casts what the side's policy returns (a refused ping is counted as not cast). The hider side uses `policy1` (default use: "none").

## Policies (side-blind: each reads only its `PolicyView`)

| Key | What it does |
|---|---|
| `none` | never pings |
| `ahead` | every ready unit pings the point `reach` ahead along the heading from that unit, on the force's own layer |
| `sweep` | a fixed list of targets: 5 bearings (-60, -30, 0, 30, 60 degrees from the heading) x 2 rings (0.5 and 1.0 of reach, from the force centre) x 5 layers; ready units take the next targets in list order, one each, the position in the list kept in `memory`; a caster too far from its target to reach it skips to the next |
| `reactive` | as `sweep`; and while any enemy is in `revealed`, or was within the last `REVEAL_MEMORY` = 200 ticks, the first ready units instead ping the last known centre of the revealed enemies moved along their last measured velocity, on their layer, so the picture is kept fresh |

Hider scripts: `still` (never moves); `drift` (moves along its heading at its own speed for the whole run); `shift` (as `drift`, and every 400 ticks changes layer by one, up then down, staying inside 0 to 4).

## The batch

`run_search_batch(settings, policies, n_placements, seed, workers)`: for every setting x seeker policy, the same `n_placements` placements (the hider side on `none`). One csv row per run with the setting, the coverage rate, the policy, the placement and both sides' results. The run file and the page follow the other batches' form (`scripts/skilllab/batches.py`, `summary.py`), with:

- per setting and policy: found-before-contact rate, median warning time, mean share revealed, mean picture age, pings per find;
- the policy spread per setting: best policy's found rate minus `ahead`'s;
- one chart: found-before-contact rate (y) against coverage rate (x, log scale), one line per policy;
- a section "What the instrument could not express": the "likely places" policy (needs terrain), the hider's decoy, Stage B, both sides pinging at once (the detection ratio), each with its reason.

The first batch, run only when the Architect says so: reach 1.5, 2 and 3 times the Vanguard's true sight; radius 250, 500, 1,000; cooldown 100, 200, 400, 800 ticks; reveal 100 ticks; force 16; 60 placements. The builder reports the measured time per run so the size can be set.

## Positive controls (real engine)

1. A hider directly ahead inside reach on the seeker's layer: `ahead` finds it before contact; `none` does not.
2. The same hider on another layer: `ahead` does not find it; `sweep` does.
3. A hider beyond reach + radius at the start and `still`: nothing finds it until the seeker has moved close enough; the first reveal tick is later than in control 1.
4. `reactive` against a `drift` hider: the picture age at contact is lower than `sweep`'s on the same placement.
5. The reveal follows the units: a `drift` hider revealed once stays in `revealed` for `reveal_ticks` after leaving the pinged disc.
6. Same seed, same inputs: identical `SearchResult`; 1 worker and 3 workers give byte-identical csv.
7. A larger radius never lowers `sweep`'s found rate over a fixed set of 20 placements.
