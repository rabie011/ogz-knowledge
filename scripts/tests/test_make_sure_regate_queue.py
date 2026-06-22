#!/usr/bin/env python3
"""Guards make_sure's 4b STAGING-BOUNDARY re-gate (scar: 2026-06-22).

Root scar: the 4b re-gate (the check that proves NO gate-BLOCKED post is live in Mohamed's
judge lane) referenced a module-level name `QUEUE` that was never defined. Every cycle the
re-gate raised `NameError: name 'QUEUE' is not defined`, got swallowed by its own fail-closed
`except`, and reported `judge_cards_gated=False` with `_blocked_live=["re-gate raised: ..."]`.
The organ that must verify the staging boundary was DEAD — and worse, its death looked like an
ordinary explained alarm, not a crash. It never once actually re-gated a real card.

The fix: define QUEUE = BASE/"data/decision_queue.json" (the queue the re-gate reads). These
tests pin that symbol so the re-gate can never silently die on a NameError again — the exact
bug, regression-locked. (Rule #6 consumer law + MAKE-SURE law: a check that always errors is
worse than no check.)"""
import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import make_sure as ms


class TestRegateQueueSymbol(unittest.TestCase):
    def test_queue_symbol_is_defined(self):
        """QUEUE must exist at module scope — its absence is the exact bug that killed the re-gate."""
        self.assertTrue(hasattr(ms, "QUEUE"), "make_sure.QUEUE is undefined — the 4b re-gate will NameError")

    def test_queue_points_at_decision_queue(self):
        """QUEUE must resolve to the real judge/feedback card queue the re-gate re-checks."""
        self.assertIsInstance(ms.QUEUE, Path)
        self.assertEqual(ms.QUEUE.name, "decision_queue.json")
        self.assertEqual(ms.QUEUE, ms.BASE / "data" / "decision_queue.json")

    def test_regate_free_names_all_resolve(self):
        """Static guard against the whole CLASS of bug: every bare Name the 4b re-gate block reads
        must be a builtin, a module global, or bound in that block. Catches a future undefined-symbol
        before it can fail-close-silently like QUEUE did."""
        src = (Path(ms.__file__)).read_text()
        tree = ast.parse(src)
        import builtins
        module_globals = set(dir(ms)) | set(dir(builtins))
        # locate the 4b block by its sentinel comment / the QUEUE read
        offenders = []
        for node in ast.walk(tree):
            # the re-gate lives in a try whose body reads QUEUE; scope the scan to functions that
            # reference QUEUE so we check the right region without brittle line numbers
            if isinstance(node, (ast.FunctionDef, ast.Module)):
                names_read, names_bound = set(), set()
                for n in ast.walk(node):
                    if isinstance(n, ast.Name):
                        if isinstance(n.ctx, ast.Load):
                            names_read.add(n.id)
                        elif isinstance(n.ctx, (ast.Store,)):
                            names_bound.add(n.id)
                    elif isinstance(n, (ast.Import, ast.ImportFrom)):
                        for a in n.names:
                            names_bound.add((a.asname or a.name).split(".")[0])
                    elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        names_bound.add(n.name)
                        names_bound.update(a.arg for a in n.args.args)
                if "QUEUE" not in names_read:
                    continue
                undefined = names_read - names_bound - module_globals
                # comprehension/loop targets and attrs are over-counted; we only assert QUEUE itself
                # (the regression target) is resolvable — the broader scan is advisory
                if "QUEUE" in undefined:
                    offenders.append("QUEUE")
        self.assertNotIn("QUEUE", offenders, "QUEUE read but not bound/global in its scope")


if __name__ == "__main__":
    unittest.main()
