#!/usr/bin/env python3
"""Deterministic control-band detector (Maintain play). No model involved.

Input: a series of numbers (newest last) via --series "0.1,0.12,..." or --file path (one value per line).
Baseline: for each tested run the mean and population std-dev of the `--window` points that precede
the run (a trailing baseline; the run never estimates its own limits). Every point after the first
`--window` is tested and the highest tier seen is reported, with the index of the breaching point.
Rules (Western Electric):
  3sigma: one point beyond 3σ
  2sigma: two of three consecutive points beyond 2σ on the same side
  1sigma: four of five consecutive points beyond 1σ on the same side
  drift:  eight consecutive points on one side of the mean (acts as the 1sigma tier)
A zero-variance baseline (thirty green days) treats any point that differs from the mean as beyond
every band, so the first bad day after a flat run still breaches.
Output: the highest breached tier as JSON ({"tier": "3sigma", "index": 30, ...}) and exit code
0 (no breach) / 3 (breach). Bad input (--window < 2, NaN, a non-numeric value) is one line on stderr
and exit 2. The caller (CI job, cron, webhook receiver) maps the tier to bands.yaml and invokes
Claude accordingly.
"""
import argparse, json, math, sys

RANK = {None: 0, "drift": 1, "1sigma": 2, "2sigma": 3, "3sigma": 4}
RULES = (  # (k sigma, points needed, run length, tier, description)
    (3, 1, 1, "3sigma", "one point beyond 3 sigma"),
    (2, 2, 3, "2sigma", "two of three beyond 2 sigma on one side"),
    (1, 4, 5, "1sigma", "four of five beyond 1 sigma on one side"),
    (0, 8, 8, "drift", "eight consecutive on one side of the mean"),
)

def stats(xs):
    n = len(xs); m = sum(xs) / n
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / n)

def side(x, m, s, k):
    """+1 above the k-sigma band, -1 below it, 0 inside. With s == 0 any difference is outside."""
    if s == 0:
        return 0 if x == m else (1 if x > m else -1)
    if x > m + k * s: return 1
    if x < m - k * s: return -1
    return 0

def test_point(series, i, window):
    """Apply each rule to the run of `of` points ending at index i. The baseline is the `window`
    points before that run, so a sustained shift is not absorbed into its own limits."""
    for k, need, of, tier, rule in RULES:
        start = i - of + 1
        if start < window:
            continue
        m, s = stats(series[start - window:start])
        run = series[start:i + 1]
        for sgn in (1, -1):
            if sum(1 for y in run if side(y, m, s, k) == sgn) >= need:
                r = {"tier": tier, "mean": m, "sd": s, "value": series[i], "index": i, "side": sgn, "rule": rule}
                if tier == "drift":
                    r["acts_as"] = "1sigma"
                return r
    return None

def detect(series, window):
    if window < 2:
        raise ValueError("--window must be at least 2 (a baseline needs two points)")
    if any(math.isnan(x) or math.isinf(x) for x in series):
        raise ValueError("series contains a non-finite value")
    if len(series) <= window:
        return {"tier": None, "reason": "not enough points beyond baseline window", "tested": 0}
    best = None
    for i in range(window, len(series)):
        r = test_point(series, i, window)
        if r and RANK[r["tier"]] > RANK[best["tier"] if best else None]:
            best = r
    if best is None:
        m, s = stats(series[-window - 1:-1])
        return {"tier": None, "mean": m, "sd": s, "value": series[-1], "tested": len(series) - window}
    best["tested"] = len(series) - window
    return best

def parse_values(tokens):
    xs = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        try:
            xs.append(float(t))
        except ValueError:
            raise ValueError(f"not a number: {t!r}")
    return xs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series"); ap.add_argument("--file"); ap.add_argument("--window", type=int, default=30)
    a = ap.parse_args()
    try:
        if a.series: xs = parse_values(a.series.split(","))
        elif a.file: xs = parse_values(open(a.file))
        else: ap.error("--series or --file required")
        r = detect(xs, a.window)
    except ValueError as e:
        print(f"detect_bands: {e}", file=sys.stderr); sys.exit(2)
    print(json.dumps(r)); sys.exit(3 if r["tier"] else 0)

if __name__ == "__main__": main()
