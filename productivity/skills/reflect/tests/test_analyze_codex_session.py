#!/usr/bin/env python3
"""Deterministic tests for the Codex session analyzer."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
FIXTURES = TEST_DIR / "fixtures"
SCRIPT = TEST_DIR.parent / "scripts" / "analyze-codex-session.py"
SPEC = importlib.util.spec_from_file_location("analyze_codex_session", SCRIPT)
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ANALYZER
SPEC.loader.exec_module(ANALYZER)


class AnalyzerTest(unittest.TestCase):
    def report(self) -> dict[str, object]:
        sessions = ANALYZER.load_sessions(FIXTURES, days=None)
        selected = ANALYZER.descendants(sessions, "root-thread")
        return ANALYZER.aggregate(selected, "root-thread")

    def test_recursive_unique_aggregate_uses_final_token_record(self) -> None:
        report = self.report()
        self.assertEqual(report["sessions"], 3)
        self.assertEqual(report["tokens"]["total_tokens"], 387)
        self.assertEqual(report["tokens"]["input_tokens"], 350)
        self.assertEqual(report["tokens"]["cached_input_tokens"], 250)
        self.assertEqual(report["observed_tool_records"], 4)
        self.assertEqual(report["observed_wait_records"], 3)
        self.assertEqual(report["observed_spawn_records"], 2)
        self.assertEqual(report["shell_records_mentioning_bzl"], 1)
        self.assertEqual(report["duplicate_thread_files"], 1)
        self.assertEqual(report["wall_seconds"], 120.0)
        self.assertEqual(report["summed_session_seconds"], 180.0)

    def test_provenance_and_skipped_records_are_explicit(self) -> None:
        report = self.report()
        provenance = report["metric_provenance"]
        self.assertEqual(provenance["tokens"], "lower_bound")
        self.assertEqual(provenance["wall_seconds"], "derived")
        self.assertEqual(provenance["observed_tool_records"], "lower_bound")
        self.assertEqual(provenance["malformed_records"], "measured")
        self.assertEqual(report["malformed_records"], 1)
        self.assertEqual(report["threads_without_token_record"], 0)
        self.assertIsNone(report["cost_usd"])
        self.assertEqual(report["cost_source"], "unknown")

    def test_root_listing_is_bounded_and_scrubs_sensitive_prompt_content(self) -> None:
        sessions = ANALYZER.load_sessions(FIXTURES, days=None)
        output = io.StringIO()
        with redirect_stdout(output):
            ANALYZER.print_roots(sessions, limit=1)
        text = output.getvalue()
        self.assertEqual(len(text.splitlines()), 1)
        self.assertNotIn("sk-secretvalue123", text)
        self.assertNotIn("https://example.test/private", text)
        self.assertIn("<secret>", text)
        self.assertIn("<url>", text)

    def test_human_and_json_outputs_are_bounded_and_do_not_replay_inputs(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT),
            "--sessions-dir",
            str(FIXTURES),
            "--root",
            "root-thread",
        ]
        human = subprocess.run(
            command, check=True, capture_output=True, text=True
        ).stdout
        encoded = subprocess.run(
            [*command, "--json"], check=True, capture_output=True, text=True
        ).stdout
        report = json.loads(encoded)
        for output in (human, encoded):
            self.assertNotIn("sk-secretvalue123", output)
            self.assertNotIn("bzl test //...", output)
            self.assertNotIn("tools.wait_agent", output)
        self.assertLessEqual(len(human.splitlines()), 30)
        self.assertLessEqual(len(report["top_uncached_input"]), 10)
        self.assertLessEqual(len(report["top_waits"]), 10)


if __name__ == "__main__":
    unittest.main()
