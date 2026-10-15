#!/usr/bin/env python3
"""Validate transcript-bound evidence from real `/do` application runs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


EVAL_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVAL_DIR.parent
SKILLS_DIR = SKILL_DIR.parent
DEFINITIONS = EVAL_DIR / "evals.json"
REPORT = EVAL_DIR / "behavioral-report.json"
WORKSPACE_SKILL = SKILLS_DIR / "workspace" / "SKILL.md"
SESSION_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27}$")
EXPECTED_SCENARIO_IDS = {
    "fast-approved-fix",
    "standard-evidence-gap",
    "deep-independent-work",
    "review-rejection-cap",
    "existing-pr-followup",
    "bounded-waiting",
    "bounded-full-artifacts",
    "workspace-handoff",
    "branch-only-default",
    "bare-resume-discovery",
    "advisory-token-budget",
}


def skill_digest() -> str:
    digest = hashlib.sha256()
    paths = [
        SKILL_DIR / "SKILL.md",
        WORKSPACE_SKILL,
        *sorted((SKILL_DIR / "references").glob("*.md")),
    ]
    for path in paths:
        digest.update(path.relative_to(SKILLS_DIR).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def definitions_digest() -> str:
    return hashlib.sha256(DEFINITIONS.read_bytes()).hexdigest()


def scenario_digest(scenario: dict[str, Any]) -> str:
    encoded = json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def required_reads(scenario: dict[str, Any]) -> list[str]:
    reads = [
        "productivity/skills/do/SKILL.md",
        "productivity/skills/do/references/artifacts.md",
    ]
    if scenario["id"] == "workspace-handoff":
        reads.append("productivity/skills/workspace/SKILL.md")
    return reads


def evaluation_prompt(scenario: dict[str, Any]) -> str:
    fields = [assertion["field"] for assertion in scenario["assertions"]]
    reads = "\n".join(f"- {path}" for path in required_reads(scenario))
    observed_shape = {field: "<derive from the skills>" for field in fields}
    evidence = {
        "skill_digest": skill_digest(),
        "scenario_digest": scenario_digest(scenario),
    }
    return f"""EVAL_SCENARIO_ID={scenario['id']}

Apply the current skills to this scenario as a read-only application test.

Read these files completely:
{reads}

Do not inspect evaluation definitions, reports, or previous evaluation evidence. Do not edit files,
run implementation commands, or spawn agents. Derive every value from the skill instructions.

Scenario:
{scenario['prompt']}

Return exactly one JSON object and no markdown. Copy the evidence values exactly:
{json.dumps({'id': scenario['id'], 'evidence': evidence, 'output': '<concise routing outcome>', 'observed': observed_shape}, indent=2)}

