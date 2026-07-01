#!/usr/bin/env python3
"""C245 patch-1: product-crop primitive. Deterministic geometry, zero network (vision mocked)."""
import sys, unittest, tempfile, json
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
from PIL import Image
import crop_product as cp


class TestCropGeometry(unittest.TestCase):
    """crop_to_bbox is PURE PIL — the geometry we can prove without spending a cent."""

    def _img(self, w=200, h=100):
        d = Path(tempfile.mkdtemp())
        p = d / "src.jpg"
        Image.new("RGB", (w, h), (10, 20, 30)).save(p, "JPEG")
        return p, d

    def test_bbox_maps_to_pixels(self):
        src, d = self._img(200, 100)
        out = d / "crop.jpg"
        saved, px = cp.crop_to_bbox(src, {"x0": 0.25, "y0": 0.5, "x1": 0.75, "y1": 1.0}, out)
        self.assertEqual(px, (50, 50, 150, 100))
        self.assertTrue(Path(saved).exists())
        with Image.open(saved) as im:
            self.assertEqual(im.size, (100, 50))

    def test_full_frame(self):
        src, d = self._img(120, 80)
        _, px = cp.crop_to_bbox(src, {"x0": 0, "y0": 0, "x1": 1, "y1": 1}, d / "c.jpg")
        self.assertEqual(px, (0, 0, 120, 80))

    def test_out_of_range_is_clamped(self):
        src, d = self._img(100, 100)
        _, px = cp.crop_to_bbox(src, {"x0": -0.5, "y0": 0.1, "x1": 2.0, "y1": 0.9}, d / "c.jpg")
        self.assertEqual(px, (0, 10, 100, 90))

    def test_degenerate_bbox_raises(self):
        src, d = self._img()
        with self.assertRaises(ValueError):
            cp.crop_to_bbox(src, {"x0": 0.5, "y0": 0.5, "x1": 0.5, "y1": 0.9}, d / "c.jpg")

    def test_collapsed_rounding_still_yields_1px(self):
        # a razor-thin box that rounds to the same pixel must not produce an empty crop
        src, d = self._img(100, 100)
        _, (l, u, r, low) = cp.crop_to_bbox(src, {"x0": 0.501, "y0": 0.2, "x1": 0.503, "y1": 0.8}, d / "c.jpg")
        self.assertGreaterEqual(r, l + 1)
        self.assertGreaterEqual(low, u + 1)


class TestCropProductComposed(unittest.TestCase):
    """crop_product = product_bbox (mocked) → crop_to_bbox. Proves the wire without a live call."""

    def _img(self):
        d = Path(tempfile.mkdtemp())
        p = d / "lifestyle.jpg"
        Image.new("RGB", (400, 400), (200, 180, 160)).save(p, "JPEG")
        return p, d

    def test_found_product_gets_cropped(self):
        src, d = self._img()
        out = d / "out.jpg"
        fake = {"found": True, "product_en": "gold pendant necklace",
                "bbox": {"x0": 0.4, "y0": 0.3, "x1": 0.6, "y1": 0.55}}
        with mock.patch.object(cp, "product_bbox", return_value=fake):
            res = cp.crop_product(src, "FAKEKEY", out)
        self.assertTrue(res["found"])
        self.assertEqual(res["product_en"], "gold pendant necklace")
        self.assertTrue(Path(res["crop"]).exists())
        self.assertEqual(res["px"], (160, 120, 240, 220))

    def test_no_product_writes_nothing(self):
        src, d = self._img()
        out = d / "out.jpg"
        with mock.patch.object(cp, "product_bbox", return_value={"found": False}):
            res = cp.crop_product(src, "FAKEKEY", out)
        self.assertFalse(res["found"])
        self.assertFalse(out.exists())  # safe: no person leaked into a bogus crop


class TestRealJpegIntegration(unittest.TestCase):
    """Panel ask (RABIE+DeepSeek, 3/5): prove crop_to_bbox on a REAL brand JPEG — real EXIF/encoding,
    not a synthetic in-memory frame. Catches file-I/O + PIL format edge cases the synthetic tests miss.
    Vision call stays mocked (money discipline; live gpt-4o spend deferred to the render-integration
    stage, not patch-1's geometry contract)."""

    REAL = cp.B / "clients" / "albaik" / "media" / "C06eKDFIYGt.jpg"

    @unittest.skipUnless(REAL.exists(), "real brand fixture not present")
    def test_crop_real_jpeg(self):
        with Image.open(self.REAL) as im:
            w, h = im.size
        d = Path(tempfile.mkdtemp())
        out = d / "real_crop.jpg"
        fake = {"found": True, "product_en": "test product",
                "bbox": {"x0": 0.2, "y0": 0.2, "x1": 0.8, "y1": 0.8}}
        with mock.patch.object(cp, "product_bbox", return_value=fake):
            res = cp.crop_product(self.REAL, "FAKEKEY", out)
        self.assertTrue(res["found"])
        self.assertTrue(Path(res["crop"]).exists())
        exp = (int(round(0.2 * w)), int(round(0.2 * h)), int(round(0.8 * w)), int(round(0.8 * h)))
        self.assertEqual(res["px"], exp)
        with Image.open(res["crop"]) as cropped:
            self.assertEqual(cropped.size, (exp[2] - exp[0], exp[3] - exp[1]))


