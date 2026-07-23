#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

expected_profile() {
    case "$1" in
        implementer|task-critic|red-teamer)
            printf '%s %s\n' "gpt-5.6-sol" "high"
            ;;
        brainstormer|code-quality-reviewer|code-simplifier|consistency-checker|explorer|memory-extractor|orchestrator|planner|refiner|researcher|reviewer|skill-comparator|skill-grader|spec-reviewer|validator)
            printf '%s %s\n' "gpt-5.6-terra" "medium"
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
done

while IFS= read -r role; do
    [[ "$role" == codex-* ]] && continue
    if ! expected_profile "$role" >/dev/null; then
        echo "  FAIL  /do dispatch role has no Codex profile: $role"
        status=1
    fi
done < <(grep -oE 'productivity:[a-z][-a-z0-9]+' "$ROOT/productivity/agents/orchestrator.md" \
    | cut -d: -f2 | sort -u)

if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

echo "  OK  Codex agent model/effort routing"
