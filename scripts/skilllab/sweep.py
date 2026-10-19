"""REFERENCE implementation used only to prove the L4 tests can go green (scratch branch, never committed to the tests branch)."""
import collections
import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from scripts.skilllab import depth, pool, rows as rows_mod, scan as scan_mod

FAMILY_ORDER = ("vision", "range_up", "damage_up", "emitting", "arc", "cone", "sign_flip")
SIZE, ENEMY_FROM, ENEMY_TO, REPLICATES = 16, 8, 48, 3
CONTROL_MAX_TICKS = 600
LAYER2_RATIO = 0.4
BASES = {
    "OM_TP_VISION_UP_1": 0.5, "OM_TP_VISION_DOWN_1": 0.5, "OM_TP_VISION_UP_2": 0.2, "OM_TP_VISION_DOWN_2": 0.2,
    "OM_TP_RANGE_UP_1": 1.0, "OM_TP_RANGE_UP_2": 1.0, "OM_TP_RANGE_DOWN_1": 1.0, "OM_TP_RANGE_DOWN_2": 1.0,
    "OM_TP_DAMAGE_UP_1": 1.0, "OM_TP_DAMAGE_UP_2": 1.0,
    "OM_TP_EMIT_SIGHT_MULT": 2.0, "OM_TP_EMIT_SEEN_MULT": 3.0,
    "OM_TP_FIRING_ARC_DEG": 360.0, "cone_range": 300.0, "cone_half_angle": 45.0,
}
PLAYS_BY_FAMILY = {
    "vision": ("s3_layer_above", "s3_types_by_reach"), "range_up": ("s3_layer_above", "s3_types_by_reach"),
    "damage_up": ("s3_layer_above", "s3_types_by_reach"), "emitting": ("s3_dark_striker",),
    "arc": ("s2_concave", "s2_mass_one_end"), "cone": ("s2_concave", "s2_mass_one_end"),
    "sign_flip": ("s3_layer_above", "s3_types_by_reach"),
}
SMOKE_LAYOUTS = ("81", "78", "192")
SMOKE_CONTROLS = (("mirror", 16), ("numbers", 8), ("planted", 16))
Capabilities = collections.namedtuple("Capabilities", "arc cone")
_REFINABLE = ("vision", "range_up", "damage_up", "arc")


@dataclass(frozen=True)
class Point:
    family: str
    knob: str
    value: float
    settings: dict
    setup: dict
    kind: str
    label: str


@dataclass(frozen=True)
class Control:
    name: str
    points: list
    reach: Optional[tuple]
    check: Any


def in_band(value, base):
    return 0.25 * base <= value <= 4.0 * base


def _vision(v, kind="grid"):
    return Point("vision", "OM_TP_VISION_UP_1", v, {"OM_TP_VISION_UP_1": v, "OM_TP_VISION_DOWN_1": v,
                                                    "OM_TP_VISION_UP_2": LAYER2_RATIO * v, "OM_TP_VISION_DOWN_2": LAYER2_RATIO * v},
                 {}, kind, "vision %s" % v)


def _range(v, kind="grid", family="range_up"):
    return Point(family, "OM_TP_RANGE_UP_1", v, {"OM_TP_RANGE_UP_1": v, "OM_TP_RANGE_UP_2": v, "OM_TP_RANGE_DOWN_1": 1.0,
                                                 "OM_TP_RANGE_DOWN_2": 1.0}, {}, kind, "range-up %s" % v)


def _damage(v, kind="grid", family="damage_up"):
    return Point(family, "OM_TP_DAMAGE_UP_1", v, {"OM_TP_DAMAGE_UP_1": v, "OM_TP_DAMAGE_UP_2": v}, {}, kind, "damage-up %s" % v)


def _emit(sight, seen, vision):
    s = _vision(vision).settings
    return Point("emitting", "OM_TP_EMIT_SIGHT_MULT", sight, {**s, "OM_TP_EMIT_SIGHT_MULT": sight, "OM_TP_EMIT_SEEN_MULT": seen},
                 {}, "grid", "emit %s/%s vision %s" % (sight, seen, vision))


def _arc(v, kind="grid"):
    return Point("arc", "OM_TP_FIRING_ARC_DEG", v, {}, {"firing_arc_deg": float(v)}, kind, "arc %s" % v)


def _cone(r, h):
    return Point("cone", "cone", r, {}, {"cone": {"Vanguard": (r, h, 1.0)}}, "grid", "cone %s/%s" % (r, h))


def grid(family):
    if family == "vision":
        return [_vision(v) for v in (0.125, 0.25, 0.5, 1.0)]
    if family == "range_up":
        return [_range(v) for v in (1.0, 0.75, 0.5, 0.25)]
    if family == "damage_up":
        return [_damage(v) for v in (1.0, 0.75, 0.5, 0.25)]
    if family == "emitting":
        return [_emit(s, t, v) for v in (0.125, 0.25) for (s, t) in ((1.0, 1.5), (2.0, 3.0), (4.0, 6.0))]
    if family == "arc":
        return [_arc(v) for v in (360, 270, 180, 120, 90)]
    if family == "cone":
        return [_cone(r, h) for r in (150, 300, 600) for h in (22.5, 45, 90)]
    if family == "sign_flip":
        return [dataclasses.replace(_range(2.0, "sign_flip", "sign_flip"), label="sign-flip control: range-up 2.0"),
                dataclasses.replace(_damage(2.0, "sign_flip", "sign_flip"), label="sign-flip control: damage-up 2.0")]
    raise ValueError("unknown family %r" % (family,))


