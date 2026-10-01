"""Sampling many scenario variables at once (SPEC.md section 8: sample.py)."""
import copy
import itertools
import math
import random

from .scenario import set_path, to_c

_KINDS = ("float", "int", "choice")


def _check(dim):
    if not isinstance(dim, dict) or "path" not in dim:
        raise ValueError("a dimension needs a 'path': %r" % (dim,))
    kind = dim.get("kind")
    if kind not in _KINDS:
        raise ValueError("dimension %r: kind must be one of %s, got %r" % (dim["path"], list(_KINDS), kind))
    if kind == "choice":
        if not dim.get("values"):
            raise ValueError("dimension %r: a choice needs non-empty 'values'" % dim["path"])
        return
    for k in ("lo", "hi"):
        if k not in dim:
            raise ValueError("dimension %r: missing %r" % (dim["path"], k))
    lo, hi = dim["lo"], dim["hi"]
    if lo > hi:
        raise ValueError("dimension %r: lo %r is above hi %r" % (dim["path"], lo, hi))
    if dim.get("log") and lo <= 0:
        raise ValueError("dimension %r: a log dimension needs lo > 0, got %r" % (dim["path"], lo))


def _axis(dim, count):
    if dim["kind"] == "choice":
        return list(dim["values"])
    lo, hi = float(dim["lo"]), float(dim["hi"])
    if count < 1:
        raise ValueError("dimension %r: per_dim must be at least 1, got %r" % (dim["path"], count))
    if count == 1:
        vals = [lo]
    elif dim.get("log"):
        a, b = math.log(lo), math.log(hi)
        vals = [lo] + [math.exp(a + (b - a) * i / (count - 1)) for i in range(1, count - 1)] + [hi]
    else:
        vals = [lo] + [lo + (hi - lo) * i / (count - 1) for i in range(1, count - 1)] + [hi]
    if dim["kind"] == "int":
        return list(dict.fromkeys(round(v) for v in vals))
    return vals


def grid(dims, per_dim):
    axes = []
    for dim in dims:
        _check(dim)
        count = per_dim
        if isinstance(per_dim, dict) and dim["kind"] != "choice":
            if dim["path"] not in per_dim:
                raise ValueError("per_dim has no count for %r" % dim["path"])
            count = per_dim[dim["path"]]
        axes.append(_axis(dim, count))
    paths = [d["path"] for d in dims]
    return [dict(zip(paths, point)) for point in itertools.product(*axes)]


def _draw(rng, dim):
    kind = dim["kind"]
    if kind == "choice":
        return rng.choice(dim["values"])
    lo, hi = dim["lo"], dim["hi"]
    if kind == "int" and not dim.get("log"):
        return rng.randint(int(lo), int(hi))
    if dim.get("log"):
        v = math.exp(rng.uniform(math.log(lo), math.log(hi)))
    else:
        v = rng.uniform(float(lo), float(hi))
    v = min(max(v, lo), hi)
    return min(max(round(v), lo), hi) if kind == "int" else float(v)


def random_samples(dims, n, seed=0):
    for dim in dims:
        _check(dim)
    rng = random.Random(seed)
    return [{d["path"]: _draw(rng, d) for d in dims} for _ in range(n)]


def make_jobs(scn, samples, seeds, constraint=None):
    seeds = list(seeds)
    jobs, skipped = [], []
    for sample in samples:
        applied = scn
        for path, value in sample.items():
            applied = set_path(applied, path, value)
        if constraint is not None and not constraint(applied):
            skipped.append((sample, "constraint"))
            continue
        try:
            to_c(applied)
        except ValueError as e:
            skipped.append((sample, str(e)))
            continue
        for seed in seeds:
            jobs.append({"scenario": copy.deepcopy(applied), "seed": seed, "settings": dict(sample)})
    return jobs, skipped
