#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_ROUTER="$ROOT/scripts/model_router.py"

status=0
for source in "$ROOT"/productivity/agents/*.md; do
    role="$(basename "$source" .md)"
    routing_tier="$(awk -F': *' '/^routing_tier: / { print $2; exit }' "$source")"
    if [[ -z "$routing_tier" ]]; then
        echo "  FAIL  $role is missing routing_tier metadata"
        status=1
        continue
    fi

    if ! read -r expected_model expected_effort <<< "$(python3 "$MODEL_ROUTER" agent-profile --surface codex --tier "$routing_tier" --format shell)"; then
        echo "  FAIL  unsupported routing tier for $role: $routing_tier"
        status=1
        continue
    fi
    read -r expected_claude_model expected_claude_effort <<< "$(python3 "$MODEL_ROUTER" agent-profile --surface claude --tier "$routing_tier" --format shell)"

    actual_claude_model="$(awk -F': *' '/^model: / { print $2; exit }' "$source")"
    actual_claude_effort="$(awk -F': *' '/^effort: / { print $2; exit }' "$source")"
    if [[ "$actual_claude_model" != "$expected_claude_model" || "$actual_claude_effort" != "$expected_claude_effort" ]]; then
        echo "  FAIL  $role expected Claude $expected_claude_model/$expected_claude_effort, got $actual_claude_model/$actual_claude_effort"
        status=1
    fi

    generated="$ROOT/.codex/agents/$role.toml"
    if [[ ! -f "$generated" ]]; then
        echo "  FAIL  missing generated Codex agent: $role"
        status=1
        continue
    fi

    actual_model="$(awk -F'"' '/^model = / { print $2 }' "$generated")"
    actual_effort="$(awk -F'"' '/^model_reasoning_effort = / { print $2 }' "$generated")"
    if [[ "$actual_model" != "$expected_model" || "$actual_effort" != "$expected_effort" ]]; then
        echo "  FAIL  $role expected $expected_model/$expected_effort, got $actual_model/$actual_effort"
        status=1
    fi

    # Validate Pi agent has the correct model and thinking from the router.
    generated_pi="$ROOT/.pi/agents/$role.md"
    if [[ ! -f "$generated_pi" ]]; then
        echo "  FAIL  missing generated Pi agent: $role"
        status=1
        continue
    fi

    read -r expected_pi_model expected_pi_thinking <<< "$(python3 "$MODEL_ROUTER" agent-profile --surface pi --tier "$routing_tier" --format shell)"
    actual_pi_model="$(awk -F': *' '/^model: / { print $2; exit }' "$generated_pi")"
    actual_pi_thinking="$(awk -F': *' '/^thinking: / { print $2; exit }' "$generated_pi")"
    if [[ "$actual_pi_model" != "$expected_pi_model" ]]; then
        echo "  FAIL  $role expected Pi model $expected_pi_model, got $actual_pi_model"
        status=1
    fi
    if [[ "$actual_pi_thinking" != "$expected_pi_thinking" ]]; then
        echo "  FAIL  $role expected Pi thinking $expected_pi_thinking, got $actual_pi_thinking"
        status=1
    fi

    # Ensure no Claude effort field leaked into the Pi agent.
    if head -20 "$generated_pi" | grep -Eq '^effort:'; then
        echo "  FAIL  $role leaked Claude effort field into generated Pi agent"
        status=1
    fi

    # Ensure the Pi model is not a Claude alias.
    if [[ "$actual_pi_model" == *"anthropic"* || "$actual_pi_model" == *"claude"* ]]; then
        echo "  FAIL  $role has a non-Baseten Pi model: $actual_pi_model"
        status=1
    fi
done

# Validate the general-purpose agent (no routing_tier, defaults to Pi critical).
gp_pi="$ROOT/.pi/agents/general-purpose.md"
if [[ -f "$gp_pi" ]]; then
    read -r gp_expected_model gp_expected_thinking <<< "$(python3 "$MODEL_ROUTER" agent-profile --surface pi --tier critical --format shell)"
    gp_actual_model="$(awk -F': *' '/^model: / { print $2; exit }' "$gp_pi")"
    gp_actual_thinking="$(awk -F': *' '/^thinking: / { print $2; exit }' "$gp_pi")"
    if [[ "$gp_actual_model" != "$gp_expected_model" ]]; then
        echo "  FAIL  general-purpose expected Pi model $gp_expected_model, got $gp_actual_model"
        status=1
    fi
    if [[ "$gp_actual_thinking" != "$gp_expected_thinking" ]]; then
        echo "  FAIL  general-purpose expected Pi thinking $gp_expected_thinking, got $gp_actual_thinking"
        status=1
    fi
fi

if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

echo "  OK  Claude/Codex/Pi agent model routing"
