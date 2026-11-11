"""Knob sweeps and the smoke run (spec docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, piece L4; rulings 3, 4, 10, 11, 13).

A family sweeps one knob over a coarse grid inside 0.25x to 4x of its base, scans each play and its baselines at every point
(bisection by default, every headcount with full_scan), refines the grid only around a sign change of the play's gain, and runs
the family's positive and null controls. Output: sweep_<family>.csv per family and sweep_summary.json; smoke.csv and
smoke_summary.json for the smoke run.
"""
import collections
import dataclasses
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from scripts.skilllab import depth, formations, maps, plays_space, pool, probe as probe_mod, rows as rows_mod, scan as scan_mod, scenes
from scripts.skilllab.contract import FROZEN_NAMES, Group, Setup

FAMILY_ORDER = ("vision", "range_up", "damage_up", "emitting", "arc", "cone", "sign_flip")
SIZE, ENEMY_FROM, ENEMY_TO, REPLICATES = 16, 8, 48, 3
CONTROL_MAX_TICKS = 600     # DRAFT-control-max-ticks (Westley's number): controls that need no result stop here; a 12000-tick no-shot fight is wasted time
LAYER2_RATIO = 0.4          # spec: vision at two layers is 0.4 of the one-layer value
DAMAGE_CONTROL_PLAY = "s3_types_by_reach"   # decisions 22: damage-up's positive control is this one designated fight
VISION_CONTROL_PLAY = "s3_vision_control"   # clause 24: the vision positive control is this one all cross-layer 16 v 16 fight
SMOKE_LAYOUTS = ("81", "78", "192")         # layout indices of the run-1 draw (depth.lhs_draw(200, 0))
SMOKE_CONTROLS = (("mirror", 16), ("numbers", 8), ("planted", 16))
LAYER_PLAYS = ("s3_layer_above", "s3_types_by_reach")
MIRROR_FIGHTS = 30          # DRAFT-mirror-fights (the Architect's number, on Westley's open list): fights of a mix's naive mirror pre-check
MIRROR_X = 350.0            # the two blobs of a mirror fight stand at -x and +x
WARDEN_PER_16 = 4           # interim lab cap, Wardens per 16 units; retires with FU-warden-no-stack (FINDING-lab-d9, a TD row removes it)
KNOWN_CAP = "known_cap:FINDING-lab-d9"      # M9's one Warden-stall cap in 30; retires with FU-warden-no-stack
MIX_LAYER_PLAYS = ("s3_raider_bombard", "s3_interceptor_bombard", "s3_interceptor_raider", "s3_bombard_bastion", "s3_bombard_bastion_level")
PLAYS_BY_FAMILY = {
    "vision": LAYER_PLAYS + MIX_LAYER_PLAYS, "range_up": LAYER_PLAYS + MIX_LAYER_PLAYS, "damage_up": LAYER_PLAYS + MIX_LAYER_PLAYS,
    "sign_flip": LAYER_PLAYS + MIX_LAYER_PLAYS,
    "emitting": ("s3_dark_striker",), "arc": ("s2_concave", "s2_mass_one_end", "s2_screen", "s2_warden_line"),
    "cone": ("s2_concave", "s2_mass_one_end", "s2_screen", "s2_warden_line"),
}
SMOKE_PLAYS = {"vision": ("s3_layer_above", "s3_types_by_reach")}      # the smoke's plays per family: a subset of PLAYS_BY_FAMILY (the batch sweeps all of them)
BASES = {
    "OM_TP_VISION_UP_1": 0.5, "OM_TP_VISION_DOWN_1": 0.5, "OM_TP_VISION_UP_2": 0.2, "OM_TP_VISION_DOWN_2": 0.2,
    "OM_TP_RANGE_UP_1": 1.0, "OM_TP_RANGE_UP_2": 1.0, "OM_TP_RANGE_DOWN_1": 1.0, "OM_TP_RANGE_DOWN_2": 1.0,
    "OM_TP_DAMAGE_UP_1": 1.0, "OM_TP_DAMAGE_UP_2": 1.0,
    "OM_TP_EMIT_SIGHT_MULT": 2.0, "OM_TP_EMIT_SEEN_MULT": 3.0,      # Westley's start (2026-10-13)
    "OM_TP_FIRING_ARC_DEG": 30.0, "cone_range": 300.0, "cone_half_angle": 45.0,      # DRAFT-firing-arc-deg: Westley's ruling 30 deg (decision 46); DRAFT cone bases
}
REFINABLE = ("vision", "range_up", "damage_up", "arc")
Capabilities = collections.namedtuple("Capabilities", "arc cone")


@dataclass(frozen=True)
class Point:
    family: str
    knob: str          # an OM_TP_* name, or "cone"
    value: float
    settings: dict     # OM_TP_* name -> number
    setup: dict        # Setup field -> value (firing_arc_deg, cone)
    kind: str          # grid | refined | sign_flip | control_positive | control_null
    label: str


