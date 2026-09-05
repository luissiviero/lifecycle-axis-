import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import log_ledger  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REAL_LOG = os.path.join(ROOT, "work", "sdlc-kit-phase-1", "log.md")
EXAMPLE_LOG = os.path.join(ROOT, "work", "_example", "log.md")


def _write(root, name, content):
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


HAPPY_PATH = """---
type: sdlc/log
id: demo-log
title: Gate ledger for demo
description: test fixture
timestamp: 2026-01-01T00:00:00Z
---
# Log: demo

Format: `- <RFC3339> | <artifact> | <from> -> <to> | <actor> | <sha> | <note>`

- 2026-01-01T00:00:00Z | intent.md | (none) -> draft | alice | abc1234 | drafted
- 2026-01-01T01:00:00Z | intent.md | draft -> approved | alice | abc1234 | approved
- 2026-01-01T02:00:00Z | spec.md | (none) -> draft | bob | def5678
"""


class ParseHappyPath(unittest.TestCase):
    def test_three_entries_in_file_order(self):
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", HAPPY_PATH)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0].artifact, "intent.md")
            self.assertEqual(entries[0].from_status, "(none)")
            self.assertEqual(entries[0].to_status, "draft")
            self.assertEqual(entries[0].actor, "alice")
            self.assertEqual(entries[0].sha, "abc1234")
            self.assertEqual(entries[0].note, "drafted")
            self.assertEqual(entries[1].to_status, "approved")
            # sixth field (note) is optional
            self.assertEqual(entries[2].note, "")
            self.assertEqual(entries[2].sha, "def5678")
            # entries come back in file order
            self.assertEqual([e.lineno for e in entries], sorted(e.lineno for e in entries))


class MalformedLines(unittest.TestCase):
    def test_malformed_line_reported_with_lineno_and_does_not_abort(self):
        content = HAPPY_PATH + "- this line has | only two fields\n" + \
            "- 2026-01-01T03:00:00Z | plan.md | (none) -> draft | carol | 9999999 | ok\n"
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(len(malformed), 1)
            bad_lineno, bad_line = malformed[0]
            self.assertEqual(bad_lineno, 15)
            self.assertIn("only two fields", bad_line)
            # parsing continues past the malformed line
            self.assertEqual(len(entries), 4)
            self.assertEqual(entries[-1].artifact, "plan.md")

    def test_missing_arrow_is_malformed(self):
        content = "- 2026-01-01T00:00:00Z | intent.md | draft to approved | alice | abc1234\n"
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(entries, [])
            self.assertEqual(len(malformed), 1)
            self.assertEqual(malformed[0][0], 1)

    def test_bad_timestamp_is_malformed(self):
        content = "- not-a-timestamp | intent.md | (none) -> draft | alice | abc1234\n"
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(entries, [])
            self.assertEqual(len(malformed), 1)


