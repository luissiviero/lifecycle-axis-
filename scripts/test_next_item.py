"""Tests for scripts/next_item.py (work/run-queue R-1).

Written from work/run-queue/spec.md's R-1 row and Interfaces section before the implementation
exists, so every case here is expected to fail today and to pass once next_item.py ships.

Fixtures carry their own identity and time (knowledge/lessons/tests-carry-their-own-environment.md):
every intent's dates are literal, and nothing here reads the ambient environment or the real repo.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import delegation  # noqa: E402
import next_item as ni  # noqa: E402

SCRIPT = os.path.join(HERE, "next_item.py")

POLICY = """\
enabled: true
agents: [claude, claude[bot]]
signable: [spec.md, plan.md, incident.md]
risk-classes: [low]
max-deviations: 5
revisions: consensus
min-reviewers: 2
"""


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _intent(status="approved", mode="delegated", on="2026-09-08", risk="low"):
    """A granted intent by default. `mode=None` omits the grant keys entirely, which is how every
    non-delegated item in this repository is written (spec G-7) -- absent, not blank."""
    lines = ["---", "type: sdlc/intent", "status: %s" % status]
    if mode is not None:
        lines += ["mode: %s" % mode, "delegated-by: luissiviero", "delegated-on: %s" % on]
    lines += ["risk-class: %s" % risk, "---", "# intent", ""]
    return "\n".join(lines)


def _repo(root, items):
    """items: {slug: (intent_text, spec_text_or_None)}. Writes .sdlc/delegation.yaml too."""
    _write(os.path.join(root, ".sdlc", "delegation.yaml"), POLICY)
    for slug, (intent, spec) in items.items():
        _write(os.path.join(root, "work", slug, "intent.md"), intent)
        if spec is not None:
            _write(os.path.join(root, "work", slug, "spec.md"), spec)
    return delegation.load(path=os.path.join(root, ".sdlc", "delegation.yaml"))


def _spec(status):
    return "---\ntype: sdlc/spec\nstatus: %s\n---\n# spec\n" % status


class Order(unittest.TestCase):
    def test_earliest_grant_first_then_slug(self):
        """Earliest delegated-on wins; same-date items tie and are broken by slug ascending.
        delegated-on is date-only, so ties are the normal case, not an edge one (spec G-6)."""
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {
                "zulu": (_intent(on="2026-09-01"), None),
                "bravo": (_intent(on="2026-09-08"), None),
                "alpha": (_intent(on="2026-09-08"), None),
            })
            self.assertEqual(ni.next_item(root, policy), "zulu")
            self.assertEqual(ni.next_item(root, policy, exclude="zulu"), "alpha")
            self.assertEqual(sorted(ni.queue(root, policy)), ["alpha", "bravo", "zulu"])
            self.assertEqual(ni.queue(root, policy), ["zulu", "alpha", "bravo"])


class Eligibility(unittest.TestCase):
    def test_started_item_is_skipped(self):
        """Unstarted means no spec.md, or a spec still draft/in-review. A signed spec means the
        item is already being worked, so the queue must not hand it out again."""
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {
                "started": (_intent(on="2026-09-01"), _spec("delegated")),
                "fresh": (_intent(on="2026-09-08"), None),
            })
            self.assertEqual(ni.next_item(root, policy), "fresh")

    def test_draft_and_in_review_specs_are_still_unstarted(self):
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {
                "drafted": (_intent(on="2026-09-01"), _spec("draft")),
                "reviewing": (_intent(on="2026-09-02"), _spec("in-review")),
            })
            self.assertEqual(ni.queue(root, policy), ["drafted", "reviewing"])

    def test_ungranted_and_retired_and_unapproved_are_skipped(self):
        """Three exclusions: no grant keys at all (the common shape, spec G-7), a retired intent,
        and an intent a human has not approved."""
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {
                "ungranted": (_intent(mode=None, on="2026-09-01"), None),
                "supervised": (_intent(mode="supervised", on="2026-09-01"), None),
                "retired": (_intent(status="superseded", on="2026-09-01"), None),
                "unapproved": (_intent(status="in-review", on="2026-09-01"), None),
                "granted": (_intent(on="2026-09-09"), None),
            })
            self.assertEqual(ni.queue(root, policy), ["granted"])

    def test_risk_class_outside_the_policy_is_skipped(self):
        """The policy delegates `low` only; a `high` grant is invalid and the chain check would
        fail anything signed under it, so the queue never offers it."""
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {
                "risky": (_intent(on="2026-09-01", risk="high"), None),
                "safe": (_intent(on="2026-09-08"), None),
            })
            self.assertEqual(ni.next_item(root, policy), "safe")

    def test_a_slug_that_is_not_a_work_item_name_is_skipped(self):
        """The slug names a path and reaches a ledger line, so it is validated the way
        check_artifact_chain.py and approve_dispatch.py validate theirs."""
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {"ok-item": (_intent(on="2026-09-08"), None)})
            _write(os.path.join(root, "work", ".hidden", "intent.md"), _intent(on="2026-09-01"))
            self.assertEqual(ni.queue(root, policy), ["ok-item"])


class EmptyQueue(unittest.TestCase):
    def test_none_when_nothing_is_eligible(self):
        with tempfile.TemporaryDirectory() as root:
            policy = _repo(root, {"done": (_intent(on="2026-09-01"), _spec("delegated"))})
            self.assertIsNone(ni.next_item(root, policy))
            self.assertEqual(ni.queue(root, policy), [])

    def test_policy_off_yields_an_empty_queue(self):
        """Delegated mode off means no item may be signed, so none may be queued either."""
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"granted": (_intent(on="2026-09-08"), None)})
            _write(os.path.join(root, ".sdlc", "delegation.yaml"), POLICY.replace("enabled: true", "enabled: false"))
            policy = delegation.load(path=os.path.join(root, ".sdlc", "delegation.yaml"))
            self.assertEqual(ni.queue(root, policy), [])


class Cli(unittest.TestCase):
    def _run(self, root, *args):
        return subprocess.run([sys.executable, SCRIPT, "--root", root, *args],
                              capture_output=True, text=True)

    def test_prints_the_slug_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"alpha": (_intent(on="2026-09-08"), None)})
            r = self._run(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "alpha")

    def test_empty_queue_prints_nothing_and_exits_three(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {"done": (_intent(on="2026-09-01"), _spec("delegated"))})
            r = self._run(root)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertEqual(r.stdout.strip(), "")

    def test_exclude_omits_one_item(self):
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {
                "alpha": (_intent(on="2026-09-08"), None),
                "bravo": (_intent(on="2026-09-09"), None),
            })
            r = self._run(root, "--exclude", "alpha")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "bravo")

    def test_list_prints_the_queue_in_order(self):
        """The skill prints this before a run starts, so the owner sees the order before leaving."""
        with tempfile.TemporaryDirectory() as root:
            _repo(root, {
                "bravo": (_intent(on="2026-09-08"), None),
                "alpha": (_intent(on="2026-09-08"), None),
            })
            r = self._run(root, "--list")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.split(), ["alpha", "bravo"])


if __name__ == "__main__":
    unittest.main()
