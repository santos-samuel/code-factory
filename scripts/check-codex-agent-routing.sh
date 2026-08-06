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

    generated_pi="$ROOT/.pi/agents/$role.md"
    if [[ -f "$generated_pi" ]] && head -20 "$generated_pi" | grep -Eq '^(model|effort):'; then
        echo "  FAIL  $role leaked Claude model/effort routing into generated Pi agent"
        status=1
    fi

    pi_profile="$(python3 "$MODEL_ROUTER" agent-profile --surface pi --tier "$routing_tier" --format shell)"
    if [[ "$pi_profile" == *"anthropic"* || "$pi_profile" == *"claude"* ]]; then
        echo "  FAIL  $role has a non-OpenAI Pi route: $pi_profile"
        status=1
    fi
done

if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

echo "  OK  Claude/Codex agent model/effort routing"
