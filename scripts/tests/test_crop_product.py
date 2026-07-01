#!/usr/bin/env python3
"""C245 patch-1: product-crop primitive. Deterministic geometry, zero network (vision mocked)."""
import sys, unittest, tempfile
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


if __name__ == "__main__":
    unittest.main()
