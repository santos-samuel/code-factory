#!/usr/bin/env python3
"""Collect fresh Codex eval sessions into the behavioral evidence report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVAL_DIR = Path(__file__).resolve().parent
DEFINITIONS = EVAL_DIR / "evals.json"
REPORT = EVAL_DIR / "behavioral-report.json"


def load_checker() -> Any:
    spec = importlib.util.spec_from_file_location("do_eval_checker", EVAL_DIR / "check-evals.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load check-evals.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_rollout(session_id: str) -> Path:
    for path in (Path.home() / ".codex" / "sessions").rglob(f"*{session_id}*.jsonl"):
        try:
            first = json.loads(path.open().readline())
        except (OSError, json.JSONDecodeError):
            continue
        if first.get("payload", {}).get("id") == session_id:
            return path
    raise FileNotFoundError(f"no rollout found for session {session_id}")


def final_object(records: list[dict[str, Any]], scenario_id: str) -> dict[str, Any]:
    matches = []
    for item in records:
        if item.get("type") != "event_msg" or item.get("payload", {}).get("type") != "agent_message":
            continue
        try:
            value = json.loads(item["payload"].get("message", ""))
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("id") == scenario_id:
            matches.append(value)
    if not matches:
        raise AssertionError(f"{scenario_id}: no structured final output")
    return matches[-1]


def result_from_rollout(checker: Any, scenario: dict[str, Any], session_id: str) -> dict[str, Any]:
    path = find_rollout(session_id)
    raw = path.read_bytes()
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    meta = records[0]["payload"]
    if meta.get("source") != "exec" or meta.get("originator") != "codex_exec":
        raise AssertionError(f"{scenario['id']}: expected a persisted codex exec rollout")
    final = final_object(records, scenario["id"])
    prompt = checker.evaluation_prompt(scenario)
    if checker.submitted_eval_prompts(records) not in ([prompt], [prompt + "\n"]):
        raise AssertionError(f"{scenario['id']}: rollout does not contain the exact answer-hidden prompt")
    token_records = [
        item["payload"]["info"]["total_token_usage"]["total_tokens"]
        for item in records
        if item.get("type") == "event_msg"
        and item.get("payload", {}).get("type") == "token_count"
        and item.get("payload", {}).get("info")
    ]
    if not token_records:
        raise AssertionError(f"{scenario['id']}: rollout has no runtime token evidence")
    spawn_calls = sum(
        1
        for item in records
        if item.get("type") == "response_item"
        and item.get("payload", {}).get("type") == "function_call"
        and item.get("payload", {}).get("name") == "spawn_agent"
    )
    duration_ms = round(
        (
            checker.parse_timestamp(records[-1]["timestamp"])
            - checker.parse_timestamp(records[0]["timestamp"])
        ).total_seconds()
        * 1000
    )
    output = final["output"]
    return {
        "id": scenario["id"],
        "session_id": meta["id"],
        "execution_mode": "codex-exec",
        "duration_ms": duration_ms,
        "total_tokens": token_records[-1],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "scenario_digest": checker.scenario_digest(scenario),
        "transcript_file": f"transcripts/{scenario['id']}.jsonl.gz",
        "transcript_sha256": hashlib.sha256(raw).hexdigest(),
        "eval_spawn_calls": spawn_calls,
        "evidence": final["evidence"],
        "output": output,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "observed": final["observed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--session",
        action="append",
        required=True,
        metavar="SCENARIO_ID=SESSION_ID",
        help="map one scenario to the fresh persisted codex exec session that evaluated it",
    )
    args = parser.parse_args()
    mappings = dict(value.split("=", 1) for value in args.session)
    definitions = json.loads(DEFINITIONS.read_text())
    scenarios = definitions["scenarios"]
    scenario_ids = {scenario["id"] for scenario in scenarios}
    if set(mappings) != scenario_ids:
        missing = sorted(scenario_ids - set(mappings))
        extra = sorted(set(mappings) - scenario_ids)
        parser.error(f"session mappings differ from scenarios; missing={missing}, extra={extra}")

    checker = load_checker()
    previous = json.loads(REPORT.read_text())
    report = {
        "schema_version": 3,
        "skill_digest": checker.skill_digest(),
        "definitions_digest": checker.definitions_digest(),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "method": "Fresh answer-hidden read-only Codex application sessions with bundled raw rollouts",
        "baseline": previous["baseline"],
        "results": [result_from_rollout(checker, scenario, mappings[scenario["id"]]) for scenario in scenarios],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"  OK  collected {len(report['results'])} fresh behavioral sessions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
