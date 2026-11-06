"""S-247 umbrella: the layout kit makes an Assault layout whose checks all pass (R-112-01..R-112-08, R-113-01..R-113-05).

Red until the cascade docs/northstar/plans/cascades/layout-kit-assault/ lands: builds layout_dump with cc into a
tmpdir using the determinism flags of tests/csim/test_VG_P_p1_layout.py:118-121, runs seed 1, Assault, separate.
"""
import json
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]
CHECKS = ["connected", "fairness", "bypass", "approaches", "chokes", "bounds"]


@pytest.fixture(scope="module")
def dump_bin(tmp_path_factory):
    out = tmp_path_factory.mktemp("lk") / "layout_dump"
    cli = CSRC / "tools" / "layout_dump.c"
    assert cli.exists(), "csrc/tools/layout_dump.c is leaf 2 of the S-247 cascade"
    srcs = sorted(CSRC.glob("layout_kit*.c")) + [CSRC / "terrain_noise.c"]
    r = subprocess.run(["cc", *FLAGS, "-I", str(CSRC), "-o", str(out), str(cli), *map(str, srcs), "-lm"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return out


def test_S_247_assault_seed_1_all_checks_green(dump_bin):
    """S-247 R-112-05: seed 1, Assault, sides separate: every check passes and the places are all there."""
    r = subprocess.run([str(dump_bin), "--seed", "1", "--archetype", "assault", "--sides", "separate"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    lay = json.loads(r.stdout)
    assert lay["schema"] == "om-layout-1"
    assert all(lay["checks"][c] is True for c in CHECKS), lay["checks"]
    kinds = [p["kind"] for p in lay["places"]]
    for need, n in (("objective", 1), ("base_home", 1), ("base_forward", 1), ("resource", 2), ("expansion", 2)):
        assert kinds.count(need) == n, (need, kinds)
    assert len(lay["chokes"]) >= 1 and len(lay["vantages"]) >= 1
