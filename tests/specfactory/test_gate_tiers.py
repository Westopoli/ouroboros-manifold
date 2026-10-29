# Rule pins: 
# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md line 444 (the HARNESS-gate-tiers paragraph, rev 2);
#       amended by docs/northstar/plans/2026-10-29-layered-gate-spec.md section 4 (amendment items a to g) and section 8
#       (audit fold-in: B1, B3, F7, F8, F10, amendment items f and g).
"""HARNESS-gate-tiers (lane H, unit 4 of the stack): `merge_gate.sh [--revert] [--tier fast|slow|full]`, the new
`select-csim` subcommand, the `GATE tier <name>` line, the `sweep` check of status_check.py, the slow tier's union
diff and base, and the baseline cache that scans `candidate_results/` and keys subset runs by their file list.

Test groups (the paragraph's six, plus the amendment's 7 and 8; the group number is the prefix of each test name):
  1 select-csim: the csim files chosen for the changed C files; the stage line for an empty selection; a subset
    run never writes the full-suite cache entry.
  2 argument handling: --tier fast|slow|full, usage errors, --revert only with full.
  3 stage sets: fast skips the heavy stages, full is today's list, `GATE tier <name>` once and first.
  4 `STATUS sweep` in status_check.py: landings counted as first-parent `--no-ff` merges whose subject begins
    `Land ` (spec section 8 B3, DEC-landing-noff-2026-10-29), hours, the BASE row as anchor (F10), DRIFT at the
    multiplier; parametrised on the constants below.
  5 a slow-tier run with a comma list of ids: acceptance for both, the union-diff stages once.
  6 a slow-tier regression_csim REJECT names every first-parent sha since the base (merge commits included, the
    commits inside a merged branch not).
  7 `_find_cached_by_inputs` scans candidate_results/ after baseline_cache/ (amendment item c) only for an entry
    whose sha is an ancestor of origin/main and whose stored rc is 0 (F8); subset runs are keyed by the sorted file
    list and the csim table's input hash (F7).
  8 `--tier slow` keeps the positional <base_ref> as the regression base (B1, amendment item f); an empty id list
    prints `skipped: no ids` for the stages that need ids (amendment item g).

CONSTANTS (named drafts of the layered gate spec section 4; Westley's to change): DRAFT-slow-tier-batch 3,
DRAFT-slow-tier-hours 2, DRAFT-slow-tier-drift-mult 2. The tests derive their counts and ages from the constants
below, never from a literal.

FIXTURES: the gate runs on the tests/specfactory/test_gate_reorder.py pattern (a candidate repo, a bare origin, a
gate repo whose scripts/specfactory is this tree's with the noisy lints stubbed); the cache tests on the
tests/specfactory/test_gate_cache_seed.py pattern (a one-test suite that appends to a marker file).

POSITIVE CONTROLS: a valid `--tier fast` run (group 2); the default run still prints the stages fast skips and
`--tier full` equals it (3); a quiet sweep check (4); the selection that names the symbol (1); a hit on an entry
that is an ancestor with rc 0 and an empty-folders miss then hit (7); the slow tier with no `--tier` override
still rebases the baseline onto origin/main (8). Each is paired with the negative case it guards.

UNSTATED INTERFACE (reported, fixed here so the tests are runnable; the builder follows or the Architect rules):
  * the date-time cell of a sweeps.md row is `YYYY-MM-DD HH:MM` in UTC (the spec says "date-time UTC" only);
    SWEEP_TS_FMT below is the single place to change it.
  * `status_check.py` reads `docs/northstar/plans/push/sweeps.md` relative to --repo, the column order is date-time,
    main sha, verdict (the section 8 B2 row layout), and the anchor is the last row whose verdict is PASS or BASE.
  * a quiet check prints `STATUS sweep OK <detail>` (every other check prints one OK line).
  * `select-csim` takes the symbol tables of this repo (the defaults of the `symbols` subcommand): the tests read
    the real tables and pick a C file with two `[symbols]` rows and a C file mapped only by signatures.toml.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
SUPPORT = SPEC_DIR / "merge_gate_support.py"
STATUS = SPEC_DIR / "status_check.py"
sys.path.insert(0, str(SPEC_DIR))

import merge_gate_support as mgs  # noqa: E402

PY = sys.executable
GATE_PATH = "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"
RUN_TIMEOUT_S = 300
SIGNATURES = REPO / "docs/northstar/spec_factory/signatures.toml"
SYMBOL_MODULES = REPO / "docs/northstar/spec_factory/symbol_modules.toml"

# DRAFT-slow-tier-batch, DRAFT-slow-tier-hours, DRAFT-slow-tier-drift-mult (layered gate spec section 4).
BATCH, HOURS, MULT = 3, 2, 2
SWEEP_TS_FMT = "%Y-%m-%d %H:%M"
SWEEPS_REL = "docs/northstar/plans/push/sweeps.md"
SWEEPS_HEADER = ("| Date-time UTC | Main sha | Verdict | New | Red | Red ids |\n"
                 "|---|---|---|---|---|---|\n")


def _git(cwd, *args, check=True):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        "-c", "protocol.file.allow=always", *args],
                       cwd=str(cwd), capture_output=True, text=True, check=check)
    return r.stdout.strip()


def _commit(repo, files, msg="c"):
    """Write {rel: text}, commit them (an empty dict makes an empty commit); returns the new HEAD sha."""
    for rel, text in files.items():
        p = Path(repo) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _ts(hours_ago=0.0):
    t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours_ago)
    return t.strftime(SWEEP_TS_FMT)


def _stage_text(out, name):
    """The text of a `GATE <name> ...` line including continuation lines up to the next `GATE ` line."""
    lines, buf, on = out.splitlines(), [], False
    for ln in lines:
        if ln.startswith("GATE "):
            on = ln.startswith(f"GATE {name} ")
        if on:
            buf.append(ln)
    return "\n".join(buf)


def _stage_names(out):
    """Ordered stage names of the gate lines: `GATE <name> <STATUS> ...` (the row summary excluded)."""
    names = []
    for ln in out.splitlines():
        m = re.match(r"GATE (\S+) (OK|REJECT|WARN|HARNESS)\b", ln)
        if m:
            names.append(m.group(1))
    return names


# ====================================================================== gate fixture (test_gate_reorder.py pattern)

MAKEFILE = "libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n"
OK_STUB = "import sys\nsys.exit(0)\n"
# Their real runs reject a toy repo for reasons unrelated to the tiers; stubbed so the only REJECT is a planted one.
NOISY_TOOLS = ("alg_constants.py", "reach_lint.py", "sig_table.py")
COPIED_INTO_CANDIDATE = ("csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml", "CLAUDE.md")
PROGRAMME = "docs/northstar/plans/2026-10-07-visible-game-programme.md"
LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"


def _pieces(*rows):
    """rows: (id, [owns], [acceptance])"""
    out = ""
    for pid, owns, acc in rows:
        o = ", ".join(f'"{x}"' for x in owns)
        a = ", ".join(f'"{x}"' for x in acc)
        out += f'[[piece]]\nid = "{pid}"\nowns = [{o}]\nacceptance = [{a}]\ndepends_on = []\n\n'
    return out


def _overlay(root, rel_file, text):
    """Make rel_file under root a real file; every dir on its path is a real dir whose other entries are symlinks to
    this tree (docs/ is large, so it is never copied)."""
    parts = Path(rel_file).parts
    src, dst = REPO, Path(root)
    for i, part in enumerate(parts[:-1]):
        src, dst = src / part, dst / part
        if dst.is_symlink():
            dst.unlink()
        dst.mkdir(exist_ok=True)
        for e in src.iterdir():
            if e.name != parts[i + 1] and not (dst / e.name).exists():
                (dst / e.name).symlink_to(e)
    (dst / parts[-1]).unlink(missing_ok=True)
    (dst / parts[-1]).write_text(text)


class Fx:
    pass


def build_gate(tmp_path, *, main_steps=None, cand_steps=None, pieces=None, stubs=None, tests_transport=False):
    """A candidate repo C whose first commit M1 is pushed to a bare origin; main_steps(C) then adds commits that are
    pushed too (origin/main = tip); cand_steps(C) adds the candidate's own commits on top. The gate repo's lane table
    cites M1 (an ancestor of every base the tests use). Returns Fx(gate, cand, m1, tip, head, pieces_path, root)."""
    fx = Fx()
    fx.tmp = tmp_path
    cand = tmp_path / "cand"
    cand.mkdir()
    _git(cand, "init", "-q", "-b", "main")
    _commit(cand, {"csrc/stub.c": "int om_stub(void) { return 0; }\n"})
    _commit(cand, {"Makefile": MAKEFILE})
    _commit(cand, {"tests/csim/.keep": "\n", "tests/qa/t1/.keep": "\n"})
    if tests_transport:
        _commit(cand, {"tests/transport/.keep": "\n"})
    for rel in COPIED_INTO_CANDIDATE:
        _commit(cand, {rel: (REPO / rel).read_text()})
    fx.m1 = _git(cand, "rev-parse", "HEAD")
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    _git(cand, "remote", "add", "origin", str(origin))
    if main_steps:
        main_steps(cand)
    _git(cand, "push", "-q", "origin", "main")
    _git(cand, "fetch", "-q", "origin")
    fx.tip = _git(cand, "rev-parse", "HEAD")
    if cand_steps:
        cand_steps(cand)
    fx.head = _git(cand, "rev-parse", "HEAD")
    fx.cand = cand

    root = tmp_path / "gaterepo"
    _git(tmp_path, "clone", "-q", str(cand), str(root))
    _git(root, "update-ref", "refs/remotes/origin/main", fx.m1)
    (root / "scripts" / "specfactory").mkdir(parents=True)
    for f in SPEC_DIR.iterdir():
        if f.name not in ("merge_gate.sh", "merge_gate_support.py", *NOISY_TOOLS):
            (root / "scripts" / "specfactory" / f.name).symlink_to(f)
    shutil.copy(SPEC_DIR / "merge_gate_support.py", root / "scripts" / "specfactory" / "merge_gate_support.py")
    for name, text in {**{n: OK_STUB for n in NOISY_TOOLS}, **(stubs or {})}.items():
        (root / "scripts" / "specfactory" / name).unlink(missing_ok=True)
        (root / "scripts" / "specfactory" / name).write_text(text)
    shutil.copy(SPEC_DIR / "merge_gate.sh", root / "scripts" / "specfactory" / "merge_gate.sh")
    _overlay(root, PROGRAMME,
             "| Lane | On main | Next piece | First look | Westley row |\n|---|---|---|---|---|\n"
             f"| X | {fx.m1} | - | - | - |\n")
    pieces_text = pieces or _pieces(("B1", ["csrc/stub.c", "feat.txt"], []))
    _overlay(root, "docs/northstar/plans/push/pieces.toml", pieces_text)
    _overlay(root, LEDGER, "")
    # The sweep check reads sweeps.md: a current BASE row at M1 keeps the status stage quiet for this fixture.
    _overlay(root, SWEEPS_REL, SWEEPS_HEADER + f"| {_ts(0)} | {fx.m1} | BASE | new: none | red: 0 | |\n")
    (tmp_path / "pieces.toml").write_text(pieces_text)
    (tmp_path / "placeholders.txt").write_text("")
    fx.gate = root / "scripts" / "specfactory" / "merge_gate.sh"
    fx.merge_root = tmp_path          # the candidate's parent dir is the gate's merge root
    return fx


def run_gate(fx, *flags, base="origin/main", ids="B1", env_extra=None):
    env = {"PATH": GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(fx.tmp / "runs.csv"),
           "MERGE_GATE_PIECES": str(fx.tmp / "pieces.toml"),
           "MERGE_GATE_PLACEHOLDERS": str(fx.tmp / "placeholders.txt")}
    env.update(env_extra or {})
    r = subprocess.run(["bash", str(fx.gate), *flags, str(fx.cand), base, ids], capture_output=True, text=True,
                       env=env, timeout=RUN_TIMEOUT_S)
    return r, r.stdout + r.stderr


def _marker_tests(marker, tag):
    return f"def test_{tag}():\n    open({str(marker)!r}, 'a').write('{tag}\\n')\n    assert True\n"


def _marks(marker):
    return marker.read_text().split() if Path(marker).exists() else []


# real-table helpers for select-csim ------------------------------------------------------------

def _symbol_tables():
    sm = tomllib.loads(SYMBOL_MODULES.read_text()).get("symbols", {})
    sig = {s["name"]: s["module"] for s in tomllib.loads(SIGNATURES.read_text()).get("symbols", [])
           if s.get("name") and s.get("module")}
    return sm, sig


def _pick_two_symbol_file():
    """(c_file, sym1, sym2): a C file with two `[symbols]` rows; the control that the fixture exists."""
    sm, _sig = _symbol_tables()
    by_file = {}
    for sym, mod in sm.items():
        by_file.setdefault(mod, []).append(sym)
    for mod, syms in sorted(by_file.items()):
        if len(syms) >= 2:
            return mod, sorted(syms)[0], sorted(syms)[1]
    raise AssertionError("no C file with two [symbols] rows in symbol_modules.toml")


def _pick_signatures_only():
    """(c_file, symbol, other_module_symbol): a symbol mapped by signatures.toml only, and a symbol of another
    module that is not a substring of it and does not contain it."""
    sm, sig = _symbol_tables()
    for sym, mod in sorted(sig.items()):
        if sym not in sm and mod.endswith(".c"):
            for sym2, mod2 in sorted(sig.items()):
                if mod2 != mod and sym2 not in sym and sym not in sym2:
                    return mod, sym, sym2
    raise AssertionError("no signatures-only symbol")


def _select_repo(tmp_path, tests):
    """A repo: M with csrc/*.c, Makefile, tests/csim/{conftest.py + tests}, docs; returns (repo, M sha)."""
    repo = tmp_path / "sel"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    files = {"csrc/ouroboros_sim.h": "/* h */\n", "csrc/x.h": "/* x */\n", "Makefile": "all:\n",
             "tests/csim/conftest.py": "# c\n", "docs/readme.md": "r\n",
             "tests/csim/helper_zz.py": "# helper, not a test file\n"}
    files.update(tests)
    m = _commit(repo, files)
    return repo, m


