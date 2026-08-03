#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

expected_profile() {
    case "$1" in
        code-simplifier|explorer|implementer|memory-extractor|researcher)
            printf '%s %s\n' "gpt-5.6-luna" "max"
            ;;
        brainstormer|code-quality-reviewer|consistency-checker|planner|red-teamer|refiner|reviewer|skill-comparator|skill-grader|spec-reviewer|task-critic|validator)
            printf '%s %s\n' "gpt-5.6-sol" "xhigh"
            ;;
        *)
            return 1
            ;;
    esac
}

status=0
for source in "$ROOT"/productivity/agents/*.md; do
    role="$(basename "$source" .md)"
    if ! read -r expected_model expected_effort <<< "$(expected_profile "$role")"; then
        echo "  FAIL  unsupported Codex agent role: $role"
        status=1
        continue
    fi

    case "$expected_model" in
        gpt-5.6-luna)
            expected_claude_model="sonnet"
            expected_claude_effort="high"
            ;;
        gpt-5.6-sol)
            expected_claude_model="opus"
            expected_claude_effort="xhigh"
            ;;
    esac

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
done

if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

echo "  OK  Claude/Codex agent model/effort routing"
