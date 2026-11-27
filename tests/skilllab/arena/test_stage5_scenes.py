# Rule pins: R-091-16, R-091-17 (lab harness story H-091, lab stage 5, piece P1 probe scenes and the drafted objective ring)
"""LAB stage 5, piece P1 (story H-091): the five probe scenes and one drafted layout under docs/northstar/research/layer_dynamics/arena/stage5/.

Rule words (docs/stories/H-091.md, "P1 scenes"):
  R-091-16  Five probe scenes and one drafted layout exist, each marked DRAFT and "Architect-made probe, not a catalogue layout" in its header: `front`, `side`, `rear` (the same holding
            block of 8 Vanguards facing east, attacked by the same block of 8 from the east, the north and the west, order rule R2: the holder holds, the attacker attack-moves onto the
            holder's centre of mass); `climb_flat` and `climb_slope` (the same attack over the same distance, flat and up one band, the holder at the top); `objective_ring` (from his words:
            the attacker in two groups from two angles around a holder; predicted 80 percent for the attacker). Each passes the lab's preflight (R1 to R8) with `--facing on`, and each runs
            to a wipe at seed 1.
  R-091-17  In `front`, `side` and `rear` the two blocks have the same shape, spacing and distance to contact, so the only difference between the three is the direction of approach
            (asserted from the files: the attackers' positions are the same block rotated about the holder's centre).

Files and ids the builder must write (the id is `L-NNNN`, the schema of arena/SNAPSHOT.md and of every layout; the probes take the unused L-94NN range, kept clear of the catalogue's
L-0001 to L-0084 and of the throw-away ids other tests use in scratch directories):
  front.toml L-9401, side.toml L-9402, rear.toml L-9403, climb_flat.toml L-9404, climb_slope.toml L-9405, objective_ring.toml L-9406.

Interface assumptions the story leaves open (each is the test writer's pick, reported):
  - The ids above; the header comment is the block of `#` lines before the first key, and holds both phrases (case as the story writes them).
  - "The holder holds" is the layout key `orders = "hold:A"` or `"hold:B"` (the catalogue's way, run.py `_orders_point`); the other side is the attacker. front, side and rear name the same holder.
  - "North" is the direction of decreasing y (the lab's own convention, h091_fixtures.APPROACH). The side block is the front block with east turned to north, i.e. an offset (dx, dy) from the
    holder's centre of mass becomes (dy, -dx); the rear block turns it to (-dx, -dy). Positions equal within ROT_WU 0.5 wu (the story's number).
  - "Every attacker facing the holder": the layout `facing` of each attacker points at the holder's centre of mass to within half the drafted arc (DRAFT-stage5-arc-deg 90, so 45 degrees):
    the holder's centre is inside the attacker's own arc and R-091-06 counts exactly half the arc as inside.
  - "Facing east" is facing 0.0 (radians, to the 4 decimals a layout carries, so 0.001).
  - "Two ranks of four, 40 wu apart": a rank is a line across the facing; two distinct rank positions 40 wu apart along the facing, four units on each, 40 wu apart across it.
  - "The attacker in two groups": a unit row names its group by `group` or by `arc` (the catalogue's tag, L-0067); exactly two names, each used by at least one unit; a group's bearing is the
    bearing of its units' centre of mass from the holder's centre of mass. "Predicted 80 percent for the attacker": `predict` names the attacker's side and `predict_rate` (the catalogue's
    key; the rate of side A, L-0067 and L-0039) is 0.8 when the attacker is side A and 0.2 when it is side B.
  - "The holder at the top" of climb_slope: the holder's centre of mass is at or beyond the slope's top edge (x of the feature plus half its length, heading 0) and the attackers start at or
    before its foot; the holder's units are on layer 1, the attackers' on layer 0; climb_flat has no slope feature and every unit on layer 0. "The same attack": the two files have the same
    roles per side, the same block shapes (each side's positions about its own centre of mass) and the same distance between the two centres of mass, within ROT_WU.
  - Preflight and the run are the lab's own: `check_layout` (R1 to R7), `unreachable` (R8) and the CLI with `--facing on` (sight off: the story gives no sight for the probes and the plan runs
    the flank and arc scenes with sight off); the run is seed 1 and ends `result.end == "wipe"`. A probe scene under `--sight on` is not tested: no rule states it (reported as a gap).
Controls (green today): the fixture's flank scene (h091_fixtures.flank_layout, the story's front scene by construction) runs to a wipe with `--facing on`; the block matchers accept the
fixture's east, north and west attackers and reject east against south; the group matcher reads L-0067 as two groups 178.6 degrees apart.
Red today: none of the six files exists."""
import math
import tomllib