def _select(repo, base):
    return subprocess.run([PY, str(SUPPORT), "select-csim", str(repo), base], capture_output=True, text=True,
                          timeout=120)


# ====================================================================== group 1: select-csim

def test_1_control_fixture_tables_have_a_two_symbol_file_and_a_signatures_only_file():
    """Group 1 control: the real symbol tables offer the two cases the fixtures need (a C file with two `[symbols]`
    rows, a C file mapped by signatures.toml only), so a green selection test is not vacuous."""
    cfile, s1, s2 = _pick_two_symbol_file()
    assert cfile.endswith(".c") and s1 != s2
    mod, sym, other = _pick_signatures_only()
    sm, sig = _symbol_tables()
    assert sym not in sm and sig[sym] == mod and sig[other] != mod
    maps = mgs._symbol_module_map(SIGNATURES, SYMBOL_MODULES)
    assert maps[s1] == cfile and maps[sym] == mod


def test_1_a_c_file_with_two_symbol_rows_selects_exactly_the_files_naming_either_symbol():
    """Group 1 (the paragraph's test 1, positive control for the selection logic): a diff touching one C file with
    two `[symbols]` rows selects exactly the tests/csim/test_*.py files whose text contains either symbol name,
    sorted, one repo-relative path per line, and nothing else. Negative cases in the same fixture: a test naming only
    another module's symbol, a test naming neither, and a non-test_ file naming the symbol are not selected."""
    cfile, s1, s2 = _pick_two_symbol_file()
    _mod, _sym, other = _pick_signatures_only()
    repo, m = _select_repo(Path(_tmp()), {
        "tests/csim/test_zz_both.py": f"# {s1} {s2}\n", "tests/csim/test_b_one.py": f"x = '{s1}'\n",
        "tests/csim/test_a_two.py": f"x = '{s2}'\n", "tests/csim/test_m_other.py": f"x = '{other}'\n",
        "tests/csim/test_n_none.py": "x = 'nothing'\n", "tests/csim/helper_has_sym.py": f"x = '{s1}'\n",
        f"csrc/{cfile}": "int a;\n"})
    _commit(repo, {f"csrc/{cfile}": "int a;\nint b;\n"})
    r = _select(repo, m)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.splitlines() == ["tests/csim/test_a_two.py", "tests/csim/test_b_one.py",
                                     "tests/csim/test_zz_both.py"], r.stdout + r.stderr


