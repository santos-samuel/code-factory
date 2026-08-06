#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from scripts.model_router import load_policy, plan_parallel, resolve_route, validate_policy


class ModelRouterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()
        validate_policy(cls.policy)

    def test_cross_surface_tiers_keep_claude_mapping_and_codex_models(self):
        economy = self.policy["tiers"]["economy"]
        critical = self.policy["tiers"]["critical"]
        self.assertEqual(economy["claude"], {"model": "sonnet", "effort": "high"})
        self.assertEqual(critical["claude"], {"model": "opus", "effort": "xhigh"})
        self.assertEqual(economy["codex"], {"model": "gpt-5.6-luna", "effort": "max"})
        self.assertEqual(critical["codex"], {"model": "gpt-5.6-sol", "effort": "xhigh"})

    def test_pi_routes_are_openai_only(self):
        for tier in self.policy["tiers"].values():
            self.assertEqual(tier["pi"]["provider"], "datadog-ai-gateway")
            self.assertTrue(tier["pi"]["model"].startswith("openai/"))
        result = resolve_route("pi", task="review", override="anthropic/claude-opus:high")
        self.assertEqual(result["selection"], "fail-open-default")
        self.assertEqual(result["selected"]["provider"], "datadog-ai-gateway")
        self.assertTrue(result["selected"]["model"].startswith("openai/"))
        self.assertEqual(result["observed"], "unknown")

    def test_committed_pi_configuration_contains_only_policy_routes(self):
        root = Path(__file__).resolve().parent.parent
        pi_config = json.loads((root / "pi.json").read_text())
        pi_settings = json.loads((root / "pi-settings.json").read_text())
        self.assertEqual(set(pi_config["providers"]), {"datadog-ai-gateway"})
        model_ids = {model["id"] for model in pi_config["providers"]["datadog-ai-gateway"]["models"]}
        self.assertEqual(model_ids, {"openai/gpt-5.6-luna", "openai/gpt-5.6-sol"})
        self.assertEqual(pi_settings["defaultProvider"], "datadog-ai-gateway")
        self.assertEqual(pi_settings["defaultModel"], "openai/gpt-5.6-sol")
        self.assertTrue(all("claude" not in item.lower() for item in pi_settings["enabledModels"]))

    def test_available_route_is_verified_without_claiming_usage(self):
        result = resolve_route(
            "pi",
            task="review",
            available=["datadog-ai-gateway/openai/gpt-5.6-sol"],
        )
        self.assertEqual(result["verification"], "available")
        self.assertEqual(result["observed"], "available")
        self.assertEqual(result["observed_usage"], "unknown")

    def test_unavailable_route_fails_open_to_configured_default(self):
        result = resolve_route("codex", task="implementation", available=["some-other-model"])
        self.assertEqual(result["selection"], "fail-open-default")
        self.assertEqual(result["selected"]["model"], "gpt-5.6-sol")
        self.assertEqual(result["verification"], "unverified")

    def test_explicit_valid_override_wins(self):
        result = resolve_route("codex", task="implementation", override="gpt-5.6-sol:xhigh")
        self.assertEqual(result["selection"], "explicit-override")
        self.assertEqual(result["selected"], {"model": "gpt-5.6-sol", "effort": "xhigh"})
        pi_result = resolve_route("pi", task="review", override="openai/gpt-5.6-luna:xhigh")
        self.assertEqual(pi_result["selection"], "explicit-override")
        self.assertEqual(pi_result["selected"]["model"], "openai/gpt-5.6-luna")

    def test_invalid_overrides_fail_open(self):
        malformed = resolve_route("codex", task="implementation", override=":bogus")
        self.assertEqual(malformed["selection"], "fail-open-default")
        forbidden_pi = resolve_route("pi", task="review", override="openai/claude-opus:xhigh")
        self.assertEqual(forbidden_pi["selection"], "fail-open-default")
        self.assertTrue(forbidden_pi["selected"]["model"].startswith("openai/gpt-5.6"))

    def test_parallelism_caps_and_probes_unknown_capacity(self):
        self.assertEqual(plan_parallel(8, capacity=8)["dispatch_now"], 3)
        self.assertEqual(plan_parallel(8, capacity=3)["dispatch_now"], 2)
        self.assertEqual(plan_parallel(8, capacity=8, active=2)["dispatch_now"], 1)
        probe = plan_parallel(8)
        self.assertEqual(probe["dispatch_now"], 1)
        self.assertEqual(probe["capacity_status"], "unknown-probe")
        self.assertEqual(plan_parallel(8, active=3)["dispatch_now"], 0)

    def test_failure_stops_dispatch_and_drains_active_workers(self):
        result = plan_parallel(4, capacity=8, active=2, failed=True)
        self.assertEqual(result["dispatch_now"], 0)
        self.assertTrue(result["drain_active"])
        self.assertEqual(result["skip_undispatched"], 4)


if __name__ == "__main__":
    unittest.main()
