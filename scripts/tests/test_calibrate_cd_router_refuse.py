#!/usr/bin/env python3
"""Locks Rule #8 on the CD-router calibrator (B057, June 19): a dry/degenerate
source must REFUSE (exit non-zero) on --apply rather than silently writing empty
affinities over the real CD brains. Root cause it guards: intelligence_layer.json
drifted — 'sector_playbooks'/'occasion_rules' are gone (data moved to
'sector_facts'/'occasion_calendar'), so calibrate() now yields all-empty scores."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import calibrate_cd_router as cc

CDS = ["cd_01", "cd_02", "cd_03", "cd_04", "cd_05"]


class TestCalibrateRefuse(unittest.TestCase):
    def test_empty_source_is_degenerate(self):
        sector = {cd: {} for cd in CDS}
        occ = {cd: {} for cd in CDS}
        self.assertTrue(cc.is_degenerate(sector, occ))

    def test_zero_only_occasions_still_degenerate(self):
        sector = {cd: {} for cd in CDS}
        occ = {cd: {"national_day": 0} for cd in CDS}  # present but no positive signal
        self.assertTrue(cc.is_degenerate(sector, occ))

    def test_real_sector_signal_not_degenerate(self):
        sector = {cd: {} for cd in CDS}
        sector["cd_01"] = {"f_and_b": 0.3}  # even a default fill = live source
        occ = {cd: {} for cd in CDS}
        self.assertFalse(cc.is_degenerate(sector, occ))

    def test_real_occasion_signal_not_degenerate(self):
        sector = {cd: {} for cd in CDS}
        occ = {cd: {} for cd in CDS}
        occ["cd_04"] = {"national_day": 0.9}
        self.assertFalse(cc.is_degenerate(sector, occ))

    def test_apply_refuses_on_degenerate_source(self):
        """The teeth: --apply with a dry source must sys.exit(non-zero) BEFORE any
        CD-brain file is touched. We force calibrate() to a degenerate result so the
        test is independent of the live data's current state."""
        orig_calibrate = cc.calibrate
        orig_argv = sys.argv[:]
        cc.calibrate = lambda: ({cd: {} for cd in CDS}, {cd: {} for cd in CDS})
        sys.argv = ["calibrate_cd_router.py", "--apply"]
        try:
            with self.assertRaises(SystemExit) as ctx:
                cc.main()
            self.assertNotEqual(ctx.exception.code, 0)
            self.assertNotEqual(ctx.exception.code, None)
        finally:
            cc.calibrate = orig_calibrate
            sys.argv = orig_argv


if __name__ == "__main__":
    unittest.main()
