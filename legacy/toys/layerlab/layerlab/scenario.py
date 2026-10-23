"""Scenario loading, dotted-path edits, diffing, and conversion to the C struct (SPEC.md section 8)."""
import copy
import math
import re
import tomllib
from pathlib import Path

from . import ffi, formations, terrain

_TOP_KEYS = {"run", "rules", "type_defaults", "types", "terrain", "groups"}
_RUN_KEYS = ("max_ticks", "stalemate_ticks")
_RULE_ARRAYS = {
    "vis_factor": (9,), "vantage_vis_factor": (9,), "range_mult": (9,), "dmg_mult": (9,),
    "aoe_layer_mult": (9,), "category_mult": (3, 3), "emit_see_mult": (2,), "emit_seen_mult": (2,),
}
# Keys added in ABI 3 that older scenario files do not carry: absent means the legacy behaviour (SPEC 15).
_RULE_DEFAULTS = {
    "emit_see_mult": [1.0, 1.0], "emit_seen_mult": [1.0, 1.0], "emit_on": 0,
    "ping_reach": 1200.0, "ping_radius": 250.0, "ping_s": 0.5, "ping_cooldown_s": 6.0,
}
_CATEGORY = {"strike": ffi.CAT_STRIKE, "line": ffi.CAT_LINE, "siege": ffi.CAT_SIEGE}
_MOVEMENT = {"fly": ffi.MOVE_FLY, "walk": ffi.MOVE_WALK}
_ORDER = {"hold": ffi.ORDER_HOLD, "move": ffi.ORDER_MOVE, "attack_move": ffi.ORDER_ATTACK_MOVE}
_POLICY = {"nearest": ffi.TARGET_NEAREST, "lowest_hp": ffi.TARGET_LOWEST_HP,
           "highest_cost": ffi.TARGET_HIGHEST_COST}
_SIDE = {"A": 0, "B": 1}
_GROUP_KEYS = {"side", "type", "count", "formation", "x", "y", "facing", "layer", "order", "goal", "goals",
               "pre_revealed", "transfer_layer", "transfer_tick", "pulse_tick", "target_policy", "spacing",
               "cols", "center", "R", "arc_deg", "screen_r",
               "emit", "emit_switch_tick", "emit_switch_to", "ping_tick", "ping_layer", "ping_x", "ping_y"}
_FORMATION_KEYS = ("cols", "center", "R", "arc_deg", "screen_r")
_GROUP_OPTIONAL = ("spacing", "pre_revealed", "transfer_layer", "transfer_tick", "pulse_tick",
                   "target_policy", "emit", "emit_switch_tick", "emit_switch_to", "ping_tick", "ping_layer",
                   "ping_x", "ping_y") + _FORMATION_KEYS
_GROUP_REQUIRED = ("side", "type", "count", "x", "y", "layer")
_COST_DIVISOR = 31.25


def _deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load(path):
    path = Path(path)
    with open(path, "rb") as fh:
        doc = tomllib.load(fh)
    parent = doc.pop("extends", None)
    if parent is None:
        return doc
    return _deep_merge(load(path.parent / parent), doc)


_TOKEN = re.compile(r"^([^\[\]]+)((?:\[\d+\])*)$")


def _tokens(path):
    toks = []
    for part in path.split("."):
        m = _TOKEN.match(part)
        if not m:
            raise KeyError("bad path component %r in %r" % (part, path))
        toks.append(m.group(1))
        toks.extend(int(i) for i in re.findall(r"\[(\d+)\]", m.group(2)))
    return toks


def _optional_key(toks, depth, scn):
    """True if toks[depth] may be created: the last key of an optional schema key (SPEC.md section 8)."""
    if depth != len(toks) - 1 or not isinstance(toks[depth], str):
        return False
    if depth == 2 and toks[0] == "types":
        return toks[2] in ("cost", "reach") and toks[1] in scn.get("types", {})
    if depth == 2 and toks[0] == "groups":
        return toks[2] in _GROUP_OPTIONAL
    if depth == 1 and toks[0] == "rules":
        return toks[1] in _RULE_DEFAULTS
    if depth == 1 and toks[0] == "terrain":
        return toks[1] in terrain.PRESET_KEYS.get(scn.get("terrain", {}).get("preset", "flat"), ())
    return False


def set_path(scn, path, value):
    out = copy.deepcopy(scn)
    toks = _tokens(path)
    node = out
    for depth, tok in enumerate(toks):
        last = depth == len(toks) - 1
        if isinstance(tok, int):
            if not isinstance(node, list) or tok >= len(node):
                raise KeyError("path %r: no index [%d]" % (path, tok))
        elif not isinstance(node, dict) or (tok not in node and not (last and _optional_key(toks, depth, scn))):
            raise KeyError("path %r: no key %r" % (path, tok))
        if last:
            node[tok] = value
        else:
            node = node[tok]
    return out


