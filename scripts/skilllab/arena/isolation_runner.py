"""LI1, the version runner of the lab-isolation measurement (docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7; interface: docs/reports/2026-11-24-li1-interface.md).

Builds a version of the repository from `git archive` into a scratch root (cached by sha, never checked out, the repository is only read), runs that version's own lab
(`python -m scripts.skilllab.arena.run`, the one order a side the lab gives) on a layout and seed, and writes one JSONL row per run keyed by (version, lab sha, arm, layout, seed).
Versions: `then` = THEN_SHA (stage 3 approval), `now` = origin/main of the repository, `fix` = a given ref. A run that cannot run is an error row (stage resolve, archive, build, layout,
fight), never a skip and never an exception out of `run_matrix`. The runner starts no memory cap of its own: start it under the cap the work's rules name (spec section 7).
Tests: tests/skilllab/integration/test_isolation_runner_*.py."""
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parents[3]
THEN_SHA = "4fa618ce78349fcc077ce552753131e737ae2cea"   # stage 3 approval, 2026-11-05 (spec section 2)
LD = "docs/northstar/research/layer_dynamics"
ARCHIVED = ("csrc", "Makefile", "scripts", LD + "/catalogue", LD + "/situations")
OPTIONAL = (LD + "/arena/approved.toml",)               # archived when the version has it
TAIL = 2000                                             # characters of a failing tool's output kept in an error message
STAGES = ("resolve", "archive", "build", "layout", "fight")


class Version(NamedTuple):
    name: str
    sha: str


class BuildError(Exception):
    """A run step that failed; `stage` is one of STAGES, `.args[0]` the reason."""

    def __init__(self, stage, message):
        super().__init__(message or "no output")
        self.stage = stage


def _git(repo, *args):
    return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args], capture_output=True)


def _tail(*texts):
    text = "\n".join(t.decode(errors="replace") if isinstance(t, bytes) else t for t in texts if t).strip()
    return text[-TAIL:]


def resolve_version(name, ref=None, repo=None):
    """`then` is THEN_SHA; `now` is origin/main of `repo`; `fix` is `ref` (branch or sha) made a full sha. ValueError for another name or `fix` without a ref; BuildError (resolve) for a ref that is no commit."""
    repo = repo or REPO
    if name == "then":
        return Version(name, THEN_SHA)
    if name == "now":
        ref = "origin/main"
    elif name != "fix":
        raise ValueError("version must be then, now or fix, not %r" % (name,))
    elif not ref:
        raise ValueError("version fix needs a branch or sha")
    done = _git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    if done.returncode != 0:
        raise BuildError("resolve", "%s is not a commit of %s" % (ref, repo))
    return Version(name, done.stdout.decode().strip())


def build_version(version, scratch_root, repo=None):
    """The tree of `version.sha` under `scratch_root/tree-<sha>` with `libouroboros.so` built by `make`; a tree already built is returned as it is (the sha is the cache key, not the name).
    The build runs in a scratch directory renamed into place on success, so a failed build leaves nothing that looks built."""
    repo, scratch_root = repo or REPO, Path(scratch_root)
    tree = scratch_root / ("tree-" + version.sha)
    if (tree / "libouroboros.so").is_file():
        return tree
    paths = list(ARCHIVED) + [p for p in OPTIONAL if _git(repo, "cat-file", "-e", "%s:%s" % (version.sha, p)).returncode == 0]
    done = _git(repo, "archive", "--format=tar", version.sha, "--", *paths)
    if done.returncode != 0:
        raise BuildError("archive", _tail(done.stderr) or "git archive %s failed" % version.sha)
    work = scratch_root / (".building-" + version.sha)
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
            tar.extractall(work, filter="data")
        made = subprocess.run(["make", "libouroboros.so"], cwd=str(work), capture_output=True, text=True)
        if made.returncode != 0 or not (work / "libouroboros.so").is_file():
            raise BuildError("build", _tail(made.stderr, made.stdout) or "make libouroboros.so failed")
        shutil.rmtree(tree, ignore_errors=True)
        work.rename(tree)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return tree


def _layout_file(tree, layout):
    """The layout file in `tree` for a catalogue id (L-0047) or a situation id (SIT-0106, converted by the tree's own converter into the tree, so the fight file names it relative to the tree)."""
    catalogue = tree / LD / "catalogue"
    if re.fullmatch(r"L-\d{4}", layout):
        path = catalogue / (layout + ".toml")
        if not path.is_file():
            raise BuildError("layout", "unknown layout %s" % layout)
        return path
    if not re.fullmatch(r"SIT-\d{4}", layout):
        raise BuildError("layout", "unknown layout %s (an L-#### or SIT-#### id)" % layout)
    out = tree / LD / "converted"
    path = out / ("L-%s.toml" % layout[4:])
    if path.is_file():
        return path
    sources = sorted((tree / LD / "situations").glob(layout + "-*.md"))
    if not sources:
        raise BuildError("layout", "unknown situation %s" % layout)
    src = tree / ".situation"
    shutil.rmtree(src, ignore_errors=True)
    src.mkdir()
    try:
        shutil.copy(sources[0], src)
        done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.situations", "--dir", str(src), "--out", str(out), "--next-id", "L-" + layout[4:]],
                              cwd=str(tree), capture_output=True, text=True)
    finally:
        shutil.rmtree(src, ignore_errors=True)
    if done.returncode != 0 or not path.is_file():
        raise BuildError("layout", _tail(done.stdout, done.stderr) or "%s did not convert" % layout)
    return path


