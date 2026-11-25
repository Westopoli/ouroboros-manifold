"""LI4-FW, arms F (one factor) and W (whole) of the lab isolation measurement, and the comparison row (docs/northstar/plans/lab-isolation-2026-11-24/spec.md sections 3 to 5, 7;
interface: docs/reports/2026-11-24-li4fw-interface.md). Runs every fight through LI1's lab-per-version (`isolation_runner`: build the version from `git archive`, run its own lab) and
measures it with LI2 (`isolation_measures.measure_fight`). Nothing is gated: a flag is a signal, a cell that cannot be measured says `not measured`, never 0.
Arm W: the layout as authored and its control twin (the lab's `control_twin`, written by `run --control-dir` inside the built tree, so no scratch path reaches a fight file).
Arm F: the same two variants of `neutral_layout` (every unit Vanguard, Vanguard's range). Tests: tests/skilllab/integration/test_isolation_fw_*.py."""
import hashlib
import json
import re
import shutil
import tomllib
from copy import deepcopy
from pathlib import Path

from scripts.skilllab.arena import isolation_measures as im
from scripts.skilllab.arena import isolation_runner as ir
from scripts.skilllab.catalogue.produce import _roster_ranges, dump_toml

STAGE3_LAYOUTS = ("L-0055", "L-0073", "L-0084", "L-0039")   # chokepoint, city, slope, cover
DRAFT_SEEDS = (10, 1)                                        # DRAFT-seeds: 10 as approved plus 1 (seeds change nothing in lab fights); the first is the headline seed
DRAFT_SAME_OR_CHANGED_RULE = "identical winner over the seeds"   # DRAFT-same-or-changed-rule
ARM_ORDER = ("M", "V", "R", "F", "P", "W")
ARMS = ("F", "W")                                            # the arms of this piece
VARIANTS = ("layout", "control")
NOT_MEASURED = im.NOT_MEASURED
NOT_RUN = "not run"
NO_PICTURE = "no per-picture verdict"
SCRATCH_DIRS = ("li4-neutral", "li4-control")                # inside a built tree: the neutral layout files, the twin of each arm

LD = ir.LD
HEURISTICS, VERDICTS, RULED = LD + "/heuristics.md", LD + "/catalogue/verdicts.md", "docs/northstar/story_reviews/westley/ruled.md"
STAGE3_ROW = "arena_stage3/"                                 # the ruled.md row of the stage 3 approval


# ---------------------------------------------------------------- the records

def approved(repo=None):
    """{layout: stage 3 row of arena/approved.toml} (expected_winner, predict_rate of side A, decision)."""
    with open(Path(repo or ir.REPO) / LD / "arena" / "approved.toml", "rb") as f:
        return {r["layout"]: r for r in tomllib.load(f)["fight"] if r["stage"] == 3}


def _situation(layout, repo):
    with open(Path(repo) / LD / "catalogue" / (layout + ".toml"), "rb") as f:
        return tomllib.load(f)["situation"]


def ruling(layout, repo=None):
    """{words, date, per_picture, stage_approval: {words, date}}: his words verbatim from the records. A layout he denied by id (verdicts.md) carries his words as `per_picture`; the layouts redrawn
    and approved only with the stage have the heuristics table's words and no per-picture verdict. ValueError for a layout that is not a stage 3 layout."""
    if layout not in STAGE3_LAYOUTS:
        raise ValueError("%s is not a stage 3 layout: he never ruled on it here" % layout)
    repo = Path(repo or ir.REPO)
    heur, verd, ruled = ((repo / p).read_text() for p in (HEURISTICS, VERDICTS, RULED))
    denied = re.search(r'^\| %s \| deny \| Westley (\d{4}-\d\d-\d\d): "(.*)" \|$' % layout, verd, re.M)
    date = re.search(r"his words \((\d{4}-\d\d-\d\d)\)", heur).group(1)
    if denied:
        words, per_picture = denied.group(2), denied.group(2)
        date = denied.group(1)
    else:
        kind = _situation(layout, repo)
        row = next((line for line in heur.splitlines() if line.startswith("| ") and line.split("|")[1].strip().split(" (")[0] == kind), None)
        if row is None:
            raise ValueError("no row for %s (%s) in %s" % (layout, kind, HEURISTICS))
        words, per_picture = row.split("|")[-2].strip().strip('"'), NO_PICTURE
    stage = next(line for line in ruled.splitlines() if STAGE3_ROW in line)
    said = re.search(r'Westley (\d{4}-\d\d-\d\d): "([^"]*)"', stage)
    return {"words": words, "date": date, "per_picture": per_picture, "stage_approval": {"words": said.group(2), "date": said.group(1)}}


