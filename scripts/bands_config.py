#!/usr/bin/env python3
"""Print the GitHub-sourced metrics of monitoring/bands.yaml as a workflow matrix.

`.github/workflows/bands.yml` runs this in its first job and feeds the output to
`strategy.matrix` via fromJSON(), so the workflow and bands.yaml cannot drift apart.

Output (one line): {"include": [{"metric": ..., "source": ..., "tools": ..., "window": N}, ...]}
  metric  -- the `metric:` name
  source  -- its `source:` command (only metrics whose source starts with scripts/github_metrics.py)
  tools   -- the 2sigma tier's `tools:` allowlist ("" if none)
  window  -- its `window:` (the detector's trailing baseline length; integer >= 2, required)

Stdlib only: verify.sh and the unit suite must run where PyYAML is absent, so this reads the
shape bands.yaml has today (a `metrics:` list of one-line scalars plus a `tiers:` mapping of flow
mappings) and refuses anything else with a message naming the line. Exit 2 on any problem.
"""
import argparse, json, sys

GH_SOURCE = "scripts/github_metrics.py"


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _strip_comment(raw):
    """Drop a trailing `# ...` unless the `#` is inside quotes."""
    quote = None
    for i, ch in enumerate(raw):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i]
    return raw


def _flow_map(text, raw):
    """`{ action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }` -> dict.
    Commas inside quotes or brackets do not split entries."""
    text = text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError(f"expected a flow mapping `{{ key: value, ... }}`: {raw.strip()!r}")
    parts, cur, depth, quote = [], "", 0, None
    for ch in text[1:-1]:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "[{":
            depth += 1
            cur += ch
        elif ch in "]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    out = {}
    for p in parts:
        k, sep, v = p.partition(":")
        if not sep:
            raise ValueError(f"flow mapping entry without a colon: {p.strip()!r} in {raw.strip()!r}")
        out[k.strip()] = _unquote(v)
    return out


def parse(text):
    """Parse the `metrics:` list of bands.yaml into a list of dicts (tiers -> dict of dicts)."""
    metrics, cur, in_tiers = [], None, False
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            if body != "metrics:":
                raise ValueError(f"unexpected top-level line: {body!r}")
            continue
        if body.startswith("- "):
            cur = {"tiers": {}}
            metrics.append(cur)
            in_tiers = False
            body = body[2:].strip()
            indent += 2
        if cur is None:
            raise ValueError(f"line before the first `- metric:` item: {body!r}")
        k, sep, v = body.partition(":")
        if not sep:
            raise ValueError(f"not a `key: value` line: {body!r}")
        k, v = k.strip(), v.strip()
        if in_tiers and indent >= 6:
            cur["tiers"][k] = _flow_map(v, raw)
            continue
        in_tiers = False
        if k == "tiers" and v == "":
            in_tiers = True
            continue
        cur[k] = _unquote(v)
    return metrics


def matrix(metrics):
    """The workflow matrix rows for every GitHub-sourced metric."""
    rows = []
    for m in metrics:
        src = m.get("source", "")
        if not src.startswith(GH_SOURCE):
            continue
        name = m.get("metric")
        if not name:
            raise ValueError("a metrics entry has no `metric:` name")
        window = m.get("window")
        if window is None:
            raise ValueError(f"metric {name!r}: missing `window:` (the detector's baseline length)")
        if not str(window).isdigit() or int(window) < 2:
            raise ValueError(f"metric {name!r}: `window:` must be an integer >= 2, got {window!r}")
        tools = m["tiers"].get("2sigma", {}).get("tools", "")
        rows.append({"metric": name, "source": src, "tools": tools, "window": int(window)})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="print monitoring/bands.yaml's GitHub-sourced metrics as a workflow matrix")
    ap.add_argument("--file", default="monitoring/bands.yaml")
    a = ap.parse_args(argv)
    try:
        with open(a.file) as fh:
            rows = matrix(parse(fh.read()))
    except (OSError, ValueError) as e:
        print(f"bands_config: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"include": rows}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
