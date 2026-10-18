"""CONST-2 (sim lane ledger row 16): the named constants of ALG-12, -16, -18, -19 are read by the
sim, and the refactor changes no byte. docs/bible/algorithms.md ALG-12 BUDGET_PRESSURE_THRESHOLD,
ALG-18 REACTIVE_REINFORCE_*, ALG-19 REINFORCE_*, ATTACK_CONFIDENCE_RANGE.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts/net_xplat_checksum.py"
HEADER = ROOT / "csrc/om_constants.h"

# Recorded from the pre-edit build (seed 11), the control beside seed 3's PINNED_FULL.
SEED11_FULL = {
    100: 8766616544047145964,
    500: 14336596349092945905,
    1000: 2141326127668279842,
    2000: 6940370603924743498,
}


def _probe(seed):
    res = subprocess.run([sys.executable, str(PROBE), str(seed), "2000"], cwd=str(ROOT),
                         capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, res.stderr[-2000:]
    got = {}
    for line in res.stdout.splitlines():
        m = re.search(r"tick=(\d+) full=(\d+)", line)
        if m:
            got[int(m.group(1))] = int(m.group(2))
    return got


def test_CONST_2_every_named_constant_is_read_by_a_c_file():
    names = re.findall(r"^#define\s+(OM_\w+)", HEADER.read_text(), re.M)
    names = [n for n in names if re.search(r"BUDGET_PRESSURE|REINFORCE|ATTACK_CONFIDENCE", n)]
    assert names
    src = "\n".join(p.read_text() for p in (ROOT / "csrc").rglob("*.c"))
    unused = [n for n in names if not re.search(r"\b%s\b" % n, src)]
    assert not unused, f"defined in om_constants.h, read by no .c file: {unused}"


def test_CONST_2_seed3_checksums_unchanged():
    from test_PP_portability import PINNED_FULL
    assert _probe(3) == PINNED_FULL


def test_CONST_2_seed11_checksums_unchanged():
    assert _probe(11) == SEED11_FULL
