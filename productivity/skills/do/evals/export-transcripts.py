#!/usr/bin/env python3
"""Export locally recorded Codex rollouts as deterministic bundled eval evidence."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
REPORT = EVAL_DIR / "behavioral-report.json"


def find_rollout(session_id: str) -> Path:
    for path in (Path.home() / ".codex" / "sessions").rglob(f"*{session_id}*.jsonl"):
        try:
            first = json.loads(path.open().readline())
        except (OSError, json.JSONDecodeError):
            continue
        if first.get("payload", {}).get("id") == session_id:
            return path
    raise FileNotFoundError(f"no local rollout for session {session_id}")


def main() -> int:
    report = json.loads(REPORT.read_text())
    transcript_root = EVAL_DIR / "transcripts"
    transcript_root.mkdir(parents=True, exist_ok=True)
    for result in report.get("results", []):
        raw = find_rollout(result["session_id"]).read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != result.get("transcript_sha256"):
            raise AssertionError(f"{result['id']}: local rollout hash differs from the report")
        expected_name = f"transcripts/{result['id']}.jsonl.gz"
        if result.get("transcript_file") != expected_name:
            raise AssertionError(f"{result['id']}: report transcript path must be {expected_name}")
        destination = EVAL_DIR / expected_name
        destination.write_bytes(gzip.compress(raw, mtime=0))
        print(f"  OK  {destination.relative_to(EVAL_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
