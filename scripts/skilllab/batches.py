"""Named batches: cell and variant definitions, and run(), which scans them and writes the csv, run file and page."""
import dataclasses
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Optional

from scripts.skilllab import maps, matchup, plays, positions, profile, report, rows, scan, skills
from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.terrain import with_terrain

NAMES = ("formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations", "layers")
BASE_SETTINGS = {"OM_TP_PURSUE_BY_STEERING": 1}
PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
NOT_EXPRESSED = "not expressed"
REPLICATES = 10
DEFENDER_ORDER = "idle"
UNIT_TYPES = ("Vanguard", "Raider", "Bombard", "Bastion")
REFERENCE = "reference"
_STALLED = ("stalemate", "cap")
PROFILE_NOTE = ("One row per subset of the five skills; break-even and advantage in whole units "
                "(unconfirmed definition).")
DRAFT_NUMBERS = "draft numbers: turn or spring tick 100, bait share 0.25, none confirmed"
LAYER_SCENES = ("mirror", "high_ground", "choke")
LAYER_NOTES = {"LA": "units on different layers cannot fire until reach by type lands (Phase C G5)",
               "LB": "needs reach by type (om_roster_set_reach) and Phase C G5",
               "LC": "needs reach by type (om_roster_set_reach) and Phase C G5"}
