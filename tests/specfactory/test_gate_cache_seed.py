"""HARNESS-gate-cache-seed (lane H) with spec Amendment A15: the merge gate's regression stages key
their baseline cache on each suite's INPUT HASH, skip a stage whose inputs did not change, and seed
the cache from the candidate's own run once it is pushed.

Sources: docs/northstar/plans/2026-10-07-visible-game-spec.md line 450 (the piece paragraph),
docs/northstar/plans/method_rev3_2026-10-26/spec.md (Amendment A15), briefs/gate_cache_seed_amendment.md.

INTERFACES SHARED BY THE BUILDER AND THESE TESTS (fixed in full; the tests are the contract)

1. scripts/specfactory/suite_inputs.toml (written by the builder from one strace run per suite):

       [suites."tests/csim"]                  # the key is the suite_key of regression_check:
       paths = ["csrc", "tests/csim", ...]    #   " ".join(test_args), WITHOUT the MALLOC_PERTURB_ suffix
                                              # paths: repo-relative files or directories, git-tracked,
                                              #   listed in the order that is hashed.
   regression_check reads <candidate_dir>/scripts/specfactory/suite_inputs.toml. A suite_key with no
   [suites."<key>"] table (or no file) keeps today's behaviour exactly: cache keyed on the base sha,
   no skip, no candidate_results beyond item 3. The toml's own path is not hashed. The shipped file
   declares at least tests/csim, tests/qa/t1, tests/specfactory, tests/transport.

2. Input hash of a revision: for each declared path p, in declared order, t = the output of
   `git rev-parse <rev>:<p>` run in candidate_dir (the string "-" when that fails, i.e. the path is
   absent at <rev>); text = "".join(f"{p}={t}\\n"); input_hash = sha256(text).hexdigest()[:16].
   The base side uses rev = base_ref, the candidate side rev = HEAD of candidate_dir. Only committed
   state counts. Helper `input_hash()` below is the reference implementation.

3. File layout. All under merge_root unless MERGE_GATE_BASELINE_CACHE is set (it moves only
   baseline_cache/). Both file kinds have the same JSON shape as today's baseline cache file:
       {"main_sha": "<sha the file is named for>", "harness_sha": "<mgs._harness_sha()>",
        "suites": {"<suite_key incl. MALLOC_PERTURB_ suffix when set>": {passed, failed, failing_ids,
                   returncode, first_assertion, skipped, xfailed, scale_gated, "input_hash": "<item 2>"}}}
   - baseline_cache/<sha>.json   written ONLY by a base run (a computed baseline), never by a candidate run.
     `input_hash` is the hash of that base's tree. Suites with a toml table are looked up by
     (harness_sha, suite_key, input_hash) across every *.json in baseline_cache/; suites without a
     table are looked up by file name <base sha>.json as today.
   - candidate_results/<candidate HEAD sha>.json   written by regression_check after the candidate run,
     for every suite_key (declared or not) when merge_root is given: the candidate's `after` RunResult,
     first_assertion normalised with _normalize_worktree_paths. For a declared suite the entry carries the
     candidate's input_hash. Ids that flake_rerun cleared (the `flaky` list) are removed from failing_ids
     and `failed` drops by their count. A skipped stage (item 5) writes no entry.

4. Subcommand: `merge_gate_support.py seed-cache <candidate_dir> --merge-root <root>`. In candidate_dir,
   sha = `git rev-parse HEAD`, main = `git rev-parse origin/main`. When equal and
   candidate_results/<sha>.json exists, copy it byte for byte to the baseline cache path of that sha
   (_baseline_cache_path) and print `seed-cache: seeded <n> suites from <gated> for <HEAD>` (H-016; was `seed-cache: seeded <sha>`). Otherwise copy nothing and print
   `seed-cache: skipped <reason>` (reason is free text). Exit code 0 in both cases.

5. Output lines of `merge_gate_support.py regression <cand> <base_ref> <suite> --merge-root <root>`:
       baseline: cached <main_sha>      a hit (main_sha = base_ref resolved; the entry may come from another
                                        sha's file when the input hash matches)
       baseline: computed <main_sha>    a miss; the base ran
       OK inputs unchanged <input_hash> the last line when the candidate's input hash equals the base's:
                                        no pytest process runs at all, base or candidate; exit 0
   The cache key's other half is mgs._harness_sha() (content of suite_regression.py next to
   merge_gate_support.py): a different harness sha never reads another's entry.

6. Library function in merge_gate_support.py, the coverage control of A15:
       undeclared_opens(strace_text: str, repo_root: Path, declared: list[str]) -> list[str]
   parses `openat(...)` / `execve(...)` lines of an `strace -f -e trace=openat,execve` log, keeps calls that
   succeeded (return value >= 0; for execve the first quoted argument), resolves the quoted path
   (relative to repo_root when not absolute), and returns the sorted repo-relative paths that are tracked
   by git in repo_root (`git ls-files`) and lie neither equal to nor under any declared path. Untracked and
   out-of-repo files are ignored.

7. rules.md section (b), Push bullet, gains the sentence
   "after the push run `merge_gate_support.py seed-cache <worktree> --merge-root ~/Projects/om-push/merge` (HARNESS-gate-cache-seed)".

Each case names its spec item (P = the piece paragraph, A15 = the amendment). Cases that are positive
controls are marked CONTROL; they pair with a case that is red on origin/main for the stated reason.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SPECFACTORY = REPO / "scripts" / "specfactory"
SUPPORT = SPECFACTORY / "merge_gate_support.py"
sys.path.insert(0, str(SPECFACTORY))

import merge_gate_support as mgs  # noqa: E402
import suite_regression as sr  # noqa: E402

PY = sys.executable
SUITE = "tests/t"
DECLARED = ["tests/t", "src"]
TOML = (
    f'[suites."{SUITE}"]\n'
    'paths = ["tests/t", "src"]\n'
)
TOML_REL = "scripts/specfactory/suite_inputs.toml"


# ------------------------------------------------------------------ fixture helpers

def _git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def input_hash(repo: Path, rev: str, paths: list[str]) -> str:
    """Reference implementation of interface item 2."""
    text = ""
    for p in paths:
        r = _git(repo, "rev-parse", f"{rev}:{p}", check=False)
        text += f"{p}={r.stdout.strip() if r.returncode == 0 else '-'}\n"
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _commit(repo: Path, msg: str, files: dict | None = None) -> str:
    for rel, text in (files or {}).items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _env(extra=None):
    e = {k: v for k, v in os.environ.items() if k not in ("MERGE_GATE_BASELINE_CACHE", "MALLOC_PERTURB_")}
    e.update(extra or {})
    return e


def _fixture(tmp_path: Path):
    """Main commit M: a one-test suite that appends a line to MARK every time pytest runs it, a
    declared source dir, an undeclared docs dir, and the toml. Returns (repo, M, marker path)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "g@t")
    _git(repo, "config", "user.name", "g")
    mark = tmp_path / "ran.txt"
    test = (f"def test_a():\n    open({str(mark)!r}, 'a').write('ran\\n')\n    assert True\n")
    m = _commit(repo, "main", {"tests/t/test_a.py": test, "src/mod.py": "X = 1\n",
                               "docs/README.md": "r0\n", TOML_REL: TOML})
    return repo, m, mark