import pytest

import h063_fixtures as fx
import h091_fixtures as f9
from scripts.skilllab.arena import run as arena_run, snapshot
from scripts.skilllab.catalogue import produce

PROBE_DIR = fx.ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "arena" / "stage5"
IDS = {"front": "L-9401", "side": "L-9402", "rear": "L-9403", "climb_flat": "L-9404", "climb_slope": "L-9405", "objective_ring": "L-9406"}
NAMES = tuple(IDS)
PHRASES = ("DRAFT", "Architect-made probe, not a catalogue layout")
ROT_WU = 0.5                   # the story: "positions equal within 0.5 wu" (the task brief for R-091-17)
SPACING_WU = 40.0              # the story: "2 ranks of 4, DRAFT 40 wu apart"
FACING_EAST_TOL = 0.001        # radians; a layout writes facing to 4 decimals
ARC_DEG = 90                   # DRAFT-stage5-arc-deg; half of it is the angle inside which a target is in the arc (R-091-06)
GROUP_GAP_DEG = 90             # the objective ring's two groups differ in bearing by at least this (task brief)
RING_RATE = 0.8                # "predicted 80 percent for the attacker"


# ------------------------------------------------------------------------------------------------ files

def path_of(name):
    return PROBE_DIR / (name + ".toml")


def load(name):
    """The layout dict of probe `name`; a missing file is a failed test with the path in the message."""
    p = path_of(name)
    if not p.is_file():
        pytest.fail("R-091-16: the probe file %s does not exist (docs/stories/H-091.md, P1 scenes)" % p.relative_to(fx.ROOT))
    with open(p, "rb") as f:
        return tomllib.load(f)


def header(name):
    """The block of `#` comment lines before the first key of the file."""
    lines = []
    for line in path_of(name).read_text().splitlines():
        s = line.strip()
        if s.startswith("#"):
            lines.append(s.lstrip("#").strip())
        elif s:
            break
    return "\n".join(lines)


@pytest.fixture(scope="module")
def fights(tmp_path_factory):
    """name -> callable running probe `name` once per test session through the CLI with `--facing on` (seed 1) and caching (process, document or None)."""
    root, cache = tmp_path_factory.mktemp("stage5_scenes"), {}

    def get(name):
        if name not in cache:
            out = root / name
            proc = fx.run(path_of(name), out, 1, "--facing", "on")
            f = out / ("%s-s1.fight.json" % IDS[name])
            cache[name] = (proc, snapshot.read(f) if f.exists() else None)
        return cache[name]
    return get


# ------------------------------------------------------------------------------------------------ geometry matchers

def com(units):
    return (sum(u["x"] for u in units) / len(units), sum(u["y"] for u in units) / len(units))


def holder_key(lay):
    """'side_a' or 'side_b': the side that holds (orders hold:A / hold:B, or under `groups` the one side whose order rows are all holds); None when the layout names none."""
    orders = lay.get("orders")
    if orders in ("hold:A", "hold:B"):
        return "side_a" if orders == "hold:A" else "side_b"
    if orders == "groups":
        holds = {r["side"] for r in lay.get("order_groups", []) if r.get("order") == "hold"}
        moves = {r["side"] for r in lay.get("order_groups", []) if r.get("order") != "hold"}
        if len(holds) == 1 and not holds & moves:
            return "side_a" if holds == {"A"} else "side_b"
    return None


def other(key):
    return "side_b" if key == "side_a" else "side_a"


def offsets(units, centre):
    return [(u["role"], u["x"] - centre[0], u["y"] - centre[1]) for u in units]


def rotate(off, how):
    """An offset (role, dx, dy) turned from the front block's frame: 'side' east to north (dx, dy) -> (dy, -dx); 'rear' -> (-dx, -dy); 'front' unchanged; 'south' the wrong way, for the control."""
    role, dx, dy = off
    return {"front": (role, dx, dy), "side": (role, dy, -dx), "rear": (role, -dx, -dy), "south": (role, -dy, dx)}[how]


