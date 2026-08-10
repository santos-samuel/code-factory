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

    def test_pi_routes_use_approved_baseten_models(self):
        economy = self.policy["tiers"]["economy"]["pi"]
        critical = self.policy["tiers"]["critical"]["pi"]
        self.assertEqual(
            economy,
            {
                "provider": "ai-gw-baseten",
                "model": "baseten/deepseek-ai/DeepSeek-V4-Flash-0731",
                "thinking": "high",
            },
        )
        self.assertEqual(
            critical,
            {
                "provider": "ai-gw-baseten",
                "model": "baseten/zai-org/GLM-5.2",
                "thinking": "xhigh",
            },
        )
        result = resolve_route("pi", task="review", override="anthropic/claude-opus:high")
        self.assertEqual(result["selection"], "fail-open-default")
        self.assertEqual(result["selected"], critical)
        self.assertEqual(result["observed"], "unknown")

    def test_committed_pi_configuration_contains_only_policy_routes(self):
        root = Path(__file__).resolve().parent.parent
        pi_config = json.loads((root / "pi.json").read_text())
        pi_settings = json.loads((root / "pi-settings.json").read_text())
        self.assertEqual(set(pi_config["providers"]), {"ai-gw-baseten"})
        model_ids = {model["id"] for model in pi_config["providers"]["ai-gw-baseten"]["models"]}
        self.assertEqual(
            model_ids,
            {
                "baseten/deepseek-ai/DeepSeek-V4-Flash-0731",
                "baseten/zai-org/GLM-5.2",
            },
        )
        glm_model = next(
            model
            for model in pi_config["providers"]["ai-gw-baseten"]["models"]
            if model["id"] == "baseten/zai-org/GLM-5.2"
        )
        self.assertEqual(glm_model["thinkingLevelMap"]["xhigh"], "xhigh")
        self.assertIsNone(glm_model["thinkingLevelMap"]["max"])
        self.assertEqual(pi_settings["defaultProvider"], "ai-gw-baseten")
        self.assertEqual(pi_settings["defaultModel"], "baseten/zai-org/GLM-5.2")
        self.assertEqual(pi_settings["defaultThinkingLevel"], "xhigh")
        self.assertEqual(
            pi_settings["enabledModels"],
            [
                "ai-gw-baseten/baseten/zai-org/GLM-5.2:xhigh",
                "ai-gw-baseten/baseten/deepseek-ai/DeepSeek-V4-Flash-0731:high",
            ],
        )

    def test_available_route_is_verified_without_claiming_usage(self):
        result = resolve_route(
            "pi",
            task="review",
            available=["ai-gw-baseten/baseten/zai-org/GLM-5.2"],
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
        pi_result = resolve_route(
            "pi",
            task="review",
            override="ai-gw-baseten/baseten/deepseek-ai/DeepSeek-V4-Flash-0731:high",
        )
        self.assertEqual(pi_result["selection"], "explicit-override")
        self.assertEqual(pi_result["selected"]["model"], "baseten/deepseek-ai/DeepSeek-V4-Flash-0731")

    def test_invalid_overrides_fail_open(self):
        malformed = resolve_route("codex", task="implementation", override=":bogus")
        self.assertEqual(malformed["selection"], "fail-open-default")
        forbidden_pi = resolve_route("pi", task="review", override="ai-gw-anthropic/anthropic/claude-opus:high")
        self.assertEqual(forbidden_pi["selection"], "fail-open-default")
        self.assertEqual(forbidden_pi["selected"]["model"], "baseten/zai-org/GLM-5.2")

    def test_pi_overrides_respect_model_thinking_levels(self):
        unsupported_glm = resolve_route(
            "pi",
            task="review",
            override="ai-gw-baseten/baseten/zai-org/GLM-5.2:max",
        )
        self.assertEqual(unsupported_glm["selection"], "fail-open-default")
        self.assertEqual(unsupported_glm["selected"]["thinking"], "xhigh")

        supported_deepseek = resolve_route(
            "pi",
            task="review",
            override="ai-gw-baseten/baseten/deepseek-ai/DeepSeek-V4-Flash-0731:max",
        )
        self.assertEqual(supported_deepseek["selection"], "explicit-override")
        self.assertEqual(supported_deepseek["selected"]["thinking"], "max")

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

    def test_generated_pi_agents_have_correct_model_and_thinking(self):
        """Every generated Pi agent must embed the Pi-specific model and thinking
        level resolved from its routing_tier, so pi-subagents uses the correct
        model at runtime instead of falling back to the session default."""
        root = Path(__file__).resolve().parent.parent
        agents_dir = root / ".pi" / "agents"
        self.assertTrue(agents_dir.is_dir(), ".pi/agents directory is missing")

        from scripts.model_router import profile_for_tier

        checked = 0
        for agent_file in sorted(agents_dir.glob("*.md")):
            name = agent_file.stem
            content = agent_file.read_text()

            # Parse frontmatter.
            lines = content.splitlines()
            fence_indices = [i for i, l in enumerate(lines) if l.strip() == "---"]
            self.assertGreaterEqual(len(fence_indices), 2, f"{name}: missing frontmatter")
            fm_lines = lines[fence_indices[0] + 1 : fence_indices[1]]

            fm = {}
            for line in fm_lines:
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip().strip('"').strip("'")

            # The general-purpose agent has no routing_tier; it defaults to critical.
            tier = fm.get("routing_tier") or "critical"
            expected = profile_for_tier("pi", tier, self.policy)

            expected_model = f"{expected['provider']}/{expected['model']}"
            self.assertEqual(
                fm.get("model"), expected_model,
                f"{name}: expected Pi model {expected_model}, got {fm.get('model')}",
            )
            self.assertEqual(
                fm.get("thinking"), expected["thinking"],
                f"{name}: expected Pi thinking {expected['thinking']}, got {fm.get('thinking')}",
            )

            # No Claude effort field should leak into Pi agents.
            self.assertNotIn("effort", fm, f"{name}: Claude effort field leaked into Pi agent")

            checked += 1

        self.assertGreater(checked, 0, "no Pi agent files found to validate")


if __name__ == "__main__":
    unittest.main()
