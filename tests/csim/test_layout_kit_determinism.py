# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-2
# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-4
"""S-247 wave 2, leaf 2: the CLI is deterministic (R-112-01) and obeys the libm ban (criterion 4).

Two runs of the CLI with the same inputs print byte-identical JSON; the -O0 and -O2 builds print byte-identical JSON
over 12 seeds by 3 sides modes (and for each --break); scripts/specfactory/libm_lint.py stays clean with the CLI
source in place (it scans every *.c under csrc/, csrc/tools/ included).
Red until csrc/tools/layout_dump.c exists. Budget: see test_layout_kit_cli.py.
"""
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import layout_kit_cli_helpers as H   # noqa: E402


@pytest.fixture(scope="module")
def cli_o2(tmp_path_factory):
    return H.build_cli(tmp_path_factory, "O2")


@pytest.fixture(scope="module")
def cli_o0(tmp_path_factory):
    return H.build_cli(tmp_path_factory, "O0")


def fresh(exe, *args):
    """A new process every time (never the helpers' cache): bytes, not text."""
    r = subprocess.run([str(exe), *map(str, args)], capture_output=True, timeout=120)
    return r.returncode, r.stdout


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_two_runs_print_byte_identical_json(cli_o2, seed, sides):
    """S-247 R-112-01: the same seed, archetype, canvas and sides mode give the same bytes on a second run."""
    a, b = fresh(cli_o2, *H.dump_args(seed, sides)), fresh(cli_o2, *H.dump_args(seed, sides))
    assert (a[0], a == b, len(a[1]) > 1000) == (0, True, True)


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_O0_and_O2_binaries_print_byte_identical_json(cli_o0, cli_o2, seed, sides):
    """S-247 R-112-01: 12 seeds by three sides modes: the -O0 and the -O2 build print the same bytes."""
    a, b = fresh(cli_o0, *H.dump_args(seed, sides)), fresh(cli_o2, *H.dump_args(seed, sides))
    assert (a[0], a == b, len(a[1]) > 1000) == (0, True, True)


@pytest.mark.parametrize("name", H.CHECKS)
def test_S_247_O0_and_O2_binaries_agree_on_every_break(cli_o0, cli_o2, name):
    """S-247 R-112-01: the edited layouts (the fairness edit does arithmetic on doubles) are byte-identical at -O0 and
    -O2 as well."""
    a = fresh(cli_o0, *H.dump_args(6, "rotate", brk=name))
    b = fresh(cli_o2, *H.dump_args(6, "rotate", brk=name))
    assert (a[0], a == b, len(a[1]) > 1000) == (0, True, True)


def test_S_247_libm_lint_is_clean_with_the_cli_present():
    """S-247 R-112-01 (criterion 4): the CLI source exists and scripts/specfactory/libm_lint.py exits 0 over csrc/ (so no pow, sin,
    cos, rand, time, qsort ... in csrc/tools/ either). When LAYOUT_DUMP_SRC points elsewhere the directory holding
    that file is linted instead."""
    src = H.cli_source()
    root = H.CSRC if src.is_relative_to(H.CSRC) else src.parent
    r = subprocess.run([sys.executable, str(H.REPO / "scripts" / "specfactory" / "libm_lint.py"), str(root)],
                       capture_output=True, text=True)
    assert (src.is_file(), r.returncode) == (True, 0), r.stdout[-500:]