def _runs(mark: Path) -> int:
    return len(mark.read_text().splitlines()) if mark.exists() else 0


def _stage(repo, base_ref, root, harness: Path | None = None, extra_env=None, suite=SUITE):
    """One `regression` stage as merge_gate.sh invokes it (junit off, as the existing cache tests do)."""
    support = (harness or SPECFACTORY) / "merge_gate_support.py"
    return subprocess.run([PY, str(support), "regression", str(repo), base_ref, suite, "--python", PY,
                           "--no-junit", "--merge-root", str(root)],
                          capture_output=True, text=True, env=_env(extra_env), timeout=300)


def _seed(repo, root, *extra):
    return subprocess.run([PY, str(SUPPORT), "seed-cache", str(repo), "--merge-root", str(root), *extra],
                          capture_output=True, text=True, env=_env(), timeout=120)


def _cache_files(root: Path, kind: str) -> list[str]:
    d = Path(root) / kind
    return sorted(p.name for p in d.glob("*.json")) if d.exists() else []


def _last(r) -> str:
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


# ------------------------------------------------------------------ P: candidate_results and seeding

def test_P_candidate_run_writes_candidate_results_and_base_run_alone_writes_baseline_cache(tmp_path):
    """P: regression_check writes the candidate's `after` entry to candidate_results/<HEAD sha>.json
    (item 3). CONTROL half: baseline_cache/ gets only the BASE sha's file, never the candidate's."""
    repo, m, _mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    r = _stage(repo, m, root)
    assert r.returncode == 0 and "baseline: computed" in r.stdout, r.stdout + r.stderr
    assert _cache_files(root, "candidate_results") == [f"{x}.json"], "candidate_results/<candidate sha>.json not written"
    assert _cache_files(root, "baseline_cache") == [f"{m}.json"], "only a base run may write baseline_cache"
    data = json.loads((root / "candidate_results" / f"{x}.json").read_text())
    entry = data["suites"][SUITE]
    assert data["harness_sha"] == mgs._harness_sha() and data["main_sha"] == x
    assert entry["input_hash"] == input_hash(repo, x, DECLARED)
    for key in ("passed", "failed", "failing_ids", "returncode", "first_assertion", "skipped", "xfailed", "scale_gated"):
        assert key in entry, key


