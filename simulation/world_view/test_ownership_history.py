import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ownership_history import OwnershipHistory


def _kf(snapshot: dict) -> dict:
    return {
        "regions_snapshot": [
            {"region_id": rid, "owner_faction_id": owner}
            for rid, owner in snapshot.items()
        ]
    }


def main() -> None:
    h = OwnershipHistory(max_jumps=5)

    jumps = [
        ("Jump 1", {"r1": "dominion", "r2": "dominion", "r3": "dominion",
                    "r4": "kestrel",  "r5": "kestrel"}),
        ("Jump 2", {"r1": "dominion", "r2": "dominion", "r3": "dominion",
                    "r4": "dominion", "r5": "kestrel"}),
        ("Jump 3", {"r1": "dominion", "r2": "dominion", "r3": "pellian",
                    "r4": "dominion", "r5": "pellian"}),
        ("Jump 4", {"r1": "pellian",  "r2": "dominion", "r3": "pellian",
                    "r4": "pellian",  "r5": "pellian"}),
        ("Jump 5", {"r1": "pellian",  "r2": "dominion", "r3": "dominion",
                    "r4": "pellian",  "r5": "pellian"}),
    ]

    print("=== ownership_history prove-it ===\n")
    for label, snap in jumps:
        h.observe_keyframe(_kf(snap))
        h.end_jump()
        print(f"{label} owners: {snap}")
    print("")

    print("per-faction region_count_history (oldest..newest)  delta  status")
    for fid in ["dominion", "kestrel", "pellian"]:
        hist = h.region_count_history(fid)
        delta = h.region_count_delta(fid)
        status = h.status(fid)
        print(f"  {fid:10s}  {str(hist):24s}  {delta:+d}     {status}")
    print("")

    print("per-region owner chains:")
    for rid in ["r1", "r2", "r3", "r4", "r5"]:
        chain = h.owner_chain(rid)
        cur = h.current_owner(rid)
        prev = h.previous_owners(rid)
        print(f"  {rid}  current={cur:8s}  previous={prev}  chain={chain}")
    print("")

    print("=== expected vs actual ===")
    expected = {
        "dominion": {"history": [3, 4, 3, 1, 2], "delta": +1, "status": "Rising"},
        "kestrel":  {"history": [2, 1, 0, 0, 0], "delta":  0, "status": "Defeated"},
        "pellian":  {"history": [2, 4, 3],       "delta": -1, "status": "Waning"},
    }
    all_ok = True
    for fid, exp in expected.items():
        got_hist = h.region_count_history(fid)
        got_delta = h.region_count_delta(fid)
        got_status = h.status(fid)
        ok = (got_hist == exp["history"]
              and got_delta == exp["delta"]
              and got_status == exp["status"])
        all_ok = all_ok and ok
        mark = "OK" if ok else "FAIL"
        print(f"  [{mark}] {fid:10s} hist={got_hist} delta={got_delta:+d} status={got_status}")

    expected_chains = {
        "r1": ["dominion", "pellian"],
        "r2": ["dominion"],
        "r3": ["dominion", "pellian", "dominion"],
        "r4": ["kestrel", "dominion", "pellian"],
        "r5": ["kestrel", "pellian"],
    }
    for rid, exp_chain in expected_chains.items():
        got = h.owner_chain(rid)
        ok = got == exp_chain
        all_ok = all_ok and ok
        mark = "OK" if ok else "FAIL"
        print(f"  [{mark}] {rid} chain={got}")

    print("")
    print("ALL PASSED" if all_ok else "SOME FAILED")


if __name__ == "__main__":
    main()