REACH_TABLE = ("Vanguard and Warden 0 up 0 down; Raider 1 up 1 down; Interceptor 2 up 1 down; "
               "Bombard and Bastion 0 up 2 down (needs om_roster_set_reach bound in the harness and Phase C G5)")


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
    weighted: bool = False


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
    return BatchDef(
        name="matchup",
        title="Skill lab matchup batch",
        scene=("Open map, no terrain, blob against blob. Side 0 of N units of one type or an even two-type mix against "
               "side 1 of half to one and a half times N of another. Sizes 16 and 32; every row against every column. "
               "The weighted firing count is on."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("the weighted count reads the lab's own sight rule, not the engine's, until Phase C side sight lands",
                     "only even two-type mixes; unequal mixes and three-type mixes are not included",
                     "arrangement is the default interleaved only"),
        weighted=True)


def _idle_defenders(build):
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        groups = tuple(dataclasses.replace(g, order=DEFENDER_ORDER) if g.side == 1 else g for g in setup.groups)
        return dataclasses.replace(setup, groups=groups)
    return wrapped


def _landscape():
    cells = []
    for kind in maps.KINDS:
        terrain = maps.sample_map(kind, 0)
        reference = with_terrain(asym_play(16, Side("blob"), Side("blob")), terrain)
        for role in ("blob", "line"):
            build = with_terrain(_idle_defenders(asym_play(16, Side(role), Side("blob"))), terrain)
            cells.append(_cell("%s:%s_v_defenders" % (kind, role), 16, build, "naive", enemy=(8, 24),
                               reference=reference))
    cells += [_cell("tall_cover", 16, None, NOT_EXPRESSED, "tall cover with height needs layer reach (Phase C G5)",
                    enemy=(8, 24)),
              _cell("tall_cover_counter", 16, None, NOT_EXPRESSED,
                    "a layer above the cover needs layer reach and layer orders (Phase C G4, G5)", enemy=(8, 24))]
    return BatchDef(
        name="landscape",
        title="Skill lab landscape batch",
        scene=("Five sampled maps (open, block, wall, lane, cover field). 16 attackers playing blob or line against 8 to "
               "24 defenders in a blob. The guard order is not built yet, so the defenders hold the order idle. Each "
               "cell also scans naive blob against naive blob on the same map as a reference."),
        cells=tuple(cells), variants=((DEFENDER_ORDER, {}),),
        unexpressed=("tall_cover", "tall_cover_counter", "guard order not built: defenders idle"))


def _enemy_position():
    blob = asym_play(16, Side("blob"), Side("blob"))
    cells = [_cell("blob", 16, blob, "naive", enemy=(8, 24))]
    for name, make in (("bait", positions.bait_play), ("ambush", positions.ambush_play),
                       ("fall_back", positions.fall_back_play)):
        cells.append(_cell(name, 16, make(16), skills.DRAFT, enemy=(8, 24)))
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
        missing = []
        for skill in sorted(s):
            try:
                skills.get(skill, "skilled")
            except ValueError:
                missing.append(skill)
        if not s:
            cells.append(_cell(label, 16, asym_play(16, Side("blob"), Side("blob")), "naive", enemy=(8, 24)))
        elif missing:
            cells.append(_cell(label, 16, None, NOT_EXPRESSED, "no skilled play for " + ", ".join(missing),
                               enemy=(8, 24)))
        elif len(s) > 1:
            cells.append(_cell(label, 16, None, NOT_EXPRESSED, "no rule for combining plays", enemy=(8, 24)))
        else:
            (skill,) = s
            cells.append(_cell(label, 16, asym_play(16, Side("skilled", skill=skill), Side("blob")),
                               skills.get(skill, "skilled").status, enemy=(8, 24)))
    cells.append(_cell("counter:S2", 16, asym_play(16, Side("counter"), Side("line")),
                       skills.get("S2", "counter").status, enemy=(8, 24)))
    return BatchDef(
        name="combinations",
        title="Skill lab combinations batch",
        scene=("Open map, no terrain. 16 Vanguards on side 0 apply a subset of the five skills (S1 to S5) against a "
               "naive blob of 8 to 24; 32 subsets, then S2's counter play against a line. A subset is played only if "
               "every skill in it has a registered skilled play and it holds at most one skill: no rule for combining "
               "two plays exists."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("subsets of two or more skills: no rule for combining plays",
                     "skills with no registered skilled play (defined with Westley later)"))


def _layer_settings(u1=None, u2=None, d=None):
    s = {}
    for n, v in ((1, 0.5), (2, 0.2), (3, 0.0), (4, 0.0)):
        s["OM_TP_VISION_UP_%d" % n] = s["OM_TP_VISION_DOWN_%d" % n] = v
    for n in (1, 2):
        for kind in ("RANGE", "DAMAGE"):
            s["OM_TP_%s_UP_%d" % (kind, n)] = s["OM_TP_%s_DOWN_%d" % (kind, n)] = 1.0
    if u1 is not None:
        s["OM_TP_RANGE_UP_1"], s["OM_TP_RANGE_UP_2"] = u1, u2
    if d is not None:
        s["OM_TP_DAMAGE_UP_1"], s["OM_TP_DAMAGE_UP_2"] = d, d / 2
    return s


def _layers():
    scenes = {"mirror": asym_play(16, Side("blob"), Side("blob")),
              "choke": with_terrain(asym_play(16, Side("blob"), Side("blob")), maps.sample_map("wall", 0))}
    pairs = [(u1, u2) for u1 in (0.5, 0.75, 1.0) for u2 in (0.25, 0.5)]
    cells = []

    def add(table, scene, suffix, settings):
        build = scenes.get(scene) if table == "LA" else None
        label = "%s:%s%s" % (table, scene, suffix)
        if build is not None:
            cells.append(_cell(label, 16, build, skills.DRAFT, "settings are draft sweep points (A174)",
                               enemy=(8, 24), settings=settings))
            return
        note = LAYER_NOTES[table] if scene != "high_ground" else (
            LAYER_NOTES["LA"] if table == "LA" else "%s; %s" % (LAYER_NOTES["LA"], LAYER_NOTES[table]))
        cells.append(_cell(label, 16, None, NOT_EXPRESSED, note, enemy=(8, 24), settings=settings))

    for scene in LAYER_SCENES:
        add("LA", scene, "", _layer_settings())
    for scene in LAYER_SCENES:
        for u1, u2 in pairs:
            add("LB", scene, ":up1=%s,up2=%s" % (u1, u2), _layer_settings(u1, u2))
    for scene in LAYER_SCENES:
        for d in (0.5, 0.75):
            for u1, u2 in pairs:
                add("LC", scene, ":up1=%s,up2=%s,dmg1=%s" % (u1, u2, d), _layer_settings(u1, u2, d))
    for r in (10, 15, 20, 30):
        for a in (150, 200, 300, 450):
            name = "RaiderR%d" % a
            side = Side("blob", mix=((name, 1),))
            build = asym_play(16, side, side, {name: {"base": "Raider", "set": {"attack_range": a}}})
            ratio = "%.1f" % (a / (2 * r))
            cells.append(_cell("body%d_range%d_ratio%s" % (2 * r, a, ratio), 16, build, skills.DRAFT,
                               "collision radius %d, body size %d, attack range %d, range-to-body ratio %s"
                               % (r, 2 * r, a, ratio), enemy=(8, 24), settings={"OM_TP_UNIT_COLLISION_RADIUS": r}))
    return BatchDef(
        name="layers",
        title="Skill lab layers batch",
        scene=("Tables LA (vision only), LB (vision and reach) and LC (vision, reach and damage) by three scenes: a "
               "mirror, high ground and a choke. 16 Vanguards against 8 to 24. The LB and LC values are sweep points "
               "proposed by the Architect as drafts (A174), not confirmed by Westley. The choke is a sampled wall, "
               "not the exact scene of the Phase B read. The last 16 cells are a Raider mirror over collision radius "
               "and attack range (reach against body size), also drafts."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("the tall-cover scene (needs reach)", REACH_TABLE,
                     "high ground and the LB and LC tables wait for reach",
                     "the choke is a sampled wall, not the Phase B scene"))


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
    if name == "layers":
        return _layers()
    raise ValueError("unknown batch %r; valid names: %s" % (name, ", ".join(NAMES)))


def _with_settings(build, settings, weighted=False):
    def wrapped(enemy_heads, swap):
        setup = dataclasses.replace(build(enemy_heads, swap), settings={**BASE_SETTINGS, **settings})
        return dataclasses.replace(setup, weighted=True) if weighted else setup
    return wrapped


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _tag(cell):
    return " (unconfirmed draft)" if cell.status == skills.DRAFT else ""


def _result_line(cell, variant, sc):
    fights = [f for c in sc.cells for f in c.fights]
    beats = ("no break-even in range" if sc.beats is None
             else "%d units beat %d, lose to %d" % (sc.size, sc.beats, sc.loses_to))
    weighted = [f.weighted_unit_seconds for f in fights if f.weighted_unit_seconds is not None]
    weighted_text = ("; mean weighted firing unit-seconds %.2f side 0, %.2f side 1"
                     % (_mean([w[0] for w in weighted]), _mean([w[1] for w in weighted]))) if weighted else ""
    return ("- %s%s, %s: %s; mean fight ticks %.1f; mean firing unit-seconds %.2f side 0, %.2f side 1%s; "
            "stalled fights %d" % (cell.label, _tag(cell), variant, beats, _mean([f.ticks for f in fights]),
                                   _mean([f.firing_unit_seconds[0] for f in fights]),
                                   _mean([f.firing_unit_seconds[1] for f in fights]), weighted_text,
                                   sum(f.outcome in _STALLED for f in fights)))


def _reference_line(sc):
    if sc.beats is None:
        return "naive against naive on this map: no break-even in range"
    return "naive against naive on this map: %d units beat %d, lose to %d" % (sc.size, sc.beats, sc.loses_to)


def _units(sc):
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
    lines = ["# " + defn.title, "", PROVISIONAL, "", "## Scene", "", defn.scene, "", "## Cells", "",
             "| cell | size | enemy range | replicates | fights per cell | status |", "|---|---|---|---|---|---|"]
    for c in defn.cells:
        lines.append("| %s | %d | %d to %d | %d | %d | %s |" % (c.label, c.size, c.enemy_from, c.enemy_to,
                                                                 c.replicates, 2 * c.replicates, c.status))
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
    lines += ["- %s: %s" % (c.label, c.note) for c in defn.cells if c.build is None]
    lines += ["", "## Files", ""] + ["- " + n for n in names] + [""]
    return "\n".join(lines)


def _matchup_page(defn, scans):
    body = ["<p>%s</p>" % escape(PROVISIONAL), "<p>%s</p>" % escape(defn.scene)]
    names = list(dict.fromkeys(c.label.split("_v_")[0] for c in defn.cells))
    for n in sorted({c.size for c in defn.cells}):
        grid = {tuple(c.label.split("@")[0].split("_v_")): scans[(c.label, defn.variants[0][0])].beats
                for c in defn.cells if c.size == n}
        body.append(matchup.matchup_grid_html(names, names, grid, n, "%s, %d units" % (defn.title, n)))
    return report._html(defn.title, body)


def _page(defn, scans, examples):
    if defn.name == "matchup":
        return _matchup_page(defn, scans)
    body = ["<h1>%s</h1>" % escape(defn.title), "<p>%s</p>" % escape(PROVISIONAL), "<p>%s</p>" % escape(defn.scene)]
    for c in defn.cells:
        body.append("<h2>%s (%s)</h2>" % (escape(c.label), escape(c.status)))
        if c.build is None:
            body.append("<p>%s</p>" % escape(c.note))
            continue
        for v, _ in defn.variants:
            body += ["<h3>%s, %s: line of fights by enemy size</h3>" % (escape(c.label), escape(v)),
                     report._scan_svg(scans[(c.label, v)]), report._scan_table(scans[(c.label, v)])]
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


def run(defn, out_dir, scan_fn=None):
    scan_fn = scan_fn or scan.scan
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scans, examples, fight_rows = {}, {}, []
    extra = {"defender_order": DEFENDER_ORDER} if defn.name == "landscape" else {}
    for c in defn.cells:
        if c.build is None:
            continue
        if c.reference is not None:
            scans[(c.label, REFERENCE)] = scan_fn(_with_settings(c.reference, defn.variants[0][1], defn.weighted),
                                                  c.size, c.enemy_from, c.enemy_to, replicates=c.replicates)
        for v, overlay in defn.variants:
            result = scan_fn(_with_settings(c.build, {**overlay, **c.settings}, defn.weighted), c.size, c.enemy_from, c.enemy_to,
                             replicates=c.replicates)
            scans[(c.label, v)] = result
            for cell in result.cells:
                if cell.enemy_heads == c.size and c.label not in examples:
                    examples[c.label] = cell.fights[0]
                for f in cell.fights:
                    fight_rows.append(rows.fight_row(f, cell=c.label, variant=v, size=c.size,
                                                     enemy_heads=cell.enemy_heads, status=c.status, **extra))
    paths = {"csv": out / (defn.name + ".csv"), "run": out / (defn.name + "_run.md"),
             "page": out / (defn.name + "_page.html")}
    rows.write_rows(fight_rows, paths["csv"])
    paths["run"].write_text(_run_file(defn, scans, [p.name for p in paths.values()]), encoding="utf-8")
    paths["page"].write_text(_page(defn, scans, examples), encoding="utf-8")
    return paths