def blocks_differ(have, want, tol=ROT_WU):
    """None when every (role, dx, dy) of `want` has its own partner in `have` (same role, both coordinates within tol, each used once), else a short reason."""
    if len(have) != len(want):
        return "%d units against %d" % (len(have), len(want))
    free = list(have)
    for role, dx, dy in want:
        hit = next((i for i, (r, x, y) in enumerate(free) if r == role and abs(x - dx) <= tol and abs(y - dy) <= tol), None)
        if hit is None:
            return "no %s within %.1f wu of offset (%.2f, %.2f) from the holder's centre" % (role, tol, dx, dy)
        free.pop(hit)
    return None


def angle_between(facing, bearing):
    """Degrees, 0 to 180, between a facing and a bearing (radians in)."""
    return f9.off_deg(facing, bearing)


def rank_problem(units, tol=ROT_WU):
    """None when `units` are 8 Vanguards in two ranks of four, SPACING_WU apart (ranks SPACING_WU apart along x, the four of a rank SPACING_WU apart along y, the two ranks at the same ys); else a
    reason. A rank is a line across an east-west facing, the block's own frame (the holder's; the attackers of `front`)."""
    if len(units) != 8 or any(u["role"] != "Vanguard" for u in units):
        return "%d units, roles %s: want 8 Vanguards" % (len(units), sorted({u["role"] for u in units}))
    cols = {}
    for u in units:
        key = next((c for c in cols if abs(c - u["x"]) <= tol), u["x"])
        cols.setdefault(key, []).append(u["y"])
    if len(cols) != 2 or any(len(ys) != 4 for ys in cols.values()):
        return "ranks along x: %s, want two ranks of four" % {round(c, 1): len(ys) for c, ys in sorted(cols.items())}
    (xa, ya), (xb, yb) = sorted(cols.items())
    if abs(abs(xb - xa) - SPACING_WU) > tol:
        return "the ranks are %.2f wu apart, want %g" % (abs(xb - xa), SPACING_WU)
    ya, yb = sorted(ya), sorted(yb)
    for ys in (ya, yb):
        if any(abs((b - a) - SPACING_WU) > tol for a, b in zip(ys, ys[1:])):
            return "a rank's units are not %g wu apart: y %s" % (SPACING_WU, [round(y, 2) for y in ys])
    if any(abs(a - b) > tol for a, b in zip(ya, yb)):
        return "the two ranks do not line up: y %s against %s" % ([round(y, 2) for y in ya], [round(y, 2) for y in yb])
    return None


def facing_problem(units, target, limit=ARC_DEG / 2.0):
    """None when every unit's layout facing is within `limit` degrees of its bearing to `target`; else the first unit that is not."""
    for i, u in enumerate(units):
        a = angle_between(u["facing"], math.atan2(target[1] - u["y"], target[0] - u["x"]))
        if a > limit:
            return "unit %d at (%.1f, %.1f) faces %.3f rad, %.1f degrees off the holder's centre (limit %.1f)" % (i, u["x"], u["y"], u["facing"], a, limit)
    return None


def scene(lay):
    """(holder units, attacker units, holder centre) of a probe layout; fails the test when the layout names no holder."""
    hk = holder_key(lay)
    if hk is None:
        pytest.fail("R-091-16: orders %r names no holder (want 'hold:A' or 'hold:B': order rule R2, the holder holds and the attacker attack-moves)" % (lay.get("orders"),))
    h, a = lay[hk]["units"], lay[other(hk)]["units"]
    return h, a, com(h)


def group_name(u):
    return u["group"] if "group" in u else u.get("arc")


def group_problem(lay):
    """(None, [bearing degrees of each group's centre of mass from the holder's centre]) or (reason, [])."""
    hk = holder_key(lay)
    if hk is None:
        return "orders %r names no holder" % (lay.get("orders"),), []
    centre, rows = com(lay[hk]["units"]), lay[other(hk)]["units"]
    names = sorted({group_name(u) for u in rows if group_name(u) is not None})
    if len(names) != 2 or any(group_name(u) is None for u in rows):
        return "the attacker's units name %d groups (by `group` or `arc`), want exactly 2 with every unit in one" % len(names), []
    out = []
    for n in names:
        c = com([u for u in rows if group_name(u) == n])
        out.append(math.degrees(math.atan2(c[1] - centre[1], c[0] - centre[0])))
    return None, out


