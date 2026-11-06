# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-5
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-6
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-7
"""S-247 wave 2, leaf 2: the layout_dump CLI, its flags, exit codes, JSON and --check (criteria 5 and 7).

R-112-01 R-112-04 R-112-05 R-113-01.
Red until csrc/tools/layout_dump.c exists (the module fixture asserts it). The CLI is built once per module with the
determinism flags and run as a black box; what it must print is judged against things written here or by the wave 1
probe (tests/csim/layout_kit_probe.c, the engine called directly), never against the CLI's own output alone.
Budget: at most 40 assertions in the eight wave 2 test files and the helper together (counted by `assert`).
Helpers: tests/csim/layout_kit_cli_helpers.py (honours LAYOUT_DUMP_SRC, default csrc/tools/layout_dump.c).
"""
import json
import pathlib
import re
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import layout_kit_cli_helpers as H   # noqa: E402

ARCHETYPE_NAMES = ["defensive_stand", "siege_breaking", "reconquest", "suppression", "multi_front_defense",
                   "interception", "evacuation", "containment", "counterinsurgency"]   # csrc/mission.c:161-170 minus assault


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    return H.build_cli(tmp_path_factory)


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    return H.build_probe(tmp_path_factory)


def check_lines(checks):
    return "".join(f"{n} {'true' if checks[n] else 'false'}\n" for n in H.CHECKS)


# ---- flags and defaults (criterion 5) ---------------------------------------------------------------------------------
def test_S_247_defaults_and_echo(cli):
    """S-247 R-112-01: with only --seed and --archetype the canvas is DRAFT_CANVAS_ASSAULT 24,000 and the sides
    mode is separate; --canvas and --sides are echoed as given."""
    plain = H.load(H.dump(cli, 7))
    r = H.run(cli, "--seed", 7, "--archetype", "assault")
    given = H.load(H.dump(cli, 7, "mirror", canvas=16000))
    assert (r.returncode, H.load(r.stdout)["sides"], H.load(r.stdout)["canvas"], plain["schema"], plain["seed"],
            plain["archetype"], given["sides"], given["canvas"]) == (0, "separate", 24000, "om-layout-1", 7,
                                                                       "assault", "mirror", 16000)


@pytest.mark.parametrize("seed", [2 ** 32 + 1, 2 ** 63, 2 ** 64 - 1])
def test_S_247_seed_is_a_full_uint64(cli, seed):
    """S-247 R-112-01: the seed is a uint64 (csrc/layout_kit.h): the largest values are accepted and printed whole."""
    r = H.run(cli, *H.dump_args(seed))
    assert (r.returncode, H.load(r.stdout)["seed"]) == (0, seed)


@pytest.mark.parametrize("sides", H.SIDES)
def test_S_247_key_order_is_the_spec_order(cli, sides):
    """S-247 R-112-04: the keys of the object, of every array element, of fairness and of checks are in exactly the
    order of the spec's JSON section."""
    assert H.order_problems(H.dump(cli, 3, sides)) == []


@pytest.mark.parametrize("sides", H.SIDES)
def test_S_247_file_layout_is_two_space_one_element_per_line(cli, sides):
    """S-247 R-112-04: two-space indent, one array element per line for places, nodes, lanes, chokes, vantages,
    requests, one line per district row, a single newline at the end."""
    assert H.text_problems(H.dump(cli, 3, sides)) == []


@pytest.mark.parametrize("sides", H.SIDES)
def test_S_247_numbers_are_quantised_hundredths_with_integer_text(cli, sides):
    """S-247 R-112-04: coordinates, widths, radii and distances print as [-]int.dd (no %g, no exponent), counts and
    indices as bare integers; an unreachable distance prints -1.00 (see the connected test)."""
    assert H.number_problems(H.dump(cli, 3, sides)) == []


@pytest.mark.parametrize("sides", H.SIDES)
def test_S_247_names_are_the_spec_strings(cli, sides):
    """S-247 R-113-01: archetype, sides, side letters and every kind / piece / landform / mode print as the strings
    of the spec's JSON section."""
    assert H.name_problems(H.load(H.dump(cli, 3, sides))) == []


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_the_json_is_what_the_engine_produced(cli, probe, seed, sides):
    """S-247 R-112-04: every place, node, lane, choke, vantage, request, district, fairness figure and check bit equals
    the engine's own dump of the same call (the wave 1 probe), to a printed hundredth."""
    assert H.probe_problems(H.load(H.dump(cli, seed, sides)), H.probe_layout(probe, seed, sides)) == []


