#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT/settings.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
settings = json.loads(path.read_text())
errors = []

if settings.get("model") != "opus":
    errors.append("main Claude model must be opus")
if settings.get("effortLevel") != "xhigh":
    errors.append("main Claude effortLevel must be xhigh")

for plugin, enabled in settings.get("enabledPlugins", {}).items():
    if enabled and plugin.endswith("-dev"):
        errors.append(f"enabled development plugin must stay in local settings: {plugin}")

required_field = {"github": "repo", "git": "url", "directory": "path"}
for name, entry in settings.get("extraKnownMarketplaces", {}).items():
    if name.endswith("-dev"):
        errors.append(f"development marketplace must stay in local settings: {name}")
    source = entry.get("source", {})
    kind = source.get("source")
    field = required_field.get(kind)
    if field is None:
        errors.append(f"{name}: unsupported marketplace source kind {kind!r}")
        continue
    value = source.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"{name}: {kind} source requires non-empty {field}")
    if kind == "directory" and isinstance(value, str) and "/worktrees/" in value:
        errors.append(f"{name}: committed marketplace cannot point into a temporary worktree")

if errors:
    for error in errors:
        print(f"  FAIL  {error}")
    raise SystemExit(1)

print("  OK  committed Claude marketplace settings")
PY