def test_1_a_c_file_that_only_signatures_toml_maps_still_selects_its_test():
    """Group 1: a changed C file that signatures.toml maps (and symbol_modules.toml does not) selects the test file
    naming that symbol; a test naming another module's symbol is left out."""
    cfile, sym, other = _pick_signatures_only()
    repo, m = _select_repo(Path(_tmp()), {"tests/csim/test_hit.py": f"x = '{sym}'\n",
                                         "tests/csim/test_miss.py": f"x = '{other}'\n",
                                         f"csrc/{cfile}": "int a;\n"})
    _commit(repo, {f"csrc/{cfile}": "int a;\nint b;\n"})
    r = _select(repo, m)
    assert r.returncode == 0 and r.stdout.splitlines() == ["tests/csim/test_hit.py"], r.stdout + r.stderr


@pytest.mark.parametrize("touched", ["csrc/x.h", "csrc/ouroboros_sim.h", "Makefile", "tests/csim/conftest.py"])
def test_1_a_header_makefile_or_conftest_change_selects_the_whole_suite(touched):
    """Group 1: a changed csrc/*.h, Makefile or tests/csim/conftest.py selects every tests/csim/test_*.py (and not
    the non-test helper file)."""
    repo, m = _select_repo(Path(_tmp()), {"tests/csim/test_b.py": "x = 1\n", "tests/csim/test_a.py": "x = 2\n"})
    _commit(repo, {touched: "changed\n"})
    r = _select(repo, m)
    assert r.returncode == 0 and r.stdout.splitlines() == ["tests/csim/test_a.py", "tests/csim/test_b.py"], \
        r.stdout + r.stderr


@pytest.mark.parametrize("touched", ["docs/readme.md", "tests/csim/test_a.py"])
def test_1_a_diff_with_no_csrc_change_selects_nothing(touched):
    """Group 1 (negative control): a docs-only diff, or an edit of a csim test file, selects nothing: empty stdout,
    exit 0."""
    cfile, s1, _s2 = _pick_two_symbol_file()
    repo, m = _select_repo(Path(_tmp()), {"tests/csim/test_a.py": f"x = '{s1}'\n", f"csrc/{cfile}": "int a;\n"})
    _commit(repo, {touched: "changed\n"})
    r = _select(repo, m)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_1_gate_empty_selection_prints_the_skipped_line_and_never_calls_regression(tmp_path):
    """Group 1: on a fixture whose diff has no csrc change, `--tier fast` prints
    `GATE regression_csim OK skipped: no csrc change`, exits 0, and runs no regression: no `baseline:` line and
    no candidate_results/ written."""
    fx = build_gate(tmp_path, cand_steps=lambda c: _commit(c, {"feat.txt": "feat\n"}))
    r, out = run_gate(fx, "--tier", "fast")
    line = _stage_text(out, "regression_csim")
    assert line.startswith("GATE regression_csim OK skipped: no csrc change"), out
    assert "baseline:" not in out and not (tmp_path / "candidate_results").exists(), out
    assert r.returncode == 0, out


def test_1_gate_subset_run_runs_only_the_selected_files_and_writes_no_full_suite_cache_entry(tmp_path):
    """Group 1 (the paragraph: 'a subset run does not write the full-suite cache entry'): a diff in a C file with a
    symbol selects test_hit.py only; test_miss.py never runs on base or candidate, and the stored candidate result
    has a key for the subset and no key that starts with the whole-suite argument `tests/csim`."""
    cfile, s1, _s2 = _pick_two_symbol_file()
    marker = tmp_path / "ran.txt"

    def main_steps(c):
        _commit(c, {"tests/csim/test_hit.py": f"# {s1}\n" + _marker_tests(marker, "hit"),
                    "tests/csim/test_miss.py": "# nothing\n" + _marker_tests(marker, "miss"),
                    f"csrc/{cfile}": "int a;\n"})

    fx = build_gate(tmp_path, main_steps=main_steps,
                    cand_steps=lambda c: _commit(c, {f"csrc/{cfile}": "int a;\nint b;\n"}),
                    pieces=_pieces(("B1", [f"csrc/{cfile}"], [])))
    r, out = run_gate(fx, "--tier", "fast")
    assert r.returncode == 0, out
    marks = _marks(marker)
    assert "hit" in marks and "miss" not in marks, f"marks={marks}\n{out}"
    res = list((tmp_path / "candidate_results").glob("*.json"))
    assert res, "no candidate_results written by the subset run\n" + out
    keys = [k for f in res for k in json.loads(f.read_text()).get("suites", {})]
    assert any(k.startswith("tests/csim/test_hit.py") for k in keys), keys
    assert not any(k.split()[0] == "tests/csim" for k in keys), f"whole-suite key written by a subset run: {keys}"


# ====================================================================== group 2: argument handling

def test_2_control_valid_fast_run_with_three_positionals_exits_0_and_names_the_tier(tmp_path):
    """Group 2 (positive control for the argument handling): `--tier fast <cand> <base> <ids>` runs, exits 0 and
    prints the tier line. (`--tier` is unknown to today's script, which proves only that the flag is new.)"""
    fx = build_gate(tmp_path, cand_steps=lambda c: _commit(c, {"feat.txt": "feat\n"}))
    r, out = run_gate(fx, "--tier", "fast")
    assert r.returncode == 0, out
    assert "GATE tier fast" in out.splitlines(), out


@pytest.mark.parametrize("flags", [("--tier", "bogus"), ("--revert", "--tier", "fast"), ("--tier", "fast", "--revert"),
                                   ("--tier", "slow", "--revert")])
def test_2_bogus_tier_and_revert_with_a_non_full_tier_exit_2_with_the_new_usage_line(tmp_path, flags):
    """Group 2: `--tier bogus`, and `--revert` with `--tier fast` or `slow` (either order), exit 2 with the usage
    line, which names `[--tier fast|slow|full]`; no stage ran."""
    fx = build_gate(tmp_path, cand_steps=lambda c: _commit(c, {"feat.txt": "feat\n"}))
    r, out = run_gate(fx, *flags)
    assert r.returncode == 2, out
    assert "usage: merge_gate.sh [--revert] [--tier fast|slow|full]" in r.stderr, r.stderr
    assert not any(ln.startswith("GATE ") and not ln.startswith("GATE row") for ln in r.stdout.splitlines()), out


@pytest.mark.parametrize("flags", [("--revert", "--tier", "full"), ("--tier", "full", "--revert")])
def test_2_revert_with_tier_full_is_allowed_in_either_order(tmp_path, flags):
    """Group 2 (control for the exit-2 rule): `--revert` is only refused with a tier other than full: with
    `--tier full` the light revert profile runs (stops after owner_lint) and exits 0, in either flag order."""
    fx = build_gate(tmp_path, cand_steps=lambda c: _commit(c, {"feat.txt": "feat\n"}))
    r, out = run_gate(fx, *flags)
    assert r.returncode == 0, out
    assert "GATE owner_lint OK" in out and "GATE regression_csim" not in out, out


# ====================================================================== group 3: stage sets and the tier line

FAST_SKIPPED = ["regression_lab", "regression_qa_t1", "specfactory_regression", "playthrough", "lane_plays",
                "checksum_trace", "tactical_trace", "undertest_check", "size_lint", "look"]
FAST_KEPT = ["base", "make", "libm_lint", "alg_constants", "allowlist_strict", "footprint", "gd_class_names",
             "symbol_ownership", "sig_blocked", "sig_check", "reach_lint", "gd_reach", "owner_lint", "rule_pins",
             "control_liveness", "placeholder_controls", "status", "acceptance", "qa_t1", "transport",
             "regression_csim"]


