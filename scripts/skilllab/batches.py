"""Named batches: cell and variant definitions, and run(), which scans them and writes the csv, run file and page."""
import dataclasses
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Optional

from scripts.skilllab import compose, depth, maps, matchup, plays, pool, positions, profile, report, rows, scan, skills, summary
from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.contract import trim_series
from scripts.skilllab.ground.scenes_ground import tall_cover, tall_cover_terrain
from scripts.skilllab.scenes import guard_defenders
from scripts.skilllab.terrain import with_terrain

NAMES = ("formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations", "layout_search")
BASE_SETTINGS = {"OM_TP_PURSUE_BY_STEERING": 1}
RULE_NOTE = ("A fight ends when one side is eliminated (Q-LAB-03). A capped fight is a lab defect, never a result; "
             "a draw (both sides die on one tick) is a defect too.")
NOT_SINGLE = "not a single group order"
REFINE_FACTOR = 3
PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
NOT_EXPRESSED = "not expressed"
REPLICATES = 10
DEFENDER_ORDER = "guard"
UNIT_TYPES = ("Vanguard", "Raider", "Bombard", "Bastion")
REFERENCE = "reference"
PROFILE_NOTE = ("One row per subset of the five skills; break-even and advantage in whole units "
                "(unconfirmed definition).")
DRAFT_NUMBERS = "draft numbers: turn or spring tick 100, bait share 0.25, none confirmed"


@dataclass(frozen=True)
class CellDef:
    label: str
    size: int
    enemy_from: int
    enemy_to: int
    replicates: int
    build: Optional[object]
    status: str
    note: str = ""
    reference: Optional[object] = None
    settings: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BatchDef:
    name: str
    title: str
    scene: str
    cells: tuple
    variants: tuple
    unexpressed: tuple