Use the listed observed keys exactly once. Replace every placeholder with a JSON boolean, number,
string, or array justified by the skills."""


def lookup(data: dict[str, Any], dotted: str) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise AssertionError(f"missing observed field: {dotted}")
        value = value[part]
    return value


def assert_observation(observed: dict[str, Any], assertion: dict[str, Any]) -> None:
    field = assertion["field"]
    actual = lookup(observed, field)
    expected = assertion["value"]
    operation = assertion["op"]
    if operation == "eq" and actual != expected:
        raise AssertionError(f"{field}: expected {expected!r}, got {actual!r}")
    if operation == "truthy" and not actual:
        raise AssertionError(f"{field}: expected a truthy value, got {actual!r}")
    if operation == "len_eq" and (not isinstance(actual, list) or len(actual) != expected):
        raise AssertionError(f"{field}: expected length {expected!r}, got {actual!r}")
    if operation == "lte" and not actual <= expected:
        raise AssertionError(f"{field}: expected <= {expected!r}, got {actual!r}")
    if operation == "contains_all":
        if not isinstance(actual, list) or any(item not in actual for item in expected):
            raise AssertionError(f"{field}: expected all of {expected!r}, got {actual!r}")
    if operation == "map_eq" and actual != expected:
        # Models sometimes serialize a visible Markdown table as an ordered list
        # instead of an object. Accept only the exact key/value rendering of the
        # expected map; the assertion remains strict about content.
        normalized: dict[str, int] = {}
        if isinstance(actual, list):
            for item in actual:
                if not isinstance(item, str) or ":" not in item:
                    normalized = {}
                    break
                key, value = item.rsplit(":", 1)
                match = re.match(r"^\s*(\d+)\b", value)
                if not match or key in normalized:
                    normalized = {}
                    break
                normalized[key] = int(match.group(1))
        if normalized != expected:
            raise AssertionError(f"{field}: expected mapping {expected!r}, got {actual!r}")


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in all_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in all_strings(item)]
    return []


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def submitted_eval_prompts(records: list[dict[str, Any]]) -> list[str]:
    prompts = []
    for item in records:
        payload = item.get("payload", {})
        if (
            item.get("type") != "response_item"
            or payload.get("type") != "message"
            or payload.get("role") != "user"
        ):
            continue
        for content in payload.get("content", []):
            text = content.get("text", "") if isinstance(content, dict) else ""
            if "EVAL_SCENARIO_ID=" in text:
                prompts.append(text)
    return prompts


def transcript_bytes(result: dict[str, Any]) -> bytes:
    expected_name = f"transcripts/{result['id']}.jsonl.gz"
    if result.get("transcript_file") != expected_name:
        raise AssertionError(f"{result['id']}: transcript path must be {expected_name}")
    path = (EVAL_DIR / expected_name).resolve()
    transcript_root = (EVAL_DIR / "transcripts").resolve()
    if path.parent != transcript_root or not path.is_file():
        raise AssertionError(f"{result['id']}: bundled rollout transcript is missing")
    try:
        return gzip.decompress(path.read_bytes())
    except (OSError, EOFError) as error:
        raise AssertionError(f"{result['id']}: invalid bundled rollout transcript: {error}") from error


def verify_rollout(result: dict[str, Any], scenario: dict[str, Any]) -> None:
    raw = transcript_bytes(result)
    if hashlib.sha256(raw).hexdigest() != result.get("transcript_sha256"):
        raise AssertionError(f"{result['id']}: rollout transcript hash mismatch")

    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not records:
        raise AssertionError(f"{result['id']}: rollout transcript is empty")
    meta = records[0].get("payload", {})
    if meta.get("source") != "exec" or meta.get("originator") != "codex_exec":
        raise AssertionError(f"{result['id']}: evidence must come from a persisted codex exec session")
    if result.get("execution_mode") != "codex-exec":
        raise AssertionError(f"{result['id']}: report execution mode mismatch")

    expected_prompt = evaluation_prompt(scenario)
    submitted = submitted_eval_prompts(records)
    if submitted not in ([expected_prompt], [expected_prompt + "\n"]):
        raise AssertionError(f"{result['id']}: transcript does not contain the exact answer-hidden prompt")
    if result.get("prompt_sha256") != hashlib.sha256(expected_prompt.encode()).hexdigest():
        raise AssertionError(f"{result['id']}: answer-hidden prompt hash mismatch")

    token_records = [
        item["payload"]["info"]["total_token_usage"]["total_tokens"]
        for item in records
        if item.get("type") == "event_msg"
        and item.get("payload", {}).get("type") == "token_count"
        and item.get("payload", {}).get("info")
    ]
    if not token_records or token_records[-1] != result.get("total_tokens"):
        raise AssertionError(f"{result['id']}: runtime token evidence mismatch")

    duration_ms = round(
        (parse_timestamp(records[-1]["timestamp"]) - parse_timestamp(records[0]["timestamp"])).total_seconds()
        * 1000
    )
    if duration_ms != result.get("duration_ms"):
        raise AssertionError(f"{result['id']}: runtime duration evidence mismatch")

    final_objects: list[dict[str, Any]] = []
    for item in records:
        if item.get("type") != "event_msg" or item.get("payload", {}).get("type") != "agent_message":
            continue
        message = item["payload"].get("message", "")
        try:
            parsed = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict) and parsed.get("id") == result["id"]:
            final_objects.append(parsed)
    if not final_objects:
        raise AssertionError(f"{result['id']}: no structured final output in transcript")
    final = final_objects[-1]
    expected_evidence = {
        "skill_digest": skill_digest(),
        "scenario_digest": scenario_digest(scenario),
    }
    if final.get("evidence") != expected_evidence or result.get("evidence") != expected_evidence:
        raise AssertionError(f"{result['id']}: transcript is not bound to current digest evidence")
    if final.get("output") != result.get("output"):
        raise AssertionError(f"{result['id']}: report output differs from transcript final output")
    if final.get("observed") != result.get("observed"):
        raise AssertionError(f"{result['id']}: report observations differ from transcript final output")

    tool_text = "\n".join(
        text
        for item in records
        if item.get("type") == "response_item"
        and item.get("payload", {}).get("type") in {"function_call", "custom_tool_call"}
        for text in all_strings(item.get("payload", {}))
    )
    for required in required_reads(scenario):
        if required not in tool_text:
            raise AssertionError(f"{result['id']}: tool trace does not show required read: {required}")
    if "productivity/skills/do/evals" in tool_text:
        raise AssertionError(f"{result['id']}: evaluator read answer-bearing evaluation artifacts")

    spawn_calls = sum(
        1
        for item in records
        if item.get("type") == "response_item"
        and item.get("payload", {}).get("type") == "function_call"
        and item.get("payload", {}).get("name") == "spawn_agent"
    )
    if spawn_calls != 0 or result.get("eval_spawn_calls") != 0:
        raise AssertionError(f"{result['id']}: eval agent must not delegate")


def validate() -> None:
    definitions = json.loads(DEFINITIONS.read_text())
    report = json.loads(REPORT.read_text())

    if definitions.get("schema_version") != 3 or report.get("schema_version") != 3:
        raise AssertionError("expected behavioral eval schema version 3")
    scenarios = definitions.get("scenarios", [])
    scenario_ids = {item["id"] for item in scenarios}
    if scenario_ids != EXPECTED_SCENARIO_IDS or len(scenarios) != len(EXPECTED_SCENARIO_IDS):
        raise AssertionError("behavioral scenario set is incomplete or duplicated")
    if report.get("skill_digest") != skill_digest():
        raise AssertionError("behavioral report is stale for the current skill sources")
    if report.get("definitions_digest") != definitions_digest():
        raise AssertionError("behavioral report is stale for the current scenario definitions")

    results = {item["id"]: item for item in report.get("results", [])}
    if set(results) != scenario_ids or len(report.get("results", [])) != len(scenarios):
        raise AssertionError("behavioral report must contain every scenario exactly once")
    session_ids = [item.get("session_id") for item in results.values()]
    if len(session_ids) != len(set(session_ids)):
        raise AssertionError("every behavioral scenario requires its own Codex session")

    for scenario in scenarios:
        result = results[scenario["id"]]
        if result.get("scenario_digest") != scenario_digest(scenario):
            raise AssertionError(f"{scenario['id']}: transcript is stale for this scenario definition")
        if not SESSION_ID.match(result.get("session_id", "")):
            raise AssertionError(f"{scenario['id']}: missing real Codex session id")
        if result.get("duration_ms", 0) <= 0 or result.get("total_tokens", 0) <= 0:
            raise AssertionError(f"{scenario['id']}: missing runtime timing/token evidence")
        output = result.get("output", "")
        if hashlib.sha256(output.encode()).hexdigest() != result.get("output_sha256"):
            raise AssertionError(f"{scenario['id']}: output evidence hash mismatch")
        observed = result.get("observed", {})
        expected_fields = {assertion["field"] for assertion in scenario["assertions"]}
        if set(observed) != expected_fields:
            raise AssertionError(f"{scenario['id']}: observed fields differ from the scenario contract")
        for assertion in scenario["assertions"]:
            assert_observation(observed, assertion)
        verify_rollout(result, scenario)

    baseline = report.get("baseline", {})
    if baseline.get("root_session_id") != "019f89ff-7e93-7782-b695-34e59b081285":
        raise AssertionError("expected the audited pathological root as RED evidence")
    if baseline.get("total_tokens", 0) < 700_000_000:
        raise AssertionError("baseline metrics do not match the final audited lower bound")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-prompt", metavar="SCENARIO_ID")
    args = parser.parse_args()
    if args.print_prompt:
        definitions = json.loads(DEFINITIONS.read_text())
        scenarios = {item["id"]: item for item in definitions.get("scenarios", [])}
        if args.print_prompt not in scenarios:
            parser.error(f"unknown scenario: {args.print_prompt}")
        print(evaluation_prompt(scenarios[args.print_prompt]))
        return 0

    validate()
    print(f"All /do behavioral evidence checks passed ({len(EXPECTED_SCENARIO_IDS)} bundled transcripts verified).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