def _feat(c):
    return _commit(c, {"feat.txt": "feat\n"})


def test_3_control_default_run_prints_every_stage_fast_skips(tmp_path):
    """Group 3 positive control: the default run (today's full list) prints each of the ten stages the fast tier
    skips, so their absence under `--tier fast` means something."""
    fx = build_gate(tmp_path, cand_steps=_feat, tests_transport=True)
    r, out = run_gate(fx)
    names = _stage_names(out)
    missing = [s for s in FAST_SKIPPED if s not in names]
    assert not missing, f"default run lacks {missing}\n{out}"


def test_3_fast_tier_prints_none_of_the_skipped_stages_and_every_kept_one(tmp_path):
    """Group 3 (the paragraph's test 3): `--tier fast` prints no `GATE regression_lab`, `playthrough`,
    `lane_plays` or `look` line, nor the other six skipped stages, and prints each kept stage."""
    fx = build_gate(tmp_path, cand_steps=_feat, tests_transport=True)
    r, out = run_gate(fx, "--tier", "fast")
    names = _stage_names(out)
    assert not [s for s in FAST_SKIPPED if s in names], f"fast tier ran {[s for s in FAST_SKIPPED if s in names]}\n{out}"
    assert not [s for s in FAST_KEPT if s not in names], f"fast tier lacks {[s for s in FAST_KEPT if s not in names]}\n{out}"
    assert r.returncode == 0, out


def test_3_full_tier_prints_the_same_stage_set_in_the_same_order_as_the_default_run(tmp_path):
    """Group 3: `--tier full` is today's run unchanged: the ordered stage-name list equals the no-flag run's."""
    fx = build_gate(tmp_path, cand_steps=_feat, tests_transport=True)
    _r0, out0 = run_gate(fx)
    r1, out1 = run_gate(fx, "--tier", "full")
    n0, n1 = _stage_names(out0), _stage_names(out1)
    assert n1 and n1 == n0, f"default {n0}\nfull {n1}\n{out1}"
    assert r1.returncode == 0, out1


@pytest.mark.parametrize("flags,name", [(("--tier", "fast"), "fast"), (("--tier", "full"), "full"), ((), "full")])
def test_3_the_tier_line_is_printed_once_and_before_the_first_stage_line(tmp_path, flags, name):
    """Group 3: exactly one `GATE tier <name>` line, ahead of every other GATE line (`--tier full` and the default
    run both print `full`)."""
    fx = build_gate(tmp_path, cand_steps=_feat)
    r, out = run_gate(fx, *flags)
    gate_lines = [ln for ln in out.splitlines() if ln.startswith("GATE ")]
    tiers = [ln for ln in gate_lines if ln.startswith("GATE tier ")]
    assert tiers == [f"GATE tier {name}"], (tiers, out)
    assert gate_lines[0] == f"GATE tier {name}", gate_lines[:3]


# ====================================================================== group 4: STATUS sweep

def _history(repo, events):
    """events: 'land' (a first-parent --no-ff merge `Land P-n <sha>`), 'plain' (records commit), 'revert' (a plain
    commit subject `Revert ...`), 'merge' (a --no-ff merge whose subject is not `Land `), 'side_land' (a Land merge
    made on a side branch and merged into main by a non-Land merge, so it is not first-parent), ('anchor', name).
    Returns {anchor name: sha}."""
    anchors, n = {}, 0
    for ev in events:
        n += 1
        if isinstance(ev, tuple):
            anchors[ev[1]] = _git(repo, "rev-parse", "HEAD")
        elif ev == "plain":
            _commit(repo, {f"rec/{n}.txt": f"{n}\n"}, f"records {n}")
        elif ev == "revert":
            _commit(repo, {f"rec/{n}.txt": f"{n}\n"}, f"Revert \"Land P-{n} abc1234\"")
        elif ev in ("land", "merge"):
            _git(repo, "checkout", "-q", "-b", f"br{n}")
            _commit(repo, {f"br/{n}.txt": f"{n}\n"}, f"work {n}")
            _git(repo, "checkout", "-q", "main")
            subject = f"Land P-{n} {_git(repo, 'rev-parse', f'br{n}')}" if ev == "land" else f"Merge branch br{n}"
            _git(repo, "merge", "-q", "--no-ff", "-m", subject, f"br{n}")
        elif ev == "side_land":
            _git(repo, "checkout", "-q", "-b", f"side{n}")
            _commit(repo, {f"s/{n}.txt": "s\n"}, "side work")
            _git(repo, "checkout", "-q", "-b", f"inner{n}")
            _commit(repo, {f"s/{n}b.txt": "i\n"}, "inner work")
            _git(repo, "checkout", "-q", f"side{n}")
            _git(repo, "merge", "-q", "--no-ff", "-m", f"Land P-{n} {_git(repo, 'rev-parse', f'inner{n}')}", f"inner{n}")
            _git(repo, "checkout", "-q", "main")
            _git(repo, "merge", "-q", "--no-ff", "-m", f"Merge branch side{n}", f"side{n}")
    return anchors


def _status_fixture(tmp_path, events, rows):
    """A repo on main with the five files status_check reads, the history `events`, and a sweeps.md of `rows`
    (callables of the anchors dict returning a table row). Returns the run result."""
    repo = tmp_path / "st"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, {
        "README.txt": "base\n",
        "docs/northstar/plans/2026-10-07-visible-game-programme.md":
            "| Lane | On main | Next piece | First look | Westley row |\n|---|---|---|---|---|\n"
            "| A | nothing yet | - | - | - |\n",
        "docs/northstar/plans/push/pieces.toml":
            '[[piece]]\nid = "P-FLY"\nowns = ["c.c"]\nowns_glob = []\nacceptance = ["t.py"]\ndepends_on = []\n'
            'status = { state = "in_flight" }\ntests_pending = true\n',
        "docs/bible/stories.md": "| Story | Epic | Words | Status | Depth |\n|---|---|---|---|---|\n",
        "docs/northstar/story_reviews/README.md": "# queue\n",
        "docs/northstar/ROADMAP.md": "# Roadmap\n\n## 1. Now building\n\n"
                                     "| Lane | Branch | State | Next |\n|---|---|---|---|\n"
                                     "| **The visible game programme** "
                                     "(`docs/northstar/plans/2026-10-07-visible-game-programme.md`) | x | y | z |\n",
    })
    anchors = _history(repo, events)
    _commit(repo, {SWEEPS_REL: SWEEPS_HEADER + "".join(row(anchors) + "\n" for row in rows)}, "records sweeps")
    return subprocess.run(
        [PY, str(STATUS), "--repo", str(repo), "--base", "main",
         "--programme", "docs/northstar/plans/2026-10-07-visible-game-programme.md",
         "--pieces", "docs/northstar/plans/push/pieces.toml", "--stories", "docs/bible/stories.md",
         "--reviews", "docs/northstar/story_reviews", "--roadmap", "docs/northstar/ROADMAP.md"],
        capture_output=True, text=True, cwd=repo, timeout=60)


def _row(anchor, verdict, hours_ago=0.0, rest="| new: none | red: 0 | |"):
    return lambda a: f"| {_ts(hours_ago)} | {a[anchor]} | {verdict} {rest}"


def _sweep_line(res):
    hits = [ln for ln in res.stdout.splitlines() if ln.startswith("STATUS sweep ")]
    assert len(hits) == 1, f"STATUS sweep lines: {hits!r}\nstdout={res.stdout!r}\nstderr={res.stderr!r}"
    return hits[0]


def test_4_a_current_pass_row_with_no_landings_after_it_stays_quiet(tmp_path):
    """Group 4 positive control (the check can stay quiet): the last PASS is current and at the tip of main:
    `STATUS sweep OK`, no WARN, no DRIFT, exit code 0 as far as this check goes."""
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")], [_row("a", "PASS", 0.1)])
    assert _sweep_line(res).startswith("STATUS sweep OK"), res.stdout + res.stderr


