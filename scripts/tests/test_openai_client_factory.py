"""B258 — the bedrock OpenAI client factory + the live-path ratchet.

Guards the one-failure-that-hides-all-others: an un-timed-out OpenAI call that
silently stalls the orchestra. Three locks:
  1. The factory ALWAYS bakes in a timeout + bounded retries (sync AND async),
     and refuses to build a keyless client (Rule #8 — refuse, don't warn).
  2. The migrated live callers go through it (never a raw client).
  3. THE RATCHET: every raw `OpenAI(...)`/`AsyncOpenAI(...)` constructed without
     an explicit timeout must be in a SHRINKING allowlist of known-unmigrated
     scripts. A NEW raw timeout-less client in any live script fails the suite
     LOUD; a migrated/removed script must be dropped from the allowlist or the
     ratchet fails — the list can only get shorter, never longer.
"""
import re
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
from lib.openai_client import (  # noqa: E402
    make_client, make_async_client, load_openai_key,
    DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES,
)
import lib.openai_client as factory  # noqa: E402

# Live-path callers explicitly migrated to the factory.
MIGRATED = ["creative_pipeline.py", "fill_occasions_v2.py",
            "deepen_brand_profiles.py", "multi_llm_collector.py",
            # B258 round 2 (June 19): the always-on enricher daemon + judge +
            # active producers/enrichers — the live paths a hung call would stall.
            "enrich_obs_openai.py", "cd_judge.py", "generate_tensions.py",
            "fill_pillar_emotion.py", "semantic_search.py",
            "generate_brand_dna_gpt.py", "extract_account_obs.py",
            "fill_sparse_visual_fields.py", "apply_dialect.py",
            "apply_emotion_pillar.py"]

# THE RATCHET — scripts that still build a raw, timeout-less client. This list
# is DEBT made visible (B258). It may only SHRINK: when a script is migrated to
# make_client/make_async_client (or given an explicit timeout=), remove it here.
# Adding a new raw timeout-less client to ANY live script (one not on this list)
# fails test_no_new_raw_clients below.
KNOWN_UNMIGRATED = {
    # Remaining debt (B258): heavy/rare one-offs not on the always-on path —
    # video-frame enrichers, the overnight rebuilders, the archive processor,
    # the CD scan/compare one-offs, vision_probe. Migrate in a later shift.
    "cd_model_compare.py", "cd_technique_scan.py",
    "enrich_video_frames.py", "enrich_video_frames_ext.py",
    "overnight_full_rebuild.py", "overnight_improver.py",
    "process_from_archive.py", "run_video_transcription.py", "vision_probe.py",
}

# Matches openai.OpenAI(, OpenAI(, AsyncOpenAI(, openai.AsyncOpenAI(, _OpenAI(...
_RAW_CLIENT = re.compile(r"(?:openai\.)?(?:Async)?OpenAI\s*\(")


def _scan_offenders():
    """Return the set of live scripts (excluding tests/, archive/, and the
    factory itself) that construct a raw client with no explicit timeout."""
    offenders = set()
    for f in sorted(SCRIPTS.rglob("*.py")):
        rel = f.relative_to(SCRIPTS)
        if rel.parts[0] in ("tests", "archive") or rel.as_posix() == "lib/openai_client.py":
            continue
        for line in f.read_text().splitlines():
            if _RAW_CLIENT.search(line) and "timeout=" not in line:
                offenders.add(rel.as_posix())
                break
    return offenders


class TestFactoryDefaults(unittest.TestCase):
    def test_timeout_and_retries_baked_in(self):
        c = make_client("sk-test-fake")
        self.assertEqual(c.timeout, 90.0)
        self.assertEqual(c.max_retries, 2)
        self.assertEqual(DEFAULT_TIMEOUT, 90.0)
        self.assertEqual(DEFAULT_MAX_RETRIES, 2)

    def test_explicit_overrides_respected(self):
        c = make_client("sk-test-fake", timeout=30.0, max_retries=5)
        self.assertEqual(c.timeout, 30.0)
        self.assertEqual(c.max_retries, 5)

    def test_refuses_keyless(self):
        original = factory.load_openai_key
        factory.load_openai_key = lambda: ""
        try:
            with self.assertRaises(RuntimeError):
                make_client("")
        finally:
            factory.load_openai_key = original


class TestAsyncFactory(unittest.TestCase):
    def test_async_timeout_baked_in(self):
        c = make_async_client("sk-test-fake")
        self.assertEqual(c.timeout, 90.0)
        self.assertEqual(c.max_retries, 2)

    def test_async_zero_retries_for_self_looping_callers(self):
        # The collector runs its own retry loop and passes max_retries=0; the
        # timeout must still be baked in.
        c = make_async_client("sk-test-fake", max_retries=0)
        self.assertEqual(c.max_retries, 0)
        self.assertEqual(c.timeout, 90.0)

    def test_async_refuses_keyless(self):
        original = factory.load_openai_key
        factory.load_openai_key = lambda: ""
        try:
            with self.assertRaises(RuntimeError):
                make_async_client("")
        finally:
            factory.load_openai_key = original


class TestMigratedCallers(unittest.TestCase):
    RAW = re.compile(r"(?:Async)?OpenAI\(api_key")

    def test_no_raw_client_in_migrated_files(self):
        for name in MIGRATED:
            src = (SCRIPTS / name).read_text()
            self.assertNotRegex(
                src, self.RAW,
                f"{name} constructs a raw timeout-less client — route it through the factory (B258)")

    def test_migrated_files_use_factory(self):
        for name in MIGRATED:
            src = (SCRIPTS / name).read_text()
            self.assertTrue(
                "make_client" in src or "make_async_client" in src,
                f"{name} no longer references the factory")


class TestRatchet(unittest.TestCase):
    def test_no_new_raw_clients(self):
        """No live script outside the known-unmigrated allowlist may build a
        raw timeout-less client. A new one = the orchestra-staller B258 killed."""
        offenders = _scan_offenders()
        new = offenders - KNOWN_UNMIGRATED
        self.assertEqual(
            new, set(),
            f"NEW raw timeout-less OpenAI client(s) in live scripts: {sorted(new)} — "
            f"route through make_client/make_async_client or pass timeout= (B258)")

    def test_ratchet_only_shrinks(self):
        """Every allowlisted script must still be a real offender. When one is
        migrated (or deleted), drop it from KNOWN_UNMIGRATED — the list never
        carries stale entries, so it can only get shorter."""
        offenders = _scan_offenders()
        stale = KNOWN_UNMIGRATED - offenders
        self.assertEqual(
            stale, set(),
            f"KNOWN_UNMIGRATED lists script(s) that are now clean: {sorted(stale)} — "
            f"remove them; the ratchet only shrinks (B258)")


if __name__ == "__main__":
    unittest.main()
