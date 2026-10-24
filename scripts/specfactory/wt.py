#!/usr/bin/env python3
"""STUB for HARNESS-wt-cap: every subcommand prints NOT BUILT and exits 4. The builder replaces this file."""
import argparse
import sys


def main(argv=None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    common.add_argument("--repo")
    common.add_argument("--slots", type=int)
    common.add_argument("--disk-cap-gb", type=float)
    common.add_argument("--free-floor-gb", type=float)
    common.add_argument("--estimate-mb", type=float)
    common.add_argument("--cache-min", type=float)
    common.add_argument("--migration-date")
    ap = argparse.ArgumentParser(prog="wt.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", parents=[common])
    p.add_argument("name")
    p.add_argument("--owner", required=True)
    p.add_argument("--purpose", required=True, nargs="+")
    p.add_argument("--base", default="origin/main")
    p.add_argument("--branch")
    p = sub.add_parser("done", parents=[common])
    p.add_argument("path")
    p.add_argument("sha")
    p = sub.add_parser("status", parents=[common])
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("reap", parents=[common])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int)
    sub.add_parser("check", parents=[common])
    ap.parse_args(argv)
    print("NOT BUILT")
    return 4


if __name__ == "__main__":
    sys.exit(main())
