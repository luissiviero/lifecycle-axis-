#!/usr/bin/env python3
"""Read `.sdlc/delegation.yaml` and answer what an agent may sign under a grant.

One file tunes delegated mode: which agent handles may sign, which artifacts they
may sign, which risk classes a grant covers, how many deviations and re-signatures
an item may accumulate, and what the merge workflow requires. It is parsed by
`scripts/approvers.py`'s two-level parser -- same shape, different top-level keys,
which is why `_parse` takes them as a parameter. No PyYAML; stdlib only.

Every query fails closed. A missing file, `enabled: false`, an unlisted handle, an
unlisted artifact and a risk class outside the policy all answer False with a
reason, so delegated mode stays off until the owner turns it on in a commit of
their own (work/delegated-mode R-1, D1).

API:
  load(path=None) -> Policy
      `path` defaults to `.sdlc/delegation.yaml` under the git root (no
      config.env key: one file, one place to look). A missing file loads a
      fail-closed Policy rather than raising; a malformed one raises ValueError
      naming `<path>:<line>` (or `<path>: <key>` for a value the shape allows
      but the policy cannot use).
  Policy.may_sign(handle) -> (bool, reason)
      Is `handle` an agent this policy lets sign? It never consults
      `.sdlc/approvers.yaml`: `never-approve` lists `claude` on purpose, and
      approving and signing are different acts (spec gotchas, D-a).
  Policy.may_sign_artifact(name) -> (bool, reason)
  Policy.risk_ok(risk_class) -> (bool, reason)
  Policy fields: enabled, agents, signable, risk_classes, max_deviations,
      revisions (`never` | `consensus` | `free`), min_reviewers, merge (a dict:
      enabled, require_review, require_checks, method, cool_off_hours),
      locked_paths, plus path and exists.

CLI:
  python3 scripts/delegation.py                     dump the parsed policy as JSON
  python3 scripts/delegation.py --may-sign HANDLE   exit 0 when HANDLE may sign, else 1;
                                                    the reason goes to stderr
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import approvers  # noqa: E402  (path set up above; `_parse` and `normalize` are reused)
from check_artifact_chain import ROOT  # noqa: E402

DEFAULT_FILE = os.path.join(".sdlc", "delegation.yaml")
TOP_KEYS = (
    "enabled", "agents", "signable", "risk-classes", "max-deviations",
    "revisions", "min-reviewers", "merge", "locked-paths",
)
MERGE_KEYS = ("enabled", "require-review", "require-checks", "method", "cool-off-hours")
REVISION_MODES = ("never", "consensus", "free")
TRUE_WORDS = ("true", "yes", "on", "1")
FALSE_WORDS = ("false", "no", "off", "0")

# What an absent key means. Every default is the closed answer, so a policy that
# forgets a key is narrower than one that names it, never wider.
DEFAULT_MERGE = {
    "enabled": False,
    "require_review": True,
    "require_checks": [],
    "method": "merge",
    "cool_off_hours": 0,
}


def _empty(value):
    """True for a key the parser saw with no value (`enabled:` -> {}) or an empty string."""
    return value is None or value == "" or value == {}


def _as_bool(value, key, path, default):
    if _empty(value):
        return default
    word = str(value).strip().casefold()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ValueError(f"{path}: {key}: '{value}' is not true or false")


def _as_int(value, key, path, default):
    if _empty(value):
        return default
    try:
        return int(str(value).strip())
    except ValueError:
        raise ValueError(f"{path}: {key}: '{value}' is not a whole number") from None


def _as_list(value):
    """A flow list stays a list; a bare scalar is a one-item list; an empty key is []."""
    if _empty(value):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _as_word(value, default):
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


class Policy:
    """A parsed delegation policy plus the file's resolved path.

    `exists=False` (no file at load time) and `enabled=False` are the two closed
    states: every `may_*` query on either answers False with that reason, whatever
    it is asked about, so a reader that forgets to check one of them still gets a no.
    """

    def __init__(self, path, exists=True, enabled=False, agents=(), signable=(),
                 risk_classes=(), max_deviations=0, revisions="never", min_reviewers=2,
                 merge=None, locked_paths=()):
        self.path = path
        self.exists = exists
        self.enabled = enabled
        self.agents = list(agents)
        self.signable = list(signable)
        self.risk_classes = list(risk_classes)
        self.max_deviations = max_deviations
        self.revisions = revisions
        self.min_reviewers = min_reviewers
        self.merge = dict(DEFAULT_MERGE, **(merge or {}))
        self.locked_paths = list(locked_paths)

    def _closed(self):
        """The one reason this policy answers no to everything, or None when it is open."""
        if not self.exists:
            return f"no delegation policy at {self.path}"
        if not self.enabled:
            return "delegated mode is off"
        return None

    def may_sign(self, handle):
        closed = self._closed()
        if closed:
            return False, closed
        norm = approvers.Approvers.normalize(handle)
        if not norm:
            return False, "empty handle"
        if norm not in {approvers.Approvers.normalize(h) for h in self.agents}:
            return False, f"'{norm}' is not an agent listed in {self.path}"
        return True, "ok"

    def may_sign_artifact(self, name):
        closed = self._closed()
        if closed:
            return False, closed
        if (name or "").strip() not in self.signable:
            return False, f"'{name}' is not a signable artifact in {self.path}"
        return True, "ok"

    def risk_ok(self, risk_class):
        closed = self._closed()
        if closed:
            return False, closed
        listed = ", ".join(self.risk_classes) or "none"
        cls = (risk_class or "").strip().casefold()
        if not cls:
            return False, f"no risk-class on the intent; {self.path} delegates {listed}"
        if cls not in {c.strip().casefold() for c in self.risk_classes}:
            return False, f"risk class '{cls}' is not delegated by {self.path} (it lists {listed})"
        return True, "ok"

    def as_dict(self):
        return {
            "path": self.path,
            "exists": self.exists,
            "enabled": self.enabled,
            "agents": self.agents,
            "signable": self.signable,
            "risk_classes": self.risk_classes,
            "max_deviations": self.max_deviations,
            "revisions": self.revisions,
            "min_reviewers": self.min_reviewers,
            "merge": self.merge,
            "locked_paths": self.locked_paths,
        }


def load(path=None):
    path = path or os.path.join(ROOT, DEFAULT_FILE)
    if not os.path.exists(path):
        return Policy(path, exists=False)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parsed = approvers._parse(text, path, top_keys=TOP_KEYS)

    merge_raw = parsed.get("merge") or {}
    if not isinstance(merge_raw, dict):
        raise ValueError(f"{path}: merge: expected a nested map, not '{merge_raw}'")
    unknown = sorted(k for k in merge_raw if k not in MERGE_KEYS)
    if unknown:
        # A typo here would silently fall back to a default; the owner meant to set something.
        raise ValueError(f"{path}: merge: unknown key(s) {', '.join(unknown)}; "
                         f"allowed: {', '.join(MERGE_KEYS)}")
    merge = {
        "enabled": _as_bool(merge_raw.get("enabled"), "merge.enabled", path, DEFAULT_MERGE["enabled"]),
        "require_review": _as_bool(merge_raw.get("require-review"), "merge.require-review", path,
                                   DEFAULT_MERGE["require_review"]),
        "require_checks": _as_list(merge_raw.get("require-checks")),
        "method": _as_word(merge_raw.get("method"), DEFAULT_MERGE["method"]),
        "cool_off_hours": _as_int(merge_raw.get("cool-off-hours"), "merge.cool-off-hours", path,
                                  DEFAULT_MERGE["cool_off_hours"]),
    }

    revisions = _as_word(parsed.get("revisions"), "never").casefold()
    if revisions not in REVISION_MODES:
        raise ValueError(f"{path}: revisions: '{revisions}' is not one of {' | '.join(REVISION_MODES)}")

    return Policy(
        path,
        exists=True,
        enabled=_as_bool(parsed.get("enabled"), "enabled", path, False),
        agents=_as_list(parsed.get("agents")),
        signable=_as_list(parsed.get("signable")),
        risk_classes=_as_list(parsed.get("risk-classes")),
        max_deviations=_as_int(parsed.get("max-deviations"), "max-deviations", path, 0),
        revisions=revisions,
        min_reviewers=_as_int(parsed.get("min-reviewers"), "min-reviewers", path, 2),
        merge=merge,
        locked_paths=_as_list(parsed.get("locked-paths")),
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--may-sign", metavar="HANDLE",
                    help="exit 0 when HANDLE may sign under this policy, 1 otherwise")
    args = ap.parse_args(argv)
    try:
        policy = load()
    except ValueError as e:
        print(f"malformed delegation policy: {e}", file=sys.stderr)
        sys.exit(1)
    if args.may_sign:
        ok, reason = policy.may_sign(args.may_sign)
        print(reason, file=sys.stderr)
        sys.exit(0 if ok else 1)
    print(json.dumps(policy.as_dict(), indent=2))


if __name__ == "__main__":
    main()
