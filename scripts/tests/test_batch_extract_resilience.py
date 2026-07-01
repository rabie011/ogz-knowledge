#!/usr/bin/env python3
"""Locks the model-resilience of batch_extract (B263 unblock, July 1): vision now
runs OpenAI gpt-4o PRIMARY (funded) with Anthropic claude-haiku FALLBACK, chosen
by which key is present. The extractor must NEVER fail-open — vision_extract RAISES
when no provider is usable or a call returns empty (Rule #8). These tests mock the
HTTP layer so no real API is called and no money is spent."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import batch_extract as be


def _fake_http(payload_text):
    """A urlopen context-manager returning an OpenAI-shaped chat completion."""
    body = {"choices": [{"message": {"content": payload_text}}]}
    resp = io.BytesIO(json.dumps(body).encode("utf-8"))
    cm = mock.MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


class TestProviderChoice(unittest.TestCase):
    def test_openai_is_primary_when_both_keys_present(self):
        with mock.patch.object(be, "_env", side_effect=lambda n: "k" if n in
                               ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") else ""):
            self.assertEqual(be.usable_provider(), "openai")

    def test_anthropic_is_fallback_when_only_it_present(self):
        with mock.patch.object(be, "_env",
                               side_effect=lambda n: "k" if n == "ANTHROPIC_API_KEY" else ""):
            self.assertEqual(be.usable_provider(), "anthropic")

    def test_none_when_no_keys(self):
        with mock.patch.object(be, "_env", return_value=""):
            self.assertEqual(be.usable_provider(), "")


class TestVisionExtract(unittest.TestCase):
    def test_openai_path_returns_text(self):
        with mock.patch.object(be, "_env",
                               side_effect=lambda n: "k" if n == "OPENAI_API_KEY" else ""), \
             mock.patch.object(be.urllib.request, "urlopen",
                               return_value=_fake_http('{"composition_style":"flatlay"}')):
            out = be.vision_extract("sys", "user", "b64data", "image/jpeg")
        self.assertIn("flatlay", out)

    def test_raises_when_no_provider(self):
        with mock.patch.object(be, "_env", return_value=""):
            with self.assertRaises(RuntimeError):
                be.vision_extract("sys", "user", "b64", "image/jpeg")

    def test_raises_on_empty_openai_content(self):
        with mock.patch.object(be, "_env",
                               side_effect=lambda n: "k" if n == "OPENAI_API_KEY" else ""), \
             mock.patch.object(be.urllib.request, "urlopen",
                               return_value=_fake_http("   ")):
            with self.assertRaises(RuntimeError):
                be.vision_extract("sys", "user", "b64", "image/jpeg")


if __name__ == "__main__":
    unittest.main()
