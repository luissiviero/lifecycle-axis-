"""A retired item no longer reads `parked` in the generated index (work/parked-marker-on-retired R-1, R-2).

Composes scripts/test_gen_index.py's fixtures -- the two-item tree, the `ParkedMarker` approvers file
and the parked intent and ledger -- and adds an item whose ledger ends with a park followed by the three
`-> superseded` lines a retirement writes. `gen_index.build_item` must then ask `next_item.parked_note`
for nothing: the stage cell comes from `_stage` and the item index has no `Parked:` line. The second
case pins the owner's answer on the intent: the marker reads `parked` only for `status: approved`, so a
park on an `in-review` intent is not marked either.

Red before build_item reads the intent's status: the stage cell reads `parked` and the item index
carries `Parked: parked: revision 2: ...` in both cases.

A new module rather than a case in scripts/test_gen_index.py: the item's plan is `kind: fix`, which locks
every existing test file (.claude/hooks/protect-tests.sh); a new file stays writable. Fixtures carry
their own identity and time (knowledge/lessons/tests-carry-their-own-environment.md).
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_index  # noqa: E402
import test_gen_index as base  # noqa: E402

APPROVERS = "roles:\n  product-owner: [alice]\nartifacts:\n  intent.md: product-owner\nnever-approve: [claude]\n"

RETIRED_INTENT = """\
---
type: sdlc/intent
id: retired
title: Retired item
description: Parked, then retired by the owner
status: superseded
approved-by: alice
mode: delegated
delegated-by: alice
delegated-on: 2026-01-01
risk-class: low
timestamp: 2026-01-01T00:00:00Z
---
# Intent: retired
"""

RETIRED_SPEC = """\
---
type: sdlc/spec
id: retired
status: superseded
approved-by: claude
timestamp: 2026-01-02T00:00:00Z
---
# Spec: retired
"""

RETIRED_PLAN = """\
---
type: sdlc/plan
id: retired
status: superseded
approved-by: claude
timestamp: 2026-01-02T00:00:00Z
---
# Plan: retired
"""

# The shape a retirement leaves on main (work/risk-detour/log.md at fd39dd0): the park is the latest
# `parked:`/`resumed:` line, and the three retiring lines after it are neither word.
RETIRED_LOG = """\
---
type: sdlc/log
id: retired-log
title: Gate ledger for retired
description: test fixture
timestamp: 2026-01-01T00:00:00Z
---
# Log: retired

- 2026-01-01T00:00:00Z | intent.md | in-review -> approved | alice | abc1234 | mode: delegated
- 2026-01-02T00:00:00Z | spec.md | in-review -> delegated | claude | def5678 | signed
- 2026-01-02T00:00:00Z | plan.md | in-review -> delegated | claude | def5678 | signed
- 2026-01-03T00:00:00Z | intent.md | approved -> approved | claude | 0123abc | parked: revision 2: no low-only route; remainder: retired-supervised
- 2026-01-04T00:00:00Z | intent.md | approved -> superseded | alice | 4567def | retired
- 2026-01-04T00:00:00Z | spec.md | delegated -> superseded | alice | 4567def | retired with the intent
- 2026-01-04T00:00:00Z | plan.md | delegated -> superseded | alice | 4567def | retired with the intent
"""

GOLDEN_RETIRED_INDEX = (
    "---\n"
    "type: sdlc/work-item\n"
    "id: retired\n"
    "title: Retired item\n"
    "description: Parked, then retired by the owner\n"
    "timestamp: 2026-01-02T00:00:00Z\n"
    "---\n"
    "# Retired item\n"
    "\n"
    "- [intent.md](intent.md) — status: superseded; approved-by: alice; Parked, then retired by the owner\n"
    "- [spec.md](spec.md) — status: superseded; approved-by: claude; \n"
    "- [plan.md](plan.md) — status: superseded; approved-by: claude; \n"
    "\n"
    "Last gate: - 2026-01-04T00:00:00Z | plan.md | delegated -> superseded | alice | 4567def | retired with the intent\n"
)

GOLDEN_RETIRED_ROW = (
    "| [retired](retired/index.md) | Retired item | plan | superseded | superseded | superseded | plan.md -> superseded by alice |\n"
)

UNAPPROVED_ROW = (
    "| [parked](parked/index.md) | Parked item | intent | in-review | — | — | intent.md -> approved by claude |\n"
)


class RetiredParkedItem(unittest.TestCase):
    def _tree(self, root):
        base._build_two_item_tree(root)
        base._write(os.path.join(root, ".sdlc", "approvers.yaml"), APPROVERS)

    def test_a_retired_item_loses_the_marker(self):
        """R-1: three superseded artifacts, the park still the latest parked:/resumed: line."""
        with tempfile.TemporaryDirectory() as root:
            self._tree(root)
            item = os.path.join(root, "work", "retired")
            base._write(os.path.join(item, "intent.md"), RETIRED_INTENT)
            base._write(os.path.join(item, "spec.md"), RETIRED_SPEC)
            base._write(os.path.join(item, "plan.md"), RETIRED_PLAN)
            base._write(os.path.join(item, "log.md"), RETIRED_LOG)
            outputs = base._outputs_by_path(gen_index.render_all(root))
            self.assertEqual(outputs[os.path.join("work", "retired", "index.md")], GOLDEN_RETIRED_INDEX)
            self.assertIn(GOLDEN_RETIRED_ROW, outputs["work/index.md"])
            # The unretired items render as their own goldens say.
            self.assertEqual(outputs[os.path.join("work", "alpha", "index.md")], base.GOLDEN_ALPHA_INDEX)
            self.assertEqual(outputs[os.path.join("work", "zeta", "index.md")], base.GOLDEN_ZETA_INDEX)

    def test_a_park_on_an_unapproved_intent_is_not_marked(self):
        """R-2: the condition is `approved`, not `not superseded`."""
        with tempfile.TemporaryDirectory() as root:
            self._tree(root)
            intent = base.PARKED_INTENT.replace("status: approved\n", "status: in-review\n")
            self.assertNotEqual(intent, base.PARKED_INTENT)
            base._write(os.path.join(root, "work", "parked", "intent.md"), intent)
            base._write(os.path.join(root, "work", "parked", "log.md"), base.PARKED_LOG)
            outputs = base._outputs_by_path(gen_index.render_all(root))
            self.assertNotIn("Parked:", outputs[os.path.join("work", "parked", "index.md")])
            self.assertIn(UNAPPROVED_ROW, outputs["work/index.md"])


if __name__ == "__main__":
    unittest.main()
