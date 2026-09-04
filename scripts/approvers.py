#!/usr/bin/env python3
"""Read `.sdlc/approvers.yaml` and answer who may approve which artifact.

Understands exactly the two-level shape the file uses: top-level keys that
map to either a nested mapping of `key: value` / `key: [a, b]` pairs, or a
flow list directly (`key: [a, b]`). No PyYAML; stdlib only.

API:
  load(path=None) -> Approvers
      `path` defaults to APPROVERS_FILE from `.sdlc/config.env` (read via
      `check_artifact_chain.config()`), falling back to
      `.sdlc/approvers.yaml`; a relative path is resolved against the git
      root. A missing file loads a fail-closed Approvers rather than
      raising -- every `is_valid()` call on it reports the file is missing.
  Approvers.role_for(artifact) -> str | None
  Approvers.has_role(role, handle) -> (bool, reason)
      The primitive: is `handle` a human listed under `role`? Fails closed on a
      missing file, an empty handle, a never-approve identity, or an unknown role.
  Approvers.is_valid(artifact, handle) -> (bool, reason)
      role_for(artifact), then has_role(role, handle).
  Approvers.normalize(handle) -> str
      Strips surrounding quotes, takes the first whitespace-delimited
      token, strips a leading '@', casefolds.

CLI:
  python3 scripts/approvers.py                       dump the parsed file as JSON
  python3 scripts/approvers.py --has-role ROLE HANDLE  exit 0 when HANDLE holds ROLE, else 1;
                                                     the reason goes to stderr
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from check_artifact_chain import ROOT, config  # noqa: E402  (path set up above)

TOP_KEYS = ("roles", "artifacts", "never-approve")


def _strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s


def _parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item) for item in inner.split(",")]
    return _strip_quotes(raw)


def _parse(text, path):
    """Parse the two-level approvers shape into a plain dict.

    Raises ValueError naming a 1-based line number (as `<path>:<line>: ...`)
    on tab indentation, a line with no ':', an indent that isn't 0 or 2
    spaces, or a top-level key outside TOP_KEYS.
    """
    result = {}
    current_key = None
    for i, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise ValueError(f"{path}:{i}: tab indentation is not allowed")
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            if ":" not in line:
                raise ValueError(f"{path}:{i}: expected 'key: value', no ':' found")
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if key not in TOP_KEYS:
                raise ValueError(f"{path}:{i}: unknown top-level key '{key}'")
            current_key = key
            if rest:
                result[key] = _parse_value(rest)
                current_key = None
            else:
                result[key] = {}
        elif indent == 2:
            if current_key is None or not isinstance(result.get(current_key), dict):
                raise ValueError(f"{path}:{i}: unexpected indentation")
            if ":" not in line:
                raise ValueError(f"{path}:{i}: expected 'key: value', no ':' found")
            key, _, rest = line.partition(":")
            result[current_key][key.strip()] = _parse_value(rest)
        else:
            raise ValueError(f"{path}:{i}: unexpected indentation ({indent} spaces; use 2)")
    return result


class Approvers:
    """Parsed roles/artifacts/never-approve plus the file's resolved path.

    `exists=False` (a missing file at load time) makes every `is_valid()`
    call fail closed, regardless of the artifact or handle asked about.
    """

    def __init__(self, roles, artifacts, never_approve, path, exists=True):
        self.roles = roles
        self.artifacts = artifacts
        self.never_approve = {self.normalize(h) for h in never_approve}
        self.path = path
        self.exists = exists

    @staticmethod
    def normalize(handle):
        h = (handle or "").strip()
        if len(h) >= 2 and h[0] == h[-1] and h[0] in ('"', "'"):
            h = h[1:-1].strip()
        parts = h.split()
        h = parts[0] if parts else ""
        if h.startswith("@"):
            h = h[1:]
        return h.casefold()

    def role_for(self, artifact):
        return self.artifacts.get(artifact)

    def has_role(self, role, handle):
        """(True, "ok") when `handle` is listed under `role`; otherwise (False, reason)."""
        if not self.exists:
            return False, f"no approvers file at {self.path}"
        norm = self.normalize(handle)
        if not norm:
            return False, "empty approver"
        if norm in self.never_approve:
            return False, "agent identities cannot approve"
        if role not in self.roles:
            return False, f"no such role {role}"
        allowed = {self.normalize(h) for h in self.roles.get(role, [])}
        if norm not in allowed:
            return False, f"{norm} is not a {role}"
        return True, "ok"

    def is_valid(self, artifact, handle):
        if not self.exists:
            return False, f"no approvers file at {self.path}"
        role = self.role_for(artifact)
        if role is None:
            norm = self.normalize(handle)
            if not norm:
                return False, "empty approver"
            if norm in self.never_approve:
                return False, "agent identities cannot approve"
            return False, f"no role defined for {artifact}"
        return self.has_role(role, handle)


def load(path=None):
    if path is None:
        try:
            values = config().get("APPROVERS_FILE") or []
            rel = values[0] if values else ".sdlc/approvers.yaml"
        except OSError:
            rel = ".sdlc/approvers.yaml"
        path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return Approvers({}, {}, [], path, exists=False)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parsed = _parse(text, path)
    roles = parsed.get("roles", {})
    artifacts = parsed.get("artifacts", {})
    never_approve = parsed.get("never-approve", [])
    if isinstance(never_approve, str):
        never_approve = [never_approve]
    return Approvers(roles, artifacts, never_approve, path, exists=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--has-role", nargs=2, metavar=("ROLE", "HANDLE"),
                    help="exit 0 when HANDLE holds ROLE in the approvers file, 1 otherwise")
    args = ap.parse_args(argv)
    try:
        a = load()
    except ValueError as e:
        print(f"malformed approvers file: {e}", file=sys.stderr)
        sys.exit(1)
    if args.has_role:
        ok, reason = a.has_role(*args.has_role)
        print(reason, file=sys.stderr)
        sys.exit(0 if ok else 1)
    print(
        json.dumps(
            {
                "path": a.path,
                "exists": a.exists,
                "roles": a.roles,
                "artifacts": a.artifacts,
                "never_approve": sorted(a.never_approve),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