def _point_at(family, v):
    return {"vision": _vision, "range_up": _range, "damage_up": _damage, "arc": _arc}[family](v, "refined")


def _identical(results_by_point):
    first = [rows_mod.fight_row(r) for r in results_by_point[0]]
    return all([rows_mod.fight_row(r) for r in rs] == first for rs in results_by_point[1:])


def _vision_zero_ok(results_by_point):
    return all(r.survivors == r.heads == (16, 16) and tuple(r.firing_unit_seconds) == (0.0, 0.0)
               for rs in results_by_point for r in rs)


def _damage_ok(results_by_point):
    base, half = results_by_point
    return (len(base) == len(half) and all(a.firing[0][1:] == b.firing[0][1:] for a, b in zip(base, half))
            and any(a.margin != b.margin for a, b in zip(base, half)))


def controls(family):
    out = {}
    if family == "sign_flip":
        return out
    out["null"] = Control("null", [dataclasses.replace(p, kind="control_null") for p in grid(family)], (0, 0), _identical)
    if family == "vision":
        zero = dataclasses.replace(_vision(0.0), kind="control_positive", label="vision 0 control")
        out["positive"] = Control("positive", [zero], None, _vision_zero_ok)
    if family == "damage_up":
        out["positive"] = Control("positive", [dataclasses.replace(_damage(v), kind="control_positive") for v in (1.0, 0.5)], None, _damage_ok)
    return out


def refine(values, differs, max_rounds=2):
    cache = {}

    def sign(v):
        if v not in cache:
            cache[v] = bool(differs(v))
        return cache[v]

    pts = sorted(values)
    brackets = [(a, b) for a, b in zip(pts, pts[1:]) if sign(a) != sign(b)]
    added = []
    for rnd in range(1, max_rounds + 1):
        nxt = []
        for a, b in brackets:
            m = (a + b) / 2
            added.append((rnd, m))
            nxt.append((a, m) if sign(m) != sign(a) else (m, b))
        brackets = nxt
    return added


def detect(engine=None):
    if engine is None:
        from scripts.skilllab import engine as engine_module
        engine = engine_module.Engine()
    try:
        engine.param_id("OM_TP_FIRING_ARC_DEG")
        arc = True
    except ValueError:
        arc = False
    w = engine.new_world(0)
    try:
        engine.set_cone(w, engine.type_id("Vanguard"), 0.0, 45.0, 1.0)
        cone = True
    except (ValueError, AttributeError):
        cone = False
    finally:
        engine.free_world(w)
    return Capabilities(arc=arc, cone=cone)


def skip_reason(family, caps):
    if family == "arc" and not caps.arc:
        return "the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)"
    if family == "cone" and not caps.cone:
        return "the library has no usable om_roster_set_cone (LAB-REV2-E2 not built)"
    return None


def baseline_roles(play):
    if play.startswith("s3_"):
        return ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer")
    return ("naive_attacker", "naive_defender")


def default_builds(play, role, layout):
    raise NotImplementedError("reference only")


def _apply(build, point, control=False):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        setup = dataclasses.replace(setup, settings={**setup.settings, **point.settings}, states=True, **point.setup)
        return dataclasses.replace(setup, max_ticks=CONTROL_MAX_TICKS) if control else setup
    return wrapped


def _refusal(builds_by_role):
    for role, b in builds_by_role.items():
        for h in (ENEMY_FROM, ENEMY_TO):
            b(h, False)
            word = b.labels.get("prefight") if hasattr(b, "labels") else None
            if word not in (None, "ok"):
                return role, word
    return None


def _scan_rows(rows, family, play, layout, point, baseline, build, replicates, fight_fn, map_fn):
    res = scan_mod.scan(_apply(build, point), SIZE, ENEMY_FROM, ENEMY_TO, replicates=replicates, fight_fn=fight_fn, map_fn=map_fn)
    for c in res.cells:
        for f in c.fights:
            rows.append(rows_mod.fight_row(f, family=family, play=play, layout=layout, kind=point.kind, enemy_heads=c.enemy_heads,
                                           knob=point.knob, knob_value=float(point.value), baseline=baseline,
                                           ceiling_hit=int(res.ceiling_hit)))
    return res


def _gain(play_res, base_res):
    return (play_res.beats or 0) - (base_res.beats or 0)