class TestPatch3CropRegistration(unittest.TestCase):
    """C245 patch-3: register_crop persists the crop into media_class.json as a clean product ref,
    and pick_reference (openclaw_convert.py) then MATCHES it by product — the Rule #6 consumer wire.
    Proves end-to-end: a jewelry brand with no clean product photo gets a SAFE crop reference instead
    of a GAP-REFUSE, while a non-matching product still refuses (Rule #8 preserved). Zero network."""

    def setUp(self):
        # sandbox the repo root both modules resolve paths against, so we never touch real clients/
        self.d = Path(tempfile.mkdtemp())
        self.handle = "testjewelry"
        prof = self.d / "clients" / self.handle / "profile" / "crops"
        prof.mkdir(parents=True)
        self.crop = prof / "lifestyle_crop.jpg"
        Image.new("RGB", (80, 80), (212, 175, 55)).save(self.crop, "JPEG")  # a "gold" crop
        import openclaw_convert as oc
        self.oc = oc
        self._cpB, self._ocB = cp.B, oc.B
        cp.B = self.d
        oc.B = self.d

    def tearDown(self):
        cp.B, self.oc.B = self._cpB, self._ocB

    def test_register_writes_clean_person_free_entry(self):
        key = cp.register_crop(self.handle, str(self.crop), "gold pendant necklace", src="src.jpg")
        mc = json.loads((self.d / "clients" / self.handle / "profile" / "media_class.json").read_text())
        self.assertIn(key, mc)
        e = mc[key]
        self.assertTrue(e["usable_as_product_reference"])
        self.assertFalse(e["has_person"])          # safe: person was cropped out
        self.assertFalse(e["is_royal_or_public_figure"])
        self.assertEqual(e["source"], "crop")
        self.assertEqual(e["product_en"], "gold pendant necklace")
        self.assertTrue((self.d / key).exists())    # B/key resolves to the real crop file

    def test_pick_reference_matches_the_registered_crop(self):
        key = cp.register_crop(self.handle, str(self.crop), "gold pendant necklace")
        ref = self.oc.pick_reference(self.handle, product="gold pendant necklace")
        self.assertEqual(ref, key)                  # the wire: crop is chosen as the flux-edit ref

    def test_non_matching_product_still_refuses(self):
        cp.register_crop(self.handle, str(self.crop), "gold pendant necklace")
        ref = self.oc.pick_reference(self.handle, product="diamond tennis bracelet")
        self.assertIsNone(ref)                       # Rule #8 preserved: no wrong-product render


class TestPatch4HarvestWire(unittest.TestCase):
    """C245 patch-4: the pipeline consumer wire (Rule #6). select_crop_candidates is PURE (zero
    spend, like crop_to_bbox) and harvest_crops composes it with an injectable cropper — so a brand
    with only model shots gets safe product crops registered, instead of pick_reference → None →
    render BLOCKED. Proves selection logic, the fallback-only guard, idempotency, and end-to-end
    register → pick_reference, all with a FAKE cropper (no network)."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.handle = "lifestylebrand"
        (self.d / "clients" / self.handle / "profile").mkdir(parents=True)
        self._cpB = cp.B
        cp.B = self.d

    def tearDown(self):
        cp.B = self._cpB

    def test_selects_only_incidental_product_shots(self):
        cache = {
            "a.jpg": {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": False},
            "b.jpg": {"has_person": True, "person_role": "subject", "is_royal_or_public_figure": False},  # portrait/model
            "c.jpg": {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": True},  # royal
            "d.jpg": {"has_person": False, "person_role": "none"},  # no person, but not a usable ref
        }
        self.assertEqual(cp.select_crop_candidates(cache), ["a.jpg"])

    def test_fallback_only_when_no_clean_ref(self):
        # a brand that already has a clean product photo needs no crop harvest
        cache = {
            "clean.jpg": {"usable_as_product_reference": True, "has_person": False, "is_royal_or_public_figure": False},
            "model.jpg": {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": False},
        }
        self.assertEqual(cp.select_crop_candidates(cache), [])

    def test_harvest_registers_and_is_idempotent(self):
        src = self.d / "clients" / self.handle / "media"
        src.mkdir(parents=True)
        (src / "model1.jpg").write_bytes(b"x")
        cache = {"clients/%s/media/model1.jpg" % self.handle:
                 {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": False}}

        def fake_cropper(s, key, out):
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (40, 40), (200, 170, 60)).save(out, "JPEG")
            return {"found": True, "product_en": "gold ring", "crop": str(out)}

        regs = cp.harvest_crops(self.handle, "KEY", cache=cache, cropper=fake_cropper, limit=8)
        self.assertEqual(len(regs), 1)
        # the crop is now a clean ref in media_class.json, and pick_reference finds it
        import openclaw_convert as oc
        _ocB = oc.B
        oc.B = self.d
        try:
            mc = json.loads((self.d / "clients" / self.handle / "profile" / "media_class.json").read_text())
            self.assertTrue(any(v.get("source") == "crop" for v in mc.values()))
            self.assertEqual(oc.pick_reference(self.handle, product="gold ring"), regs[0])
            # idempotency: re-run over the updated cache selects nothing (crop counts as a clean ref)
            self.assertEqual(cp.select_crop_candidates(mc), [])
        finally:
            oc.B = _ocB

    def test_one_failed_crop_does_not_abort_batch(self):
        cache = {
            "clients/%s/media/a.jpg" % self.handle: {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": False},
            "clients/%s/media/b.jpg" % self.handle: {"has_person": True, "person_role": "incidental", "is_royal_or_public_figure": False},
        }
        calls = {"n": 0}

        def flaky_cropper(s, key, out):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("vision API 500")
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (40, 40), (200, 170, 60)).save(out, "JPEG")
            return {"found": True, "product_en": "silver cuff", "crop": str(out)}

        regs = cp.harvest_crops(self.handle, "KEY", cache=cache, cropper=flaky_cropper, limit=8)
        self.assertEqual(len(regs), 1)   # first failed (Rule #8 per-image), second still registered


if __name__ == "__main__":
    unittest.main()