def units_firing(doc, version_name):
    """{"by_frame": [[tick, A units that fired, B units that fired], ...], "peak": [max A, max B]} from the per-unit `fired` flag of a fight document; the string
    `not measured at <version_name>` when the fight file has none (the lab of `then` does not write it)."""
    if not any("fired" in u for f in doc["frames"] for u in f["units"]):
        return "not measured at %s" % version_name
    by_frame = [[f["tick"]] + [sum(1 for u in f["units"] if u["side"] == s and u.get("fired")) for s in "AB"] for f in doc["frames"]]
    return {"by_frame": by_frame, "peak": [max(r[1] for r in by_frame), max(r[2] for r in by_frame)]}


def row_key(row):
    return (row["version"], row["lab_sha"], row["arm"], row["layout"], row["seed"])


def _fight(tree, layout_file, seed, out):
    """Run the tree's own lab once; the path of the fight file. Exit 2 with no fight file is the lab's REJECT of the layout; exit 2 with the file is a fight the rule checker marked invalid, not an error (the file says so)."""
    path = out / ("%s-s%d.fight.json" % (layout_file.stem, seed))
    path.unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.run", "--layout", str(layout_file), "--seed", str(seed), "--out", str(out)],
                          cwd=str(tree), capture_output=True, text=True)
    if done.returncode == 2 and not path.is_file():      # REJECT: the lab refused the layout and wrote nothing; an INVALID fight (exit 2) wrote its file, which carries `invalid` and `violations`
        raise BuildError("layout", _tail(done.stdout, done.stderr))
    if not path.is_file():
        raise BuildError("fight", _tail(done.stderr, done.stdout) or "the lab wrote no fight file (exit %d)" % done.returncode)
    return path


def run_one(name, layout, seed, scratch_root, *, arm="W", ref=None, repo=None, out_dir=None):
    """One row (see the interface report). A run that fails is an error row: result, margin, units_firing, fight_path and fight_sha256 null, `error` {stage, message}."""
    repo, scratch_root = repo or REPO, Path(scratch_root)
    row = {"version": name, "lab_sha": None, "arm": arm, "layout": layout, "seed": seed, "result": None, "margin": None, "units_firing": None,
           "fight_path": None, "fight_sha256": None, "error": None}
    try:
        version = resolve_version(name, ref, repo)
        row["lab_sha"] = version.sha
        tree = build_version(version, scratch_root, repo)
        out = Path(out_dir or scratch_root / "fights").resolve() / ("%s-%s-%s-%s" % (name, version.sha[:12], arm, layout))
        path = _fight(tree, _layout_file(tree, layout), seed, out)
        doc = json.loads(path.read_text())
        res = doc["result"]
        row["result"] = {"winner": res["winner"], "survivors": res["survivors"], "last_tick": res["ticks"], "end": res["end"]}
        row["margin"] = res["survivors"][0] - res["survivors"][1]
        row["units_firing"] = units_firing(doc, name)
        row["fight_path"] = str(path)
        row["fight_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    except BuildError as err:
        row.update(result=None, margin=None, units_firing=None, fight_path=None, fight_sha256=None, error={"stage": err.stage, "message": err.args[0]})
    except (OSError, ValueError, KeyError, IndexError) as err:        # a fight file the lab wrote but this runner cannot read: said, not skipped
        row.update(result=None, margin=None, units_firing=None, fight_path=None, fight_sha256=None, error={"stage": "fight", "message": "%s: %s" % (type(err).__name__, err)})
    return row


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))


def run_matrix(names, layouts, seeds, scratch_root, rows_path, *, arm="W", refs=None, repo=None, out_dir=None):
    """Every (name, layout, seed), nested in that order; `rows_path` is rewritten and a line appended and flushed per run, so a kill loses one run. Returns the rows."""
    refs = refs or {}
    rows = []
    Path(rows_path).parent.mkdir(parents=True, exist_ok=True)
    with open(rows_path, "w") as f:
        for name in names:
            for layout in layouts:
                for seed in seeds:
                    rows.append(run_one(name, layout, seed, scratch_root, arm=arm, ref=refs.get(name), repo=repo, out_dir=out_dir))
                    f.write(json.dumps(rows[-1], sort_keys=True) + "\n")
                    f.flush()
    return rows


def main(argv=None):
    """CLI wiring (LI1 interface): exit 0 when every row is ok, 1 when any row is an error row; the rows are written either way."""
    import argparse
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.isolation_runner")
    ap.add_argument("--version", required=True, choices=("then", "now", "fix"))
    ap.add_argument("--ref")
    ap.add_argument("--layout", required=True, help="a catalogue id (L-0047) or a situation id (SIT-0106)")
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--arm", default="W")
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    if args.version == "fix" and not args.ref:
        ap.error("--version fix needs --ref")
    rows = run_matrix([args.version], [args.layout], [args.seed], args.scratch, args.rows, arm=args.arm, refs={args.version: args.ref}, repo=args.repo, out_dir=args.out)
    for row in rows:
        err = row["error"]
        print("%s %s %s seed %d %s" % (row["version"], row["lab_sha"], row["layout"], row["seed"], "ERROR %s: %s" % (err["stage"], err["message"]) if err else "ok"))
    return 1 if any(r["error"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
