#!/usr/bin/env python3
"""Deterministic control-band detector (Maintain play). No model involved.

Input: a series of numbers (newest last) via --series "0.1,0.12,..." or --file path (one value per line).
Baseline: mean and population std-dev over the first `--window` points; the remaining points are tested.
Rules (Western Electric):
  3sigma: one point beyond 3σ
  2sigma: two of the last three points beyond 2σ on the same side
  1sigma: four of the last five points beyond 1σ on the same side
Output: the highest breached tier as JSON ({"tier": "3sigma", ...}) and exit code 0 (no breach) / 3 (breach).
The caller (CI job, cron, webhook receiver) maps the tier to bands.yaml and invokes Claude accordingly.
"""
import argparse, json, math, sys

def stats(xs):
    n = len(xs); m = sum(xs) / n
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / n)

def side(x, m, s, k):
    if s == 0: return 0
    if x > m + k * s: return 1
    if x < m - k * s: return -1
    return 0

def detect(series, window):
    if len(series) <= window: return {"tier": None, "reason": "not enough points beyond baseline window"}
    base, recent = series[:window], series[window:]
    m, s = stats(base)
    last = recent[-1]
    if side(last, m, s, 3): return {"tier": "3sigma", "mean": m, "sd": s, "value": last}
    for k, need, of, tier in ((2, 2, 3, "2sigma"), (1, 4, 5, "1sigma")):
        tail = recent[-of:]
        for sgn in (1, -1):
            if sum(1 for x in tail if side(x, m, s, k) == sgn) >= need:
                return {"tier": tier, "mean": m, "sd": s, "value": last, "side": sgn}
    return {"tier": None, "mean": m, "sd": s, "value": last}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series"); ap.add_argument("--file"); ap.add_argument("--window", type=int, default=30)
    a = ap.parse_args()
    if a.series: xs = [float(v) for v in a.series.split(",") if v.strip()]
    elif a.file: xs = [float(l) for l in open(a.file) if l.strip()]
    else: ap.error("--series or --file required")
    r = detect(xs, a.window); print(json.dumps(r)); sys.exit(3 if r["tier"] else 0)

if __name__ == "__main__": main()