def test_S_247_drafts_block_names_every_draft_in_table_order(cli, probe):
    """S-247 R-112-04: `drafts` lists every entry of om_lk_draft_name/value, in the order of the X-macro table of
    csrc/layout_drafts.h and of the probe, with the engine's values to a printed hundredth; DRAFT_INF (1e30) clamps
    and prints as exactly 9000000000000000.00 (spec "JSON": a magnitude above 9e15 wu clamps to that value)."""
    text = H.dump(cli, 3)
    raw_inf = H.load_raw(text)["drafts"].get("DRAFT_INF")
    pairs = dict(json.loads(text, parse_float=Decimal, object_pairs_hook=lambda p: p))["drafts"]
    want = H.probe_drafts(probe)
    problems = []
    if [k for k, _ in pairs] != [n for n, _ in want] or [n for n, _ in want] != H.header_draft_names():
        problems.append("names or order differ")
    for (k, v), (_, c) in zip(pairs, want):
        if k == "DRAFT_INF":
            if raw_inf != "9000000000000000.00":
                problems.append(f"{k} prints {raw_inf!r}")
        elif abs(H.cents(v) - c) > 1:
            problems.append(f"{k}: {v} vs {c / 100}")
    assert problems == []


def test_S_247_out_writes_the_file_and_leaves_stdout_empty(cli, tmp_path):
    """S-247 R-112-04: --out F puts the same JSON in F and prints nothing."""
    f = tmp_path / "one.json"
    r = H.run(cli, *H.dump_args(5, "rotate"), "--out", f)
    assert (r.returncode, r.stdout, f.read_text()) == (0, "", H.dump(cli, 5, "rotate"))


@pytest.mark.parametrize("sides,lo,hi", [("separate", 1, 12), ("rotate", 3, 5), ("mirror", 7, 7)])
def test_S_247_seeds_range_writes_named_files_and_one_line_each(cli, tmp_path, sides, lo, hi):
    """S-247 R-112-04: --seeds A..B --out-dir D writes exactly D/layout_assault_s<N>_<sides>.json for N in A..B
    (the single-seed run's JSON) and prints `seed N sides S checks 6/6` per seed; A..A is one seed."""
    r = H.run(cli, "--seeds", f"{lo}..{hi}", "--archetype", "assault", "--sides", sides, "--out-dir", tmp_path)
    names = [f"layout_assault_s{n}_{sides}.json" for n in range(lo, hi + 1)]
    files = {p.name: p.read_text() for p in tmp_path.iterdir()}
    lines = [f"seed {n} sides {sides} checks 6/6" for n in range(lo, hi + 1)]
    assert (r.returncode, r.stdout.splitlines(), sorted(files), [files[n] for n in names]) == (
        0, lines, sorted(names), [H.dump(cli, n, sides) for n in range(lo, hi + 1)])


# ---- exit codes (criterion 5) -----------------------------------------------------------------------------------------
USAGE = [
    ["--seed", "1", "--archetype", "assault", "--bogus"],
    ["--seed", "1", "--archetype", "banana"],
    ["--seed", "1", "--archetype", "assault", "--sides", "sideways"],
    ["--seed", "1", "--archetype"],
]       # criterion 5 names only the unknown archetype; the other malformed-input cases (a non-number, a missing file, an
        # unknown break name ...) are left to the CLI and not pinned here (audit Y3)


@pytest.mark.parametrize("args", USAGE, ids=[" ".join(a)[-40:] for a in USAGE])
def test_S_247_usage_errors_exit_2_with_a_message(cli, args):
    """S-247 R-112-01: a usage error (unknown option, unknown archetype or sides name, a flag without its value)
    exits 2, names the error on stderr and prints no JSON."""
    r = H.run(cli, *args)
    assert (r.returncode, bool(r.stderr.strip()), r.stdout) == (2, True, "")


def test_S_247_an_archetype_other_than_assault_is_not_built(cli):
    """S-247 R-112-01: a known archetype that round A does not build exits 2 and says "not built" (the names are the
    nine other archetypes of csrc/mission.c:161-170 in snake_case, see questions/test-writer2-Q2.md)."""
    rs = [H.run(cli, "--seed", "1", "--archetype", n) for n in ARCHETYPE_NAMES]
    assert ([r.returncode for r in rs], [r.stdout for r in rs], all("not built" in r.stderr for r in rs)) == (
        [2] * 9, [""] * 9, True)


