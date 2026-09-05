#!/usr/bin/env python3
"""Every eval case must be able to fail (work/agent-evals R-3).

Reads evals/cases/*.yaml in the shape scripts/run_evals.sh reads them (`key: value` lines and
`key: |` blocks) and refuses:

  - a `check:` block that runs under `set -e` and asserts with a bare negated command (`! cmd`)
    anywhere but as its last command: bash never triggers errexit on a negation, so when `cmd`
    unexpectedly succeeds the line's failure is ignored and the case passes. End such a line with
    `|| exit 1` (or let it be the block's last command).
  - a `kind:` outside hook | skill | e2e;
  - a case with neither `check:` nor `prompt:`.

Commands are split the way bash reads them: a physical line ending in `\\` continues the command,
comments and blank lines are not commands, and a heredoc body (`<<TAG` ... `TAG`) is data.

Usage: scripts/check_eval_cases.py [--root DIR]
Last line: `EVAL-CASES: N cases, M problems`; exit 1 when M > 0.
"""
import argparse, os, re, sys

KINDS = ("hook", "skill", "e2e")
NEG_OK = re.compile(r"\|\|\s*exit(\s+\d+)?\s*$")
SET_E = re.compile(r"(^|[;\s])set\s+-[a-zA-Z]*e\b")
HEREDOC = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")


def read_fields(text):
    """key -> (value, 1-based line number of the value's first line). Blocks end at the first
    non-indented line, as run_evals.sh's field() does."""
    lines = text.split("\n")
    fields, i = {}, 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2)
        if rest.strip() == "|":
            j = i + 1
            body = []
            while j < len(lines) and lines[j].startswith((" ", "\t")):
                body.append(lines[j])
                j += 1
            fields[key] = ("\n".join(body), i + 2)
            i = j
        else:
            value = rest.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = (value, i + 1)
            i += 1
    return fields


def _outside_quotes(text, pos):
    """True when text[pos] is not inside a single- or double-quoted string."""
    single = double = False
    i = 0
    while i < pos:
        ch = text[i]
        if double and ch == "\\":
            i += 2
            continue
        if ch == "'" and not double:
            single = not single
        elif ch == '"' and not single:
            double = not double
        i += 1
    return not (single or double)


def heredoc_tag(cmd):
    """The terminator of a heredoc the command opens, or None. A `<<TAG` inside quotes (a printf
    argument that builds a command for a hook to judge, say) is text, not a heredoc."""
    for m in HEREDOC.finditer(cmd):
        if _outside_quotes(cmd, m.start()):
            return m.group(1)
    return None


def commands(block, start_lineno):
    """(first_lineno, last_lineno, command) for each logical command of a check block."""
    raw = block.split("\n")
    out, i = [], 0
    while i < len(raw):
        line = raw[i].strip()
        first = start_lineno + i
        if not line or line.startswith("#"):
            i += 1
            continue
        cmd = line
        while cmd.endswith("\\") and i + 1 < len(raw):
            i += 1
            cmd = cmd[:-1].rstrip() + " " + raw[i].strip()
        term = heredoc_tag(cmd)
        if term is not None:
            i += 1
            while i < len(raw) and raw[i].strip() != term:
                i += 1
        out.append((first, start_lineno + i, cmd))
        i += 1
    return out


def check_case(rel, text):
    problems = []
    fields = read_fields(text)
    kind = fields.get("kind", ("", 0))[0]
    if kind not in KINDS:
        problems.append(f"{rel}: kind '{kind}' is not one of {', '.join(KINDS)}")
    if "check" not in fields and "prompt" not in fields:
        problems.append(f"{rel}: neither check nor prompt")
    if "check" in fields:
        block, start = fields["check"]
        if SET_E.search(block):
            cmds = commands(block, start)
            for idx, (lineno, _last, cmd) in enumerate(cmds):
                if cmd.startswith("!") and idx != len(cmds) - 1 and not NEG_OK.search(cmd):
                    problems.append(f"{rel}:{lineno}: negated command cannot fail under set -e; end it with '|| exit 1'")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd())
    a = ap.parse_args(argv)
    cases_dir = os.path.join(a.root, "evals", "cases")
    names = sorted(n for n in os.listdir(cases_dir) if n.endswith(".yaml")) if os.path.isdir(cases_dir) else []
    problems = []
    for n in names:
        rel = "/".join(("evals", "cases", n))
        with open(os.path.join(cases_dir, n), encoding="utf-8") as fh:
            problems.extend(check_case(rel, fh.read()))
    for p in problems:
        print(p)
    print(f"EVAL-CASES: {len(names)} cases, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