def _cell(label, size, build, status, note="", enemy=None, reference=None, settings=None):
    lo, hi = enemy or (size // 2, size * 3 // 2)
    return CellDef(label, size, lo, hi, REPLICATES, build, status, note, reference, settings or {})


def _formation():
    cells = []
    for suffix, mix in (("", (("Vanguard", 1),)), (":Raider", (("Raider", 1),))):
        for n in (16, 8, 32):
            blob, line = Side("blob", mix=mix), Side("line", mix=mix)
            for kind, side0, side1 in (("line", line, blob), ("blob", blob, blob),
                                       ("concave", Side("skilled", mix=mix), blob),
                                       ("counter", Side("counter", mix=mix), line)):
                build = asym_play(n, side0, side1)
                status = build.labels["status_side0"]
                cells.append(_cell("%s@%d%s" % (kind, n, suffix), n, build, status))
    return BatchDef(
        name="formation",
        title="Skill lab formation batch",
        scene=("Open map, no terrain. Side 0 of Vanguards plays line, blob, a 120-degree concave or a column counter "
               "against a naive blob (the counter plays against a line). Sizes 16, then 8 and 32; the enemy runs "
               "from half to one and a half times the size. The units start just outside sensor range of each other."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("skills S1, S3, S4, S5 have no formation play",
                     "concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point"))


def _focus_fire():
    s2 = lambda label, a, b: _cell(label, 16, asym_play(16, a, b), skills.get("S2", a.role).status, enemy=(8, 24))
    cells = [_cell("identical", 16, plays.blob_play(16), "naive", enemy=(8, 24)),
             _cell("damage", 16, plays.damage_play(16), "naive", enemy=(8, 24)),
             _cell("reach", 16, plays.reach_play(16), "naive", enemy=(8, 24)),
             s2("S2_skilled", Side("skilled"), Side("blob")),
             s2("S2_counter", Side("counter"), Side("line"))]
    gaps = ("S1", "S3", "S4", "S5")
    cells += [_cell("%s_skilled" % s, 16, None, NOT_EXPRESSED, "no skilled play until defined with Westley (A145)",
                    enemy=(8, 24)) for s in gaps]
    return BatchDef(
        name="focus_fire",
        title="Skill lab focus fire batch",
        scene=("Open map, no terrain. 16 Vanguards on side 0 against 8 to 24 on side 1. Each cell is fought twice: "
               "enemy units pick the nearest target, then the most damaged one in reach."),
        cells=tuple(cells),
        variants=(("nearest", {"OM_TP_TARGET_POLICY": 0}), ("most_damaged", {"OM_TP_TARGET_POLICY": 1})),
        unexpressed=gaps)


def _matchup():
    axis = [(u, ((u, 1),)) for u in UNIT_TYPES]
    axis += [("%s+%s" % (a, b), ((a, 1), (b, 1))) for i, a in enumerate(UNIT_TYPES) for b in UNIT_TYPES[i + 1:]]
    cells = [_cell("%s_v_%s@%d" % (r, c, n), n, asym_play(n, Side("blob", mix=rm), Side("blob", mix=cm)), "naive")
             for n in (16, 32) for r, rm in axis for c, cm in axis]
    short = lambda m: Side("blob", mix=m, arrangement="layered_short_front" if len(m) > 1 else "interleaved")
    cells += [_cell("%s_v_%s@16:layered" % (r, c), 16, asym_play(16, short(rm), short(cm)), "unconfirmed draft")
              for r, rm in axis for c, cm in axis if len(rm) > 1 or len(cm) > 1]
    return BatchDef(
        name="matchup",
        title="Skill lab matchup batch",
        scene=("Open map, no terrain, blob against blob. Side 0 of N units of one type or an even two-type mix against "
               "side 1 of half to one and a half times N of another. Sizes 16 and 32; every row against every column. "
               "The type-weighted firing count is recorded for every fight. Layered cells (short-range types in front, long-range behind) run at size 16 only, "
               "so the batch stays under about 30 minutes."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("the weighted count reads the target of record (the engine's target when it can engage, else the nearest eligible enemy)",
                     "only even two-type mixes; unequal mixes and three-type mixes are not included",
                     "arrangement: interleaved in every cell; layered (short range in front, long range behind) only at size 16 "
                     "and only on the even two-type mixes, in the first pass; the reverse arrangement and layered at 32 are not run"),
        )


def _landscape():
    cells = []
    for kind in maps.KINDS:
        terrain = maps.sample_map(kind, 0)
        reference = with_terrain(asym_play(16, Side("blob"), Side("blob")), terrain)
        for role in ("blob", "line"):
            build = with_terrain(guard_defenders(asym_play(16, Side(role), Side("blob"))), terrain)
            cells.append(_cell("%s:%s_v_defenders" % (kind, role), 16, build, "naive", enemy=(8, 24),
                               reference=reference))
    for label, counter in (("tall_cover", False), ("tall_cover_counter", True)):
        note = ("draft numbers: height 3, discs of radius 100 every 150 wu" +
                ("; attackers on layer 3 reach 3 layers down" if counter else ""))
        cells.append(_cell(label, 16, tall_cover(3, counter)(16), "unconfirmed draft", note, enemy=(8, 24),
                           reference=with_terrain(asym_play(16, Side("blob"), Side("blob")), tall_cover_terrain(3))))
    return BatchDef(
        name="landscape",
        title="Skill lab landscape batch",
        scene=("Five sampled maps (open, block, wall, lane, cover field). 16 attackers playing blob or line against 8 to "
               "24 defenders in a blob. The defenders hold the guard order. Each "
               "cell also scans naive blob against naive blob on the same map as a reference."),
        cells=tuple(cells), variants=((DEFENDER_ORDER, {}),),
        unexpressed=())


def _enemy_position():
    blob = asym_play(16, Side("blob"), Side("blob"))
    cells = [_cell("blob", 16, blob, "naive", enemy=(8, 24))]
    notes = {"bait": "the bait is a second group, so the play is " + NOT_SINGLE,
             "fall_back": "the retreat is a later move, so the play is " + NOT_SINGLE}
    for name, make in (("bait", positions.bait_play), ("ambush", positions.ambush_play),
                       ("fall_back", positions.fall_back_play)):
        cells.append(_cell(name, 16, make(16), skills.DRAFT, notes.get(name, ""), enemy=(8, 24)))
    hold, dark = "needs hold-fire, not built", "going dark, emission per unit, needs Phase C G6"
    cells += [_cell(label, 16, None, NOT_EXPRESSED, note, enemy=(8, 24)) for label, note in (
        ("bait_hold_fire", hold), ("ambush_hold_fire", hold), ("dark_approach", dark), ("dark_ambush", dark))]
    return BatchDef(
        name="enemy_position",
        title="Skill lab enemy position batch",
        scene=("Open map, no terrain. 16 Vanguards on side 0 play a position play (bait, ambush or fall back) against a "
               "naive blob of 8 to 24; a blob against a blob is the control. The plays are drafts: the turn or spring "
               "tick is 100 and the bait share is 0.25, neither confirmed."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=tuple(c.label for c in cells if c.build is None) + (DRAFT_NUMBERS,))


def _combinations():
    cells = []
    for s in profile.subsets():
        label = "combo:" + ("+".join(sorted(s)) if s else "none")
        comp = compose.compose(s)
        if comp.expressible:
            status = skills.get(comp.skills[0], "skilled").status if s else "naive"
            cells.append(_cell(label, 16, comp.build(16), status, enemy=(8, 24)))
        else:
            cells.append(_cell(label, 16, None, NOT_EXPRESSED, comp.note, enemy=(8, 24)))
    cells.append(_cell("counter:S2", 16, asym_play(16, Side("counter"), Side("line")),
                       skills.get("S2", "counter").status, enemy=(8, 24)))
    return BatchDef(
        name="combinations",
        title="Skill lab combinations batch",
        scene=("Open map, no terrain. 16 Vanguards on side 0 apply a subset of the five skills (S1 to S5) against a "
               "naive blob of 8 to 24; 32 subsets, then S2's counter play against a line. A subset is played only if "
               "every skill in it has a registered skilled play and it holds at most one skill: the slot plays that "
               "would merge several skills' plays do not exist yet."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("subsets of two or more skills: slot plays that merge several skills' plays do not exist yet",
                     "skills with no registered skilled play (defined with Westley later)"))


def get(name):
    if name == "formation":
        return _formation()
    if name == "focus_fire":
        return _focus_fire()
    if name == "matchup":
        return _matchup()
    if name == "landscape":
        return _landscape()
    if name == "enemy_position":
        return _enemy_position()
    if name == "combinations":
        return _combinations()
    raise ValueError("unknown batch %r; valid names: %s" % (name, ", ".join(NAMES)))


def _with_settings(build, settings):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        return dataclasses.replace(setup, settings={**setup.settings, **BASE_SETTINGS, **settings})
    return wrapped


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def terrain_had_no_effect(cell_result, open_result):
    """True when the two scans agree on break-even and on every fight's outcome, margin, survivors and ticks."""
    key = lambda sc: (sc.beats, sc.loses_to, [(c.enemy_heads, c.won, [(f.outcome, f.margin, f.survivors, f.ticks)
                                                                  for f in c.fights]) for c in sc.cells])
    return key(cell_result) == key(open_result)


def _no_effect_lines(defn, scans):
    """Landscape: each non-open cell whose scan equals the open cell's of the same role, per variant."""
    out = []
    for c in defn.cells:
        kind, _, rest = c.label.partition(":")
        if c.build is None or kind == "open" or "_v_defenders" not in rest or kind not in maps.KINDS:
            continue
        for v, _ in defn.variants:
            if terrain_had_no_effect(scans[(c.label, v)], scans[("open:" + rest, v)]):
                out.append("- %s, %s: the sampled map did not change the fight against the open map" % (c.label, v))
    return out


def _tag(cell):
    return " (unconfirmed draft)" if cell.status == skills.DRAFT else ""


def _spread_text(sc):
    """" | pair spread LOW to HIGH" for the cell at the break-even edge, else empty."""
    edge = next((c for c in sc.cells if c.enemy_heads == sc.beats), None)
    if edge is None:
        return ""
    low, high = scan.pair_spread(edge)
    return " | pair spread %.2f to %.2f" % (low, high)


def _beats_text(sc):
    if sc.ceiling_hit:
        return "%d units beat all %d enemy units (ceiling hit)" % (sc.size, sc.beats)
    if sc.beats is None:
        return "no break-even in range"
    return "%d units beat %d, lose to %d" % (sc.size, sc.beats, sc.loses_to)


def _result_line(cell, variant, sc):
    fights = [f for c in sc.cells for f in c.fights]
    weighted = [f.weighted_unit_seconds for f in fights]
    spread = _spread_text(sc)
    return ("- %s%s, %s: %s; mean fight ticks %.1f; mean firing unit-seconds %.2f side 0, %.2f side 1; "
            "mean weighted firing unit-seconds %.2f side 0, %.2f side 1; caps %d; draws %d; defect cells %d%s"
            % (cell.label, _tag(cell), variant, _beats_text(sc), _mean([f.ticks for f in fights]),
               _mean([f.firing_unit_seconds[0] for f in fights]), _mean([f.firing_unit_seconds[1] for f in fights]),
               _mean([w[0] for w in weighted]), _mean([w[1] for w in weighted]),
               sum(f.outcome == "cap" for f in fights), sum(f.outcome == "draw" for f in fights),
               sum(c.defect for c in sc.cells), spread))


def _reference_line(sc):
    return "naive against naive on this map: " + _beats_text(sc)


def _units(sc):
    if sc.ceiling_hit:
        return "%d units beat all %d (ceiling hit)" % (sc.size, sc.beats)
    if sc.beats is None:
        return "%d units: no break-even in range" % sc.size
    return "%d units beat %d" % (sc.size, sc.beats)


def _raider_pairs(defn, scans):
    first = defn.variants[0][0]
    out = []
    for c in defn.cells:
        if c.label.endswith(":Raider"):
            continue
        a, b = scans[(c.label, first)], scans[(c.label + ":Raider", first)]
        va, vb = -1 if a.beats is None else a.beats, -1 if b.beats is None else b.beats
        out.append((c.label, a, b, "same" if va == vb else "Raider larger" if vb > va else "Raider smaller"))
    return out


def _profile_rows(defn, scans):
    first = defn.variants[0][0]
    cells = {c.label: c for c in defn.cells}
    control = scans.get(("combo:none", first))
    rows_ = []
    for sub in profile.subsets():
        cell = cells["combo:" + ("+".join(sorted(sub)) if sub else "none")]
        if cell.build is None:
            rows_.append(("+".join(sorted(sub)), NOT_EXPRESSED, NOT_EXPRESSED, NOT_EXPRESSED))
            continue
        got = scans[(cell.label, first)].beats
        if got is None:
            beats = adv = "no break-even in range"
        else:
            beats = str(got)
            adv = "no break-even in range" if control.beats is None else str(got - control.beats)
        rows_.append(("+".join(sorted(sub)) or "none", cell.status, beats, adv))
    return rows_


def _changes(defn, scans):
    (first, _), (second, _) = defn.variants
    out = []
    for cell in defn.cells:
        if cell.build is None:
            continue
        a, b = scans[(cell.label, first)].beats, scans[(cell.label, second)].beats
        word = "no change" if a == b else "gains" if (b or -1) > (a or -1) else "loses"
        out.append((cell, a, b, word))
    return first, second, out


def _run_file(defn, scans, names):
    lines = ["# " + defn.title, "", PROVISIONAL, "", RULE_NOTE, "", "## Scene", "", defn.scene, "", "## Cells", "",
             "| cell | size | enemy range | replicates | fights per cell | status |", "|---|---|---|---|---|---|"]
    for c in defn.cells:
        lines.append("| %s | %d | %d to %d | %d | %d | %s |" % (c.label, c.size, c.enemy_from, c.enemy_to,
                                                                 c.replicates, 2 * c.replicates, c.status))
    lines += ["", "Cells within 2 enemy units of a break-even run %d times the fights." % REFINE_FACTOR]
    lines += ["", "## Results", ""]
    for c in defn.cells:
        if c.build is None:
            continue
        lines += [_result_line(c, v, scans[(c.label, v)]) for v, _ in defn.variants]
        if c.reference is not None:
            lines.append("- " + _reference_line(scans[(c.label, REFERENCE)]))
    if defn.name == "formation":
        lines += ["", "## Vanguard against Raider", ""]
        lines += ["- %s: Vanguard %s; Raider %s; %s" % (label, _units(a), _units(b), word)
                  for label, a, b, word in _raider_pairs(defn, scans)]
    if defn.name == "combinations":
        lines += ["", "## Profile", "", PROFILE_NOTE, "", "| skills | status | break-even | advantage over combo:none |",
                  "|---|---|---|---|"]
        lines += ["| %s |" % " | ".join(r) for r in _profile_rows(defn, scans)]
    if defn.name == "focus_fire":
        first, second, changes = _changes(defn, scans)
        lines += ["", "## What changes", ""]
        lines += ["- %s: break-even %s %s, %s %s, %s" % (c.label, first, a if a is not None else "none", second,
                                                          b if b is not None else "none", word)
                  for c, a, b, word in changes]
    lines += ["", "## What the instrument could not express", ""]
    lines += ["- " + u for u in defn.unexpressed]
    if defn.name == "landscape":
        lines += _no_effect_lines(defn, scans)
    lines += ["- %s: %s" % (c.label, c.note) for c in defn.cells if c.build is None or NOT_SINGLE in c.note]
    lines += ["", "## Files", ""] + ["- " + n for n in names] + [""]
    return "\n".join(lines)


def _matchup_page(defn, scans):
    body = ["<p>%s</p>" % escape(PROVISIONAL), "<p>%s</p>" % escape(RULE_NOTE),
            "<p>%s</p>" % escape(defn.scene)]
    names = list(dict.fromkeys(c.label.split("_v_")[0] for c in defn.cells))
    plain = [c for c in defn.cells if not c.label.endswith(":layered")]
    for n in sorted({c.size for c in plain}):
        grid = {tuple(c.label.split("@")[0].split("_v_")): scans[(c.label, defn.variants[0][0])].beats
                for c in plain if c.size == n}
        body.append(matchup.matchup_grid_html(names, names, grid, n, "%s, %d units" % (defn.title, n)))
    grid = {tuple(c.label.split("@")[0].split("_v_")): scans[(c.label, defn.variants[0][0])].beats
            for c in plain if c.size == 16}
    grid.update({tuple(c.label.split("@")[0].split("_v_")): scans[(c.label, defn.variants[0][0])].beats
                 for c in defn.cells if c.label.endswith(":layered")})
    body.append(matchup.matchup_grid_html(names, names, grid, 16, "layered, 16 units"))
    body.append("<p>The third grid is the layered arrangement at 16 units: pairs with a mix use the layered cell, "
                "pure-versus-pure pairs repeat the interleaved result.</p>")
    return report._html(defn.title, body)


def _page(defn, scans, examples):
    if defn.name == "matchup":
        return _matchup_page(defn, scans)
    body = ["<h1>%s</h1>" % escape(defn.title), "<p>%s</p>" % escape(PROVISIONAL), "<p>%s</p>" % escape(RULE_NOTE),
            "<p>%s</p>" % escape(defn.scene)]
    for c in defn.cells:
        body.append("<h2>%s (%s)</h2>" % (escape(c.label), escape(c.status)))
        if c.build is None:
            body.append("<p>%s</p>" % escape(c.note))
            continue
        for v, _ in defn.variants:
            body += ["<h3>%s, %s: line of fights by enemy size</h3>" % (escape(c.label), escape(v)),
                     report._scan_svg(scans[(c.label, v)]), report._scan_table(scans[(c.label, v)])]
            if _spread_text(scans[(c.label, v)]):
                body.append("<p>Margin at the break-even edge%s</p>" % escape(_spread_text(scans[(c.label, v)])))
        if c.reference is not None:
            body.append("<p>%s</p>" % escape(_reference_line(scans[(c.label, REFERENCE)])))
        fr = examples.get(c.label)
        if fr is not None:
            body += ["<h3>%s: units able to fire through one fight</h3>" % escape(c.label),
                     report._firing_svg(fr.firing)]
    if defn.name == "formation":
        body += ["<h2>Vanguard against Raider</h2>", "<table>",
                 "<tr><th>Cell</th><th>Vanguard</th><th>Raider</th><th>Comparison</th></tr>"]
        body += ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (escape(label), _units(a), _units(b), word)
                 for label, a, b, word in _raider_pairs(defn, scans)]
        body.append("</table>")
    if defn.name == "combinations":
        body += ["<h2>Profile</h2>", "<p>%s</p>" % escape(PROFILE_NOTE), "<table>",
                 "<tr><th>Skills</th><th>Status</th><th>Break-even</th><th>Advantage over combo:none</th></tr>"]
        body += ["<tr>%s</tr>" % "".join("<td>%s</td>" % escape(c) for c in r) for r in _profile_rows(defn, scans)]
        body.append("</table>")
    if defn.name == "focus_fire":
        first, second, changes = _changes(defn, scans)
        body += ["<h2>What changes</h2>", "<table>",
                 "<tr><th>Cell</th><th>%s</th><th>%s</th><th>Change</th></tr>" % (escape(first), escape(second))]
        body += ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            escape(c.label), a if a is not None else "none", b if b is not None else "none", word)
            for c, a, b, word in changes]
        body.append("</table>")
    return report._html(defn.title, body)


def run(defn, out_dir, scan_fn=None, workers=1):
    """Run every cell of the batch; workers above 1 fights in a process pool shared by all the scans (same results)."""
    if workers < 1:
        raise ValueError("workers must be at least 1")
    if workers == 1:
        return _run(defn, out_dir, scan_fn)
    with pool.FightPool(workers, lean=True) as p:
        return _run(defn, out_dir, scan_fn, map_fn=p.map)


def _trimmed(result, keep):
    """Drop the per-tick series from every fight of the scan except `keep` (the charted example); row values stay."""
    for cell in result.cells:
        cell.fights = [f if f is keep else trim_series(f) for f in cell.fights]
    return result


def _run(defn, out_dir, scan_fn=None, map_fn=None):
    scan_fn = scan_fn or scan.scan
    more = {} if map_fn is None else {"map_fn": map_fn}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scans, examples, fight_rows = {}, {}, []
    extra = {"defender_order": DEFENDER_ORDER} if defn.name == "landscape" else {}
    for c in defn.cells:
        if c.build is None:
            continue
        if c.reference is not None:
            scans[(c.label, REFERENCE)] = _trimmed(scan_fn(_with_settings(c.reference, defn.variants[0][1]),
                                                  c.size, c.enemy_from, c.enemy_to, replicates=c.replicates,
                                                  refine_factor=REFINE_FACTOR, **more), None)
        for v, overlay in defn.variants:
            result = scan_fn(_with_settings(c.build, {**overlay, **c.settings}), c.size, c.enemy_from, c.enemy_to,
                             replicates=c.replicates, refine_factor=REFINE_FACTOR, **more)
            scans[(c.label, v)] = result
            keep = None
            for cell in result.cells:
                if cell.enemy_heads == c.size and c.label not in examples:
                    examples[c.label] = keep = cell.fights[0]
                for f in cell.fights:
                    fight_rows.append(rows.fight_row(f, cell=c.label, variant=v, size=c.size,
                                                     enemy_heads=cell.enemy_heads, status=c.status, **extra))
            _trimmed(result, keep)
    paths = {"csv": out / (defn.name + ".csv"), "run": out / (defn.name + "_run.md"),
             "page": out / (defn.name + "_page.html"), "summary": out / "summary.json"}
    rows.write_rows(fight_rows, paths["csv"])
    paths["run"].write_text(_run_file(defn, scans, [p.name for p in paths.values()]), encoding="utf-8")
    paths["page"].write_text(_page(defn, scans, examples), encoding="utf-8")
    summary.write(defn, scans, paths["summary"], RULE_NOTE)
    return paths


def layout_search(n_layouts, seed, workers, out_dir, replicates=3):
    return depth.run(n_layouts, seed, workers, out_dir, replicates=replicates)
