"""Run a back end over a control set (<dir>/controls.json); report false passes and agreement.

Exit 1 if false passes exceed DRAFT-look-false-pass-max (Westley's number). UNSURE counts as FAIL.
"""
import argparse
import json
import sys
from pathlib import Path

from scripts.look.backends import judge

DRAFT_LOOK_FALSE_PASS_MAX = 0  # DRAFT-look-false-pass-max


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", required=True)
    ap.add_argument("--backend", required=True)
    args = ap.parse_args(argv)
    root = Path(args.controls)
    rows = json.loads((root / "controls.json").read_text())
    false_pass, agree = {}, 0
    for row in rows:
        chk = {"name": row["check"], "backend": args.backend, "truth": row["truth"],
               "prompt": row.get("prompt", "Check: %s. Look at the frame." % row["check"])}
        verdict = judge(root / row["frame"], chk)["verdict"]
        verdict = "PASS" if verdict == "PASS" else "FAIL"
        false_pass.setdefault(row["check"], 0)
        if row["role"] == "break" and verdict == "PASS":
            false_pass[row["check"]] += 1
        agree += verdict == row["label"]
    report = {"false_pass": false_pass, "agreement": agree / len(rows) if rows else 1.0, "controls": len(rows)}
    print(json.dumps(report, sort_keys=True))
    return 1 if sum(false_pass.values()) > DRAFT_LOOK_FALSE_PASS_MAX else 0


if __name__ == "__main__":
    sys.exit(main())