class TimestampFormats(unittest.TestCase):
    def test_z_and_offset_both_parse(self):
        content = (
            "- 2026-01-01T00:00:00Z | intent.md | (none) -> draft | alice | abc1234\n"
            "- 2026-01-01T00:00:00+00:00 | intent.md | draft -> approved | alice | abc1234\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].ts, "2026-01-01T00:00:00Z")
            self.assertEqual(entries[1].ts, "2026-01-01T00:00:00+00:00")


class Approvals(unittest.TestCase):
    def test_filters_by_status_and_artifact(self):
        entries, malformed = log_ledger.parse(_write(
            tempfile.mkdtemp(), "log.md", HAPPY_PATH
        ))
        self.assertEqual(malformed, [])
        approved_intent = log_ledger.approvals(entries, "intent.md")
        self.assertEqual(len(approved_intent), 1)
        self.assertEqual(approved_intent[0].to_status, "approved")
        self.assertEqual(approved_intent[0].artifact, "intent.md")
        # spec.md never reached approved in the fixture
        self.assertEqual(log_ledger.approvals(entries, "spec.md"), [])
        # unknown artifact
        self.assertEqual(log_ledger.approvals(entries, "plan.md"), [])


class MissingFile(unittest.TestCase):
    def test_missing_file_returns_empties(self):
        entries, malformed = log_ledger.parse("/nonexistent/path/log.md")
        self.assertEqual(entries, [])
        self.assertEqual(malformed, [])


class Normalize(unittest.TestCase):
    def test_normalize_strips_quotes_at_first_token_leading_at_and_casefolds(self):
        self.assertEqual(log_ledger.normalize('"@Luissiviero"'), "luissiviero")
        self.assertEqual(log_ledger.normalize("@Bob extra-token"), "bob")
        self.assertEqual(log_ledger.normalize("claude[bot]"), "claude[bot]")


class RoundTrip(unittest.TestCase):
    def test_render_of_parsed_entry_equals_original_line(self):
        # canonical spacing: exactly what render() produces
        line = "- 2026-09-02T12:05:00Z | intent.md | draft -> approved | luissiviero | 372801f | approved as product-owner"
        content = (
            "---\ntype: sdlc/log\nid: demo-log\ntitle: t\ndescription: d\ntimestamp: 2026-09-02T12:00:00Z\n---\n"
            "# Log: demo\n\nFormat: n/a\n\n" + line + "\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            self.assertEqual(len(entries), 1)
            self.assertEqual(log_ledger.render(entries[0]), line)

    def test_round_trip_without_note(self):
        line = "- 2026-09-02T12:05:00Z | plan.md | (none) -> draft | bob | 372801f"
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", "# a heading, not an entry\n" + line + "\n")
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            self.assertEqual(len(entries), 1)
            self.assertEqual(log_ledger.render(entries[0]), line)


class Signatures(unittest.TestCase):
    """work/delegated-mode R-2: signatures() is the 'delegated' twin of approvals()."""

    def test_filters_by_delegated_status_and_artifact(self):
        content = HAPPY_PATH + (
            "- 2026-01-01T03:00:00Z | spec.md | in-review -> delegated | claude | 1111111 | \n"
            "- 2026-01-01T04:00:00Z | plan.md | in-review -> delegated | claude | 2222222 | \n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            spec_sigs = log_ledger.signatures(entries, "spec.md")
            self.assertEqual(len(spec_sigs), 1)
            self.assertEqual(spec_sigs[0].to_status, "delegated")
            self.assertEqual(spec_sigs[0].artifact, "spec.md")
            self.assertEqual(spec_sigs[0].actor, "claude")
            # intent.md reached 'approved' in the fixture, never 'delegated'
            self.assertEqual(log_ledger.signatures(entries, "intent.md"), [])
            # unknown artifact
            self.assertEqual(log_ledger.signatures(entries, "incident.md"), [])

    def test_does_not_confuse_approved_and_delegated(self):
        content = (
            "- 2026-01-01T00:00:00Z | spec.md | in-review -> approved | alice | abc1234\n"
            "- 2026-01-01T01:00:00Z | plan.md | in-review -> delegated | claude | def5678\n"
        )
        with tempfile.TemporaryDirectory() as root:
            path = _write(root, "log.md", content)
            entries, malformed = log_ledger.parse(path)
            self.assertEqual(malformed, [])
            self.assertEqual(log_ledger.approvals(entries, "spec.md")[0].to_status, "approved")
            self.assertEqual(log_ledger.signatures(entries, "spec.md"), [])
            self.assertEqual(log_ledger.signatures(entries, "plan.md")[0].to_status, "delegated")
            self.assertEqual(log_ledger.approvals(entries, "plan.md"), [])


class RealLedgers(unittest.TestCase):
    def test_real_work_item_log_parses_with_zero_malformed(self):
        # The ledger is append-only and grows at every gate, so pin a floor, not an exact count.
        entries, malformed = log_ledger.parse(REAL_LOG)
        self.assertEqual(malformed, [])
        self.assertGreaterEqual(len(entries), 4)

    def test_example_log_has_zero_malformed(self):
        entries, malformed = log_ledger.parse(EXAMPLE_LOG)
        self.assertEqual(malformed, [])
        self.assertGreater(len(entries), 0)


if __name__ == "__main__":
    unittest.main()