@dataclass
class Control:
    points: list
    reach: Optional[tuple]      # (0, 0): fought on the reach_zero build
    check: Any                  # check(results_by_point) -> bool
    max_ticks: Optional[int] = CONTROL_MAX_TICKS    # None: the fight runs to its own end
    play: Optional[str] = None  # None: every play of the run; a name: one designated fight on that play


def in_band(value, base):
    return 0.25 * base <= value <= 4.0 * base


def _vision_settings(v):
    return {"OM_TP_VISION_UP_1": v, "OM_TP_VISION_DOWN_1": v, "OM_TP_VISION_UP_2": LAYER2_RATIO * v,
            "OM_TP_VISION_DOWN_2": LAYER2_RATIO * v}


def _vision(v, kind="grid"):
    return Point("vision", "OM_TP_VISION_UP_1", v, _vision_settings(v), {}, kind, "vision %s" % v)


def _range_up(v, kind="grid", family="range_up"):
    return Point(family, "OM_TP_RANGE_UP_1", v, {"OM_TP_RANGE_UP_1": v, "OM_TP_RANGE_UP_2": v, "OM_TP_RANGE_DOWN_1": 1.0,
                                                  "OM_TP_RANGE_DOWN_2": 1.0}, {}, kind, "range-up %s" % v)


def _damage_up(v, kind="grid", family="damage_up"):
    return Point(family, "OM_TP_DAMAGE_UP_1", v, {"OM_TP_DAMAGE_UP_1": v, "OM_TP_DAMAGE_UP_2": v}, {}, kind, "damage-up %s" % v)


def _emitting(sight, seen, vision):
    return Point("emitting", "OM_TP_EMIT_SIGHT_MULT", sight,
                 {**_vision_settings(vision), "OM_TP_EMIT_SIGHT_MULT": sight, "OM_TP_EMIT_SEEN_MULT": seen}, {}, "grid",
                 "emitting sight %s seen %s at vision %s" % (sight, seen, vision))


def _arc(v, kind="grid"):
    return Point("arc", "OM_TP_FIRING_ARC_DEG", v, {}, {"firing_arc_deg": float(v)}, kind, "arc %s" % v)


def _cone(rng, half):
    return Point("cone", "cone", rng, {}, {"cone": {"Vanguard": (rng, half, 1.0)}}, "grid", "cone range %s half-angle %s" % (rng, half))


def point_label(point):
    """Decision 31 A: the series a row belongs to along its knob: a cone's half-angle, an emitting point's vision, else '-'."""
    if point.family == "cone" and point.setup.get("cone"):
        return "half=%s" % next(iter(point.setup["cone"].values()))[1]
    if point.family == "emitting":
        return "vision=%s" % point.settings["OM_TP_VISION_UP_1"]
    return "-"


def grid(family):
    """The coarse points of a family in the spec's order."""
    if family == "vision":
        return [_vision(v) for v in (0.125, 0.25, 0.5, 1.0)]
    if family == "range_up":
        return [_range_up(v) for v in (1.0, 0.75, 0.5, 0.25)]
    if family == "damage_up":
        return [_damage_up(v) for v in (1.0, 0.75, 0.5, 0.25)]
    if family == "emitting":
        return [_emitting(s, t, v) for v in (0.125, 0.25) for s, t in ((1.0, 1.5), (2.0, 3.0), (4.0, 6.0))]
    if family == "arc":
        return [_arc(v) for v in (7.5, 15, 30, 60, 120)]
    if family == "cone":
        return [_cone(r, h) for r in (150, 300, 600) for h in (22.5, 45, 90)]
    if family == "sign_flip":
        return [dataclasses.replace(_range_up(2.0, "sign_flip", "sign_flip"), label="sign-flip control: range-up 2.0"),
                dataclasses.replace(_damage_up(2.0, "sign_flip", "sign_flip"), label="sign-flip control: damage-up 2.0")]
    raise ValueError("unknown family %r; valid names: %s" % (family, ", ".join(FAMILY_ORDER)))


def _refined_point(family, v):
    return {"vision": _vision, "range_up": _range_up, "damage_up": _damage_up, "arc": _arc}[family](v, "refined")


def refine(values, differs, max_rounds=2):
    """[(round, value), ...]: halve (arithmetic midpoint) each bracket of two coarse values whose sign differs, then the half that
    still brackets the change, at most max_rounds times. differs(value) -> bool is called once per value."""
    signs = {}

    def sign(v):
        if v not in signs:
            signs[v] = bool(differs(v))
        return signs[v]

    ordered = sorted(values)
    brackets = [(a, b) for a, b in zip(ordered, ordered[1:]) if sign(a) != sign(b)]
    added = []
    for rnd in range(1, max_rounds + 1):
        nxt = []
        for a, b in brackets:
            mid = (a + b) / 2
            added.append((rnd, mid))
            nxt.append((a, mid) if sign(mid) != sign(a) else (mid, b))
        brackets = nxt
    return added


