#!/usr/bin/env python3
"""Fast structural assertions for the persisted /do regression scenarios."""

from __future__ import annotations

import json
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVAL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
RESOURCE = SKILL_DIR / "references" / "resource-efficiency.md"
PHASE = SKILL_DIR / "references" / "phase-flow.md"
DISPATCH = SKILL_DIR / "references" / "dispatch-templates.md"
SCHEMA = SKILL_DIR / "references" / "state-file-schema.md"


def require(text: str, *fragments: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise AssertionError(f"missing required fragments: {missing}")


def main() -> int:
    definitions = json.loads((EVAL_DIR / "evals.json").read_text())
    if len(definitions.get("evals", [])) != 7:
        raise AssertionError("expected seven persisted /do scenarios")
    green = json.loads((EVAL_DIR / "green-report.json").read_text())
    results = green.get("scenario_results", [])
    if len(results) != 7 or any(item.get("status") != "pass" for item in results):
        raise AssertionError("expected seven passing GREEN scenario results")

    skill = SKILL.read_text()
    resource = RESOURCE.read_text()
    phase = PHASE.read_text()
    dispatch = DISPATCH.read_text()
    schema = SCHEMA.read_text()

    if len(skill.splitlines()) >= 500:
        raise AssertionError("primary /do SKILL.md must remain under 500 lines")
    require(skill, "Prepared-Context Reuse", "report reuse in one line and do not ask again")
    require(resource, "targeted verification", "Low | 0", "Medium | 2 maximum")
    require(resource, "two consecutive status checks", "Confirm the original worker stopped")
    require(
        resource,
        "measured",
        "derived",
        "lower_bound",
        "reasoning effort",
        'cost_source: "unknown"',
    )
    require(phase, "HEAD == reviewed_head")
    require(skill, "one group orchestrator owns")
    require(dispatch, "Dispatched once per ready milestone group", "single message")
    require(schema, "created with FEATURE.md", 'source: "legacy_resume"')
    require(schema, "`metric_provenance`", "`BUDGET_WARNING`", "`BUDGET_EXHAUSTED`")
    print("All /do persisted evaluation assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