@pytest.mark.parametrize("n,expect", [(BATCH, "OK"), (BATCH + 1, "WARN"), (MULT * BATCH - 1, "WARN"),
                                      (MULT * BATCH + 1, "DRIFT")])
def test_4_landings_after_the_last_pass_warn_above_the_batch_and_drift_at_the_multiplier(tmp_path, n, expect):
    """Group 4 (the paragraph's test 4, parametrised on DRAFT-slow-tier-batch and -drift-mult; Q4 ruled in spec
    section 8 B3): n `Land ` merges after the last PASS row: n == batch is due but quiet (WARN fires one landing
    later), batch+1 WARNs, batch*mult+1 is DRIFT. DRIFT makes the exit code 1 as for every check."""
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")] + ["land"] * n, [_row("a", "PASS", 0.1)])
    line = _sweep_line(res)
    assert line.startswith(f"STATUS sweep {expect}"), (n, line)
    if expect == "DRIFT":
        assert res.returncode == 1, res.stdout + res.stderr
    elif expect == "WARN":
        assert not re.search(r"^STATUS sweep DRIFT", res.stdout, re.M) and res.returncode == 0, res.stdout + res.stderr


def test_4_only_first_parent_land_merges_count_as_landings(tmp_path):
    """Group 4 (spec section 8 B3: 'counts `Land ` merges on a fixture with a branch-lineage merge and ignores a
    revert commit'): many records commits, revert commits, ordinary branch-lineage merges and a `Land ` merge that
    is not first-parent count for nothing; the only landing counted is the one first-parent `Land ` merge, so the
    check is quiet at one landing even with BATCH * MULT other first-parent entries after the anchor."""
    noise = ["plain", "revert", "merge", "side_land"] * (BATCH * MULT)
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")] + noise + ["land"], [_row("a", "PASS", 0.1)])
    assert _sweep_line(res).startswith("STATUS sweep OK"), res.stdout + res.stderr


def test_4_control_the_same_noise_plus_enough_land_merges_does_warn(tmp_path):
    """Group 4 positive control for the noise test: the same noise with BATCH + 1 real `Land ` merges WARNs."""
    noise = ["plain", "revert", "merge", "side_land"] * (BATCH * MULT)
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")] + noise + ["land"] * (BATCH + 1),
                          [_row("a", "PASS", 0.1)])
    assert _sweep_line(res).startswith("STATUS sweep WARN"), res.stdout + res.stderr


@pytest.mark.parametrize("hours,expect", [(HOURS * 0.5, "OK"), (HOURS * 1.5, "WARN"), (HOURS * MULT + 1, "DRIFT")])
def test_4_a_pass_row_older_than_the_hours_limit_warns_and_at_the_multiplier_drifts(tmp_path, hours, expect):
    """Group 4 (the paragraph's test 4, hours half, parametrised on DRAFT-slow-tier-hours and -drift-mult): no
    landings since the PASS row, only its age differs: under the limit is OK, over it WARN, over mult times it
    DRIFT."""
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")], [_row("a", "PASS", hours)])
    assert _sweep_line(res).startswith(f"STATUS sweep {expect}"), (hours, res.stdout)


def test_4_the_base_row_is_the_anchor_of_the_first_sweep(tmp_path):
    """Group 4 (F10, Q7): a sweeps.md holding only a BASE row anchors the count at its sha: landings before the BASE
    sha do not count (quiet), BATCH + 1 landings after it WARN."""
    (tmp_path / "q").mkdir()
    quiet = _status_fixture(tmp_path / "q", ["land"] * (MULT * BATCH + 2) + [("anchor", "b")], [_row("b", "BASE", 0.1)])
    assert _sweep_line(quiet).startswith("STATUS sweep OK"), quiet.stdout + quiet.stderr
    (tmp_path / "w").mkdir()
    warn = _status_fixture(tmp_path / "w", ["land", ("anchor", "b")] + ["land"] * (BATCH + 1), [_row("b", "BASE", 0.1)])
    assert _sweep_line(warn).startswith("STATUS sweep WARN"), warn.stdout + warn.stderr


def test_4_the_last_pass_or_base_row_wins_and_a_reject_row_is_never_the_anchor(tmp_path):
    """Group 4 (F10): rows BASE at b (old), PASS at a (later), REJECT at c (latest, current). Landings are counted from
    the PASS sha a, not from b (older) and not from the REJECT row's sha c: BATCH + 1 landings after a WARN even
    though fewer follow c."""
    events = ["land", ("anchor", "b"), "land", ("anchor", "a")] + ["land"] * (BATCH + 1) + [("anchor", "c")]
    rows = [_row("b", "BASE", 30), _row("a", "PASS", 0.5), _row("c", "REJECT", 0.1, "| new: t::x | red: 1 | t::x |")]
    res = _status_fixture(tmp_path, events, rows)
    assert _sweep_line(res).startswith("STATUS sweep WARN"), res.stdout + res.stderr


def test_4_a_red_sweep_is_never_a_drift(tmp_path):
    """Group 4 (F10: 'a red sweep is a FINDING row, never a DRIFT'): a current PASS at the tip and a current REJECT
    row after it with no landings pending: no DRIFT and no WARN."""
    events = ["land", ("anchor", "a"), ("anchor", "c")]
    rows = [_row("a", "PASS", 0.5), _row("c", "REJECT", 0.1, "| new: t::x | red: 1 | t::x |")]
    res = _status_fixture(tmp_path, events, rows)
    assert _sweep_line(res).startswith("STATUS sweep OK"), res.stdout + res.stderr
    assert res.returncode == 0, res.stdout + res.stderr


# ====================================================================== group 5 and 6: the slow tier's window

def test_5_a_comma_list_runs_acceptance_for_both_ids_and_the_union_diff_stages_once(tmp_path):
    """Group 5 (the paragraph's test 5): `--tier slow <wt> <base> A,B` runs the acceptance tests of both pieces and
    prints each union-diff stage (footprint, symbol_ownership, rule_pins, control_liveness) once; footprint is OK on
    the union of the two owns lists."""
    marker = tmp_path / "ran.txt"

    def main_steps(c):
        _commit(c, {"a_file.txt": "a\n", "tests/acc_a.py": _marker_tests(marker, "a")}, "a")
        _commit(c, {"b_file.txt": "b\n", "tests/acc_b.py": _marker_tests(marker, "b")}, "b")

    pieces = _pieces(("A", ["a_file.txt", "tests/acc_a.py"], ["tests/acc_a.py"]),
                     ("B", ["b_file.txt", "tests/acc_b.py"], ["tests/acc_b.py"]))
    fx = build_gate(tmp_path, main_steps=main_steps, pieces=pieces)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1, ids="A,B")
    assert "GATE tier slow" in out.splitlines(), out
    assert sorted(set(_marks(marker))) == ["a", "b"], f"acceptance marks {_marks(marker)}\n{out}"
    names = _stage_names(out)
    for stage in ("footprint", "symbol_ownership", "rule_pins", "control_liveness"):
        assert names.count(stage) == 1, f"{stage} printed {names.count(stage)} times\n{out}"
    assert _stage_text(out, "footprint").startswith("GATE footprint OK"), out


def test_5_control_a_single_id_of_the_pair_leaves_the_other_acceptance_unrun(tmp_path):
    """Group 5 negative control: with the single id A only A's acceptance test runs (so the marker test above cannot
    pass by running everything under tests/)."""
    marker = tmp_path / "ran.txt"

    def main_steps(c):
        _commit(c, {"a_file.txt": "a\n", "tests/acc_a.py": _marker_tests(marker, "a")}, "a")
        _commit(c, {"b_file.txt": "b\n", "tests/acc_b.py": _marker_tests(marker, "b")}, "b")

    pieces = _pieces(("A", ["a_file.txt", "tests/acc_a.py", "b_file.txt", "tests/acc_b.py"], ["tests/acc_a.py"]),
                     ("B", ["zz.txt"], ["tests/acc_b.py"]))
    fx = build_gate(tmp_path, main_steps=main_steps, pieces=pieces)
    run_gate(fx, "--tier", "slow", base=fx.m1, ids="A")
    assert sorted(set(_marks(marker))) == ["a"], _marks(marker)


