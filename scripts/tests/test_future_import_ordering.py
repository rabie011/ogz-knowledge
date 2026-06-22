#!/usr/bin/env python3
"""Pins the 3 deprecated-judge scripts as PARSEABLE (py_compile clean).

Scar (2026-06-22 audit): cd_judge.py / cd_model_compare.py / build_calibration_set.py each
placed `from __future__ import annotations` AFTER real statements (the `import sys as _s`
+ `--legacy` guard), so Python raised `SyntaxError: from __future__ imports must occur at
the beginning of the file`. The files could not be parsed, imported, or even run with the
--legacy override (the SyntaxError fires at parse time, before any guard executes); and
cd_model_compare/build_calibration_set both `from cd_judge import judge_caption`, so the
break cascaded. The fix moved the future-import to be the FIRST statement after the shebang.

This test compiles each file and asserts the future-import precedes the first real statement,
so the ordering can never silently regress."""
import py_compile
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent
TARGETS = ["cd_judge.py", "cd_model_compare.py", "build_calibration_set.py"]


class TestFutureImportOrdering(unittest.TestCase):
    def test_all_three_compile(self):
        """Each deprecated judge parses cleanly (no SyntaxError)."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in TARGETS:
                src = SCRIPTS / name
                try:
                    py_compile.compile(str(src), cfile=str(Path(tmp) / f"{name}c"),
                                       doraise=True)
                except py_compile.PyCompileError as e:  # pragma: no cover
                    self.fail(f"{name} fails py_compile: {e}")

    def test_future_import_is_first_real_statement(self):
        """`from __future__ import annotations` must come before any other statement
        (shebang + comments are fine; `import sys as _s` / the --legacy guard are NOT)."""
        for name in TARGETS:
            future_line = None
            first_real_line = None
            for i, line in enumerate((SCRIPTS / name).read_text().splitlines()):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue  # shebang, comments, blanks don't count as statements
                if stripped.startswith("from __future__ import"):
                    future_line = i
                    break
                if first_real_line is None:
                    first_real_line = i
            self.assertIsNotNone(future_line, f"{name}: no future-import found")
            self.assertIsNone(
                first_real_line,
                f"{name}: a real statement precedes the future-import (will SyntaxError)")


if __name__ == "__main__":
    unittest.main()