# ---------------------------------------------------------------- the layouts of arm F

def neutral_layout(layout):
    """Arm F's layout: every unit of both sides Vanguard at Vanguard's range, nothing else changed (the isolation is the feature against its twin). A new layout; the input is not changed;
    the id gets `-neutral` so a variant never wears the authored id."""
    out = deepcopy(layout)
    out["id"] = layout["id"] + "-neutral"
    for side in ("side_a", "side_b"):
        for u in out[side]["units"]:
            u["role"], u["range"] = "Vanguard", _roster_ranges()["Vanguard"]
    return out


# ---------------------------------------------------------------- readings over seeds

def same_or_changed(then, now):
    """`then` and `now` are {seed: winner}. `same` when every seed's winner is equal (DRAFT-same-or-changed-rule), else `changed`, `seeds_flipped` the number that differ. ValueError for unequal seed sets;
    a winner that starts `not measured` on either side gives a verdict that does too (two failures are not `same`)."""
    if set(then) != set(now):
        raise ValueError("the seeds differ: %s against %s" % (sorted(then), sorted(now)))
    if any(str(w).startswith(NOT_MEASURED) for w in list(then.values()) + list(now.values())):
        return {"verdict": NOT_MEASURED + ": a side did not produce a winner", "seeds_flipped": None, "rule": DRAFT_SAME_OR_CHANGED_RULE}
    flipped = sum(1 for s in then if then[s] != now[s])
    return {"verdict": "same" if flipped == 0 else "changed", "seeds_flipped": flipped, "rule": DRAFT_SAME_OR_CHANGED_RULE}


def first_differing_arm(readings):
    """`readings` is {arm: {version: reading}}. The first arm of ARM_ORDER whose `then` and `now` readings differ (the `fix` column is later); `none, the whole differs only at W` when that is W,
    `none` when none differs. ValueError for an arm outside ARM_ORDER."""
    for arm in readings:
        if arm not in ARM_ORDER:
            raise ValueError("arm must be one of %s, not %r" % (ARM_ORDER, arm))
    for arm in ARM_ORDER:
        if arm in readings and readings[arm].get("then") != readings[arm].get("now"):
            return "none, the whole differs only at W" if arm == "W" else arm
    return "none"


def measured_rate(winners, predict_rate):
    """The rate of side A over the seeds beside his `predict_rate` and the gap in points (rate.py's `band_gap`), shown and scored nowhere; a cap or a draw is not a win."""
    rate_a = sum(1 for w in winners if w == "A") / len(winners)
    return {"rate_a": rate_a, "predict_rate": predict_rate, "band_gap": abs(rate_a - predict_rate) * 100}


# ---------------------------------------------------------------- running

def _invalid(tree, version_name, doc):
    """The distinct rule ids of the fight file's `violations` (`[]` when valid); `not measured at <version>` when the version's tree has no rule checker, so the tree decides, not the file."""
    if not (tree / "scripts" / "skilllab" / "invariants.py").is_file():
        return "%s at %s" % (NOT_MEASURED, version_name)
    return sorted({v["rule"] for v in doc.get("violations", [])})


def _row(name, version, tree, arm, layout, variant, seed, path):
    """The row of a fight file (the LI1 keys, then variant, invalid, measures)."""
    doc = im.load_fight(path)
    res = doc["result"]
    return {"version": name, "lab_sha": version.sha, "arm": arm, "layout": layout, "seed": seed,
            "result": {"winner": res["winner"], "survivors": res["survivors"], "last_tick": res["ticks"], "end": res["end"]},
            "margin": res["survivors"][0] - res["survivors"][1], "units_firing": ir.units_firing(doc, name), "fight_path": str(path),
            "fight_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "error": None, "variant": variant,
            "invalid": _invalid(tree, name, doc), "measures": json.loads(json.dumps(im.measure_fight(doc)))}


def _error_row(name, sha, arm, layout, variant, seed, err):
    return {"version": name, "lab_sha": sha, "arm": arm, "layout": layout, "seed": seed, "result": None, "margin": None, "units_firing": None, "fight_path": None,
            "fight_sha256": None, "error": {"stage": err.stage, "message": err.args[0]}, "variant": variant, "invalid": None, "measures": None}


