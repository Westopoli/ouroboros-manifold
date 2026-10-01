"""C1 / gap-fix S5: no stale "STUB" label on om_tactical_step.

om_tactical_step is a real orchestrator (csrc/unit.c, called from sim.c and the
pipe's tactical_step verb). The header comment above the E-11 block and the
pipe's top-of-file comment still call it a STUB. Source-text test: no STUB
within 200 characters of a mention of om_tactical_step in those two comments.

Positive control: the helper must flag a synthetic stale sentence.
Ids: S5.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [ROOT / "csrc/ouroboros_sim.h", ROOT / "csrc/pipe/om_pipe.c"]
NEAR = re.compile(r"om_tactical_step.{0,200}?STUB|STUB.{0,200}?om_tactical_step", re.S)


def test_s5_detector_positive_control():
    assert NEAR.search("om_tactical_step is a STUB in csrc/unit.c")
    assert NEAR.search("... STUBs (csrc/unit.c: wiring) ... and om_tactical_step itself")
    assert not NEAR.search("om_tactical_step runs the tactical systems once")


def test_s5_no_stub_label_on_om_tactical_step():
    stale = []
    for path in FILES:
        m = NEAR.search(path.read_text())
        if m:
            stale.append(f"{path.relative_to(ROOT)}: {' '.join(m.group(0).split())[:120]}")
    assert not stale, "stale STUB label on om_tactical_step: " + "; ".join(stale)
