"""Named batches: cell and variant definitions, and run(), which scans them and writes the csv, run file and page."""
import dataclasses
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional

from scripts.skilllab import plays, report, rows, scan, skills
from scripts.skilllab.asym import Side, asym_play

NAMES = ("formation", "focus_fire")
BASE_SETTINGS = {"OM_TP_PURSUE_BY_STEERING": 1}
PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
NOT_EXPRESSED = "not expressed"
REPLICATES = 10
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


@dataclass(frozen=True)
class BatchDef:
    name: str
    title: str
    scene: str
    cells: tuple
    variants: tuple
    unexpressed: tuple


def _cell(label, size, build, status, note="", enemy=None):
    lo, hi = enemy or (size // 2, size * 3 // 2)
    return CellDef(label, size, lo, hi, REPLICATES, build, status, note)


def _formation():
    cells = []
    for n in (16, 8, 32):
        blob, line = Side("blob"), Side("line")
        for kind, side0, side1 in (("line", line, blob), ("blob", blob, blob),
                                   ("concave", Side("skilled"), blob),
                                   ("counter", Side("counter"), line)):
            build = asym_play(n, side0, side1)
            status = build.labels["status_side0"]
            cells.append(_cell("%s@%d" % (kind, n), n, build, status))
    return BatchDef(
        name="formation",
        title="Skill lab formation batch",
        scene=("Open map, no terrain. Side 0 of Vanguards plays line, blob, a 120-degree concave or a column counter "
               "against a naive blob (the counter plays against a line). Sizes 16, then 8 and 32; the enemy runs "
               "from half to one and a half times the size. The units start just outside sensor range of each other."),
        cells=tuple(cells), variants=(("default", {}),),
        unexpressed=("skills S1, S3, S4, S5 have no formation play",
                     "Raider (short-range) variant not included",
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


def get(name):
    if name == "formation":
        return _formation()
    if name == "focus_fire":
        return _focus_fire()
    raise ValueError("unknown batch %r; valid names: %s" % (name, ", ".join(NAMES)))


def _with_settings(build, settings):
    def wrapped(enemy_heads, swap):
        return dataclasses.replace(build(enemy_heads, swap), settings={**BASE_SETTINGS, **settings})
    return wrapped


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _tag(cell):
    return " (unconfirmed draft)" if cell.status == skills.DRAFT else ""


def _result_line(cell, variant, sc):
    fights = [f for c in sc.cells for f in c.fights]
    beats = ("no break-even in range" if sc.beats is None
             else "%d units beat %d, lose to %d" % (sc.size, sc.beats, sc.loses_to))
    return ("- %s%s, %s: %s; mean fight ticks %.1f; mean firing unit-seconds %.2f side 0, %.2f side 1; "
            "stalled fights %d" % (cell.label, _tag(cell), variant, beats, _mean([f.ticks for f in fights]),
                                   _mean([f.firing_unit_seconds[0] for f in fights]),
                                   _mean([f.firing_unit_seconds[1] for f in fights]),
                                   sum(f.outcome in _STALLED for f in fights)))


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
    lines += [_result_line(c, v, scans[(c.label, v)]) for c in defn.cells if c.build is not None
              for v, _ in defn.variants]
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


def _page(defn, scans, examples):
    body = ["<h1>%s</h1>" % escape(defn.title), "<p>%s</p>" % escape(PROVISIONAL)]
    for c in defn.cells:
        body.append("<h2>%s (%s)</h2>" % (escape(c.label), escape(c.status)))
        if c.build is None:
            body.append("<p>%s</p>" % escape(c.note))
            continue
        for v, _ in defn.variants:
            body += ["<h3>%s, %s: line of fights by enemy size</h3>" % (escape(c.label), escape(v)),
                     report._scan_svg(scans[(c.label, v)]), report._scan_table(scans[(c.label, v)])]
        fr = examples.get(c.label)
        if fr is not None:
            body += ["<h3>%s: units able to fire through one fight</h3>" % escape(c.label),
                     report._firing_svg(fr.firing)]
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
    for c in defn.cells:
        if c.build is None:
            continue
        for v, overlay in defn.variants:
            result = scan_fn(_with_settings(c.build, overlay), c.size, c.enemy_from, c.enemy_to,
                             replicates=c.replicates)
            scans[(c.label, v)] = result
            for cell in result.cells:
                if cell.enemy_heads == c.size and c.label not in examples:
                    examples[c.label] = cell.fights[0]
                for f in cell.fights:
                    fight_rows.append(rows.fight_row(f, cell=c.label, variant=v, size=c.size,
                                                     enemy_heads=cell.enemy_heads, status=c.status))
    paths = {"csv": out / (defn.name + ".csv"), "run": out / (defn.name + "_run.md"),
             "page": out / (defn.name + "_page.html")}
    rows.write_rows(fight_rows, paths["csv"])
    paths["run"].write_text(_run_file(defn, scans, [p.name for p in paths.values()]), encoding="utf-8")
    paths["page"].write_text(_page(defn, scans, examples), encoding="utf-8")
    return paths
