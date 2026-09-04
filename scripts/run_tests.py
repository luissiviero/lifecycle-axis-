#!/usr/bin/env python3
"""Run the kit's test modules concurrently, one `unittest discover` subprocess per module.

Same discovery as `python3 -m unittest discover -s scripts -p 'test_*.py'`, same exit code
(0 only when every module passes), and a final summary in the same two-line shape --
`Ran N tests in Xs` then `OK` / `FAILED (...)` -- so nothing that reads verify.sh output has
to change.

Why this exists: the suite is subprocess-bound (every hook case spawns bash+jq, and
test_adopt.py runs adopt.sh). That costs ~30 s on Linux CI and ~10 min serial on the owner's
2-core Windows PC, where process creation is the whole bill. The modules are independent --
each builds its own temp tree -- so running them side by side turns the sum into roughly the
slowest module. `-j 1` (or SDLC_TEST_JOBS=1) is the old serial behaviour, useful when a
failure needs a quiet log.

Failure output is printed per module, in full, after its summary line; passing modules print
one line each.
"""
import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

RAN_RE = re.compile(r"^Ran (\d+) tests? in [0-9.]+s$", re.M)
OK_RE = re.compile(r"^OK(?: \((.*)\))?$", re.M)
FAILED_RE = re.compile(r"^FAILED \((.*)\)$", re.M)
# Labels can carry a space ("expected failures=1", "unexpected successes=1"); keep them whole so
# they are not folded into the plain failures= / successes= buckets.
COUNT_RE = re.compile(r"([a-z]+(?: [a-z]+)?)=(\d+)")

# Modules that dominate the wall clock start first so their run overlaps the small ones.
FIRST = ("test_adopt.py",)


def discover(start, pattern):
    import fnmatch

    names = sorted(n for n in os.listdir(start) if fnmatch.fnmatch(n, pattern) and n.endswith(".py"))
    head = [n for n in FIRST if n in names]
    return head + [n for n in names if n not in head]


def run_module(start, name):
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", start, "-p", name, "-q"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    m = RAN_RE.search(out)
    counts = {}
    verdict = OK_RE.search(out) or FAILED_RE.search(out)
    if verdict and verdict.group(1):
        counts = {k: int(v) for k, v in COUNT_RE.findall(verdict.group(1))}
    return {
        "name": name,
        "rc": proc.returncode,
        "tests": int(m.group(1)) if m else None,  # None: the module never reached a summary
        "counts": counts,
        "output": out,
        "secs": time.monotonic() - t0,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-s", "--start", default=HERE, help="directory to discover in (default: scripts/)")
    ap.add_argument("-p", "--pattern", default="test_*.py", help="module glob (default: test_*.py)")
    ap.add_argument(
        "-j", "--jobs", type=int, default=int(os.environ.get("SDLC_TEST_JOBS") or 0),
        help="concurrent modules (default: SDLC_TEST_JOBS or the CPU count)",
    )
    args = ap.parse_args(argv)
    jobs = args.jobs if args.jobs > 0 else (os.cpu_count() or 2)

    # When stdout is a pipe on Windows, Python picks cp1252 and the ✔/✘ marks below would raise.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    names = discover(args.start, args.pattern)
    if not names:
        print("run_tests: no modules match %s in %s" % (args.pattern, args.start), file=sys.stderr)
        return 1

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(lambda n: run_module(args.start, n), names))

    total = 0
    counts = {}
    failed = []
    for r in results:
        broken = r["rc"] != 0 or r["tests"] is None
        mark = "✘" if broken else "✔"
        detail = ("%d tests" % r["tests"]) if r["tests"] is not None else "no summary line"
        extra = "".join(" %s=%d" % kv for kv in sorted(r["counts"].items()))
        print("  %s %-40s %s%s  %.1fs" % (mark, r["name"], detail, extra, r["secs"]))
        if broken:
            failed.append(r)
            print(r["output"].rstrip())
            print()
        total += r["tests"] or 0
        for k, v in r["counts"].items():
            counts[k] = counts.get(k, 0) + v

    summary = ", ".join("%s=%d" % kv for kv in sorted(counts.items()))
    print()
    print("Ran %d tests in %.3fs" % (total, time.monotonic() - t0))
    if failed:
        if "no summary line" in summary or any(r["tests"] is None for r in failed):
            summary = (summary + ", " if summary else "") + "modules_without_summary=%d" % sum(
                1 for r in failed if r["tests"] is None
            )
        print("FAILED (%s)" % summary)
        return 1
    print("OK" + (" (%s)" % summary if summary else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