def test_P_candidate_results_written_for_a_suite_without_a_toml_table(tmp_path):
    """P (item 1): an undeclared suite_key keeps the legacy sha-keyed path but still writes candidate_results."""
    repo, m, _mark = _fixture(tmp_path)
    (repo / TOML_REL).write_text("")
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    r = _stage(repo, m, root)
    assert r.returncode == 0 and f"baseline: computed {m}" in r.stdout, r.stdout + r.stderr
    assert _cache_files(root, "candidate_results") == [f"{x}.json"]
    assert "input_hash" not in json.loads((root / "candidate_results" / f"{x}.json").read_text())["suites"][SUITE]
    assert f"baseline: cached {m}" in _stage(repo, m, root).stdout, "legacy sha-keyed hit must survive"


def test_P_flaky_id_is_removed_from_the_stored_candidate_entry(tmp_path, monkeypatch):
    """P: before candidate_results is written, ids in `flaky` leave failing_ids and `failed` drops by their count."""
    repo, m, _mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    old, flake = "t.py::test_old_red", "t.py::test_flake"
    cand_dir = repo.resolve()

    def fake_run(cwd, python_exe=None, test_args=None, timeout=0, extra_args=None, junit_path=None):
        if Path(cwd).resolve() == cand_dir:
            return sr.RunResult(passed=1, failed=2, failing_ids=(old, flake), wall_s=0.0, returncode=1)
        return sr.RunResult(passed=2, failed=1, failing_ids=(old,), wall_s=0.0, returncode=1)

    monkeypatch.setattr(mgs.sr, "run_pytest", fake_run)
    monkeypatch.setattr(mgs, "flake_rerun", lambda *a, **k: (a[1] == flake or k.get("test_id") == flake, "x"))
    ok, detail, _rep = mgs.regression_check(repo, m, [SUITE], python_exe=PY, junit=False,
                                            merge_root=tmp_path / "root", worktree_root=tmp_path)
    assert ok and "flake" in detail, detail
    entry = json.loads((tmp_path / "root" / "candidate_results" / f"{x}.json").read_text())["suites"][SUITE]
    assert entry["failing_ids"] == [old], entry
    assert entry["failed"] == 1, entry


def test_P_seed_cache_copies_candidate_results_when_origin_main_equals_the_gated_sha(tmp_path):
    """P (item 4): after the push origin/main == gated HEAD -> candidate_results copied to baseline_cache/<sha>.json."""
    repo, m, _mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    assert _stage(repo, m, root).returncode == 0
    _git(repo, "update-ref", "refs/remotes/origin/main", x)
    r = _seed(repo, root)
    assert r.returncode == 0 and f"seed-cache: seeded 1 suites from {x} for {x}" in r.stdout, r.stdout + r.stderr
    assert (root / "baseline_cache" / f"{x}.json").read_bytes() == (root / "candidate_results" / f"{x}.json").read_bytes()


