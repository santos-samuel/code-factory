#!/usr/bin/env python3
"""Summarize a Codex root session and its descendants without replaying messages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


TOKEN_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
WAIT_TOOLS = {"wait", "wait_agent", "write_stdin"}
SPAWN_TOOLS = {"spawn_agent"}
NOISY_USER_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
    "<recommended_plugins>",
    "<permissions instructions>",
    "<collaboration_mode>",
)
SECRET_PATTERN = re.compile(
    r"(?i)\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,}\b"
)
URL_PATTERN = re.compile(r"https?://\S+")
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
MAX_PREVIEW_CHARS = 80
MAX_PREVIEW_WORDS = 12
MAX_ROOTS = 50
MAX_TOP_ROWS = 10


@dataclass
class Session:
    path: Path
    id: str = ""
    root_id: str = ""
    parent_id: str | None = None
    cwd: str = ""
    role: str = "root"
    agent_path: str = "/root"
    started_at: str = ""
    ended_at: str = ""
    preview: str = ""
    tool_calls: int = 0
    waits: int = 0
    spawns: int = 0
    bzl_calls: int = 0
    malformed_records: int = 0
    duplicate_files: int = 0
    has_token_record: bool = False
    tokens: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in TOKEN_KEYS}
    )

    @property
    def duration_seconds(self) -> float:
        start = parse_time(self.started_at)
        end = parse_time(self.ended_at)
        return max(0.0, (end - start).total_seconds()) if start and end else 0.0


def parse_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def text_content(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    return " ".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type") == "input_text"
    ).strip()


def useful_preview(text: str) -> bool:
    return bool(text) and not text.startswith(NOISY_USER_PREFIXES)


def sanitize_preview(text: str) -> str:
    """Return a bounded, secret-scrubbed fragment rather than a complete prompt."""
    value = re.sub(r"<[^>]{1,200}>", "<tag>", text)
    value = SECRET_PATTERN.sub("<secret>", value)
    value = URL_PATTERN.sub("<url>", value)
    value = EMAIL_PATTERN.sub("<email>", value)
    words = value.split()[:MAX_PREVIEW_WORDS]
    return " ".join(words)[:MAX_PREVIEW_CHARS]


def scan(path: Path) -> Session | None:
    session = Session(path=path)
    latest_tokens: dict[str, int] | None = None

    try:
        lines = path.open(encoding="utf-8")
    except OSError:
        return None

    with lines:
        for line in lines:
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                session.malformed_records += 1
                continue

            timestamp = record.get("timestamp", "")
            if timestamp:
                session.started_at = session.started_at or timestamp
                session.ended_at = timestamp

            kind = record.get("type")
            payload = record.get("payload") or {}

            if kind == "session_meta":
                session.id = payload.get("id") or payload.get("session_id") or session.id
                session.root_id = payload.get("session_id") or session.id
                session.parent_id = payload.get("parent_thread_id")
                session.cwd = payload.get("cwd", session.cwd)
                session.role = payload.get("agent_role") or session.role
                session.agent_path = payload.get("agent_path") or session.agent_path
                session.started_at = session.started_at or payload.get("timestamp", "")
                continue

            if kind == "response_item":
                if payload.get("type") == "function_call":
                    name = payload.get("name", "")
                    session.tool_calls += 1
                    session.waits += int(name in WAIT_TOOLS)
                    session.spawns += int(name in SPAWN_TOOLS)
                    if name in {"exec_command", "write_stdin"}:
                        arguments = payload.get("arguments", "")
                        if isinstance(arguments, dict):
                            arguments = json.dumps(arguments)
                        session.bzl_calls += int(
                            bool(re.search(r"(?<![\w-])bzl\s", arguments))
                        )
                elif payload.get("type") == "custom_tool_call":
                    source = payload.get("input", "")
                    nested_names = re.findall(r"tools\.([A-Za-z_][A-Za-z0-9_]*)", source)
                    names = nested_names or [payload.get("name", "custom_tool")]
                    session.tool_calls += 1
                    session.waits += sum(name in WAIT_TOOLS for name in names)
                    session.spawns += sum(name in SPAWN_TOOLS for name in names)
                    session.bzl_calls += int(
                        bool(re.search(r"(?<![\w-])bzl\s", source))
                    )
                elif (
                    not session.preview
                    and payload.get("type") == "message"
                    and payload.get("role") == "user"
                ):
                    candidate = text_content(payload.get("content"))
                    if useful_preview(candidate):
                        session.preview = sanitize_preview(candidate)
                continue

            if kind == "event_msg" and payload.get("type") == "token_count":
                usage = ((payload.get("info") or {}).get("total_token_usage") or {})
                latest_tokens = {
                    key: int(usage.get(key, 0) or 0) for key in TOKEN_KEYS
                }

    if not session.id:
        session.id = path.stem.rsplit("-", 5)[-1]
        session.root_id = session.id
    if latest_tokens is not None:
        session.tokens = latest_tokens
        session.has_token_record = True
    return session


def deduplicate_sessions(sessions: list[Session]) -> list[Session]:
    """Keep one canonical cumulative record per thread identity."""
    unique: dict[str, Session] = {}
    for session in sessions:
        current = unique.get(session.id)
        if current is None:
            unique[session.id] = session
            continue
        candidates = (current, session)
        chosen = max(
            candidates,
            key=lambda item: (
                item.has_token_record,
                item.tokens["total_tokens"],
                item.ended_at,
                str(item.path),
            ),
        )
        chosen.duplicate_files = (
            current.duplicate_files + session.duplicate_files + 1
        )
        unique[session.id] = chosen
    return list(unique.values())


def load_sessions(directory: Path, days: int | None) -> list[Session]:
    cutoff = (
        dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
        if days is not None
        else None
    )
    sessions: list[Session] = []
    try:
        paths = directory.rglob("*.jsonl")
    except OSError:
        return sessions
    for path in paths:
        if cutoff:
            try:
                modified = dt.datetime.fromtimestamp(
                    path.stat().st_mtime, dt.timezone.utc
                )
            except OSError:
                continue
            if modified < cutoff:
                continue
        session = scan(path)
        if session:
            sessions.append(session)
    return deduplicate_sessions(sessions)


def descendants(sessions: list[Session], root_id: str) -> list[Session]:
    selected = {
        session.id
        for session in sessions
        if session.id == root_id or session.root_id == root_id
    }
    changed = True
    while changed:
        changed = False
        for session in sessions:
            if session.parent_id in selected and session.id not in selected:
                selected.add(session.id)
                changed = True
    return [session for session in sessions if session.id in selected]


def aggregate(sessions: list[Session], root_id: str) -> dict[str, Any]:
    ordered = sorted(sessions, key=lambda item: item.started_at)
    totals = {key: sum(item.tokens[key] for item in sessions) for key in TOKEN_KEYS}
    incomplete = any(
        item.malformed_records or not item.has_token_record for item in sessions
    )
    incomplete_time = any(
        not parse_time(item.started_at) or not parse_time(item.ended_at)
        for item in sessions
    )
    first = parse_time(ordered[0].started_at) if ordered else None
    last = parse_time(max((item.ended_at for item in sessions), default=""))
    wall_seconds = max(0.0, (last - first).total_seconds()) if first and last else 0.0
    top_tokens = sorted(
        sessions,
        key=lambda item: item.tokens["input_tokens"] - item.tokens["cached_input_tokens"],
        reverse=True,
    )[:MAX_TOP_ROWS]
    top_waits = sorted(
        sessions, key=lambda item: item.waits, reverse=True
    )[:MAX_TOP_ROWS]
    return {
        "root_id": root_id,
        "sessions": len(sessions),
        "started_at": ordered[0].started_at if ordered else None,
        "ended_at": max((item.ended_at for item in sessions), default=None),
        "wall_seconds": round(wall_seconds, 3),
        "summed_session_seconds": round(sum(item.duration_seconds for item in sessions), 3),
        "observed_tool_records": sum(item.tool_calls for item in sessions),
        "observed_wait_records": sum(item.waits for item in sessions),
        "observed_spawn_records": sum(item.spawns for item in sessions),
        "shell_records_mentioning_bzl": sum(item.bzl_calls for item in sessions),
        "malformed_records": sum(item.malformed_records for item in sessions),
        "duplicate_thread_files": sum(item.duplicate_files for item in sessions),
        "threads_without_token_record": sum(
            not item.has_token_record for item in sessions
        ),
        "cost_usd": None,
        "cost_source": "unknown",
        "tokens": totals,
        "metric_provenance": {
            "sessions": "derived",
            "tokens": "lower_bound" if incomplete else "derived",
            "uncached_input_tokens": "lower_bound" if incomplete else "derived",
            "wall_seconds": "lower_bound" if incomplete_time else "derived",
            "summed_session_seconds": (
                "lower_bound" if incomplete_time else "derived"
            ),
            "observed_tool_records": "lower_bound",
            "observed_wait_records": "lower_bound",
            "observed_spawn_records": "lower_bound",
            "shell_records_mentioning_bzl": "lower_bound",
            "malformed_records": "measured",
            "duplicate_thread_files": "measured",
            "threads_without_token_record": "measured",
        },
        "top_uncached_input": [session_row(item) for item in top_tokens],
        "top_waits": [session_row(item) for item in top_waits if item.waits],
    }


def session_row(session: Session) -> dict[str, Any]:
    return {
        "id": session.id,
        "path": session.agent_path,
        "role": session.role,
        "uncached_input_tokens": (
            session.tokens["input_tokens"] - session.tokens["cached_input_tokens"]
        ),
        "total_tokens": session.tokens["total_tokens"],
        "observed_tool_records": session.tool_calls,
        "observed_wait_records": session.waits,
        "duration_seconds": round(session.duration_seconds, 3),
        "metric_provenance": {
            "total_tokens": (
                "measured" if session.has_token_record else "lower_bound"
            ),
            "uncached_input_tokens": (
                "derived" if session.has_token_record else "lower_bound"
            ),
            "observed_tool_records": "lower_bound",
            "observed_wait_records": "lower_bound",
            "duration_seconds": (
                "derived"
                if parse_time(session.started_at) and parse_time(session.ended_at)
                else "lower_bound"
            ),
        },
    }


def print_roots(sessions: list[Session], limit: int) -> None:
    roots = [
        item
        for item in sessions
        if not item.parent_id or item.id == item.root_id
    ]
    for item in sorted(
        roots, key=lambda entry: entry.started_at, reverse=True
    )[:limit]:
        print(
            f"{item.started_at}\t{item.id}\t{item.cwd}\t"
            f"{item.preview or '(no user prompt found)'}"
        )


def print_report(report: dict[str, Any]) -> None:
    tokens = report["tokens"]
    print(f"# Codex Session Audit: {report['root_id']}")
    print()
    print(
        f"Sessions: {report['sessions']} | Observed spawn records: "
        f"{report['observed_spawn_records']} | Observed tool records: "
        f"{report['observed_tool_records']} | Observed wait records: "
        f"{report['observed_wait_records']} | Shell records mentioning bzl: "
        f"{report['shell_records_mentioning_bzl']}"
    )
    print(
        f"Wall span: {report['wall_seconds']:.0f}s | "
        f"Summed session time: {report['summed_session_seconds']:.0f}s"
    )
    print(
        "Tokens: "
        f"{tokens['total_tokens']:,} total; "
        f"{tokens['input_tokens'] - tokens['cached_input_tokens']:,} uncached input; "
        f"{tokens['cached_input_tokens']:,} cached input; "
        f"{tokens['output_tokens']:,} output; "
        f"{tokens['reasoning_output_tokens']:,} reasoning"
    )
    print(f"Cost: unknown ({report['cost_source']})")
    provenance = report["metric_provenance"]
    print(
        "Provenance: "
        f"tokens={provenance['tokens']}; durations={provenance['wall_seconds']}; "
        "observed activity=lower_bound"
    )
    if report["malformed_records"]:
        print(
            f"Warning: skipped {report['malformed_records']} malformed records; "
            "totals are lower bounds."
        )
    print()
    print("## Top uncached-input sessions")
    for row in report["top_uncached_input"]:
        print(
            f"- {row['path']} ({row['role']}): "
            f"{row['uncached_input_tokens']:,} uncached, "
            f"{row['total_tokens']:,} total, "
            f"{row['observed_wait_records']} observed wait records"
        )
    if report["top_waits"]:
        print()
        print("## Top wait-heavy sessions")
        for row in report["top_waits"]:
            print(
                f"- {row['path']} ({row['role']}): "
                f"{row['observed_wait_records']} observed wait records"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
    )
    parser.add_argument("--root", help="Root Codex thread/session ID to summarize")
    parser.add_argument("--list-roots", action="store_true")
    parser.add_argument("--days", type=int, help="Only inspect files modified this recently")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help=f"Maximum roots to list (1-{MAX_ROOTS}; default: 20)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    sessions = load_sessions(args.sessions_dir.expanduser(), args.days)
    if args.list_roots:
        print_roots(sessions, max(1, min(args.limit, MAX_ROOTS)))
        return 0
    if not args.root:
        parser.error("provide --root or --list-roots")

    selected = descendants(sessions, args.root)
    if not selected:
        parser.error(f"root session not found: {args.root}")
    report = aggregate(selected, args.root)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
