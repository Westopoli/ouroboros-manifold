"""Named batches: cell and variant definitions, and run(), which scans them and writes the csv, run file and page."""
import dataclasses
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional

from scripts.skilllab import maps, matchup, plays, report, rows, scan, skills
from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.terrain import with_terrain

NAMES = ("formation", "focus_fire", "matchup", "landscape")
BASE_SETTINGS = {"OM_TP_PURSUE_BY_STEERING": 1}
PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
NOT_EXPRESSED = "not expressed"
REPLICATES = 10
DEFENDER_ORDER = "idle"
UNIT_TYPES = ("Vanguard", "Raider", "Bombard", "Bastion")
REFERENCE = "reference"
_STALLED = ("stalemate", "cap")


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


@dataclass(frozen=True)
class BatchDef:
    name: str
    title: str
    scene: str
    cells: tuple
    variants: tuple
    unexpressed: tuple
    weighted: bool = False


def _cell(label, size, build, status, note="", enemy=None, reference=None):
    lo, hi = enemy or (size // 2, size * 3 // 2)
    return CellDef(label, size, lo, hi, REPLICATES, build, status, note, reference)


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


def get(name):
    if name == "formation":
        return _formation()
    if name == "focus_fire":
        return _focus_fire()
    if name == "matchup":
        return _matchup()
    if name == "landscape":
        return _landscape()
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
            result = scan_fn(_with_settings(c.build, overlay, defn.weighted), c.size, c.enemy_from, c.enemy_to,
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
