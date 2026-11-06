# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-4
"""S-247 wave 1, leaf 1: the engine's source rules (R-112-06; the DRAFT rule of spec 'Acceptance' criterion 4).

R-112-06: the kit is never fed the retired hand-drawn library, so no csrc/layout_kit* or csrc/layout_drafts.h text
names it and none includes layout_internal.h. Criterion 4: every numeric literal in csrc/layout_kit*.c other than 0, 1,
2 and array sizes is a macro (DRAFT_, or an LK_RNG_ constant defined in layout_drafts.h), libm_lint passes, no heap.
The file-set assertion keeps this file red on the sentinel.
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
CSRC = REPO / "csrc"
EXPECTED_FILES = ["layout_drafts.h", "layout_kit.c", "layout_kit_pieces.c", "layout_kit_graph.c"]
# Comments, string literals and character literals first (so digits in them do not count).
_STRIP = re.compile(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])+'", re.S)
_ARRAY_SIZE = re.compile(r"\[\s*\d+\s*\]")
_TOKEN = re.compile(r"(?P<id>[A-Za-z_]\w*)|(?P<hex>0[xX][0-9a-fA-F]+[uUlL]*)"
                    r"|(?P<num>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fFuUlL]*)")


def literals_other_than_0_1_2(src):
    """Numeric literals of C source outside comments/strings/#include lines/array sizes whose value is not 0, 1 or 2."""
    src = _STRIP.sub(" ", src)
    src = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#include"))
    src = _ARRAY_SIZE.sub("[]", src)
    bad = []
    for m in _TOKEN.finditer(src):
        txt = m.group("hex") or m.group("num")
        if not txt:
            continue
        digits = txt.rstrip("uUlLfF") if not m.group("hex") else txt.rstrip("uUlL")
        val = float(int(digits, 16)) if m.group("hex") else float(digits)
        if val not in (0.0, 1.0, 2.0):
            bad.append(txt)
    return bad


def test_S_247_the_engine_is_four_files_and_a_header():
    """S-247 R-112-02: leaf 1 delivers csrc/layout_drafts.h, layout_kit.c, layout_kit_pieces.c, layout_kit_graph.c."""
    missing = [f for f in EXPECTED_FILES if not (CSRC / f).is_file()]
    assert missing == [], missing


def test_S_247_every_literal_in_the_kit_is_a_draft_macro():
    """S-247 R-112-02 (criterion 4): every numeric literal in csrc/layout_kit*.c other than 0, 1, 2 and array sizes is
    a DRAFT_ (or LK_RNG_) macro; the drafts live in csrc/layout_drafts.h inside the LK_DRAFT_TABLE(X) table, with the
    splitmix constants as LK_RNG_ macros beside it."""
    # detector control: 37, 0x9E37u, 1.5 and a #define body are flagged; 0, 1, 2, 2.0, array sizes, strings, comments not
    flagged = literals_other_than_0_1_2("int a = 37; u64 b = 0x9E37u; double c = 1.5; #define Q 3\n")
    spared = literals_other_than_0_1_2('int t[16]; /* 99 */ // 98\nchar *s = "7 8"; int z = 0, o = 1, w = 2; double d = 2.0;\n'
                                      '#include <stdint.h>\nint e = DRAFT_X + om_tn_sin_q16(0);\n')
    assert flagged == ["37", "0x9E37u", "1.5", "3"] and spared == []
    files = sorted(CSRC.glob("layout_kit*.c"))
    assert len(files) >= 3, files
    bad = {f.name: literals_other_than_0_1_2(f.read_text()) for f in files}
    bad = {k: v[:8] for k, v in bad.items() if v}
    assert bad == {}, bad
    drafts = (CSRC / "layout_drafts.h").read_text()
    assert "LK_DRAFT_TABLE" in drafts and "LK_RNG_" in drafts and "DRAFT_EQUAL_TOL" in drafts


def test_S_247_libm_lint_passes_and_there_is_no_heap_or_clock():
    """S-247 R-112-01 (criterion 4): scripts/specfactory/libm_lint.py exits 0 on csrc/ and the kit never allocates
    or reads a clock or file (no heap; the engine reads nothing)."""
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "specfactory" / "libm_lint.py"), str(CSRC)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-1500:]
    assert len(sorted(CSRC.glob("layout_kit*.c"))) >= 3      # the lint must have had the pieces and graph files to scan
    src = "\n".join(_STRIP.sub(" ", f.read_text()) for f in sorted(CSRC.glob("layout_kit*.c")))
    assert re.findall(r"\b(malloc|calloc|realloc|free|fopen|getenv)\s*\(", src) == [] and src.strip()


def test_S_247_the_kit_never_reads_the_old_library_or_the_sibling_engine():
    """S-247 R-112-06: no layout_kit* or layout_drafts file names simulation/layout_library or includes
    layout_internal.h (the sibling places engine's header)."""
    texts = {f.name: f.read_text() for f in sorted(CSRC.glob("layout_kit*")) + [CSRC / "layout_drafts.h"] if f.is_file()}
    hits = [n for n, t in texts.items() if "layout_library" in t or re.search(r'#\s*include\s*[<"]layout_internal\.h', t)]
    assert hits == [] and "layout_drafts.h" in texts
