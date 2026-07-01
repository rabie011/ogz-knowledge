#!/usr/bin/env python3
"""Locks Rule #8 on overnight_improver's intel readers (B057 sibling, July 1):
a drifted/degenerate intelligence_layer.json must REFUSE loudly (raise) rather
than silently write empty output (task_deep_why) or crash with an opaque
IndexError (task_sector_comparison). Root cause it guards: 'universal_rules' /
'sector_playbooks' are gone (data moved to 'sector_facts' / 'occasion_calendar'),
so these readers .get() empty and produce garbage. Mirrors
test_calibrate_cd_router_refuse.py for the sibling reader."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import overnight_improver as oi


class TestRequireIntelKey(unittest.TestCase):
    def test_missing_key_refuses(self):
        with self.assertRaises(RuntimeError) as ctx:
            oi._require_intel_key({}, "universal_rules")
        self.assertIn("schema drift", str(ctx.exception).lower())
        self.assertIn("universal_rules", str(ctx.exception))

    def test_empty_value_refuses(self):
        for empty in ([], {}, None, ""):
            with self.assertRaises(RuntimeError):
                oi._require_intel_key({"sector_playbooks": empty}, "sector_playbooks")

    def test_live_value_passes_through(self):
        val = [{"pattern": "heritage", "engagement": 72}]
        self.assertEqual(oi._require_intel_key({"universal_rules": val}, "universal_rules"), val)

    def test_names_the_drift_target(self):
        """The message must point at the new home so a fixer knows where data went."""
        try:
            oi._require_intel_key({}, "sector_playbooks")
        except RuntimeError as e:
            self.assertIn("sector_facts", str(e))
            self.assertIn("occasion_calendar", str(e))


if __name__ == "__main__":
    unittest.main()
