"""Tests for intel_consumer_health.py — the Rule #6 orphaned-reader detector.

Covers the scope-resolution edge cases that bit during the build (each was a real false
positive/negative caught by eyeballing, Rule #9): present-key not flagged (negative control),
absent-key flagged, the `{}`-default-then-load guard pattern, a var reused as a function
PARAMETER, and a derived-dict reassignment in a DIFFERENT function scope. Plus a live-repo
assertion that the known orphaned reader is detected and no live key is ever flagged.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import intel_consumer_health as h  # noqa: E402


def _run(reader_src: str, live_keys):
    """Write a fake intel file + one reader script to a temp dir, return orphaned reads.
    The intel file MUST carry the real basename — the detector keys off it."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        intel = d / h.INTEL_BASENAME
        intel.write_text(json.dumps({k: {} for k in live_keys}), encoding="utf-8")
        (d / "reader.py").write_text(reader_src, encoding="utf-8")
        return h.orphaned_intel_reads(scripts_dir=d, intel_path=intel)


# fixtures load the temp intel file by its real basename so _is_intel_load + the file filter match
LOAD = 'import json\nintel = json.loads(open("intelligence_layer.json").read())\n'
LOAD_GLOBAL = 'import json\nINTELLIGENCE = json.loads(open("intelligence_layer.json").read())\n'


class TestIntelConsumerHealth(unittest.TestCase):
    def test_absent_key_flagged(self):
        f = _run(LOAD + 'x = intel.get("gone")\n', live_keys=["present"])
        self.assertEqual([(r["key"]) for r in f], ["gone"])

    def test_present_key_not_flagged_negative_control(self):
        # the negative control: a key that EXISTS must never be reported
        f = _run(LOAD + 'x = intel.get("present")\n', live_keys=["present"])
        self.assertEqual(f, [])

    def test_default_empty_then_load_guard_pattern(self):
        # INTELLIGENCE = {}  /  INTELLIGENCE = json.loads(...)  — must still count (any-load)
        src = ('import json\nINTELLIGENCE = {}\n'
               'INTELLIGENCE = json.loads(open("intelligence_layer.json").read())\n'
               'y = INTELLIGENCE.get("gone")\n')
        f = _run(src, live_keys=["present"])
        self.assertEqual([r["key"] for r in f], ["gone"])

    def test_param_named_intel_not_flagged(self):
        # `intel` as a function PARAMETER holds a caller dict, not the loaded file
        src = LOAD + 'def use(intel=None):\n    return intel.get("gone")\n'
        f = _run(src, live_keys=["present"])
        self.assertEqual(f, [])  # the module load is never .get()d; the param read is excluded

    def test_derived_dict_in_other_scope_not_flagged(self):
        # the creative_pipeline.py shape: load in one function, derived-dict reuse in another
        src = ('import json\n'
               'def load():\n    intel = json.loads(open("intelligence_layer.json").read())\n'
               '    return intel.get("gone")\n'              # real orphan
               'def gen():\n    intel = load()\n'
               '    return intel.get("emotion")\n')          # derived dict — NOT an orphan
        f = _run(src, live_keys=["present"])
        self.assertEqual([r["key"] for r in f], ["gone"])

    def test_module_global_read_inside_function(self):
        # INTELLIGENCE global loaded at module scope, read inside a function (brief-engine shape)
        src = (LOAD_GLOBAL
               + 'def brief():\n    return INTELLIGENCE.get("gone")\n')
        f = _run(src, live_keys=["present"])
        self.assertEqual([r["key"] for r in f], ["gone"])

    def test_live_repo_known_orphan_detected(self):
        # against the real repo: the live brief engine's dropped-key reads must surface,
        # and NO key that exists in the live intelligence_layer.json may ever be flagged
        findings = h.orphaned_intel_reads()
        files = {r["file"] for r in findings}
        self.assertIn("build_production_brief_engine.py", files)
        live = h.live_intel_keys()
        self.assertTrue(all(r["key"] not in live for r in findings))


if __name__ == "__main__":
    unittest.main()