def gap_deg(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


# ------------------------------------------------------------------------------------------------ controls (green today)

def test_R_091_16_control_fixture_flank_scene_runs_to_a_wipe_with_facing_on(tmp_path):
    """R-091-16 control: the story's front scene as the fixture builds it (holder block facing east, attackers from the east, hold:A) passes R1 to R8 and runs to a wipe at seed 1 with
    `--facing on`: a red test below means the probe file is missing or wrong, not that the harness cannot run such a scene."""
    lay = f9.flank_layout("L-9401", "east")
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == []
    assert arena_run.unreachable(lay) is None
    proc, doc = fx.fight(lay, tmp_path, 1, "--facing", "on")
    assert proc.returncode == 0 and "REJECT" not in proc.stdout, proc.stdout + proc.stderr
    assert doc["result"]["end"] == "wipe", "the control fight ended %r, not in a wipe" % doc["result"]["end"]


def test_R_091_17_control_block_matcher_accepts_the_fixture_approaches_and_rejects_the_wrong_one():
    """R-091-17 control: the rotation matcher passes the fixture's attacker blocks from the north and the west against its east block turned 90 and 180 degrees, and fails east against
    south (the wrong way round), so a green below is a rotated block and not a matcher that accepts anything."""
    holder = f9.holder_block()
    centre = com(holder)
    front = offsets(f9.attacker_block("east"), centre)
    for approach, how in (("east", "front"), ("north", "side"), ("west", "rear")):
        got = offsets(f9.attacker_block(approach), centre)
        assert blocks_differ(got, [rotate(o, how) for o in front]) is None, "fixture %s block is not the east block turned (%s)" % (approach, how)
    south = offsets(f9.attacker_block("south"), centre)
    assert blocks_differ(south, [rotate(o, "side") for o in front]) is not None, "the matcher accepted a block 90 degrees the wrong way round"
    assert rank_problem(f9.holder_block()) is None and rank_problem(f9.attacker_block("east")) is None
    assert rank_problem(f9.attacker_block("north")) is not None, "the rank check accepted a block rotated off the east-west frame"


def test_R_091_16_control_group_matcher_reads_L_0067_as_two_groups_far_apart():
    """R-091-16 control: the group matcher on his own two-pronged layout L-0067 (units tagged `arc` 0 and 1, holder side B) finds two groups far over 90 degrees apart (dumped 178.6), and finds one group
    in a layout whose tags are merged."""
    with open(f9.CATALOGUE / "L-0067.toml", "rb") as f:
        lay = tomllib.load(f)
    why, bearings = group_problem(lay)
    assert why is None, why
    assert gap_deg(*bearings) >= GROUP_GAP_DEG, bearings   # dumped: 179.3 and 0.7 degrees (the centres of mass of two arcs, 178.6 apart)
    for u in lay["side_a"]["units"]:
        u["arc"] = 0
    assert group_problem(lay)[0] is not None


# ------------------------------------------------------------------------------------------------ R-091-16: the files

@pytest.mark.parametrize("name", NAMES)
def test_R_091_16_the_probe_file_exists_with_its_id(name):
    """R-091-16: "Five probe scenes and one drafted layout exist": the file <name>.toml is under arena/stage5/ and its `id` is the L-NNNN id named in this file."""
    lay = load(name)
    assert lay.get("id") == IDS[name], "%s.toml has id %r, want %s" % (name, lay.get("id"), IDS[name])


@pytest.mark.parametrize("name", NAMES)
def test_R_091_16_the_header_says_draft_and_architect_made_probe(name):
    """R-091-16: "each marked DRAFT and 'Architect-made probe, not a catalogue layout' in its header": both phrases are in the file's leading comment block."""
    load(name)
    head = header(name)
    for phrase in PHRASES:
        assert phrase in head, "%s.toml header comment lacks %r; header was %r" % (name, phrase, head[:200])


@pytest.mark.parametrize("name", NAMES)
def test_R_091_16_the_probe_passes_the_preflight_r1_to_r8(name):
    """R-091-16: "Each passes the lab's preflight (R1 to R8)": `check_layout` names no rule (R1 to R7) and `unreachable` (R8) names no unit."""
    lay = load(name)
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == [], "%s.toml breaks %s" % (name, produce.check_layout(lay, produce.presets(), produce.rules()))
    assert arena_run.unreachable(lay) is None, "%s.toml R8: %s cannot reach its orders point" % (name, arena_run.unreachable(lay))


@pytest.mark.parametrize("name", NAMES)
def test_R_091_16_the_probe_runs_to_a_wipe_at_seed_1_with_facing_on(name, fights):
    """R-091-16: "each runs to a wipe at seed 1": the CLI with `--facing on` exits 0 with no REJECT line, writes the file, and `result.end` is "wipe"."""
    load(name)
    proc, doc = fights(name)
    assert proc.returncode == 0 and "REJECT" not in proc.stdout, "%s: exit %s; %s" % (name, proc.returncode, (proc.stdout + proc.stderr)[-400:])
    assert doc is not None, "%s: no fight file written" % name
    assert doc["stage5"]["arc_deg"] == ARC_DEG, "the run was not a --facing on run: stage5 %r" % doc.get("stage5")
    assert doc["result"]["end"] == "wipe", "%s ended %r at tick %s, not in a wipe" % (name, doc["result"]["end"], doc["result"]["ticks"])


# ------------------------------------------------------------------------------------------------ R-091-16: front, side, rear

@pytest.mark.parametrize("name", ("front", "side", "rear"))
def test_R_091_16_the_holder_holds_a_block_of_8_vanguards_facing_east(name):
    """R-091-16: "the same holding block of 8 Vanguards facing east": orders hold:<side>, the holder's units are 8 Vanguards in 2 ranks of 4, 40 wu apart, layer 0, facing 0.0; the
    attacker (the other side) is 8 units, order rule R2: it has no hold, so it attack-moves onto the holder's centre of mass (run.py `_orders_point`)."""
    lay = load(name)
    holder, attacker, _ = scene(lay)
    assert rank_problem(holder) is None, "%s holder: %s" % (name, rank_problem(holder))
    assert all(f9.off_deg(u["facing"], 0.0) <= FACING_EAST_TOL * 180.0 / math.pi and u["layer"] == 0 for u in holder), "%s: a holder does not face east on layer 0" % name
    assert len(attacker) == 8 and all(u["role"] == "Vanguard" for u in attacker), "%s: the attacker is not 8 Vanguards" % name
    assert lay["side_a"]["headcount"] == 8 and lay["side_b"]["headcount"] == 8


def test_R_091_16_front_side_and_rear_have_the_same_holder_and_the_same_orders():
    """R-091-16: "the same holding block ... attacked by the same block of 8": the three files hold the same side with the same orders and the holder's 8 positions (within 0.5 wu) and
    facings are the same in all three."""
    lays = {n: load(n) for n in ("front", "side", "rear")}
    assert len({lay["orders"] for lay in lays.values()}) == 1, "orders differ: %s" % {n: lay["orders"] for n, lay in lays.items()}
    front_h, _, centre = scene(lays["front"])
    want = offsets(front_h, centre)
    for n in ("side", "rear"):
        h, _, c = scene(lays[n])
        assert blocks_differ(offsets(h, c), want) is None, "%s holder block differs from front: %s" % (n, blocks_differ(offsets(h, c), want))
        assert abs(c[0] - centre[0]) <= ROT_WU and abs(c[1] - centre[1]) <= ROT_WU, "%s holder stands at %s, front at %s" % (n, c, centre)
        assert all(abs(a["facing"] - b["facing"]) <= FACING_EAST_TOL for a, b in zip(sorted(h, key=lambda u: (u["x"], u["y"])), sorted(front_h, key=lambda u: (u["x"], u["y"]))))


@pytest.mark.parametrize("name", ("front", "side", "rear"))
def test_R_091_16_every_attacker_faces_the_holder(name):
    """R-091-16: "every attacker facing the holder": each attacker's layout facing is within half the drafted arc (45 degrees) of its bearing to the holder's centre of mass."""
    holder, attacker, centre = scene(load(name))
    assert facing_problem(attacker, centre) is None, "%s: %s" % (name, facing_problem(attacker, centre))


def test_R_091_16_the_front_attacker_block_comes_from_the_east_in_two_ranks_of_four():
    """R-091-16: "attacked by the same block of 8 from the east": in `front` the attackers' centre of mass is due east of the holder's (same y within 0.5 wu), and they are 8 Vanguards in 2
    ranks of 4, 40 wu apart, the ranks across the line of approach."""
    holder, attacker, centre = scene(load("front"))
    mid = com(attacker)
    assert mid[0] > centre[0] and abs(mid[1] - centre[1]) <= ROT_WU, "front attackers' centre %s is not due east of the holder's %s" % (mid, centre)
    assert min(u["x"] for u in attacker) > max(u["x"] for u in holder), "front attackers are not all east of every holder"
    assert rank_problem(attacker) is None, "front attackers: %s" % rank_problem(attacker)


# ------------------------------------------------------------------------------------------------ R-091-17: rotation

@pytest.mark.parametrize("name,how", (("side", "side"), ("rear", "rear")))
def test_R_091_17_the_attackers_are_the_front_block_turned_about_the_holders_centre(name, how):
    """R-091-17: "the attackers' positions are the same block rotated about the holder's centre": the attackers of `side` are the front attackers' offsets from the holder's centre of mass
    turned 90 degrees (east to north) and those of `rear` turned 180 degrees (east to west), each position within 0.5 wu."""
    fh, fa, fc = scene(load("front"))
    h, a, c = scene(load(name))
    want = [rotate(o, how) for o in offsets(fa, fc)]
    assert blocks_differ(offsets(a, c), want) is None, "%s attackers are not the front block turned (%s): %s" % (name, how, blocks_differ(offsets(a, c), want))


def test_R_091_17_the_three_distances_to_contact_are_the_same():
    """R-091-17: "the same shape, spacing and distance to contact": the distance from the holder's centre of mass to the nearest attacker (the front rank) and to the attackers' centre
    of mass is the same in front, side and rear to within 0.5 wu. (Premise dumped on a reference set: attacker-to-nearest-holder-unit is NOT the same, 180 wu from the east and 140 wu
    from the north, because the holder's block is 120 wu across and 40 deep; the rule rotates about the holder's centre, so contact is measured from it.)"""
    got = {}
    for n in ("front", "side", "rear"):
        h, a, c = scene(load(n))
        got[n] = (min(math.hypot(x["x"] - c[0], x["y"] - c[1]) for x in a), math.hypot(com(a)[0] - c[0], com(a)[1] - c[1]))
    for n in ("side", "rear"):
        assert all(abs(p - q) <= ROT_WU for p, q in zip(got[n], got["front"])), "%s (nearest attacker, attackers' centre) distances from the holder's centre %s differs from front %s" % (n, got[n], got["front"])


# ------------------------------------------------------------------------------------------------ R-091-16: climb_flat and climb_slope

def test_R_091_16_climb_flat_is_the_same_attack_without_a_slope():
    """R-091-16: "climb_flat ... flat": no slope feature, every unit on layer 0, the holder holds a block of Vanguards and the attacker attack-moves onto it."""
    lay = load("climb_flat")
    assert not any(f.get("kind") == "slope" for f in lay.get("features", [])), "climb_flat carries a slope feature"
    assert all(u["layer"] == 0 for k in ("side_a", "side_b") for u in lay[k]["units"]), "climb_flat has a unit off layer 0"
    scene(lay)


def test_R_091_16_climb_slope_puts_the_holder_one_band_up_at_the_top():
    """R-091-16: "climb_slope ... up one band, the holder at the top": the layout carries a slope feature (heading 0, from band 0 to band 1), the attackers are on layer 0 at or before its foot,
    the holder's units are on layer 1 and its centre of mass is at or beyond the slope's top edge."""
    lay = load("climb_slope")
    slopes = [f for f in lay.get("features", []) if f.get("kind") == "slope"]
    assert len(slopes) == 1, "climb_slope carries %d slope features, want 1" % len(slopes)
    s = slopes[0]
    assert s.get("heading", 0.0) == 0.0 and s["from_band"] == 0 and s["to_band"] == 1, "the slope is %r, want heading 0, band 0 up to band 1" % s
    holder, attacker, centre = scene(lay)
    assert all(u["layer"] == 1 for u in holder), "a holder is not on layer 1"
    assert all(u["layer"] == 0 for u in attacker), "an attacker is not on layer 0"
    foot, top = s["x"] - s["length"] / 2, s["x"] + s["length"] / 2
    assert max(u["x"] for u in attacker) <= foot, "an attacker starts at x %.1f, past the slope's foot at %.1f" % (max(u["x"] for u in attacker), foot)
    assert centre[0] >= top, "the holder's centre x %.1f is before the slope's top at %.1f" % (centre[0], top)


def test_R_091_16_climb_flat_and_climb_slope_are_the_same_units_over_the_same_distance():
    """R-091-16: "the same attack over the same distance": the two files have the same roles on each side, the same block shapes (each side about its own centre of mass, within 0.5 wu)
    and the same distance between the two centres of mass (within 0.5 wu); only the slope and the holder's band differ."""
    flat, slope = load("climb_flat"), load("climb_slope")
    hf, af, cf = scene(flat)
    hs, as_, cs = scene(slope)
    assert holder_key(flat) == holder_key(slope), "the holder is not the same side in the two files"
    for what, x, y in (("holder", hf, hs), ("attacker", af, as_)):
        assert sorted(u["role"] for u in x) == sorted(u["role"] for u in y), "the %s's roles differ between the files" % what
        why = blocks_differ(offsets(x, com(x)), offsets(y, com(y)))
        assert why is None, "the %s's block shape differs between the files: %s" % (what, why)
    df = math.hypot(com(af)[0] - cf[0], com(af)[1] - cf[1])
    ds = math.hypot(com(as_)[0] - cs[0], com(as_)[1] - cs[1])
    assert abs(df - ds) <= ROT_WU, "attacker to holder: %.2f wu flat, %.2f wu on the slope" % (df, ds)


def test_R_091_16_the_attackers_climb_in_climb_slope_and_never_in_climb_flat(tmp_path):
    """R-091-16 ("flat and up one band"): in an every-10-ticks file of the facing-on fight each attacker of climb_slope has a frame with `climbing` strictly between 0 and 1, and in
    climb_flat every unit has `climbing` 0.0 in every frame, so the pair differs by the climb and the scene really climbs."""
    out = {}
    for n in ("climb_flat", "climb_slope"):
        lay = load(n)
        proc, doc = f9.closeup_doc(lay, tmp_path / n, 10, "--facing", "on")
        assert proc.returncode == 0 and doc is not None, "%s closeup: exit %s; %s" % (n, proc.returncode, (proc.stdout + proc.stderr)[-300:])
        out[n] = doc
    assert all(u["climbing"] == 0.0 for f in out["climb_flat"]["frames"] for u in f["units"]), "a unit of climb_flat has climbing above 0"
    doc = out["climb_slope"]
    attackers = {u["id"] for u in doc["frames"][0]["units"] if u["side"] == ("A" if holder_key(load("climb_slope")) == "side_b" else "B")}
    climbed = {u["id"] for f in doc["frames"] for u in f["units"] if 0.0 < u["climbing"] < 1.0}
    assert attackers and attackers <= climbed, "attackers never seen with climbing between 0 and 1: %s" % sorted(attackers - climbed)


# ------------------------------------------------------------------------------------------------ R-091-16: objective_ring

def test_R_091_16_objective_ring_has_the_attacker_in_two_groups_at_least_90_degrees_apart():
    """R-091-16: "the attacker in two groups from two angles around a holder": the attacker's units name exactly two groups (`group` or `arc`) and the bearings of the groups' centres of
    mass from the holder's centre of mass differ by at least 90 degrees."""
    why, bearings = group_problem(load("objective_ring"))
    assert why is None, "objective_ring: " + why
    assert gap_deg(*bearings) >= GROUP_GAP_DEG, "the two groups come from bearings %s degrees, %.1f apart; want at least %d" % ([round(b, 1) for b in bearings], gap_deg(*bearings), GROUP_GAP_DEG)


def test_R_091_16_objective_ring_predicts_80_percent_for_the_attacker():
    """R-091-16: "predicted 80 percent for the attacker": `predict` is the attacker's side and `predict_rate` (the rate of side A) is 0.8 for an attacker on side A, 0.2 on side B."""
    lay = load("objective_ring")
    hk = holder_key(lay)
    assert hk is not None, "orders %r names no holder" % (lay.get("orders"),)
    letter = "A" if other(hk) == "side_a" else "B"
    want = RING_RATE if letter == "A" else 1.0 - RING_RATE
    assert lay.get("predict") == letter, "predict is %r, the attacker is side %s" % (lay.get("predict"), letter)
    assert abs(lay.get("predict_rate", -1.0) - want) < 1e-9, "predict_rate is %r, want %s (80 percent for the attacker, side %s)" % (lay.get("predict_rate"), want, letter)