def test_P_negative_control_origin_main_moved_by_a_docs_commit_seeds_nothing(tmp_path):
    """P negative control: origin/main is one docs commit past the gated sha -> nothing is seeded, exit 0.
    TD-HARNESS-gate-tiers-2 (layered gate spec section 8 F8, HARNESS-gate-tiers): the next landing's base (that docs
    commit) is a HIT through candidate_results/, because the gated sha is an ancestor of origin/main and its rc is 0.
    CONTROL half: a candidate_results entry whose sha is NOT an ancestor of origin/main (an unlanded branch) is
    never read: `baseline: computed`."""
    repo, m, _mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    assert _stage(repo, m, root).returncode == 0
    _git(repo, "checkout", "-q", "-b", "records")
    rec = _commit(repo, "records", {"docs/README.md": "r1\n"})
    _git(repo, "update-ref", "refs/remotes/origin/main", rec)
    _git(repo, "checkout", "-q", "--detach", x)
    r = _seed(repo, root)
    assert r.returncode == 0 and "seed-cache: skipped" in r.stdout, r.stdout + r.stderr
    assert f"{x}.json" not in _cache_files(root, "baseline_cache"), "a moved origin/main must seed nothing"
    _git(repo, "checkout", "-q", "records")
    y = _commit(repo, "next landing", {"src/mod.py": "X = 3\n"})
    nxt = _stage(repo, rec, root)
    assert f"baseline: cached {rec}" in nxt.stdout, nxt.stdout + nxt.stderr
    assert y != x
    # CONTROL: the same scene, but the gated sha sits on an unlanded branch that origin/main does not contain.
    (tmp_path / "unlanded").mkdir()
    repo2, m2, _mark2 = _fixture(tmp_path / "unlanded")
    _git(repo2, "checkout", "-q", "-b", "other")
    other = _commit(repo2, "other line", {"docs/README.md": "other\n"})
    _git(repo2, "checkout", "-q", "-b", "cand", m2)
    x2 = _commit(repo2, "edit src", {"src/mod.py": "X = 2\n"})
    root2 = tmp_path / "root2"
    assert _stage(repo2, m2, root2).returncode == 0
    assert _cache_files(root2, "candidate_results") == [f"{x2}.json"]
    _git(repo2, "update-ref", "refs/remotes/origin/main", other)
    base2 = _commit(repo2, "records on the candidate line", {"docs/README.md": "r1\n"})
    _commit(repo2, "next landing", {"src/mod.py": "X = 3\n"})
    ctl = _stage(repo2, base2, root2)
    assert f"baseline: computed {base2}" in ctl.stdout, ctl.stdout + ctl.stderr


def test_P_fixture_gate_run_seeds_the_cache_and_the_next_run_reads_it(tmp_path):
    """P: gate run on X seeds; the next landing, gated against X, reads the seeded entry."""
    repo, m, mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    assert _stage(repo, m, root).returncode == 0
    _git(repo, "update-ref", "refs/remotes/origin/main", x)
    assert f"seed-cache: seeded 1 suites from {x} for {x}" in _seed(repo, root).stdout
    before = _runs(mark)
    _commit(repo, "next landing", {"src/mod.py": "X = 3\n"})
    nxt = _stage(repo, x, root)
    assert nxt.returncode == 0 and f"baseline: cached {x}" in nxt.stdout, nxt.stdout + nxt.stderr
    assert _runs(mark) - before == 1, "a cached base must leave only the candidate run"


def test_A15_records_commit_between_gate_and_next_landing_still_hits_the_seeded_cache(tmp_path):
    """A15 (the hole the paragraph states): X is seeded, a docs-only records commit R lands on top, the next
    landing is gated against R. R's declared inputs equal X's, so the entry seeded under X's sha is a hit."""
    repo, m, mark = _fixture(tmp_path)
    x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    root = tmp_path / "root"
    assert _stage(repo, m, root).returncode == 0
    _git(repo, "update-ref", "refs/remotes/origin/main", x)
    assert f"seed-cache: seeded 1 suites from {x} for {x}" in _seed(repo, root).stdout
    rec = _commit(repo, "records", {"docs/README.md": "r1\n"})
    before = _runs(mark)
    _commit(repo, "next landing", {"src/mod.py": "X = 3\n"})
    nxt = _stage(repo, rec, root)
    assert nxt.returncode == 0 and f"baseline: cached {rec}" in nxt.stdout, nxt.stdout + nxt.stderr
    assert _runs(mark) - before == 1


# ------------------------------------------------------------------ H-016: seed from the gated sha (issue 7)
# Spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 9 issue 7 (HARNESS-gate-cache-seed).
# Tests, word for word: "seeding from a `--no-ff` merge commit whose second parent has a candidate_results file
# prints the seeded line and `baseline_cache/<HEAD>.json` exists with n suite keys (e); a seed whose gated sha is
# not an ancestor of origin/main seeds nothing and prints the skipped line (negative control, the F8 rule); an
# input change between seed and gate prints `baseline: computed` for that suite only (g; positive control that the
# hash still guards, run with candidate_results removed so the fallback cannot mask it)."

