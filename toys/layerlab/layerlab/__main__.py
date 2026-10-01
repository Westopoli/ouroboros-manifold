"""Command line: python3 -m layerlab run | check | exchange | sweep | replay | batch | crossings (SPEC.md section 8)."""
import argparse
import json
import sys
import tomllib

from .ffi import WIN_A, WIN_B, WIN_CAP, WIN_MUTUAL, WIN_STALEMATE
from .scenario import load, set_path

_WINNER = {WIN_A: "A", WIN_B: "B", WIN_STALEMATE: "STALEMATE", WIN_CAP: "CAP", WIN_MUTUAL: "MUTUAL"}


def _literal(text):
    try:
        return tomllib.loads("v = " + text)["v"]
    except tomllib.TOMLDecodeError:
        return text.strip()


def _load(args):
    scn = load(args.scenario)
    for item in getattr(args, "set", None) or []:
        path, sep, val = item.partition("=")
        if not sep:
            raise ValueError("--set needs path=value, got %r" % item)
        scn = set_path(scn, path.strip(), _literal(val))
    return scn


def _run(args):
    from .run import run
    res = run(_load(args), seed=args.seed)
    print("winner %s  ticks %d  survivors %d %d" % (_WINNER.get(res.winner, res.winner), res.ticks, *res.survivors))
    print("hp_ratio A %.3f B %.3f  cost_lost A %g B %g" % (*res.hp_ratio, *res.cost_lost))


def _check(args):
    from .analysis import check
    print(check(_load(args), range(args.seeds), window=args.window).text)


def _exchange(args):
    from .analysis import check_exchange, exchange
    from .run import run
    scn = _load(args)
    r = check_exchange(scn, range(args.seeds), window=args.window)
    show = lambda v: "-" if v is None else "%.3f" % v
    print("exchange check: seeds %d  window %d  agree fraction %s  mean firing ratio %s  "
          "mean damage ratio %s  higher-firing side won %s"
          % (args.seeds, args.window, show(r["agree_fraction"]), show(r["firing_ratio"]),
             show(r["damage_ratio"]), show(r["higher_firing_won"])))
    if args.seeds > 0:
        print(exchange(run(scn, seed=0, trace=True), scn, window=args.window).text)


def _sweep(args):
    import matplotlib
    from .sweep import sweep
    matplotlib.use("Agg")
    values = [_literal(v) for v in args.values.split(",")]
    values2 = [_literal(v) for v in args.values2.split(",")] if args.values2 else None
    t = sweep(_load(args), args.var, values, seeds=range(args.seeds), var2=args.var2, values2=values2,
              metric=args.metric, expect=args.expect, out_dir=args.out_dir, log=not args.no_log,
              transfer_class=args.transfer_class)
    print("png %s" % t.png)


def _replay(args):
    scn = _load(args)
    if args.gif:
        import matplotlib
        matplotlib.use("Agg")
    from .replay import replay, save_gif
    anim = replay(scn, seed=args.seed)
    if args.gif:
        save_gif(anim, args.gif)
        print("gif %s" % args.gif)
    else:
        import matplotlib.pyplot as plt
        plt.show()


def _batch(args):
    from .batch import run_rows, write_rows
    from .sample import grid, make_jobs, random_samples
    scn = _load(args)
    with open(args.dims) as fh:
        dims = json.load(fh)
    if not isinstance(dims, list):
        raise ValueError("%s: the dims file must hold a JSON list of dimensions" % args.dims)
    samples = random_samples(dims, args.n, args.seed) if args.n is not None else grid(dims, args.grid)
    jobs, skipped = make_jobs(scn, samples, range(args.seeds))
    rows = run_rows(jobs, processes=args.procs)
    write_rows(rows, args.out)
    print("wrote %d rows to %s (%d samples skipped)" % (len(rows), args.out, len(skipped)))
    for sample, reason in skipped:
        print("skipped %s: %s" % (sample, reason), file=sys.stderr)


