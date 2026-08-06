#!/usr/bin/env python3
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

GOLDEN_PACKAGES = [
    "npm:context-mode",
    "npm:pi-subagents",
    "npm:pi-mcp-adapter",
    "npm:pi-markdown-preview",
    "npm:pi-powerline-footer",
    "npm:@juicesharp/rpiv-ask-user-question",
    "npm:@datadog/pi-plugin",
    "../../dd/datadog-pi-packages/packages/refresh-models",
    "../../dd/datadog-pi-packages/packages/research-web",
    "../../dd/datadog-pi-packages/packages/session-cost",
    "../../dd/datadog-pi-packages/packages/compaction-continue",
]


class PiConfigTest(unittest.TestCase):
    def test_settings_extend_golden_without_duplicates_or_competing_tools(self):
        settings = json.loads((ROOT / "pi-settings.json").read_text())
        self.assertEqual(
            settings["packages"],
            GOLDEN_PACKAGES + ["../../dd/datadog-pi-packages/packages/confluence-adf"],
        )
        self.assertEqual(len(settings["packages"]), len(set(settings["packages"])))
        self.assertNotIn("npm:pi-web-search@1.3.0", settings["packages"])
        self.assertFalse((ROOT / "pi-extensions" / "ask-question").exists())

    def test_generated_assets_use_golden_question_and_web_tools(self):
        general_agent = (ROOT / ".pi" / "agents" / "general-purpose.md").read_text()
        self.assertIn('"ask_user_question"', general_agent)
        self.assertNotIn('"ask_question"', general_agent)
        generated_text = "\n".join(
            path.read_text(errors="ignore")
            for path in (ROOT / ".pi").rglob("*.md")
        )
        self.assertIn("web_search", generated_text)
        self.assertNotIn("AskUserQuestion", generated_text)
        self.assertFalse((ROOT / ".pi" / "extensions" / "ask-question").exists())

    def test_generated_mcp_merges_shared_servers_with_pi_overrides(self):
        overlay = json.loads((ROOT / "pi-mcp-overrides.json").read_text())
        self.assertEqual(
            overlay["mcpServers"]["atlassian"]["url"],
            "https://mcp.atlassian.com/v1/mcp/authv2",
        )
        generated = json.loads((ROOT / ".pi" / "mcp.json").read_text())
        servers = generated["mcpServers"]
        self.assertEqual(servers["atlassian"]["auth"], "oauth")
        self.assertTrue(servers["atlassian"]["oauth"]["skipIssuerValidation"])
        self.assertEqual(
            servers["datadog"]["url"],
            "https://mcp.datadoghq.com/api/unstable/mcp-server/mcp",
        )
        self.assertEqual(servers["slack"]["oauth"]["redirectUri"], "http://localhost:3118/callback")
        self.assertIn("datadog-google-workspace", servers)

    def test_bootstrap_preserves_managed_settings_and_upgrades_legacy_providers(self):
        bootstrap = (ROOT / "init.sh").read_text()
        self.assertIn('local managed_provider="ai-gw-baseten"', bootstrap)
        self.assertNotIn('map(select(startswith("ai-gw-")', bootstrap)
        self.assertIn('DD_PI_CANONICAL_REPO="$HOME/dd/datadog-pi-packages"', bootstrap)
        self.assertIn('ln -s "$DD_PI_REPO" "$DD_PI_CANONICAL_REPO"', bootstrap)
        self.assertNotIn('pi install "$pkg_path"', bootstrap)

    def test_sync_check_accepts_absent_empty_extensions_output(self):
        extensions = ROOT / ".pi" / "extensions"
        if extensions.exists():
            extensions.rmdir()

        result = subprocess.run(
            ["bash", str(ROOT / "sync-pi.sh"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