SUITE2 = "tests/u"
TOML2 = TOML + f'[suites."{SUITE2}"]\npaths = ["tests/u", "lib"]\n'


def _two_suite_base(tmp_path: Path):
    """The _fixture main plus a second declared suite (tests/u reading lib): returns (repo, base sha)."""
    repo, _m, _mark = _fixture(tmp_path)
    base = _commit(repo, "second suite", {"tests/u/test_b.py": "def test_b():\n    assert True\n",
                                          "lib/mod.py": "Y = 1\n", TOML_REL: TOML2})
    return repo, base


def _gated_candidate(tmp_path: Path):
    """A candidate x on branch `cand` (edits src and lib), both suites gated so candidate_results/<x>.json holds
    two suite keys. Leaves HEAD on `cand`. Returns (repo, base, x, root)."""
    repo, base = _two_suite_base(tmp_path)
    _git(repo, "checkout", "-q", "-b", "cand")
    x = _commit(repo, "edit src and lib", {"src/mod.py": "X = 2\n", "lib/mod.py": "Y = 2\n"})
    root = tmp_path / "root"
    for suite in (SUITE, SUITE2):
        r = _stage(repo, base, root, suite=suite)
        assert r.returncode == 0, r.stdout + r.stderr
    got = json.loads((root / "candidate_results" / f"{x}.json").read_text())
    assert sorted(got["suites"]) == [SUITE, SUITE2], "premise: candidate_results/<gated>.json holds both suites"
    return repo, base, x, root


def _land_noff(tmp_path: Path):
    """_gated_candidate, then `git merge --no-ff cand` into main and origin/main = the merge commit H.
    Returns (repo, base, x, h, root); HEAD is H, its second parent is x."""
    repo, base, x, root = _gated_candidate(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "land cand", "cand")
    h = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert _git(repo, "rev-parse", "HEAD^2").stdout.strip() == x and h != x, "premise: H is a --no-ff merge of x"
    _git(repo, "update-ref", "refs/remotes/origin/main", h)
    return repo, base, x, h, root