def run_family(family, out_dir, *, builds=None, layouts=None, plays=None, fight_fn=None, map_fn=None, caps=None, replicates=REPLICATES):
    builds = builds or default_builds
    layouts = layouts if layouts is not None else smoke_layouts()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    caps = caps or detect(None)
    entry = {"family": family, "skipped": skip_reason(family, caps), "csv": None, "rows": 0, "refined": [], "refused": [], "controls": {}}
    if entry["skipped"]:
        return entry
    rows, oks, refined = [], {}, set()
    for layout, features in layouts.items():
        for play in (plays or PLAYS_BY_FAMILY[family]):
            roles = ("play",) + baseline_roles(play)
            by_role = {r: builds(play, r, features) for r in roles + ("reach_zero",)}
            bad = _refusal(by_role)
            if bad:
                entry["refused"].append({"family": family, "play": play, "layout": layout, "role": bad[0], "reason": bad[1]})
                continue
            results = {}

            def point_rows(point):
                got = {}
                for role in roles:
                    got[role] = _scan_rows(rows, family, play, layout, point, "none" if role == "play" else role, by_role[role],
                                           replicates, fight_fn, map_fn)
                results[point.value] = got
                return _gain(got["play"], got["naive_attacker"]) > 0

            for p in grid(family):
                point_rows(p)
            if family in _REFINABLE:
                signs = {v: _gain(r["play"], r["naive_attacker"]) > 0 for v, r in results.items()}
                added = refine(sorted(signs), lambda v: signs[v] if v in signs else point_rows(_point_at(family, v)))
                # refine() evaluates new midpoints through `differs`, which fought them above
                refined |= {v for _r, v in added}
            for name, ctl in controls(family).items():
                per_point = []
                for p in ctl.points:
                    role = "reach_zero" if ctl.reach else "play"
                    cell = scan_mod.cell(_apply(by_role[role], p, control=True), SIZE, replicates, fight_fn=fight_fn, map_fn=map_fn)
                    per_point.append(cell.fights)
                    for f in cell.fights:
                        rows.append(rows_mod.fight_row(f, family=family, play=play, layout=layout, kind=p.kind, enemy_heads=SIZE,
                                                       knob=p.knob, knob_value=float(p.value), baseline="none", ceiling_hit=0))
                oks[name] = oks.get(name, True) and bool(ctl.check(per_point))
    entry["refined"] = sorted(refined)
    entry["controls"] = {n: {"ok": ok} for n, ok in oks.items()}
    if family == "emitting":
        entry["saturated_at_vision"] = [0.5]
    entry["csv"], entry["rows"] = "sweep_%s.csv" % family, len(rows)
    rows_mod.write_rows(rows, out / entry["csv"])
    return entry


def run(families, out_dir, workers=1, **kw):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def go(**more):
        summary = {"order": list(families), "replicates": REPLICATES, "families": {}}
        for name in families:
            summary["families"][name] = run_family(name, out, **{**kw, **more})
        (out / "sweep_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        return summary

    if workers > 1 and kw.get("map_fn") is None and kw.get("fight_fn") is None:
        with pool.FightPool(workers, lean=True) as p:
            return go(map_fn=p.map)
    return go()


def smoke_layouts():
    draw = depth.lhs_draw(200, 0)
    return {k: draw[int(k)] for k in SMOKE_LAYOUTS}


def run_smoke(out_dir, workers=12, *, builds=None, control_builds=None, layouts=None, fight_fn=None, map_fn=None):
    builds = builds or default_builds
    layouts = layouts if layouts is not None else smoke_layouts()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def go(map_fn):
        rows, refused, ok = [], [], 0
        point = [p for p in grid("vision") if p.value == 0.5][0]
        point = dataclasses.replace(point, kind="smoke")
        for layout, features in layouts.items():
            for play in PLAYS_BY_FAMILY["vision"]:
                roles = ("play",) + baseline_roles(play)
                by_role = {r: builds(play, r, features) for r in roles}
                bad = _refusal(by_role)
                if bad:
                    refused.append({"play": play, "layout": layout, "role": bad[0], "reason": bad[1]})
                    continue
                ok += 1
                for role in roles:
                    _scan_rows(rows, "vision", play, layout, point, "none" if role == "play" else role, by_role[role],
                               REPLICATES, fight_fn, map_fn)
        for name, heads in SMOKE_CONTROLS:
            ok += 1
            cell = scan_mod.cell(_apply((control_builds or {})[name], dataclasses.replace(point, settings={}, kind="smoke_control")),
                                 heads, REPLICATES, fight_fn=fight_fn, map_fn=map_fn)
            for f in cell.fights:
                rows.append(rows_mod.fight_row(f, family="controls", play=name, layout="none", kind="smoke_control", enemy_heads=heads))
        rows_mod.write_rows(rows, out / "smoke.csv")
        outcomes = collections.Counter(r["outcome"] for r in rows)
        summary = {"rows_sha256": hashlib.sha256((out / "smoke.csv").read_bytes()).hexdigest(), "rows": len(rows),
                   "outcomes": dict(sorted(outcomes.items())), "prefight": {"ok": ok}, "refused": refused}
        (out / "smoke_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        return summary

    if workers > 1 and map_fn is None and fight_fn is None:
        with pool.FightPool(workers, lean=True) as p:
            return go(p.map)
    return go(map_fn)