def _leaves(node, prefix, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            _leaves(v, prefix + "." + k if prefix else k, acc)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _leaves(v, "%s[%d]" % (prefix, i), acc)
    else:
        acc[prefix] = node


def scenario_diff(a, b):
    la, lb = {}, {}
    _leaves(a, "", la)
    _leaves(b, "", lb)
    out = {}
    for p in list(la) + [p for p in lb if p not in la]:
        va, vb = la.get(p), lb.get(p)
        if p not in la or p not in lb or va != vb:
            out[p] = (va, vb)
    return out


def _check_keys(where, keys, allowed):
    bad = sorted(set(keys) - set(allowed))
    if bad:
        raise ValueError("%s: unknown keys %s" % (where, bad))


def _enum(where, table, value):
    if value not in table:
        raise ValueError("%s: %r is not one of %s" % (where, value, sorted(table)))
    return table[value]


def _fill_rules(rules_c, scn):
    rules = scn.get("rules", {})
    run_d = scn.get("run", {})
    _check_keys("[run]", run_d, _RUN_KEYS)
    scalar_fields = []
    for name, ctype in ffi.ll_rules._fields_:
        if name.startswith("pad") or name in _RULE_ARRAYS or name in _RUN_KEYS:
            continue
        scalar_fields.append((name, ctype))
    _check_keys("[rules]", rules, [n for n, _ in scalar_fields] + list(_RULE_ARRAYS))
    for name, ctype in scalar_fields:
        if name not in rules:
            if name not in _RULE_DEFAULTS:
                raise ValueError("[rules]: missing %r" % name)
            rules = {**rules, name: _RULE_DEFAULTS[name]}
        setattr(rules_c, name, int(rules[name]) if ctype is ffi.i32 else float(rules[name]))
    for name, shape in _RULE_ARRAYS.items():
        if name not in rules and name not in _RULE_DEFAULTS:
            raise ValueError("[rules]: missing %r" % name)
        val = rules[name] if name in rules else _RULE_DEFAULTS[name]
        if len(shape) == 1:
            if len(val) != shape[0]:
                raise ValueError("[rules] %s needs %d entries, got %d" % (name, shape[0], len(val)))
            for i, v in enumerate(val):
                getattr(rules_c, name)[i] = float(v)
        else:
            if len(val) != shape[0] or any(len(r) != shape[1] for r in val):
                raise ValueError("[rules] %s needs a %dx%d table" % (name, shape[0], shape[1]))
            for i, row in enumerate(val):
                for j, v in enumerate(row):
                    getattr(rules_c, name)[i][j] = float(v)
    for k in _RUN_KEYS:
        if k not in run_d:
            raise ValueError("[run]: missing %r" % k)
        setattr(rules_c, k, int(run_d[k]))


def _fill_type(tc, name, tdict):
    fields = {n: t for n, t in ffi.ll_unit_type._fields_ if not n.endswith("_")}
    _check_keys("[types.%s]" % name, tdict, fields)
    # reach by unit type (ABI 3): optional; a list of 9 multipliers by signed offset -4..+4 (index 4 is the own
    # layer) or a dict {offset: multiplier} (missing offsets 0); absent means the legacy behaviour (reach_on 0).
    reach = tdict.get("reach")
    tc.reach_on = 0
    for i in range(9):
        tc.reach[i] = 1.0
    if reach is not None:
        if isinstance(reach, dict):
            vals = [0.0] * 9
            for off, m in reach.items():
                if not -4 <= int(off) <= 4:
                    raise ValueError("[types.%s] reach offset %r outside -4..4" % (name, off))
                vals[int(off) + 4] = float(m)
        else:
            if len(reach) != 9:
                raise ValueError("[types.%s] reach needs 9 entries (offsets -4..+4)" % name)
            vals = [float(m) for m in reach]
        for i, v in enumerate(vals):
            tc.reach[i] = v
        tc.reach_on = 1
    for fname, ctype in fields.items():
        if fname in ("cost", "reach", "reach_on"):
            continue
        if fname not in tdict:
            raise ValueError("[types.%s]: missing %r" % (name, fname))
        v = tdict[fname]
        if fname == "category":
            v = _enum("[types.%s] category" % name, _CATEGORY, v)
        elif fname == "movement_kind":
            v = _enum("[types.%s] movement_kind" % name, _MOVEMENT, v)
        setattr(tc, fname, int(v) if ctype is ffi.i32 else float(v))
    if "cost" in tdict:
        tc.cost = float(tdict["cost"])
    else:
        tc.cost = tc.hp * tc.dmg / tc.interval_s / _COST_DIVISOR


def _check_spawn(terr, jitter, where, x, y, layer, walker):
    """Every cell the unit can be jittered into must be open on its layer (and land for a walker)."""
    cell, bit = terr.cell, 1 << (layer - 1)
    c0, r0 = math.floor((x - jitter) / cell), math.floor((y - jitter) / cell)
    c1 = math.ceil((x + jitter) / cell) - 1 if jitter > 0 else c0
    r1 = math.ceil((y + jitter) / cell) - 1 if jitter > 0 else r0
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            ok = 0 <= c < terr.w_cells and 0 <= r < terr.h_cells
            if ok:
                i = r * terr.w_cells + c
                ok = terr.open[i] & bit and (not walker or terr.land[i] & bit)
            if not ok:
                raise ValueError("%s at (%g, %g) layer %d: cell (%d, %d) is not %s on that layer"
                                 % (where, x, y, layer, c, r, "land" if walker else "open"))


def to_c(scn):
    _check_keys("scenario", scn, _TOP_KEYS)
    sc = ffi.ll_scenario()
    _fill_rules(sc.rules, scn)

    types = scn.get("types", {})
    if len(types) > ffi.MAX_TYPES:
        raise ValueError("%d types exceed LL_MAX_TYPES %d" % (len(types), ffi.MAX_TYPES))
    defaults = scn.get("type_defaults", {})
    index = {}
    for i, (name, tdict) in enumerate(types.items()):
        _fill_type(sc.types[i], name, {**defaults, **tdict})
        index[name] = i
    sc.n_types = len(types)

    terrain.build(scn["terrain"], sc.terrain)

    n = 0
    for gi, g in enumerate(scn.get("groups", [])):
        where = "groups[%d]" % gi
        _check_keys(where, g, _GROUP_KEYS)
        for k in _GROUP_REQUIRED:
            if k not in g:
                raise ValueError("%s: missing %r" % (where, k))
        if g["type"] not in index:
            raise ValueError("%s: unknown type %r (known: %s)" % (where, g["type"], list(index)))
        count = int(g["count"])
        if n + count > ffi.MAX_UNITS:
            raise ValueError("%s: %d spawns exceed LL_MAX_UNITS %d" % (where, n + count, ffi.MAX_UNITS))
        side = _enum(where + " side", _SIDE, g["side"])
        order = _enum(where + " order", _ORDER, g.get("order", "hold"))
        policy = _enum(where + " target_policy", _POLICY, g.get("target_policy", "nearest"))
        layer = int(g["layer"])
        if not 1 <= layer <= ffi.LAYERS:
            raise ValueError("%s: layer %d outside 1..%d" % (where, layer, ffi.LAYERS))
        ti = index[g["type"]]
        spacing = float(g["spacing"]) if "spacing" in g else 2.5 * sc.types[ti].body_radius
        if "goal" in g and "goals" in g:
            raise ValueError("%s: 'goal' and 'goals' together" % where)
        goals = g.get("goals")
        if goals is not None and len(goals) != count:
            raise ValueError("%s: goals has %d entries for %d units" % (where, len(goals), count))
        gx, gy = g.get("goal", [g["x"], g["y"]])
        params = {k: g[k] for k in _FORMATION_KEYS if k in g}
        places = formations.place(g.get("formation", "line"), count, float(g["x"]), float(g["y"]),
                                  float(g.get("facing", 0.0)), spacing, **params)
        walker = sc.types[ti].movement_kind == ffi.MOVE_WALK
        for k, (x, y, facing) in enumerate(places):
            _check_spawn(sc.terrain, sc.rules.spawn_jitter, "%s unit %d" % (where, k), x, y, layer, walker)
            s = sc.spawns[n]
            s.side, s.type, s.x, s.y, s.facing_deg, s.layer = side, ti, x, y, facing, layer
            if goals is not None:
                gx, gy = goals[k]
            s.order, s.gx, s.gy = order, float(gx), float(gy)
            s.pre_revealed = int(g.get("pre_revealed", 0))
            s.transfer_layer = int(g.get("transfer_layer", 0))
            s.transfer_tick = int(g.get("transfer_tick", 0))
            s.pulse_tick = int(g.get("pulse_tick", -1))
            s.emit = int(g.get("emit", 1))
            s.emit_switch_tick = int(g.get("emit_switch_tick", -1))
            s.emit_switch_to = int(g.get("emit_switch_to", 0))
            s.ping_tick = int(g.get("ping_tick", -1))
            s.ping_layer = int(g.get("ping_layer", 0))
            s.ping_x = float(g.get("ping_x", 0.0))
            s.ping_y = float(g.get("ping_y", 0.0))
            s.target_policy = policy
            n += 1
    sc.n_spawns = n
    return sc