NEW_RED = "def test_new_red():\n    assert False, 'new red on the candidate'\n"


def _window_with_a_merged_branch(box):
    """M1 -> c1 -> merge(side: s1 carries the new red csim test) -> c3. First-parent shas since M1: c1, mg, c3."""
    def steps(c):
        box["c1"] = _commit(c, {"c1.txt": "1\n"}, "c1")
        _git(c, "checkout", "-q", "-b", "side")
        box["s1"] = _commit(c, {"tests/csim/test_new_red.py": NEW_RED}, "s1")
        _git(c, "checkout", "-q", "main")
        _git(c, "merge", "-q", "--no-ff", "-m", "Land B1 side", "side")
        box["mg"] = _git(c, "rev-parse", "HEAD")
        box["c3"] = _commit(c, {"c3.txt": "3\n"}, "c3")
    return steps


WINDOW_PIECES = _pieces(("B1", ["c1.txt", "c3.txt", "tests/csim/test_new_red.py"], []))


def test_6_a_slow_tier_regression_reject_names_every_first_parent_sha_since_the_base(tmp_path):
    """Group 6 (the paragraph's test 6): `--tier slow` against the base M1 on a window whose merged branch brings a
    new red csim test: `GATE regression_csim REJECT` and its detail names the first-parent shas c1, the merge and c3
    (at least 7 characters each) and not the commit inside the merged branch. Exit 1."""
    box = {}
    fx = build_gate(tmp_path, main_steps=_window_with_a_merged_branch(box), pieces=WINDOW_PIECES)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1, ids="B1")
    text = _stage_text(out, "regression_csim")
    assert text.startswith("GATE regression_csim REJECT"), out
    for name in ("c1", "mg", "c3"):
        assert box[name][:7] in text, f"{name} {box[name][:7]} missing from the reject detail:\n{text}"
    assert box["s1"][:7] not in text, f"a commit inside the merged branch is listed:\n{text}"
    assert r.returncode == 1, out


def test_6_control_the_same_window_without_the_red_test_passes_regression_csim(tmp_path):
    """Group 6 positive control: the same window with a green csim test: regression_csim is OK and no REJECT line."""
    tmp2 = tmp_path / "green"
    tmp2.mkdir()

    def green_steps(c):
        _commit(c, {"c1.txt": "1\n"}, "c1")
        _git(c, "checkout", "-q", "-b", "side")
        _commit(c, {"tests/csim/test_new_red.py": "def test_new_red():\n    assert True\n"}, "s1")
        _git(c, "checkout", "-q", "main")
        _git(c, "merge", "-q", "--no-ff", "-m", "Land B1 side", "side")
        _commit(c, {"c3.txt": "3\n"}, "c3")

    fx2 = build_gate(tmp2, main_steps=green_steps, pieces=WINDOW_PIECES)
    r, out = run_gate(fx2, "--tier", "slow", base=fx2.m1, ids="B1")
    assert _stage_text(out, "regression_csim").startswith("GATE regression_csim OK"), out
    assert "REJECT" not in out and r.returncode == 0, out


# ====================================================================== group 7: the baseline cache

SUITE = "tests/csim"
DECLARED = ["tests/csim", "src"]
TOML_REL = "scripts/specfactory/suite_inputs.toml"
TOML = f'[suites."{SUITE}"]\npaths = ["tests/csim", "src"]\n'


def _env(extra=None):
    e = {k: v for k, v in os.environ.items() if k not in ("MERGE_GATE_BASELINE_CACHE", "MALLOC_PERTURB_")}
    e.update(extra or {})
    return e


def _cache_fixture(tmp_path):
    """Main commit M: three one-test files that append to a marker, a declared src dir, an undeclared docs dir and
    the inputs toml. origin/main is set to M. Returns (repo, M, marker)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    marker = tmp_path / "ran.txt"
    files = {f"tests/csim/test_{n}.py": _marker_tests(marker, n) for n in ("a", "b", "c")}
    files.update({"src/mod.py": "X = 1\n", "docs/README.md": "r0\n", TOML_REL: TOML})
    m = _commit(repo, files, "main")
    _git(repo, "update-ref", "refs/remotes/origin/main", m)
    return repo, m, marker


def _stage(repo, base_ref, root, args=(SUITE,)):
    return subprocess.run([PY, str(SUPPORT), "regression", str(repo), base_ref, *args, "--python", PY,
                           "--no-junit", "--merge-root", str(root)],
                          capture_output=True, text=True, env=_env(), timeout=300)


def _set_origin_main(repo, sha):
    _git(repo, "update-ref", "refs/remotes/origin/main", sha)


def _candidate_gated_against_m(tmp_path):
    """The shared scene of the candidate_results tests: X (edits src) gated against M, records commit R on top of X,
    origin/main = R, nothing seeded. Returns (repo, root, M, X, R, marker)."""
    repo, m, marker = _cache_fixture(tmp_path)
    x = _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    r = _stage(repo, m, root)
    assert r.returncode == 0 and f"baseline: computed {m}" in r.stdout, r.stdout + r.stderr
    assert [p.name for p in (root / "candidate_results").glob("*.json")] == [f"{x}.json"]
    rec = _commit(repo, {"docs/README.md": "r1\n"}, "records")
    _set_origin_main(repo, rec)
    return repo, root, m, x, rec, marker


def test_7_an_entry_only_under_candidate_results_is_a_hit_for_the_next_gate(tmp_path):
    """Group 7 (amendment item c; the negative control of test_P_negative_control_origin_main_moved_by_a_docs_commit_
    seeds_nothing): X was gated and never seeded because a records commit R moved origin/main first. X is an ancestor
    of origin/main and its stored rc is 0. The next landing, gated against R (same declared inputs as X), prints
    `baseline: cached` and runs only its own candidate pass."""
    repo, root, m, x, rec, marker = _candidate_gated_against_m(tmp_path)
    assert not (root / "baseline_cache" / f"{x}.json").exists(), "fixture: X must not be seeded"
    before = len(_marks(marker))
    _commit(repo, {"src/mod.py": "X = 3\n"}, "next landing")
    nxt = _stage(repo, rec, root)
    assert nxt.returncode == 0 and f"baseline: cached {rec}" in nxt.stdout, nxt.stdout + nxt.stderr
    assert len(_marks(marker)) - before == 3, "a cached base leaves only the candidate pass (three tests)"


def test_7_an_entry_whose_sha_is_not_an_ancestor_of_origin_main_is_never_read(tmp_path):
    """Group 7 negative control (F8, a REJECTed or abandoned candidate): same scene, but origin/main is on a line
    that does not contain X. X's candidate_results entry (rc 0) is not read: `baseline: computed`."""
    repo, m, marker = _cache_fixture(tmp_path)
    _git(repo, "checkout", "-q", "-b", "other")
    other = _commit(repo, {"docs/README.md": "other\n"}, "other line")
    _git(repo, "checkout", "-q", "-b", "cand", m)
    x = _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    assert _stage(repo, m, root).returncode == 0
    assert (root / "candidate_results" / f"{x}.json").exists()
    _set_origin_main(repo, other)
    # The next candidate descends from X (so X's inputs equal the base's) but origin/main does not contain X.
    _commit(repo, {"docs/README.md": "r1\n"}, "records on the candidate line")
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, {"src/mod.py": "X = 3\n"}, "next landing")
    nxt = _stage(repo, base, root)
    assert f"baseline: computed {base}" in nxt.stdout, nxt.stdout + nxt.stderr


def test_7_an_entry_with_a_non_zero_stored_rc_is_never_read(tmp_path):
    """Group 7 negative control (F8): the entry for X is an ancestor of origin/main but its stored returncode is 1
    (a red run): not read, `baseline: computed`."""
    repo, root, m, x, rec, marker = _candidate_gated_against_m(tmp_path)
    f = root / "candidate_results" / f"{x}.json"
    data = json.loads(f.read_text())
    for entry in data["suites"].values():
        entry["returncode"] = 1
    f.write_text(json.dumps(data))
    _commit(repo, {"src/mod.py": "X = 3\n"}, "next landing")
    nxt = _stage(repo, rec, root)
    assert f"baseline: computed {rec}" in nxt.stdout, nxt.stdout + nxt.stderr