def test_H016_e_seed_after_a_noff_merge_reads_the_second_parent(tmp_path):
    """H-016 (e): "seeding from a `--no-ff` merge commit whose second parent has a candidate_results file prints
    the seeded line and `baseline_cache/<HEAD>.json` exists with n suite keys". No --gated given: for a merge HEAD
    the gated sha is the second parent. Line proved: `seed-cache: seeded <n> suites from <gated> for <HEAD>`."""
    repo, _base, x, h, root = _land_noff(tmp_path)
    assert f"{h}.json" not in _cache_files(root, "baseline_cache"), "premise: nothing seeded yet"
    r = _seed(repo, root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"seed-cache: seeded 2 suites from {x} for {h}" in r.stdout.splitlines(), r.stdout + r.stderr
    dst = root / "baseline_cache" / f"{h}.json"
    assert dst.exists(), "baseline_cache/<HEAD>.json not written"
    assert sorted(json.loads(dst.read_text())["suites"]) == [SUITE, SUITE2]


def test_H016_gated_flag_names_the_sha_when_head_is_not_the_merge(tmp_path):
    """H-016: "`seed-cache --gated <sha>`; absent, the second parent of a merge HEAD, else HEAD". A records commit
    R sits on the merge H, origin/main == R; `--gated <x>` seeds baseline_cache/<R>.json from candidate_results/<x>.
    CONTROL half: without --gated, HEAD R is not a merge and has no candidate_results, so nothing is seeded."""
    repo, _base, x, h, root = _land_noff(tmp_path)
    rec = _commit(repo, "records", {"docs/README.md": "r1\n"})
    _git(repo, "update-ref", "refs/remotes/origin/main", rec)
    plain = _seed(repo, root)
    assert plain.returncode == 0 and plain.stdout.startswith("seed-cache: skipped"), plain.stdout + plain.stderr
    assert f"{rec}.json" not in _cache_files(root, "baseline_cache")
    r = _seed(repo, root, "--gated", x)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"seed-cache: seeded 2 suites from {x} for {rec}" in r.stdout.splitlines(), r.stdout + r.stderr
    assert (root / "baseline_cache" / f"{rec}.json").exists()


def test_H016_control_the_origin_main_equals_head_guard_stays(tmp_path):
    """H-016: "the `origin/main == HEAD` guard stays". CONTROL, green today: origin/main is one commit past the
    merge H -> nothing is seeded, exit 0, and the line starts `seed-cache: skipped`."""
    repo, _base, _x, h, root = _land_noff(tmp_path)
    ahead = _commit(repo, "records", {"docs/README.md": "r1\n"})
    _git(repo, "update-ref", "refs/remotes/origin/main", ahead)
    _git(repo, "checkout", "-q", "--detach", h)
    r = _seed(repo, root)
    assert r.returncode == 0 and r.stdout.startswith("seed-cache: skipped"), r.stdout + r.stderr
    assert f"{h}.json" not in _cache_files(root, "baseline_cache")


def test_H016_guard_also_holds_when_gated_is_given(tmp_path):
    """H-016: "the `origin/main == HEAD` guard stays" with --gated <x> (an ancestor) but origin/main past HEAD:
    nothing is seeded and the line starts `seed-cache: skipped`."""
    repo, _base, x, h, root = _land_noff(tmp_path)
    ahead = _commit(repo, "records", {"docs/README.md": "r1\n"})
    _git(repo, "update-ref", "refs/remotes/origin/main", ahead)
    _git(repo, "checkout", "-q", "--detach", h)
    r = _seed(repo, root, "--gated", x)
    assert r.returncode == 0 and r.stdout.startswith("seed-cache: skipped"), r.stdout + r.stderr
    assert f"{h}.json" not in _cache_files(root, "baseline_cache")


def test_H016_negative_control_gated_sha_not_an_ancestor_of_origin_main_seeds_nothing(tmp_path):
    """H-016 negative control (F8 rule): "a seed whose gated sha is not an ancestor of origin/main seeds nothing and
    prints the skipped line" -> `seed-cache: skipped gated <gated> is not an ancestor of origin/main`, exit 0.
    The candidate_results file for the gated sha exists and holds both suites, so only the ancestry blocks it.
    CONTROL half: test_H016_e_* seeds from the same kind of scene when the gated sha is an ancestor."""
    repo, _base, x, root = _gated_candidate(tmp_path)
    _git(repo, "checkout", "-q", "main")
    other = _commit(repo, "main moves without the candidate", {"docs/README.md": "other\n"})
    _git(repo, "update-ref", "refs/remotes/origin/main", other)
    assert _git(repo, "merge-base", "--is-ancestor", x, "origin/main", check=False).returncode != 0
    r = _seed(repo, root, "--gated", x)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"seed-cache: skipped gated {x} is not an ancestor of origin/main" in r.stdout.splitlines(), r.stdout
    assert f"{other}.json" not in _cache_files(root, "baseline_cache"), "nothing may be seeded"


def _gate_both_after_an_src_edit(repo, root):
    """After the seed point: landing z edits src only; the next candidate y (edits src and lib so neither suite
    skips on unchanged inputs) is gated against base z. Returns {suite: stdout}."""
    shutil.rmtree(root / "candidate_results")  # no fallback may mask the hash guard
    z = _commit(repo, "landing z edits src", {"src/mod.py": "X = 3\n"})
    _commit(repo, "candidate y", {"src/mod.py": "X = 4\n", "lib/mod.py": "Y = 4\n"})
    return z, {s: _stage(repo, z, root, suite=s) for s in (SUITE, SUITE2)}


def test_H016_g_input_change_between_seed_and_gate_computes_that_suite_only(tmp_path):
    """H-016 (g): "an input change between seed and gate prints `baseline: computed` for that suite only", run
    with candidate_results removed "so the fallback cannot mask the hash guard". After the seed, z edits src
    (tests/t's input) and not lib (tests/u's input): tests/t prints `baseline: computed <z>`, tests/u prints
    `baseline: cached <z>` from baseline_cache/<H>.json."""
    repo, _base, x, h, root = _land_noff(tmp_path)
    assert f"seed-cache: seeded 2 suites from {x} for {h}" in _seed(repo, root).stdout
    z, out = _gate_both_after_an_src_edit(repo, root)
    assert out[SUITE].returncode == 0 and f"baseline: computed {z}" in out[SUITE].stdout, out[SUITE].stdout + out[SUITE].stderr
    assert out[SUITE2].returncode == 0 and f"baseline: cached {z}" in out[SUITE2].stdout, out[SUITE2].stdout + out[SUITE2].stderr


def test_H016_g_control_without_a_seed_and_without_candidate_results_both_suites_compute(tmp_path):
    """H-016 (g) CONTROL, green today: the (g) scene with no seed and candidate_results removed -> both suites
    print `baseline: computed <z>`, so a `cached` in the (g) test can only come from the seeded baseline_cache."""
    repo, _base, _x, h, root = _land_noff(tmp_path)
    z, out = _gate_both_after_an_src_edit(repo, root)
    for suite in (SUITE, SUITE2):
        assert out[suite].returncode == 0 and f"baseline: computed {z}" in out[suite].stdout, out[suite].stdout + out[suite].stderr


# ------------------------------------------------------------------ A15: skip on unchanged inputs

@pytest.mark.parametrize("how", ["empty commit", "edit outside the declared set", "new top-level file"])
def test_A15_candidate_with_unchanged_inputs_prints_the_line_and_runs_nothing(tmp_path, how):
    """A15 + CONTROL 'an edit outside the declared set skips the stage'."""
    repo, m, mark = _fixture(tmp_path)
    if how == "empty commit":
        _commit(repo, "nothing")
    elif how == "edit outside the declared set":
        _commit(repo, "docs", {"docs/README.md": "r1\n"})
    else:
        _commit(repo, "top", {"NOTES": "n\n"})
    r = _stage(repo, m, tmp_path / "root")
    want = f"OK inputs unchanged {input_hash(repo, m, DECLARED)}"
    assert r.returncode == 0 and _last(r) == want, r.stdout + r.stderr
    assert _runs(mark) == 0, "an unchanged-inputs stage must run no pytest at all"


@pytest.mark.parametrize("edit", ["tests", "src"])
def test_A15_control_edit_under_a_declared_input_runs_the_stage(tmp_path, edit):
    """A15 CONTROL: an edit under a declared input runs the stage (base and candidate), prints no skip line,
    and leaves a candidate_results entry carrying the candidate's input hash."""
    repo, m, mark = _fixture(tmp_path)
    if edit == "tests":
        x = _commit(repo, "new test", {"tests/t/test_b.py": "def test_b():\n    assert True\n"})
    else:
        x = _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    r = _stage(repo, m, tmp_path / "root")
    assert r.returncode == 0 and "inputs unchanged" not in r.stdout, r.stdout + r.stderr
    assert _runs(mark) >= 2, "base and candidate both run"
    got = json.loads((tmp_path / "root" / "candidate_results" / f"{x}.json").read_text())["suites"][SUITE]
    assert got["input_hash"] == input_hash(repo, x, DECLARED) != input_hash(repo, m, DECLARED)


# ------------------------------------------------------------------ A15: harness sha in the key

def _harness_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "harness_b"
    shutil.copytree(SPECFACTORY, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    with open(dst / "suite_regression.py", "a") as f:
        f.write("\n# a different harness sha\n")
    return dst


def test_A15_a_different_harness_sha_ignores_the_cache(tmp_path):
    """A15 CONTROL: the same input hash under another harness sha is a miss. The hit leg (a records commit R
    with M's declared inputs, gated under the same harness) is the part red on origin/main."""
    repo, m, _mark = _fixture(tmp_path)
    root = tmp_path / "root"
    _commit(repo, "edit src", {"src/mod.py": "X = 2\n"})
    assert f"baseline: computed {m}" in _stage(repo, m, root).stdout
    _git(repo, "checkout", "-q", "-b", "side", m)
    rec = _commit(repo, "records", {"docs/README.md": "r1\n"})
    _commit(repo, "other edit", {"src/mod.py": "X = 5\n"})
    same = _stage(repo, rec, root)
    assert f"baseline: cached {rec}" in same.stdout, same.stdout + same.stderr
    other = _stage(repo, rec, root, harness=_harness_copy(tmp_path))
    assert f"baseline: computed {rec}" in other.stdout, other.stdout + other.stderr


# ------------------------------------------------------------------ A15: coverage control

STRACE = """\
12345 execve("{r}/scripts/run.sh", ["run.sh"], 0x7ffd) = 0
12345 openat(AT_FDCWD, "{r}/tests/t/test_a.py", O_RDONLY|O_CLOEXEC) = 3
12345 openat(AT_FDCWD, "{r}/src/mod.py", O_RDONLY) = 4
12345 openat(AT_FDCWD, "/usr/lib/python3/os.py", O_RDONLY) = 5
12345 openat(AT_FDCWD, "{r}/src/__pycache__/mod.cpython-312.pyc", O_RDONLY) = 6
12345 openat(AT_FDCWD, "{r}/docs/missing.md", O_RDONLY) = -1 ENOENT (No such file or directory)
"""


def test_A15_coverage_flags_a_repo_file_opened_outside_the_declared_set(tmp_path):
    """A15 CONTROL: a sample run that opens a repo file outside the declared set fails the coverage check;
    a successful open of a declared file, an untracked file, a file outside the repo and a failed open do not."""
    repo, _m, _mark = _fixture(tmp_path)
    (repo / "src" / "__pycache__").mkdir()
    (repo / "src" / "__pycache__" / "mod.cpython-312.pyc").write_text("x")
    (repo / "scripts" / "run.sh").write_text("#!/bin/sh\n")
    _git(repo, "add", "scripts/run.sh")
    _git(repo, "commit", "-q", "-m", "run.sh")
    log = STRACE.format(r=repo)
    assert mgs.undeclared_opens(log, repo, DECLARED) == ["scripts/run.sh"]
    extra = log + f'12345 openat(AT_FDCWD, "{repo}/docs/README.md", O_RDONLY) = 7\n'
    assert mgs.undeclared_opens(extra, repo, DECLARED) == ["docs/README.md", "scripts/run.sh"]
    assert mgs.undeclared_opens(extra, repo, DECLARED + ["docs", "scripts/run.sh"]) == []


def test_A15_coverage_is_empty_when_every_opened_repo_file_is_declared(tmp_path):
    """A15 CONTROL (negative leg): nothing outside the declared set -> empty list."""
    repo, _m, _mark = _fixture(tmp_path)
    log = (f'1 openat(AT_FDCWD, "{repo}/tests/t/test_a.py", O_RDONLY) = 3\n'
           f'1 openat(AT_FDCWD, "{repo}/src/mod.py", O_RDONLY) = 4\n')
    assert mgs.undeclared_opens(log, repo, DECLARED) == []


# ------------------------------------------------------------------ the shipped files

def test_A15_shipped_suite_inputs_toml_declares_the_four_regression_suites():
    """A15 (item 1): scripts/specfactory/suite_inputs.toml exists, parses, and for each regression suite lists
    git-tracked paths that include the suite's own directory."""
    toml = REPO / TOML_REL
    assert toml.exists(), f"{TOML_REL} not written"
    suites = tomllib.loads(toml.read_text())["suites"]
    tracked = set(subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split("\n"))
    for suite in ("tests/csim", "tests/qa/t1", "tests/specfactory", "tests/transport"):
        paths = suites[suite]["paths"]
        assert suite in paths, (suite, paths)
        for p in paths:
            assert p in tracked or any(t.startswith(p.rstrip("/") + "/") for t in tracked), (suite, p)


def test_P_every_regression_stage_of_merge_gate_sh_passes_merge_root():
    """P: the four stages read and write the cache only through --merge-root (CONTROL, green today)."""
    text = (SPECFACTORY / "merge_gate.sh").read_text().replace("\\\n", " ")
    for suite in ("tests/csim", "tests/qa/t1", "tests/specfactory", "tests/transport"):
        lines = [ln for ln in text.splitlines() if "merge_gate_support.py\" regression" in ln and f" {suite} " in ln + " "]
        assert lines and all('--merge-root "$MERGE_ROOT"' in ln for ln in lines), suite


def test_P_rules_md_push_bullet_names_the_seed_cache_line():
    """P (item 7): rules.md section (b)'s Push bullet carries the seed-cache sentence."""
    text = (REPO / "docs/northstar/plans/workflows_2026-10-07/rules.md").read_text()
    push = [ln for ln in text.splitlines() if ln.startswith("- Push:")]
    assert push, "no Push bullet"
    assert ("after the push run `merge_gate_support.py seed-cache <worktree> --merge-root "
            "~/Projects/om-push/wt` (HARNESS-gate-cache-seed)") in push[0]