def detect(engine=None):
    """What the library can do: the arc parameter (named in the header's parameter table) and a usable om_roster_set_cone."""
    if engine is None:
        from scripts.skilllab.engine import Engine
        engine = Engine()
    try:
        engine.param_id("OM_TP_FIRING_ARC_DEG")
        arc = True
    except ValueError:
        arc = False
    w = engine.new_world(0)
    try:
        engine.set_cone(w, engine.type_id("Vanguard"), 0.0, 45.0, 1.0)     # AttributeError: no symbol; ValueError: the E0 stub
        cone = True
    except (ValueError, AttributeError):
        cone = False
    finally:
        engine.free_world(w)
    return Capabilities(arc=arc, cone=cone)


def skip_reason(family, caps):
    if family == FROZEN_NAMES[1]:
        return ("the library never reads OM_TP_CATMULT_* (csrc/unit.c uses the compile-time OM_CATEGORY_MULTIPLIER_* constants), "
                "so every point would give one row; FINDING-lab-d6, waits for an engine piece")
    if family == "arc" and not caps.arc:
        return "the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)"
    if family == "cone" and not caps.cone:
        return "the library has no usable om_roster_set_cone (LAB-REV2-E2 not built)"
    return None


def baseline_roles(setup):
    """The naive baselines a play is read against (ruling 3; decision 41 item 3), derived from the play's own Setup and never from its
    name. A holder (a side-0 group on guard) is read against the naive attacker and the naive defender; one with a guard group on a
    layer no side-1 group stands on gets the defender twice, on the attacker's layer and on the play's layer (DRAFT, Architect). A
    meeting has no holder and no naive defender."""
    holders = [g for g in setup.groups if g.side == 0 and g.order == "guard"]
    if not holders:
        return ("naive_attacker",)
    enemy_layers = {g.layer for g in setup.groups if g.side == 1}
    if any(g.layer not in enemy_layers for g in holders):
        return ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer")
    return ("naive_attacker", "naive_defender")


def _play_roles(builds, play, features):
    """(play build, baseline roles): the roles are read from the play's build at the first headcount, unswapped."""
    play_build = builds(play, "play", features)
    return play_build, baseline_roles(play_build(ENEMY_FROM, False))


# ---- controls --------------------------------------------------------------------------------------------------------------------

def _identical(results_by_point):
    first = [rows_mod.fight_row(r) for r in results_by_point[0]]
    return all([rows_mod.fight_row(r) for r in rs] == first for rs in results_by_point[1:])


def _vision_zero_ok(results_by_point):
    return all(r.survivors == r.heads == (16, 16) and tuple(r.firing_unit_seconds) == (0.0, 0.0)
               for rs in results_by_point for r in rs)


def _damage_ok(results_by_point):
    """Damage-up 0.5 changes the result and not the count. The count is the opening-window row values: a lean result (the pool)
    has no per-tick firing series."""
    base, half = results_by_point
    return (len(base) == len(half) and all(a.firing_window == b.firing_window and a.weighted_window == b.weighted_window
                                           for a, b in zip(base, half))
            and any((a.outcome, a.margin, a.survivors) != (b.outcome, b.margin, b.survivors) for a, b in zip(base, half)))


def _as(point, kind):
    return dataclasses.replace(point, kind=kind)


def controls(family):
    """{"positive"/"null": Control} of a family. The null control of a reach family is the reach (0, 0) build at every grid point."""
    if family == "sign_flip":
        return {}
    if family == "arc":
        explicit = Point("arc", "OM_TP_FIRING_ARC_DEG", 360.0, {"OM_TP_FIRING_ARC_DEG": 360.0}, {}, "control_null", "arc 360 set")
        unset = Point("arc", "OM_TP_FIRING_ARC_DEG", 360.0, {}, {}, "control_null", "arc never set")
        return {"null": Control([explicit, unset], None, _identical)}
    if family == "cone":
        zero = Point("cone", "cone", 0.0, {}, {"cone": {"Vanguard": (0.0, 45.0, 1.0)}}, "control_null", "cone range 0")
        none = Point("cone", "cone", 0.0, {}, {}, "control_null", "no cone")
        return {"null": Control([zero, none], None, _identical)}
    out = {"null": Control([_as(p, "control_null") for p in grid(family)], (0, 0), _identical)}
    if family == "vision":
        out["positive"] = Control([_as(_vision(0.0), "control_positive")], None, _vision_zero_ok,
                                  play=VISION_CONTROL_PLAY)
    if family == "damage_up":
        out["positive"] = Control([_as(_damage_up(v), "control_positive") for v in (1.0, 0.5)], None, _damage_ok,
                                  max_ticks=None, play=DAMAGE_CONTROL_PLAY)
    return out


# ---- builds -----------------------------------------------------------------------------------------------------------------------

class Applied:
    """A build with a knob point applied to every setup it makes (states on, the point's settings and Setup fields), and the
    prefight word of each headcount it built, for the rows."""

    def __init__(self, build, point, max_ticks=None):
        self.build, self.point, self.max_ticks, self.prefight = build, point, max_ticks, {}
        self.labels = getattr(build, "labels", {})

    def __call__(self, enemy_heads, swap):
        setup = self.build(enemy_heads, swap)
        self.prefight[enemy_heads] = self.labels.get("prefight") or "ok"
        fields = dict(self.point.setup, states=True, settings={**setup.settings, **self.point.settings})
        if self.max_ticks is not None:
            fields["max_ticks"] = self.max_ticks
        return dataclasses.replace(setup, **fields)