def _lab_pair(tree, arm, layout, seed, out):
    """(layout fight file, control twin fight file) of one lab run of the tree's own lab: arm W on the catalogue file, arm F on its neutral copy (written under the tree, so the fight file's
    `layout_path` is tree-relative); the twin made by the lab's `--control-dir` inside the tree and moved to `out`. BuildError (layout) when the lab refuses the layout or has none,
    (fight) for a twin that was not written."""
    layout_file = ir._layout_file(tree, layout)
    if arm == "F":
        with open(layout_file, "rb") as f:
            neutral = neutral_layout(tomllib.load(f))
        layout_file = tree / SCRATCH_DIRS[0] / (neutral["id"] + ".toml")
        layout_file.parent.mkdir(parents=True, exist_ok=True)
        layout_file.write_text(dump_toml(neutral))
    control_dir = tree / SCRATCH_DIRS[1] / arm
    twin = control_dir / ("%s-control-s%d.fight.json" % (layout_file.stem, seed))
    twin.unlink(missing_ok=True)
    path = ir._fight(tree, layout_file, seed, out, control_dir)
    if not twin.is_file():
        return path, ir.BuildError("fight", "the lab wrote no control twin fight file for %s (a layout with no feature has no twin)" % layout)
    kept = out / twin.name
    kept.unlink(missing_ok=True)
    shutil.move(str(twin), str(kept))
    return path, kept


def run_arms(versions, scratch_root, rows_path, *, arms=ARMS, layouts=STAGE3_LAYOUTS, seeds=DRAFT_SEEDS, refs=None, repo=None, out_dir=None):
    """The fights of arms F and W: one row per (version, arm, layout, variant, seed), nested in that order, `layout` before `control`. `rows_path` is rewritten, a line appended and flushed per run.
    A run that cannot run (a ref that is no commit, a layout the lab does not have, a build failure) is an error row, never an exception; an arm outside ARMS is a ValueError before any run."""
    bad = [a for a in arms if a not in ARMS]
    if bad:
        raise ValueError("arms of this piece are %s, not %s" % (ARMS, bad))
    repo, refs, scratch_root = repo or ir.REPO, refs or {}, Path(scratch_root)
    rows, built, pairs = [], {}, {}
    Path(rows_path).parent.mkdir(parents=True, exist_ok=True)
    with open(rows_path, "w") as f:
        for name in versions:
            for arm in arms:
                for layout in layouts:
                    for variant in VARIANTS:
                        for seed in seeds:
                            row = _one(name, arm, layout, variant, seed, refs, repo, scratch_root, out_dir, built, pairs)
                            rows.append(row)
                            f.write(json.dumps(row, sort_keys=True) + "\n")
                            f.flush()
    return rows


def _one(name, arm, layout, variant, seed, refs, repo, scratch_root, out_dir, built, pairs):
    version = None
    try:
        if name not in built:
            try:
                v = ir.resolve_version(name, refs.get(name), repo)
                built[name] = (v, ir.build_version(v, scratch_root, repo))
            except ir.BuildError as err:
                built[name] = err
        if isinstance(built[name], ir.BuildError):
            raise built[name]
        version, tree = built[name]
        key = (name, arm, layout, seed)
        if key not in pairs:
            out = Path(out_dir or scratch_root / "fights").resolve() / ("%s-%s-%s-%s" % (name, version.sha[:12], arm, layout))
            try:
                pairs[key] = _lab_pair(tree, arm, layout, seed, out)
            except ir.BuildError as err:
                pairs[key] = (err, err)
        got = pairs[key][variant == "control"]
        if isinstance(got, ir.BuildError):
            raise got
        return _row(name, version, tree, arm, layout, variant, seed, got)
    except ir.BuildError as err:
        return _error_row(name, version.sha if version else None, arm, layout, variant, seed, err)
    except (OSError, ValueError, KeyError, IndexError) as err:        # a fight file the lab wrote but this module cannot read: said, not skipped
        return _error_row(name, version.sha if version else None, arm, layout, variant, seed, ir.BuildError("fight", "%s: %s" % (type(err).__name__, err)))


# ---------------------------------------------------------------- cells and the comparison row

def _nm(row):
    err = row["error"]
    return "%s: %s: %s" % (NOT_MEASURED, err["stage"], (err["message"].splitlines() or [""])[0])


