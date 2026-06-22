#!/usr/bin/env python3
"""Locks the PROPORTIONATE model-change hedge (I1–I5, 2026-06-22). The consult flagged a real
time-bomb: a fal/caption model UPDATE/DEPRECATION could silently invalidate visual consistency or
the taste-Elo and nobody would know. These tests lock that it's now DETECTABLE:
  • model_registry FINGERPRINTs carry the model id+version+date (I2)
  • detect_*_drift catches a changed model AND a MISSING stamp, passes a matching one (I1)
  • check_model_drift.check() reads the real on-disk stamps and BITES on a mismatch (I4, Rule #8)
  • BOTH live render paths are fingerprinted + drift-checked: the MASTER (render_openclaw/flux-2-pro)
    and the DRAFT (render_image/schnell), so a silent swap on either is detectable.
(The persona/visual-asset contract is NOT here — it lives model-agnostically at
12_data_shapes/brand_visual_dna_v37_v1.schema.json; the premature dataclass was cut as out of scope.)
Pure + $0 — no fal, no LLM, no network."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import model_registry as mr
import check_model_drift as cmd


class TestRegistryAndFingerprints(unittest.TestCase):
    def test_registries_have_the_required_keys(self):
        r = mr.render_registry()
        self.assertEqual(set(r), {"render_model", "render_model_version", "registered"})
        c = mr.caption_registry()
        self.assertIn("caption_models", c)
        self.assertEqual(c["caption_models"][0], mr.CAPTION_MODEL_PRIMARY)

    def test_render_fingerprint_stamps_id_version_date(self):
        fp = mr.fingerprint_render()["model_fingerprint"]
        self.assertEqual(fp["kind"], "render")
        self.assertEqual(fp["registry_model"], mr.RENDER_MODEL)
        self.assertEqual(fp["model_version"], mr.RENDER_MODEL_VERSION)
        self.assertTrue(fp["stamped_at"])  # a date was stamped

    def test_render_fingerprint_records_the_model_actually_used(self):
        fp = mr.fingerprint_render("some/other-backend")["model_fingerprint"]
        self.assertEqual(fp["model"], "some/other-backend")        # what ran
        self.assertEqual(fp["registry_model"], mr.RENDER_MODEL)    # what's declared

    def test_caption_fingerprint_for_taste_elo_is_flat(self):
        cf = mr.caption_fingerprint()
        self.assertEqual(cf["caption_model_primary"], mr.CAPTION_MODEL_PRIMARY)
        self.assertIn(mr.CAPTION_MODEL_FALLBACK, cf["caption_models"])


class TestDriftDetection(unittest.TestCase):
    def test_render_drift_false_when_matching(self):
        stamp = mr.fingerprint_render()["model_fingerprint"]
        self.assertFalse(mr.detect_render_drift(stamp)["drift"])

    def test_render_drift_true_on_changed_model(self):
        stamp = {"registry_model": "fal-ai/OLD-model", "model_version": "old"}
        v = mr.detect_render_drift(stamp)
        self.assertTrue(v["drift"])
        self.assertIn("changed", v["reason"])

    def test_render_missing_stamp_is_unverified_not_drift(self):
        # a legacy un-fingerprinted render is UNVERIFIED (can't vouch), NOT a model CHANGE (Rule #9)
        v = mr.detect_render_drift(None)
        self.assertFalse(v["drift"])
        self.assertTrue(v["unverified"])
        self.assertTrue(mr.detect_render_drift({})["unverified"])

    def test_caption_drift_false_when_matching(self):
        self.assertFalse(mr.detect_caption_drift(mr.caption_fingerprint())["drift"])

    def test_caption_drift_true_on_changed_primary(self):
        v = mr.detect_caption_drift({"caption_model_primary": "gpt-OLD"})
        self.assertTrue(v["drift"])

    def test_caption_missing_stamp_is_unverified_not_drift(self):
        v = mr.detect_caption_drift(None)
        self.assertFalse(v["drift"])
        self.assertTrue(v["unverified"])


class TestCheckModelDriftGate(unittest.TestCase):
    """check_model_drift.check() over scratch on-disk artifacts (Rule #9: reads real stamps)."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "data").mkdir()
        self._orig_fal, self._orig_elo = cmd.FAL_COST_LOG, cmd.TASTE_ELO
        cmd.FAL_COST_LOG = self.d / "data/fal_cost_log.jsonl"
        cmd.TASTE_ELO = self.d / "data/taste_elo.json"

    def tearDown(self):
        cmd.FAL_COST_LOG, cmd.TASTE_ELO = self._orig_fal, self._orig_elo

    def _render_line(self, fp):
        row = {"day": "2026-06-22", "handle": "albaik", "chain": "S01",
               "model": "x", "usd": 0.03, "image_url": "/static/renders_v37/x.jpg"}
        if fp is not None:
            row["model_fingerprint"] = fp
        cmd.FAL_COST_LOG.write_text(json.dumps(row, ensure_ascii=False) + "\n")

    def _elo(self, cf):
        cmd.TASTE_ELO.write_text(json.dumps(
            {"n_pairs": 1, "caption_model_fingerprint": cf} if cf else {"n_pairs": 1},
            ensure_ascii=False))

    def test_no_artifacts_is_no_drift_and_unchecked(self):
        v = cmd.check()
        self.assertFalse(v["drift"])
        self.assertFalse(v["axes"]["render"]["checked"])
        self.assertFalse(v["axes"]["caption_taste"]["checked"])

    def test_matching_stamps_no_drift(self):
        self._render_line(mr.fingerprint_render()["model_fingerprint"])
        self._elo(mr.caption_fingerprint())
        v = cmd.check()
        self.assertFalse(v["drift"])
        self.assertTrue(v["axes"]["render"]["checked"])

    def test_changed_render_model_bites(self):
        self._render_line({"registry_model": "fal-ai/OLD", "model_version": "old"})
        self._elo(mr.caption_fingerprint())
        v = cmd.check()
        self.assertTrue(v["drift"])
        self.assertTrue(v["axes"]["render"]["drift"])
        self.assertFalse(v["axes"]["caption_taste"]["drift"])

    def test_changed_caption_model_bites(self):
        self._render_line(mr.fingerprint_render()["model_fingerprint"])
        self._elo({"caption_model_primary": "gpt-OLD"})
        v = cmd.check()
        self.assertTrue(v["drift"])
        self.assertTrue(v["axes"]["caption_taste"]["drift"])

    def test_unfingerprinted_live_render_is_unverified_not_drift(self):
        self._render_line(None)   # a real render with NO stamp (legacy)
        self._elo(mr.caption_fingerprint())
        v = cmd.check()
        self.assertFalse(v["drift"])          # not a CHANGE → not a hard gate fail
        self.assertTrue(v["unverified"])      # but flagged as un-vouched
        self.assertTrue(v["axes"]["render"]["unverified"])

    def test_last_render_wins_over_older_lines(self):
        # an older matching render then a newer CHANGED one → drift (we judge the live model)
        good = json.dumps({"model": "x", "image_url": "/a.jpg",
                           "model_fingerprint": mr.fingerprint_render()["model_fingerprint"]}, ensure_ascii=False)
        bad = json.dumps({"model": "x", "image_url": "/b.jpg",
                          "model_fingerprint": {"registry_model": "fal-ai/OLD", "model_version": "old"}}, ensure_ascii=False)
        cmd.FAL_COST_LOG.write_text(good + "\n" + bad + "\n")
        self._elo(mr.caption_fingerprint())
        self.assertTrue(cmd.check()["drift"])


class TestDraftRenderPath(unittest.TestCase):
    """The DRAFT render path (render_image / schnell) is fingerprinted + drift-checked like the master."""

    def test_draft_registry_shape_matches_master(self):
        r = mr.render_draft_registry()
        self.assertEqual(set(r), {"render_model", "render_model_version", "registered"})
        self.assertEqual(r["render_model"], mr.RENDER_MODEL_DRAFT)

    def test_draft_fingerprint_stamps_id_version_date(self):
        fp = mr.fingerprint_render_draft()["model_fingerprint"]
        self.assertEqual(fp["kind"], "render_draft")
        self.assertEqual(fp["registry_model"], mr.RENDER_MODEL_DRAFT)
        self.assertEqual(fp["model_version"], mr.RENDER_MODEL_DRAFT_VERSION)
        self.assertTrue(fp["stamped_at"])

    def test_draft_drift_false_when_matching(self):
        stamp = mr.fingerprint_render_draft()["model_fingerprint"]
        self.assertFalse(mr.detect_render_draft_drift(stamp)["drift"])

    def test_draft_drift_true_on_changed_model(self):
        v = mr.detect_render_draft_drift({"registry_model": "fal-ai/OLD-schnell", "model_version": "old"})
        self.assertTrue(v["drift"])
        self.assertIn("changed", v["reason"])

    def test_draft_missing_stamp_is_unverified_not_drift(self):
        v = mr.detect_render_draft_drift(None)
        self.assertFalse(v["drift"])
        self.assertTrue(v["unverified"])


class TestCheckDraftAxis(unittest.TestCase):
    """check_model_drift.check() over a scratch image cost log (the DRAFT axis, Rule #9)."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "data").mkdir()
        self._orig_fal, self._orig_img, self._orig_elo = cmd.FAL_COST_LOG, cmd.IMAGE_COST_LOG, cmd.TASTE_ELO
        cmd.FAL_COST_LOG = self.d / "data/fal_cost_log.jsonl"
        cmd.IMAGE_COST_LOG = self.d / "data/image_cost_log.jsonl"
        cmd.TASTE_ELO = self.d / "data/taste_elo.json"

    def tearDown(self):
        cmd.FAL_COST_LOG, cmd.IMAGE_COST_LOG, cmd.TASTE_ELO = self._orig_fal, self._orig_img, self._orig_elo

    def _draft_line(self, fp):
        row = {"day": "2026-06-22", "card": "x.json", "model": "x", "usd": 0.003,
               "image_url": "/static/renders/x.jpg"}
        if fp is not None:
            row["model_fingerprint"] = fp
        cmd.IMAGE_COST_LOG.write_text(json.dumps(row, ensure_ascii=False) + "\n")

    def test_no_draft_artifacts_is_unchecked(self):
        v = cmd.check()
        self.assertFalse(v["axes"]["render_draft"]["checked"])

    def test_matching_draft_stamp_no_drift(self):
        self._draft_line(mr.fingerprint_render_draft()["model_fingerprint"])
        v = cmd.check()
        self.assertFalse(v["axes"]["render_draft"]["drift"])
        self.assertTrue(v["axes"]["render_draft"]["checked"])

    def test_changed_draft_model_bites(self):
        self._draft_line({"registry_model": "fal-ai/OLD-schnell", "model_version": "old"})
        v = cmd.check()
        self.assertTrue(v["drift"])
        self.assertTrue(v["axes"]["render_draft"]["drift"])

    def test_unfingerprinted_live_draft_is_unverified_not_drift(self):
        self._draft_line(None)
        v = cmd.check()
        self.assertFalse(v["drift"])
        self.assertTrue(v["unverified"])
        self.assertTrue(v["axes"]["render_draft"]["unverified"])


class TestLiveReposCurrentlyConsistent(unittest.TestCase):
    """Eyes-on the REAL repo this shift (Rule #9): no model has CHANGED under the live artifacts, so
    the hard drift gate is GREEN. (The render cost-log may still read UNVERIFIED — those lines are
    legacy renders made before fingerprinting; they re-stamp on the next render. That's the honest
    state, not a failure.) If a real model swap ever happens without re-validating, drift flips True
    and this fails loudly — exactly the alarm the hedge exists to raise."""
    def test_live_drift_check_has_no_real_drift(self):
        v = cmd.check()
        self.assertFalse(v["drift"], f"a model CHANGED under the live repo: {v['axes']}")

    def test_live_taste_elo_carries_caption_fingerprint(self):
        # taste_elo.json is regenerated on the heartbeat; after this build it carries the stamp,
        # so the caption axis is verified (not just unverified-legacy).
        v = cmd.check()
        ct = v["axes"]["caption_taste"]
        if ct.get("checked"):
            self.assertFalse(ct.get("unverified"),
                             "taste_elo.json is missing its caption fingerprint — re-run taste_elo.py")


if __name__ == "__main__":
    unittest.main()
