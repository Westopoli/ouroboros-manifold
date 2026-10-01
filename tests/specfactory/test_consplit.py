# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md A31 (hand constants move to csrc/om_constants_extra.h), A33/A34
"""Constants split: the hand-added constants live in the hand-owned
csrc/om_constants_extra.h; `alg_constants.py --emit` writes the generated
csrc/om_constants.h ending with `#include "om_constants_extra.h"`.

The macro golden (tests/specfactory/fixtures/om_constants_macros.txt) is the
`cc -dM -E` name/value set seen through om_constants.h, recorded from the
header of origin/push/HDR5-ver-td 46db3f71 (OM_WORLD_REGION_COUNT_RANGE_LO/HI
250/400), because HDR5 had not landed on origin/main when it was recorded."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CSRC = REPO / "csrc"
TOOL = REPO / "scripts" / "specfactory" / "alg_constants.py"
GOLDEN = REPO / "tests" / "specfactory" / "fixtures" / "om_constants_macros.txt"
HEADER = CSRC / "om_constants.h"
EXTRA = CSRC / "om_constants_extra.h"
INCLUDE = '#include "om_constants_extra.h"'

# Emitter-only names that enter the macro set through the first full --emit
# (piece 1) or after the names fix (piece 3). Allowed but not required, so the
# golden stays green in either order of the pieces.
EMITTER_ONLY = {
    "OM_OM_MACRO_EXTERNAL_REINFORCEMENT_PROB",
    "OM_OM_MACRO_ROUT_HP_THRESHOLD",
    "OM_TACTICAL_TICK_RATE_ASSAULT",
    "OM_TACTICAL_TICK_RATE_CONTAINMENT",
    "OM_TACTICAL_TICK_RATE_COUNTERINSURGENCY",
    "OM_TACTICAL_TICK_RATE_DEFENSIVE",
    "OM_TACTICAL_TICK_RATE_EVACUATION",
    "OM_TACTICAL_TICK_RATE_FRONT",
    "OM_TACTICAL_TICK_RATE_INTERCEPTION",
    "OM_TACTICAL_TICK_RATE_RECONQUEST",
    "OM_TACTICAL_TICK_RATE_SIEGE",
    "OM_TACTICAL_TICK_RATE_SUPPRESSION",
}
HAND_COUNT = 147


def _macros(csrc: Path) -> dict[str, str]:
    """Name -> value of every valued OM_ macro seen through om_constants.h."""
    out = subprocess.run(
        ["cc", "-dM", "-E", "-x", "c", f"-I{csrc}", "-"],
        input='#include "om_constants.h"\n', capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    return _parse_macros(out.stdout)


def _parse_macros(text: str) -> dict[str, str]:
    macros = {}
    for line in text.splitlines():
        m = re.match(r"#define (OM_\w+) (.+)$", line)
        if m:
            macros[m.group(1)] = m.group(2).strip()
    return macros


def _golden() -> dict[str, str]:
    return _parse_macros(GOLDEN.read_text())


def _golden_diff(seen: dict[str, str]) -> list[str]:
    gold = _golden()
    problems = []
    for name, value in gold.items():
        if name not in seen:
            problems.append(f"missing {name}")
        elif seen[name] != value:
            problems.append(f"changed {name}: {gold[name]} -> {seen[name]}")
    for name in seen:
        if name not in gold and name not in EMITTER_ONLY:
            problems.append(f"unexpected {name}")
    return problems


def _emit_to(path: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--emit", str(path)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return path.read_text()


def _define_names(text: str) -> list[str]:
    return re.findall(r"^#define (OM_\w+) \S", text, re.M)


def _csrc_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "csrc"
    dst.mkdir()
    for h in CSRC.glob("om_constants*.h"):
        shutil.copy(h, dst / h.name)
    return dst


# --- (1) macro golden -------------------------------------------------------


def test_macro_set_through_om_constants_h_matches_golden():
    problems = _golden_diff(_macros(CSRC))
    assert not problems, "\n".join(problems[:20])


# --- (2) --emit reproduces om_constants.h exactly ---------------------------


def test_emit_reproduces_om_constants_h_exactly(tmp_path):
    emitted = _emit_to(tmp_path / "om_constants.h")
    assert emitted == HEADER.read_text()


# --- (3) hand-owned extra header, include at the end of the generated one ---


def test_extra_header_exists_and_is_hand_owned():
    assert EXTRA.is_file(), "csrc/om_constants_extra.h missing"
    text = EXTRA.read_text()
    assert "GENERATED" not in text
    assert len(_define_names(text)) == HAND_COUNT


def test_extra_names_disjoint_from_emitted_names(tmp_path):
    emitted = _define_names(_emit_to(tmp_path / "om_constants.h"))
    clash = set(emitted) & set(_define_names(EXTRA.read_text()))
    assert not clash, sorted(clash)


def test_generated_header_ends_with_extra_include():
    lines = [ln for ln in HEADER.read_text().splitlines() if ln.strip()]
    assert lines[-1] == "#endif /* OM_CONSTANTS_H */"
    assert lines[-2] == INCLUDE


def test_emit_output_ends_with_extra_include(tmp_path):
    lines = [ln for ln in _emit_to(tmp_path / "x.h").splitlines() if ln.strip()]
    assert lines[-2] == INCLUDE


# --- (4) positive controls --------------------------------------------------


def test_control_hand_edit_in_generated_part_fails_exact_emit(tmp_path):
    csrc = _csrc_copy(tmp_path)
    header = csrc / "om_constants.h"
    text = header.read_text()
    edited = re.sub(r"(#define OM_ECON_OSCILLATION_AMPLITUDE )\S+", r"\g<1>7.0", text)
    assert edited != text
    header.write_text(edited)
    assert _emit_to(tmp_path / "fresh.h") != header.read_text()


def test_control_constant_removed_from_extra_fails_golden(tmp_path):
    csrc = _csrc_copy(tmp_path)
    target = "OM_ABILITY_BARRAGE_RADIUS"
    hit = False
    for h in csrc.glob("om_constants*.h"):
        kept = [ln for ln in h.read_text().splitlines(keepends=True)
                if not ln.startswith(f"#define {target} ")]
        if len(kept) != len(h.read_text().splitlines(keepends=True)):
            h.write_text("".join(kept))
            hit = True
    assert hit, f"{target} not defined in any om_constants*.h"
    assert f"missing {target}" in _golden_diff(_macros(csrc))