def test_7_a_candidate_that_ran_red_stores_a_non_zero_rc_that_is_never_read(tmp_path):
    """Group 7 (F8, end to end): X's own run had a red test (red on base and candidate, so the stage is OK) and stores
    its real returncode; it is an ancestor of origin/main yet the next gate does not read it."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"tests/csim/test_red.py": "def test_red():\n    assert False\n"}, "red test on main")
    m2 = _git(repo, "rev-parse", "HEAD")
    _set_origin_main(repo, m2)
    x = _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    assert _stage(repo, m2, root).returncode == 0
    stored = json.loads((root / "candidate_results" / f"{x}.json").read_text())["suites"]
    assert all(e["returncode"] != 0 for e in stored.values()), stored
    rec = _commit(repo, {"docs/README.md": "r1\n"}, "records")
    _set_origin_main(repo, rec)
    _commit(repo, {"src/mod.py": "X = 3\n"}, "next landing")
    nxt = _stage(repo, rec, root)
    assert f"baseline: computed {rec}" in nxt.stdout, nxt.stdout + nxt.stderr


def test_7_with_both_folders_empty_the_next_gate_computes_once_and_then_reads_the_cache(tmp_path):
    """Group 7 positive control (amendment item c): empty baseline_cache/ and candidate_results/ print
    `baseline: computed` once; the same base again prints `baseline: cached`."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    assert not (root / "baseline_cache").exists() and not (root / "candidate_results").exists()
    first = _stage(repo, m, root)
    assert f"baseline: computed {m}" in first.stdout, first.stdout + first.stderr
    second = _stage(repo, m, root)
    assert f"baseline: cached {m}" in second.stdout and "computed" not in second.stdout, second.stdout


SUBSET_AB = ("tests/csim/test_a.py", "tests/csim/test_b.py")


def test_7_a_subset_is_cached_by_its_file_list_whatever_the_argument_order(tmp_path):
    """Group 7 (F7, 'keyed by ... the sorted selected file list'): a subset run computes its base once and the same
    selection given in the other order is a hit; select-csim prints sorted, but the key must not depend on it."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    first = _stage(repo, m, root, SUBSET_AB)
    assert f"baseline: computed {m}" in first.stdout, first.stdout + first.stderr
    again = _stage(repo, m, root, SUBSET_AB[::-1])
    assert f"baseline: cached {m}" in again.stdout, again.stdout + again.stderr


def test_7_a_different_selection_is_a_miss_computed_once_and_then_cached(tmp_path):
    """Group 7 (F7 'a new selection computes once'): subset {a,b} cached, subset {a,c} computes, then hits."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    assert f"baseline: computed {m}" in _stage(repo, m, root, SUBSET_AB).stdout
    ac = ("tests/csim/test_a.py", "tests/csim/test_c.py")
    assert f"baseline: computed {m}" in _stage(repo, m, root, ac).stdout
    assert f"baseline: cached {m}" in _stage(repo, m, root, ac).stdout


def test_7_a_subset_baseline_survives_a_records_commit_through_the_csim_input_hash(tmp_path):
    """Group 7 (F7, 'keyed by (the csim table's input hash, ...)'): the subset's base was computed at M; the next
    landing is gated against R = M plus a docs-only records commit (declared inputs unchanged): the subset is a hit."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root = tmp_path / "root"
    assert f"baseline: computed {m}" in _stage(repo, m, root, SUBSET_AB).stdout
    _git(repo, "checkout", "-q", "-b", "records", m)
    rec = _commit(repo, {"docs/README.md": "r1\n"}, "records")
    _commit(repo, {"src/mod.py": "X = 4\n"}, "next landing")
    nxt = _stage(repo, rec, root, SUBSET_AB)
    assert f"baseline: cached {rec}" in nxt.stdout, nxt.stdout + nxt.stderr


def test_7_a_subset_run_neither_reads_nor_writes_the_full_suite_entry(tmp_path):
    """Group 7 (F7, the paragraph: 'a subset run never writes or reads the full-suite cache entry'): after a
    full-suite base at M, a subset against M still computes; after a subset base at M, the full suite against M
    still computes."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"src/mod.py": "X = 2\n"}, "edit src")
    root1, root2 = tmp_path / "r1", tmp_path / "r2"
    assert f"baseline: computed {m}" in _stage(repo, m, root1).stdout
    assert f"baseline: computed {m}" in _stage(repo, m, root1, SUBSET_AB).stdout, "subset read the full-suite entry"
    assert f"baseline: computed {m}" in _stage(repo, m, root2, SUBSET_AB).stdout
    assert f"baseline: computed {m}" in _stage(repo, m, root2).stdout, "full suite read the subset entry"


# ====================================================================== group 8: slow tier base, empty ids

def _two_main_commits(c):
    _commit(c, {"m2.txt": "m2\n"}, "m2")
    _commit(c, {"m3.txt": "m3\n"}, "m3")


M_PIECES = _pieces(("B1", ["m2.txt", "m3.txt"], []))


def test_8_slow_tier_keeps_the_positional_base_ref_as_the_regression_base(tmp_path):
    """Group 8 (B1, amendment item f): with `--tier slow` and a <base_ref> that is older than origin/main, the
    regression stages print `baseline: computed <the base_ref sha>` and never the sha of HEAD / origin/main."""
    fx = build_gate(tmp_path, main_steps=_two_main_commits, pieces=M_PIECES)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1)
    assert fx.tip != fx.m1
    assert f"baseline: computed {fx.m1}" in out, out
    assert f"baseline: computed {fx.tip}" not in out and f"baseline: cached {fx.tip}" not in out, out


@pytest.mark.parametrize("flags", [(), ("--tier", "full"), ("--tier", "fast")])
def test_8_control_without_the_slow_tier_stage_0_still_rebases_onto_origin_main(tmp_path, flags):
    """Group 8 control (the default is unchanged): the same fixture with the default tier, `--tier full` or
    `--tier fast` replaces the positional base by origin/main: `GATE base OK <tip sha>`, and no `baseline` line for
    the older sha."""
    fx = build_gate(tmp_path, main_steps=_two_main_commits, pieces=M_PIECES)
    r, out = run_gate(fx, *flags, base=fx.m1)
    assert f"GATE base OK {fx.tip}" in out, out
    assert f"baseline: computed {fx.m1}" not in out and f"baseline: cached {fx.m1}" not in out, out


def test_8_slow_tier_stage_0_still_requires_the_candidate_to_contain_origin_main(tmp_path):
    """Group 8 (B1): the slow tier keeps stage 0's ancestry rule: a candidate that lacks origin/main still REJECTs
    `base` (the positional base_ref changes the baseline, not the check)."""
    def cand_steps(c):
        _git(c, "checkout", "-q", "-b", "stale", fx_box["m1"])
        _commit(c, {"m2.txt": "other\n"}, "diverged")

    fx_box = {}
    fx = build_gate(tmp_path, main_steps=lambda c: (fx_box.setdefault("m1", _git(c, "rev-parse", "HEAD")),
                                                    _two_main_commits(c)), cand_steps=cand_steps, pieces=M_PIECES)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1)
    assert _stage_text(out, "base").startswith("GATE base REJECT"), out
    assert r.returncode == 1, out


def test_8_an_empty_id_list_prints_skipped_no_ids_for_the_stages_that_need_ids(tmp_path):
    """Group 8 (amendment item g): `--tier slow <wt> <base> ""` is not a usage error; the stages that need ids
    (footprint and acceptance) print `skipped: no ids`; nothing REJECTs, exit 0."""
    fx = build_gate(tmp_path, main_steps=_two_main_commits, pieces=M_PIECES)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1, ids="")
    assert r.returncode == 0, out
    for stage in ("footprint", "acceptance"):
        assert "skipped: no ids" in _stage_text(out, stage), f"{stage}: {_stage_text(out, stage)!r}\n{out}"
    assert "REJECT" not in out, out