def cell(rows):
    """One (version, arm, layout, variant) over its seeds (the headline seed is DRAFT_SEEDS[0] when present). An error row gives `not measured: <stage>: <first line>` in every measured key."""
    head = next((r for r in rows if r["seed"] == DRAFT_SEEDS[0]), rows[0])
    winners = [[r["seed"], _nm(r) if r["error"] else r["measures"]["result"]["winner"]] for r in rows]
    out = {"version": head["version"], "lab_sha": head["lab_sha"], "seed": head["seed"], "winners": winners, "error": head["error"]}
    out["winner_counts"] = {}
    for _, w in winners:
        out["winner_counts"][w] = out["winner_counts"].get(w, 0) + 1
    if head["error"]:
        said = _nm(head)
        out.update(winner=said, survivors=said, last_tick=said, end=said, defect=said, invalid=said, units_firing=said, predictions={k: said for k in ("count", "type", "agreement")})
        return out
    m = head["measures"]
    out.update(winner=m["result"]["winner"], survivors=m["result"]["survivors"], last_tick=m["result"]["last_tick"], end=m["result"]["end"], defect=m["result"]["defect"],
               invalid=head["invalid"], units_firing=m["units_firing"], predictions={k: m["predictions"][k] for k in ("count", "type", "agreement")})
    return out


def comparison_rows(rows, repo=None):
    """One comparison row per stage 3 layout present in `rows` (arms F and W), in STAGE3_LAYOUTS order (spec section 5): his ruling, the approved expected winner, the then, now and fix cells of the layout
    and its control twin, arm F's cells, whether each matches, the rate beside predict_rate, same or changed by the named rule, the first differing arm. A version with no rows is `not run`."""
    repo = Path(repo or ir.REPO)
    ok = approved(repo)
    out = []
    for layout in STAGE3_LAYOUTS:
        mine = [r for r in rows if r["layout"] == layout]
        if not mine:
            continue
        cells = {}
        for arm in ARMS:
            for variant in VARIANTS:
                for version in ("then", "now", "fix"):
                    pick = [r for r in mine if (r["arm"], r["variant"], r["version"]) == (arm, variant, version)]
                    cells[arm, variant, version] = cell(pick) if pick else NOT_RUN
        expected, rate = ok[layout]["expected_winner"], ok[layout]["predict_rate"]
        row = {"layout": layout, "kind": _situation(layout, repo), "ruling": ruling(layout, repo), "expected_winner": expected, "predict_rate": rate, "rule": DRAFT_SAME_OR_CHANGED_RULE,
               "control": {}, "f": {}, "matches_expected": {}, "rate": {}}
        readings = {"W": {}, "F": {}}
        for v in ("then", "now", "fix"):
            w, wc, fl, fc = cells["W", "layout", v], cells["W", "control", v], cells["F", "layout", v], cells["F", "control", v]
            row[v], row["control"][v] = w, wc
            row["f"][v] = NOT_RUN if NOT_RUN in (fl, fc) else {"layout": fl, "control": fc, "same_winner": fl["winner"] == fc["winner"]}
            if w == NOT_RUN:
                row["matches_expected"][v] = row["rate"][v] = NOT_RUN
                continue
            seeds = [x for _, x in w["winners"]]
            nm = next((x for x in seeds if x.startswith(NOT_MEASURED)), None)
            row["matches_expected"][v] = w["winner"] if w["winner"].startswith(NOT_MEASURED) else "n/a" if w["defect"] else w["winner"] == expected
            row["rate"][v] = nm or measured_rate(seeds, rate)
            readings["W"][v] = seeds
            if row["f"][v] != NOT_RUN:
                readings["F"][v] = {"layout": [x for _, x in fl["winners"]], "control": [x for _, x in fc["winners"]]}
        both = row["then"] != NOT_RUN and row["now"] != NOT_RUN
        change = same_or_changed(dict(row["then"]["winners"]), dict(row["now"]["winners"])) if both else {"verdict": NOT_RUN, "seeds_flipped": None}
        row["same_or_changed"], row["seeds_flipped"] = change["verdict"], change["seeds_flipped"]
        readings = {a: r for a, r in readings.items() if r}
        row["arm_readings"] = readings
        row["first_differing_arm"] = first_differing_arm({a: r for a, r in readings.items() if "then" in r and "now" in r}) if both else NOT_RUN
        out.append(row)
    return out