def _crossings(args):
    from .batch import read_rows
    from .crossing_search import crossing_shift
    rows = read_rows(args.rows)
    if not rows:
        raise ValueError("%s has no rows" % args.rows)
    for path in (args.var, args.by):
        if "set:" + path not in rows[0]:
            raise ValueError("%s has no column 'set:%s'" % (args.rows, path))
    print(crossing_shift(rows, args.var, args.by, expect=args.expect).text)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m layerlab")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run one engagement")
    r.add_argument("scenario")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--set", action="append", metavar="PATH=VALUE", help="override a scenario path (TOML literal)")
    r.set_defaults(fn=_run)

    c = sub.add_parser("check", help="compare the firing-share prediction with actual winners")
    c.add_argument("scenario")
    c.add_argument("--seeds", type=int, default=20, help="N means seeds 0..N-1")
    c.add_argument("--window", type=int, default=40, help="opening-window ticks from the first shot; 0 turns it off")
    c.add_argument("--set", action="append", metavar="PATH=VALUE")
    c.set_defaults(fn=_check)

    x = sub.add_parser("exchange", help="windowed firing, damage and loss shares per window")
    x.add_argument("scenario")
    x.add_argument("--seeds", type=int, default=20, help="N means seeds 0..N-1")
    x.add_argument("--window", type=int, default=20, help="ticks per window from the first shot")
    x.add_argument("--set", action="append", metavar="PATH=VALUE")
    x.set_defaults(fn=_exchange)

    s = sub.add_parser("sweep", help="sweep one or two scenario paths over several seeds")
    s.add_argument("scenario")
    s.add_argument("--var", required=True)
    s.add_argument("--values", required=True, help="comma-separated TOML literals")
    s.add_argument("--var2")
    s.add_argument("--values2")
    s.add_argument("--seeds", type=int, default=5, help="N means seeds 0..N-1")
    s.add_argument("--metric", default="win_rate")
    s.add_argument("--expect", default="A", choices=["A", "B"])
    s.add_argument("--class", dest="transfer_class", choices=["T1", "T2", "T3"])
    s.add_argument("--out-dir")
    s.add_argument("--no-log", action="store_true")
    s.add_argument("--set", action="append", metavar="PATH=VALUE")
    s.set_defaults(fn=_sweep)

    v = sub.add_parser("replay", help="animate a traced run")
    v.add_argument("scenario")
    v.add_argument("--seed", type=int, default=0)
    v.add_argument("--gif")
    v.add_argument("--set", action="append", metavar="PATH=VALUE")
    v.set_defaults(fn=_replay)

    b = sub.add_parser("batch", help="sample many variables, run every fight, write one CSV row per fight")
    b.add_argument("scenario")
    b.add_argument("--dims", required=True, help="JSON file: a list of dimension dicts")
    how = b.add_mutually_exclusive_group(required=True)
    how.add_argument("--n", type=int, help="N random samples")
    how.add_argument("--grid", type=int, help="K points per dimension")
    b.add_argument("--seed", type=int, default=0, help="seed of the sampler")
    b.add_argument("--seeds", type=int, default=5, help="N means fight seeds 0..N-1")
    b.add_argument("--procs", type=int, help="worker processes; omitted, 0 or 1 runs serially")
    b.add_argument("--out", required=True)
    b.set_defaults(fn=_batch)

    k = sub.add_parser("crossings", help="does the 0.5 crossing of --var move, or gain a second, with --by")
    k.add_argument("rows")
    k.add_argument("--var", required=True)
    k.add_argument("--by", required=True)
    k.add_argument("--expect", default="A", choices=["A", "B"])
    k.set_defaults(fn=_crossings)

    args = p.parse_args(argv)
    if args.cmd == "sweep" and args.var2 and not args.values2 or args.cmd == "sweep" and args.values2 and not args.var2:
        p.error("--var2 and --values2 go together")
    try:
        args.fn(args)
    except (KeyError, ValueError, OSError, NotImplementedError, RuntimeError) as e:
        print("error: %s" % (e.args[0] if isinstance(e, KeyError) and e.args else e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