def test_8_control_a_non_empty_id_list_does_not_print_skipped_no_ids(tmp_path):
    """Group 8 control: with the id B1 the footprint stage runs for real, so the skipped line is specific to the
    empty list."""
    fx = build_gate(tmp_path, main_steps=_two_main_commits, pieces=M_PIECES)
    r, out = run_gate(fx, "--tier", "slow", base=fx.m1, ids="B1")
    assert "skipped: no ids" not in out, out
    assert _stage_text(out, "footprint").startswith("GATE footprint OK"), out


# ====================================================================== group 9: unmapped C, fast acceptance, dropped base files, quiet sweep
# Architect rulings after the first build (the dispatcher's brief to the tiers test writer, 2026-10-29). Group 8 above is
# the slow-tier base group (B1, item g), so this group is 9. Each test names the item it proves.

def test_9_an_unmapped_c_file_selects_the_whole_csim_suite(tmp_path):
    """Group 9 (i), layered gate spec section 2 layer 1 ('a row without the key is `sim`, the strict case') applied to
    `select-csim`: a changed csrc/*.c that no symbol table maps selects the WHOLE csim suite, as a header change does
    (it used to select nothing). A mapped file keeps its narrow selection (group 1), so this is not a blanket rule."""
    unmapped = "csrc/zz_unmapped_by_any_table.c"
    sm, sig = _symbol_tables()
    assert unmapped.rsplit("/", 1)[1] not in set(sm.values()) | set(sig.values()), \
        "fixture: the unmapped file must not be in either symbol table"
    repo, m = _select_repo(Path(_tmp()), {"tests/csim/test_b.py": "x = 1\n", "tests/csim/test_a.py": "x = 2\n",
                                         unmapped: "int a;\n"})
    _commit(repo, {unmapped: "int a;\nint b;\n"})
    sel = _select(repo, m)
    assert sel.returncode == 0 and sel.stdout.splitlines() == ["tests/csim/test_a.py", "tests/csim/test_b.py"], \
        f"unmapped .c selected {sel.stdout.splitlines()!r}, wanted the whole suite\n{sel.stderr}"


def test_9_the_gate_prints_the_unmapped_line_and_runs_the_whole_suite(tmp_path):
    """Group 9 (i), the gate half: for a changed csrc/stub.c (om_stub is in neither table) `--tier fast` prints
    `select-csim: <file> unmapped, whole suite` and runs every csim file (both marker tests ran)."""
    marker = tmp_path / "ran.txt"

    def main_steps(c):
        _commit(c, {"tests/csim/test_a.py": "# nothing\n" + _marker_tests(marker, "a"),
                    "tests/csim/test_b.py": "# nothing\n" + _marker_tests(marker, "b")})

    fx = build_gate(tmp_path, main_steps=main_steps,
                    cand_steps=lambda c: _commit(c, {"csrc/stub.c": "int om_stub(void) { return 1; }\n"}))
    r, out = run_gate(fx, "--tier", "fast")
    assert re.search(r"select-csim: (csrc/)?stub\.c unmapped, whole suite", out), out
    assert sorted(set(_marks(marker))) == ["a", "b"], f"marks={_marks(marker)}\n{out}"
    assert r.returncode == 0, out


def test_9_fast_tier_adds_changed_test_files_to_acceptance_but_never_the_desktop_plays(tmp_path):
    """Group 9 (ii), the HARNESS-gate-tiers paragraph ('the row's `acceptance` key plus every file under `tests/` the
    diff touches') with merge_gate.sh's own exclusion of tests/qa/desktop/* (no frame in the fast tier): a changed
    tests/unit/test_changed.py runs under `acceptance` although the row does not list it (GREEN control); a changed
    tests/qa/desktop/test_desk.py, a valid collectable test, never runs (negative control)."""
    marker = tmp_path / "ran.txt"
    pieces = _pieces(("B1", ["feat.txt", "tests/unit/test_changed.py", "tests/qa/desktop/test_desk.py"], []))

    def cand_steps(c):
        _commit(c, {"feat.txt": "feat\n", "tests/unit/test_changed.py": _marker_tests(marker, "changed"),
                    "tests/qa/desktop/test_desk.py": _marker_tests(marker, "desk")})

    fx = build_gate(tmp_path, cand_steps=cand_steps, pieces=pieces)
    r, out = run_gate(fx, "--tier", "fast")
    assert _marks(marker) == ["changed"], f"marks={_marks(marker)} (the desktop file must not run)\n{out}"
    assert _stage_text(out, "acceptance").startswith("GATE acceptance OK"), out


def _subset_with_new_files(tmp_path):
    """A subset {test_a (on the base), test_new, test_new2 (new in the candidate)}; returns (stage result, marker)."""
    repo, m, marker = _cache_fixture(tmp_path)
    _commit(repo, {"tests/csim/test_new.py": _marker_tests(marker, "new"),
                   "tests/csim/test_new2.py": _marker_tests(marker, "new2"), "src/mod.py": "X = 2\n"}, "new tests")
    sel = ("tests/csim/test_a.py", "tests/csim/test_new.py", "tests/csim/test_new2.py")
    return _stage(repo, m, tmp_path / "root", sel), marker


def test_9_a_csim_subset_base_run_drops_files_the_base_lacks(tmp_path):
    """Group 9 (iii), F7 (a subset run, spec section 8) with `regression_check`'s base-side filter: a selected file the
    base does not have (a new test file has no base result) is left out of the base run, so pytest does not error on a
    missing path, and the candidate still runs it. GREEN control: base ran test_a only, candidate ran all three."""
    r, marker = _subset_with_new_files(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert sorted(_marks(marker)) == ["a", "a", "new", "new2"], f"base ran a, candidate ran a, new, new2: {_marks(marker)}"


def test_9_the_log_names_each_file_the_base_run_dropped(tmp_path):
    """Group 9 (iii), the logging half: the stage log names each dropped file (and not test_a.py, which the base has)."""
    r, _marker = _subset_with_new_files(tmp_path)
    log = r.stdout + r.stderr
    for dropped in ("tests/csim/test_new.py", "tests/csim/test_new2.py"):
        assert re.search(rf"dropp?ed.*{re.escape(dropped)}|{re.escape(dropped)}.*dropp?ed", log, re.I), \
            f"the log does not name the dropped base file {dropped}\n{log}"
    assert not re.search(r"dropp?ed.*test_a\.py", log, re.I), f"test_a.py exists on the base and is not dropped\n{log}"


def test_9_the_sweep_age_and_batch_rules_count_only_landings_since_the_last_row(tmp_path):
    """Group 9 (iv), layered gate spec section 8 F10 and B3 ('the last PASS or BASE row is the anchor'; a landing is a
    `Land ` first-parent merge): the last sweeps.md row is 3 * HOURS * MULT hours old (past the drift age) but nothing has landed since it,
    so there is nothing to sweep: no WARN and no DRIFT."""
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")], [_row("a", "PASS", HOURS * MULT * 3)])
    line = _sweep_line(res)
    assert line.startswith("STATUS sweep OK"), f"zero landings since the last row but the check said: {line}"
    assert res.returncode == 0, res.stdout + res.stderr


def test_9_control_the_old_row_with_landings_past_the_limit_does_warn(tmp_path):
    """Group 9 (iv) positive control: a row past the hours limit (under the drift multiple) with BATCH + 1 landings since
    it WARNs, so the red test above is red because no landings were counted, not because the check cannot warn."""
    res = _status_fixture(tmp_path, ["land", ("anchor", "a")] + ["land"] * (BATCH + 1), [_row("a", "PASS", HOURS * 1.5)])
    assert _sweep_line(res).startswith("STATUS sweep WARN"), res.stdout + res.stderr


# ---------------------------------------------------------------------------------------------------

def _tmp():
    """A fresh directory for the pure-git fixtures that need no pytest tmp_path argument in their signature."""
    import tempfile
    d = tempfile.mkdtemp(prefix="gate_tiers_")
    _CLEANUP.append(d)
    return d


_CLEANUP = []


@pytest.fixture(autouse=True, scope="module")
def _remove_temp_dirs():
    yield
    for d in _CLEANUP:
        shutil.rmtree(d, ignore_errors=True)
