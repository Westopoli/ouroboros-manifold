"""Direct probes of csrc/chronicle.c categorisers over ctypes (sim-lane scout B).

The real template names are Title Case ("Regional Revolt", csrc/events.c evt_mk); the
categorisers match lower-case substrings with strstr (csrc/chronicle.c, R-067-02/04).
Run: .venv python -m scripts.simlane.chronicle_probe
"""
import ctypes
from pathlib import Path

from scripts.simlane.chronicle_source import TEMPLATES

LIB = ctypes.CDLL(str(Path(__file__).resolve().parents[2] / "libouroboros.so"))
CHAIN = LIB.om_chronicle_categorize_chain_cluster
CHAIN.restype = ctypes.c_uint32
CHAIN.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32] + [ctypes.c_double] * 3
LINE = LIB.om_chronicle_categorize_lineage_cluster
LINE.restype = ctypes.c_uint32
LINE.argtypes = [ctypes.c_void_p, ctypes.c_char_p] + [ctypes.c_double] * 3

CHAIN_NAMES = {10: "chain_revolt_spawned", 11: "chain_expansion", 12: "chain_cascade",
               13: "chain_conflict_victory", 14: "chain_conflict_defeat",
               15: "chain_conflict_stalemate", 16: "chain_crisis_resolved_well",
               17: "chain_crisis_resolved_badly"}
LINE_NAMES = {0: "lineage_succession", 1: "lineage_military_action", 2: "lineage_thrived",
              3: "lineage_suffered", 4: "lineage_quiet"}


def main():
    print("chain categoriser, net 0/0/0 (so only the name can pick revolt/expansion), 1 event")
    for name in TEMPLATES:
        t = CHAIN(None, name.encode(), 1, 0.0, 0.0, 0.0)
        lo = CHAIN(None, name.lower().encode(), 1, 0.0, 0.0, 0.0)
        flag = "" if t == lo else "   <-- case changes the category"
        print("  %-26s as sent %-28s lower-cased %-28s%s" % (name, CHAIN_NAMES[t], CHAIN_NAMES[lo], flag))
    print("lineage categoriser, net 0/0/0")
    for name in TEMPLATES + ["Succession Crisis", "Natural Death"]:
        t = LINE(None, name.encode(), 0.0, 0.0, 0.0)
        lo = LINE(None, name.lower().encode(), 0.0, 0.0, 0.0)
        flag = "" if t == lo else "   <-- case changes the category"
        print("  %-26s as sent %-26s lower-cased %-26s%s" % (name, LINE_NAMES[t], LINE_NAMES[lo], flag))
    print("chain 'expansion'/'coloniz' substrings in any launch template name:",
          [n for n in TEMPLATES if "expansion" in n.lower() or "coloniz" in n.lower()])


if __name__ == "__main__":
    main()