@pytest.mark.parametrize("canvas,rc", [("7999", 1), ("8000", 0), ("64000", 0), ("64001", 1)])
def test_S_247_a_failed_generation_exits_1_and_prints_the_return_code(cli, canvas, rc):
    """S-247 R-112-01: om_lk_generate's -3 (canvas outside 8,000..64,000, both ends accepted) is exit 1 with the
    return code on stderr and no JSON; the ends themselves succeed."""
    r = H.run(cli, *H.dump_args(1, "mirror", canvas=canvas))
    assert (r.returncode, "-3" in r.stderr or rc == 0, bool(r.stdout)) == (rc, True, rc == 0)


# ---- --check (criterion 7) ----------------------------------------------------------------------------------------------
def test_S_247_check_agrees_with_the_checks_in_the_json(cli, tmp_path):
    """S-247 R-112-05: --check on a file this tool wrote prints the six results one per line in spec order, equal to
    the file's own `checks`, exits 0 when all are true; canvases 8,000 and 64,000 included (the canvas comes from the
    file)."""
    cases = [(s, m, None) for s, m in H.ALL36] + [(1, m, c) for m in H.SIDES for c in (8000, 64000)]
    bad = []
    for seed, sides, canvas in cases:
        f = tmp_path / f"c{seed}_{sides}_{canvas}.json"
        f.write_text(H.dump(cli, seed, sides, canvas=canvas))
        checks = H.load(f.read_text())["checks"]
        r = H.run(cli, "--check", f)
        if (r.returncode, r.stdout) != (0 if all(checks.values()) else 1, check_lines(checks)):
            bad.append((seed, sides, canvas, r.returncode, r.stdout))
    assert bad == []


@pytest.mark.parametrize("name", H.CHECKS)
def test_S_247_check_on_a_broken_layout_agrees_with_its_json(cli, tmp_path, name):
    """S-247 R-112-05: the file written by `--break <name>` fails --check: exit 1, the same six lines as its own
    `checks` object, the named check false."""
    f = tmp_path / "broken.json"
    f.write_text(H.dump(cli, 2, "rotate", brk=name))
    checks = H.load(f.read_text())["checks"]
    r = H.run(cli, "--check", f)
    assert (r.returncode, r.stdout, checks[name]) == (1, check_lines(checks), False)


def _edit_approaches(text, canvas):
    lay = H.load(text)
    return H.delete_lane_line(text, H.objective_lanes(lay)[1][0])


def _edit_chokes(text, canvas):
    lines = text.split("\n")
    i = lines.index('  "chokes": [') + 1
    lines[i] = re.sub(r'"width": [-\d.]+', '"width": 800.00', lines[i], count=1)
    return "\n".join(lines)


def _edit_bounds(text, canvas):
    lines = text.split("\n")
    i = lines.index('  "places": [') + 1
    lines[i] = re.sub(r'"x": [-\d.]+', f'"x": {canvas + 100}.00', lines[i], count=1)
    return "\n".join(lines)


@pytest.mark.parametrize("name,edit,canvas", [("approaches", _edit_approaches, 24000), ("chokes", _edit_chokes, 24000),
                                              ("bounds", _edit_bounds, 8000)])
def test_S_247_check_reads_the_file_not_the_seed(cli, tmp_path, name, edit, canvas):
    """S-247 R-112-05: --check judges the lanes, chokes and places in the file: a lane deleted, a choke widened to
    800 wu, a place moved 100 wu past the canvas edge (read from the file: 8,000) each turn the named check from true
    to false, exit 1. The unedited file is the control."""
    text = H.dump(cli, 1, "separate", canvas=canvas)
    got = {}
    for tag, body in (("control", text), ("edited", edit(text, canvas))):
        f = tmp_path / f"{tag}.json"
        f.write_text(body)
        r = H.run(cli, "--check", f)
        got[tag] = (r.returncode if tag == "edited" else None, [ln for ln in r.stdout.splitlines() if ln.startswith(name + " ")])
    assert got == {"control": (None, [f"{name} true"]), "edited": (1, [f"{name} false"])}