def smoke_layouts():
    draw = depth.lhs_draw(200, 0)
    return {name: draw[int(name)] for name in SMOKE_LAYOUTS}


def _layout_seed(features):
    """The run-1 seed of a layout: its index in the seed-0 draw (the first, when the draw repeats it); 0 for any other values."""
    draw = depth.lhs_draw(200, 0)
    return draw.index(features) if features in draw else 0


_layouts = {}


def _placed(play, features):
    key = (play, json.dumps(features, sort_keys=True))
    if key not in _layouts:
        d = features["start_distance"]
        feats = depth._features(features)
        frame = maps.Frame((-d / 2, 0.0), (d / 2, 0.0), 0)
        layout = maps.layout_map(feats, _layout_seed(features), frame=frame)
        _layouts[key] = scenes.placed_scene(layout, play, d, feats)
    return _layouts[key]


def _reach_zero(build):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        types = {k: dict(v) for k, v in setup.unit_types.items()}
        for g in setup.groups:
            types.setdefault(g.unit, {"base": g.unit})["reach"] = (0, 0)
        wrapped.labels["prefight"] = build.labels.get("prefight")
        return dataclasses.replace(setup, unit_types=types)
    wrapped.labels = {}
    return wrapped


def _mean_point(groups):
    pts = [p for g in groups for p in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def _naive_side(build, role):
    """The play's scene with side 0 arranged naively: one blob per unit type at the plain mean of that type's group anchors (one per
    (type, layer) in the play-layer variant, where a type's layers differ), the play's timeline dropped, same units and counts
    (ruling 2; decisions 25 and 41). naive_defender and naive_defender_attacker_layer put every blob on the attacker's (the
    enemy's) layer; naive_defender_play_layer keeps each type on the layer the play gave it (DRAFT, Architect: a blob of
    ground types moved up to the play's layer could not fire at the attackers at all). A holder's blob whose anchor sees no clear
    line to the attackers' start moves to the nearest cell that does, else the build is refused blind_post and nothing moves
    (decision 44); labels['placement_shift'] is the largest distance moved."""
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        own = [g for g in setup.groups if g.side == 0]
        enemy = [g for g in setup.groups if g.side == 1]
        order = "guard" if any(g.order == "guard" for g in own) else "attack_move"
        members = collections.defaultdict(list)
        for g in own:
            members[(g.unit, g.layer if role == "naive_defender_play_layer" else enemy[0].layer)].append(g)
        anchors = {key: (sum(g.x for g in gs) / len(gs), sum(g.y for g in gs) / len(gs)) for key, gs in members.items()}
        shift = 0.0
        if order == "guard" and setup.terrain is not None:
            starts = [(x, y, g.layer) for g in enemy for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
            moved = {key: scenes.shifted_post(setup.terrain, key[1], a, starts) for key, a in anchors.items()}
            if all(m is not None for m in moved.values()):
                shift = max([math.hypot(moved[key][0] - a[0], moved[key][1] - a[1]) for key, a in anchors.items()], default=0.0)
                anchors = moved
        blobs = tuple(Group(side=0, unit=u, count=sum(g.count for g in gs), formation="blob", x=anchors[(u, layer)][0],
                            y=anchors[(u, layer)][1], facing_deg=own[0].facing_deg, layer=layer, order=order,
                            params={"radius": 80 + 12 * math.sqrt(sum(g.count for g in gs))}) for (u, layer), gs in members.items())
        blobs = tuple(scenes.skip_blocked(g, setup.terrain) for g in blobs)
        point = _mean_point(blobs) if order == "guard" else setup.point
        out = dataclasses.replace(setup, groups=blobs + tuple(enemy), timeline=(), point=point)
        wrapped.labels["prefight"] = scenes.preflight(out, None, naive_defender=True)
        wrapped.labels["placement_shift"] = shift
        return out
    wrapped.labels = {"placement_shift": 0.0, "prefight": None}
    return wrapped


def default_builds(play, role, features):
    """builds(play, role, features) -> BuildFn for the real engine. Roles: play, reach_zero (the null control's build),
    naive_attacker (scenes' naive blob attacking the same post), naive_defender and its two layer variants."""
    if role == "naive_attacker":
        return scenes.naive_mix(_placed("naive", features), play) if play in plays_space.PLAYS else _placed("naive", features)
    base = _placed(play, features)
    if role == "play":
        return base
    if role == "reach_zero":
        return _reach_zero(base)
    return _naive_side(base, role)


def default_control_builds():
    from scripts.skilllab import plays
    return {"mirror": plays.blob_play(16), "numbers": plays.blob_play(16), "planted": plays.damage_play(16)}


# ---- the mirror pre-check of a mix ------------------------------------------------------------------------------------------------

def _mirror_setup(units):
    """A naive mirror: the mix on both sides, one blob per type, attack-moving, one layer, no timeline, built-in types."""
    def side(s):
        return [Group(side=s, unit=t, count=n, formation="blob", x=-MIRROR_X if s == 0 else MIRROR_X, y=0.0,
                      facing_deg=0.0 if s == 0 else 180.0, layer=0, order="attack_move", goal=None,
                      params={"radius": 80 + 12 * math.sqrt(n)}) for t, n in units.items()]
    return Setup(groups=tuple(side(0) + side(1)), unit_types={}, point=(0.0, 0.0))


def _warden_stall(living):
    """P1 (the Warden pattern of FINDING-lab-d9): at the cap some side still has living units and every living unit of that side is a Warden."""
    return any(roster and set(roster) == {"Warden"} for roster in living)


def mirror_precheck(units, *, fights=MIRROR_FIGHTS, fight_fn=None, map_fn=None):
    """R1: `fights` naive mirror fights of the mix (fight i is seed i // 2, swapped when i is odd). More than WARDEN_PER_16 Wardens per
    16 is refused before any fight (FU-warden-no-stack retires the cap). A capped fight rejects the mix, except on M9 when every capped
    fight matches P1 (known_cap:FINDING-lab-d9). `rosters` maps each capped fight's index to its living roster."""
    verdict = {"mix": dict(units), "ok": True, "reason": None, "fights": 0, "caps": 0, "rosters": {}}
    if units.get("Warden", 0) * 16 > WARDEN_PER_16 * sum(units.values()):
        return {**verdict, "ok": False, "reason": "warden_cap"}
    setup = _mirror_setup(units)
    results = scan_mod.run_jobs([(setup, i // 2, i % 2 == 1) for i in range(fights)], fight_fn, map_fn)
    capped = [i for i, r in enumerate(results) if r.outcome == "cap"]
    verdict.update(fights=len(results), caps=len(capped), rosters={i: results[i].living for i in capped})
    if capped:
        m9 = next(r["units"] for r in plays_space.MIXES if r["name"] == "M9")
        known = dict(units) == m9 and all(_warden_stall(results[i].living) for i in capped)
        verdict.update(ok=known, reason=KNOWN_CAP if known else "capped")
    return verdict


def vet_mixes(rows, *, fight_fn=None, map_fn=None):
    """The enabled rows of a MIXES table through mirror_precheck; no row is edited (a person flips `enabled` after the report).
    `verdicts` maps each name to its verdict: the artifact's summary["mixes"]."""
    report = {"accepted": [], "rejected": [], "verdicts": {}}
    for row in rows:
        if not row["enabled"]:
            continue
        verdict = mirror_precheck(row["units"], fight_fn=fight_fn, map_fn=map_fn)
        report["verdicts"][row["name"]] = verdict
        if verdict["ok"]:
            report["accepted"].append(row["name"])
        else:
            report["rejected"].append({**verdict, "mix": row["name"]})
    return report


# ---- running a family -------------------------------------------------------------------------------------------------------------

def _refusal(builds_by_role):
    """(role, word) of the first build that refuses the cell at the smallest or the largest headcount, else None."""
    for role, build in builds_by_role.items():
        for heads in (ENEMY_FROM, ENEMY_TO):
            build(heads, False)
            word = getattr(build, "labels", {}).get("prefight")
            if word not in (None, "ok"):
                return role, word
    return None


def _usable_baselines(by_role, refused, family, play, layout, shifted=None):
    """(roles, top): the baseline roles whose build fits the cell, and the last headcount at which every one of them placed (decision
    26): ENEMY_TO when none ran out, None when one cannot be placed at ENEMY_FROM. A baseline refused no_reach or unroutable at the
    smallest or largest headcount, or that runs out of room, is listed with its role and left out; the play still runs. `shifted`, when
    given, gets one {family, play, layout, role, shift_wu} per baseline that runs and moved a post: shift_wu is the largest
    labels['placement_shift'] over the headcounts it runs at (decision 45 item 1, decision 47)."""
    roles, top, shifts = [], ENEMY_TO, {}
    for r in by_role:
        if r in ("play", "reach_zero"):
            continue
        bad = _refusal({r: by_role[r]})
        if bad and bad[1] != "no_fit":
            refused.append({"family": family, "play": play, "layout": layout, "role": r, "reason": bad[1]})
            continue
        build = by_role[r]
        words = {}
        for heads in range(ENEMY_FROM, ENEMY_TO + 1):
            build(heads, False)
            words[heads] = getattr(build, "labels", {}).get("prefight")
            shifts[(r, heads)] = getattr(build, "labels", {}).get("placement_shift", 0.0)
        short = [heads for heads, word in words.items() if word == "no_fit"]
        if short:
            refused.append({"family": family, "play": play, "layout": layout, "role": r, "reason": "no_fit"})
            top = None if top is None or min(short) <= ENEMY_FROM else min(top, min(short) - 1)
        roles.append(r)
    if shifted is not None and top is not None:
        for r in roles:
            wu = max(shifts[(r, heads)] for heads in range(ENEMY_FROM, top + 1))
            if wu > 0.0:
                shifted.append({"family": family, "play": play, "layout": layout, "role": r, "shift_wu": wu})
    return tuple(roles), top


def _scan_rows(rows, family, play, layout, point, baseline, build, replicates, fight_fn, map_fn, full_scan, top=ENEMY_TO):
    """Scan ENEMY_FROM..top. A scan cut short of ENEMY_TO by a baseline that ran out of room is neither a ceiling hit nor a finding."""
    applied = Applied(build, point)
    cut = top < ENEMY_TO
    result = scan_mod.scan(applied, SIZE, ENEMY_FROM, top, replicates=replicates, fight_fn=fight_fn, map_fn=map_fn,
                           full_scan=full_scan)
    for c in result.cells:
        for f in c.fights:
            rows.append(rows_mod.fight_row(f, knob=point.knob, knob_value=float(point.value), baseline=baseline,
                                           ceiling_hit=0 if cut else int(result.ceiling_hit),
                                           prefight=applied.prefight.get(c.enemy_heads, "ok"), baseline_no_fit=int(cut),
                                           blind_post=int(f.blind_cap), invalid=int(getattr(f, "invalid", False)), family=family, play=play, layout=layout,
                                           kind=point.kind, point=point_label(point), enemy_heads=c.enemy_heads))
    return result


def _control_rows(rows, family, play, layout, point, build, replicates, fight_fn, map_fn, max_ticks):
    applied = Applied(build, point, max_ticks)
    cell = scan_mod.cell(applied, SIZE, replicates, fight_fn=fight_fn, map_fn=map_fn)
    for f in cell.fights:
        rows.append(rows_mod.fight_row(f, knob=point.knob, knob_value=float(point.value), prefight=applied.prefight.get(SIZE, "ok"),
                                       baseline_no_fit=0, blind_post=int(f.blind_cap), invalid=int(getattr(f, "invalid", False)), family=family, play=play,
                                       layout=layout, kind=point.kind, point=point_label(point), enemy_heads=SIZE))
    return cell.fights


def _break_even(result):
    """The break-even a gain is read from: a ceiling hit is the top of the range, no break-even is 0."""
    return result.cells[-1].enemy_heads if result.ceiling_hit else (result.beats or 0)


def _defects(rows):
    """Caps outside the control kinds are the lab's defects to trace unless the survivors were blind to each other (decision 43: a
    finding, counted apart in blind_post_rows and making no defect cell)."""
    cell = lambda r: (r["play"], r["layout"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    live = lambda r: not r["kind"].startswith("control_")
    blind = lambda r: r["outcome"] == "cap" and r["blind_post"] == 1
    bad = [r for r in rows if live(r) and (r["outcome"] == "draw" or (r["outcome"] == "cap" and not blind(r)))]
    return {"cap_rows": sum(r["outcome"] == "cap" for r in bad), "blind_post_rows": sum(live(r) and blind(r) for r in rows),
            "draw_rows": sum(r["outcome"] == "draw" for r in rows), "cells": len({cell(r) for r in bad})}


def _probe_args(family):
    """(settings, base_settings) of the family's extreme grid point, the one with the smallest value (rev 3 plan R6); None when the point
    sets no OM_TP_* setting (arc and cone act through Setup fields, which the probe does not merge). The probe's base is that point
    with only the family's own keys reset to BASES: every key of the point, except emitting, whose point also sets the joint vision
    (a base at the default vision would differ through the vision alone), so its own keys are the two EMIT_* ones."""
    point = min(grid(family), key=lambda p: p.value)
    if not point.settings:
        return None
    own = ("OM_TP_EMIT_SIGHT_MULT", "OM_TP_EMIT_SEEN_MULT") if family == "emitting" else tuple(point.settings)
    return point.settings, {**point.settings, **{k: BASES[k] for k in own}}


def _probe_play(family, play, layout, build, probe_args, fight_fn, base_cache):
    """(record, inert): the survey of the family's extreme on the play's own build and the `probed` record of it (rev 3 plan R6). The base
    rows are kept in base_cache under (play, layout, base settings), so families that reset the same keys fight them once."""
    settings, base_settings = probe_args
    cache = base_cache.setdefault((play, layout, tuple(sorted(base_settings.items()))), {})
    got = probe_mod.survey(build, settings, fight_fn=fight_fn, base_settings=base_settings, base_cache=cache)
    first = next(((h, seed) for (h, seed), v in got.items() if v["differed"]), None)
    if first is None:
        line = "inert at every point"
    else:
        silent = [k for k, v in got.items() if k[0] <= first[0] and not v["differed"]]
        line = "bites from %d heads seed %d" % first + ("; silent at %s" % silent if silent else "")
    record = {"family": family, "play": play, "layout": layout,
              "first_differing": None if first is None else {"heads": first[0], "seed": first[1]}, "line": line,
              "base_cached": all(v["base_cached"] for v in got.values())}
    return record, first is None


def run_family(family, out_dir, *, builds=None, layouts=None, plays=None, fight_fn=None, map_fn=None, caps=None,
               replicates=REPLICATES, full_scan=False, probe=False, base_cache=None):
    builds = builds or default_builds
    layouts = smoke_layouts() if layouts is None else layouts
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if caps is None:
        caps = detect() if family in ("arc", "cone") else Capabilities(True, True)
    entry = {"family": family, "skipped": skip_reason(family, caps), "csv": None, "rows": 0, "refined": [], "refined_vs": {},
             "refused": [], "baseline_no_fit": [], "controls": {}, "shifted_posts": []}
    if entry["skipped"]:
        return entry
    rows, refined, refined_vs, verdicts = [], set(), {}, {}
    family_controls = controls(family)
    run_plays = plays if plays is not None else PLAYS_BY_FAMILY[family]
    scan_args = (replicates, fight_fn, map_fn, full_scan)
    probe_args = _probe_args(family) if probe else None
    base_cache = {} if base_cache is None else base_cache
    if probe_args:
        entry[FROZEN_NAMES[5]] = []

    def run_control(name, ctl, play, layout, features):
        role = "reach_zero" if ctl.reach else "play"
        build = builds(play, role, features)
        if _refusal({role: build}):
            return
        per_point = [_control_rows(rows, family, play, layout, p, build, replicates, fight_fn, map_fn, ctl.max_ticks)
                     for p in ctl.points]
        verdicts.setdefault(name, []).append(bool(ctl.check(per_point)))

    for layout, features in layouts.items():
        for play in run_plays:
            play_build, roles_wanted = _play_roles(builds, play, features)
            by_role = {"play": play_build, "reach_zero": builds(play, "reach_zero", features),
                       **{r: builds(play, r, features) for r in roles_wanted}}
            bad = _refusal({r: by_role[r] for r in ("play", "reach_zero")})
            if bad:
                entry["refused"].append({"family": family, "play": play, "layout": layout, "role": bad[0], "reason": bad[1]})
                continue
            if probe_args:
                record, inert = _probe_play(family, play, layout, by_role["play"], probe_args, fight_fn, base_cache)
                entry[FROZEN_NAMES[5]].append(record)
                if inert:
                    entry["refused"].append({"family": family, "play": play, "layout": layout, "role": "play", "reason": FROZEN_NAMES[0],
                                             FROZEN_NAMES[3]: probe_mod.coarse_heads(), FROZEN_NAMES[4]: list(probe_mod.SEEDS)})
                    continue
            roles, top = _usable_baselines(by_role, entry["refused"], family, play, layout, entry["shifted_posts"])
            if top is None or top < ENEMY_TO:
                entry["baseline_no_fit"].append({"family": family, "play": play, "layout": layout, "last_headcount": top})
            if top is None:
                continue
            for r in roles:
                refined_vs.setdefault(r, set())
            results = {}

            def fight_point(point):
                got = {"play": _scan_rows(rows, family, play, layout, point, "none", by_role["play"], *scan_args, top)}
                for r in roles:
                    got[r] = _scan_rows(rows, family, play, layout, point, r, by_role[r], *scan_args, top)
                return got

            if family in REFINABLE:
                for point in grid(family):
                    results[point.value] = fight_point(point)
                coarse = sorted(results)

                def ahead(role, v):
                    if v not in results:
                        results[v] = fight_point(_refined_point(family, v))
                    return _break_even(results[v]["play"]) - _break_even(results[v][role]) > 0

                for r in roles:
                    added = [v for _round, v in refine(coarse, lambda v, r=r: ahead(r, v))]
                    refined_vs[r].update(added)
                    refined.update(added)
            else:
                for point in grid(family):
                    fight_point(point)
            for name, ctl in family_controls.items():
                if ctl.play is None:
                    run_control(name, ctl, play, layout, features)
        for name, ctl in family_controls.items():
            if ctl.play is not None:
                run_control(name, ctl, ctl.play, layout, features)
    entry["refined"] = sorted(refined)
    entry["refined_vs"] = {r: sorted(v) for r, v in refined_vs.items()}
    entry["controls"] = {name: {"ok": all(verdicts[name]) if name in verdicts else None} for name in family_controls}
    if "positive" in family_controls:
        entry["controls"]["positive"]["play"] = family_controls["positive"].play
    entry["defects"] = _defects(rows)
    if family == "emitting":
        entry["saturated_at_vision"] = [BASES["OM_TP_VISION_UP_1"]]
    entry["csv"], entry["rows"] = "sweep_%s.csv" % family, len(rows)
    rows_mod.write_rows(rows, out / entry["csv"])
    return entry


def _with_map(workers, kw, work):
    """Run work(**kw) with the fights going through a lean process pool when workers > 1 and the caller gave no fight function."""
    if workers > 1 and kw.get("map_fn") is None and kw.get("fight_fn") is None:
        with pool.FightPool(workers, lean=True) as p:
            return work(**dict(kw, map_fn=p.map))
    return work(**kw)


def run(families, out_dir, workers=1, full_scan=False, **kw):
    if kw.get("probe") is False:
        raise ValueError("a batch needs the inert-knob probe on (probe=True): a knob that cannot bite on a play must be refused, not swept")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    base_cache = {}

    def work(**more):
        summary = {"order": list(families), "replicates": kw.get("replicates", REPLICATES), "families": {},
                   "unavailable": {FROZEN_NAMES[1]: skip_reason(FROZEN_NAMES[1], None)}}
        if kw.get("probe"):
            summary["probe"] = "on"
            summary[FROZEN_NAMES[5]] = []
        for name in families:
            summary["families"][name] = run_family(name, out, full_scan=full_scan, base_cache=base_cache, **more)
            if kw.get("probe"):
                summary[FROZEN_NAMES[5]].extend(summary["families"][name].get(FROZEN_NAMES[5]) or ())
        (out / "sweep_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        return summary

    return _with_map(workers, kw, work)


def _default_parity():
    """firing.parity on a dedicated open-ground 16 v 16 mirror world (the lab's own blob play, seed 0), the units placed and ordered
    exactly as fight() does, checked once at tick 0 with the arc off (360 degrees; decision 41 item 1; decision 44 item 9)."""
    from scripts.skilllab import fight as fight_mod, firing
    from scripts.skilllab.engine import Engine
    setup = default_control_builds()["mirror"](16, False)
    engine = Engine()
    w = engine.new_world(0)
    try:
        if not setup.abilities:
            engine.disable_abilities(w)
        types = fight_mod._register_types(engine, w, setup)
        rng, ids_by_group, ranges = random.Random(0), {}, {}
        for side in (0, 1):
            fight_mod._spawn_side(engine, w, setup, side, types, rng, ids_by_group, ranges)
        fight_mod._issue_orders(engine, w, setup, ids_by_group)
        sides = tuple([u for gi, g in enumerate(setup.groups) if g.side == side for u in ids_by_group[gi]] for side in (0, 1))
        return firing.parity(engine, w, sides[0], sides[1], 360.0)
    finally:
        engine.free_world(w)


def run_smoke(out_dir, workers=12, *, builds=None, control_builds=None, layouts=None, fight_fn=None, map_fn=None,
              full_scan=False, replicates=REPLICATES, caps=None, parity_fn=None):
    """Vision 0.5 alone on the three named layouts for both vision plays and their baselines, plus the three lab controls; the
    rows are written to smoke.csv and hashed in smoke_summary.json (the same bytes at any worker count). `parity` in the summary is
    "skipped: E0 absent" when the library has no firing arc (caps.arc False), else parity_fn()'s value."""
    builds = builds or default_builds
    caps = detect() if caps is None else caps
    layouts = smoke_layouts() if layouts is None else layouts
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def work(**more):
        rows, refused, words, cuts, shifted = [], [], collections.Counter(), [], []
        point = next(p for p in grid("vision") if p.value == 0.5)
        control_set = control_builds or default_control_builds()
        for layout, features in layouts.items():
            for play in SMOKE_PLAYS["vision"]:
                play_build, roles_wanted = _play_roles(builds, play, features)
                by_role = {"play": play_build, **{r: builds(play, r, features) for r in roles_wanted}}
                bad = _refusal({"play": by_role["play"]})
                if bad:
                    refused.append({"play": play, "layout": layout, "role": bad[0], "reason": bad[1]})
                    words[bad[1]] += 1
                    continue
                listed = []
                moved = []
                roles, top = _usable_baselines(by_role, listed, "vision", play, layout, moved)
                shifted += [{k: v for k, v in m.items() if k != "family"} for m in moved]
                refused += [{k: v for k, v in r.items() if k != "family"} for r in listed]
                words.update(r["reason"] for r in listed)
                if top is None or top < ENEMY_TO:
                    cuts.append({"play": play, "layout": layout, "last_headcount": top})
                if top is None:
                    continue
                words["ok"] += 1
                for r in ("play",) + roles:
                    _scan_rows(rows, "vision", play, layout, point, "none" if r == "play" else r, by_role[r], replicates,
                               more.get("fight_fn"), more.get("map_fn"), full_scan, top)
        for name, heads in SMOKE_CONTROLS:
            applied = Applied(control_set[name], dataclasses.replace(point, settings={}, kind="control_smoke"))
            for f in scan_mod.cell(applied, heads, replicates, fight_fn=more.get("fight_fn"), map_fn=more.get("map_fn")).fights:
                rows.append(rows_mod.fight_row(f, baseline_no_fit=0, blind_post=int(f.blind_cap), family="controls", play=name,
                                               layout="none", kind="control_smoke", point="-", enemy_heads=heads))
            words["ok"] += 1
        rows_mod.write_rows(rows, out / "smoke.csv")
        summary = {"rows_sha256": hashlib.sha256((out / "smoke.csv").read_bytes()).hexdigest(), "rows": len(rows),
                   "outcomes": dict(sorted(collections.Counter(r["outcome"] for r in rows).items())),
                   "prefight": dict(sorted(words.items())), "refused": refused, "baseline_no_fit": cuts, "shifted_posts": shifted,
                   "defects": _defects(rows), "parity": (parity_fn or _default_parity)() if caps.arc else "skipped: E0 absent"}
        (out / "smoke_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        return summary

    return _with_map(workers, {"fight_fn": fight_fn, "map_fn": map_fn}, work)
