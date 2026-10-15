#!/usr/bin/env bash

set -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
    echo "  SKIP  codex CLI not found"
    exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

make_temp_dir() {
    mktemp -d 2>/dev/null || mktemp -d -p /private/tmp
}

TMP_DIR="$(make_temp_dir)"
trap 'rm -rf "$TMP_DIR"' EXIT

cat > "$TMP_DIR/config.toml" <<'EOF'
model = "gpt-5.6-sol"
approval_policy = "on-request"
sandbox_mode = "read-only"
default_permissions = "stale-profile"

[sandbox_workspace_write]
network_access = false

[permissions.datadog-dev]
description = "stale profile that should be replaced"

[permissions.datadog-dev.filesystem]
"/tmp/stale-codex-permissions" = "write"

[permissions.code-factory]
description = "stale profile that should be removed"

[permissions.code-factory.filesystem]
"/tmp/stale-code-factory-permissions" = "write"

[permissions.read-all-write-selected]
description = "legacy managed profile that should be removed"

[permissions.read-all-write-selected.filesystem]
"/tmp/legacy-codex-permissions" = "write"

[projects."/tmp/code-factory-preserve"]
trust_level = "trusted"

[mcp_servers.unrelated]
command = "true"
EOF

CODEX_HOME="$TMP_DIR" "$ROOT/install-codex-mcp.sh" >/dev/null

python3 - "$TMP_DIR/config.toml" "$ROOT/mcp.json" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text()

required = [
    "# --- Codex Settings (managed by code-factory from codex/config.toml) ---",
    "# --- End Codex Settings ---",
    "# --- MCP Servers (managed by code-factory from mcp.json) ---",
    "# --- End MCP Servers ---",
    'sandbox_mode = "danger-full-access"',
    'allow_login_shell = true',
    'approvals_reviewer = "auto_review"',
    'mcp_oauth_credentials_store = "file"',
    "[approval_policy.granular]",
    "sandbox_approval = false",
    "rules = true",
    "mcp_elicitations = true",
    "request_permissions = true",
    "skill_approval = true",
    "[shell_environment_policy]",
    'inherit = "all"',
    'set = { BROWSER = "/usr/bin/open", TMPDIR = "/tmp", TMP = "/tmp", TEMP = "/tmp" }',
    "[mcp_servers.atlassian]",
    'default_tools_approval_mode = "auto"',
    "[mcp_servers.unrelated]",
    '[projects."/tmp/code-factory-preserve"]',
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "xhigh"',
    'plan_mode_reasoning_effort = "xhigh"',
]

missing = [item for item in required if item not in content]
if missing:
    raise SystemExit(f"missing expected Codex config entries: {missing}")

singletons = [
    "sandbox_mode",
    "mcp_oauth_callback_port",
    "mcp_oauth_callback_url",
    "mcp_oauth_credentials_store",
]
for key in singletons:
    count = len(re.findall(rf"(?m)^{re.escape(key)}\s*=", content))
    if count != 1:
        raise SystemExit(f"expected exactly one {key}, found {count}")

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

data = tomllib.loads(content)
if data.get("sandbox_mode") != "danger-full-access":
    raise SystemExit("sandbox_mode must be danger-full-access")

if data.get("approvals_reviewer") != "auto_review":
    raise SystemExit("approvals_reviewer must be auto_review")

if data.get("mcp_oauth_credentials_store") != "file":
    raise SystemExit("mcp_oauth_credentials_store must be file (not the OS keychain, so mcp-auth can own credentials)")

granular_approvals = data.get("approval_policy", {}).get("granular", {})
expected_granular_approvals = {
    "sandbox_approval": False,
    "rules": True,
    "mcp_elicitations": True,
    "request_permissions": True,
    "skill_approval": True,
}
for key, expected in expected_granular_approvals.items():
    actual = granular_approvals.get(key)
    if actual is not expected:
        raise SystemExit(f"approval_policy.granular.{key}: expected {expected}, got {actual}")

shell_environment_policy = data.get("shell_environment_policy", {})
if "sandbox_mode" in shell_environment_policy:
    raise SystemExit("sandbox_mode must not be nested under shell_environment_policy")

environment_set = shell_environment_policy.get("set", {})
expected_environment = {
    "BROWSER": "/usr/bin/open",
    "TMPDIR": "/tmp",
    "TMP": "/tmp",
    "TEMP": "/tmp",
}
for key, expected in expected_environment.items():
    actual = environment_set.get(key)
    if actual != expected:
        raise SystemExit(f"shell_environment_policy.set.{key}: expected {expected}, got {actual}")

if re.search(r"(?m)^\[sandbox_workspace_write\]\s*$", content):
    raise SystemExit("legacy [sandbox_workspace_write] table should be removed")

permissions = data.get("permissions", {})
if "read-all-write-selected" in permissions:
    raise SystemExit("legacy permissions.read-all-write-selected table should be removed")
if "datadog-dev" in permissions:
    raise SystemExit("legacy permissions.datadog-dev table should be removed")
if "code-factory" in permissions:
    raise SystemExit("permissions.code-factory table should be removed (no longer managed)")

mcp_servers = data.get("mcp_servers", {})
for name in [
    "atlassian",
    "slack",
    "slack-sandbox",
    "datadog-google-workspace",
    "datadog-gmail",
    "datadog-google-calendar",
]:
    server = mcp_servers.get(name, {})
    if server.get("default_tools_approval_mode") != "auto":
        raise SystemExit(f"{name}: default_tools_approval_mode must be auto")

if "default_tools_approval_mode" in mcp_servers.get("unrelated", {}):
    raise SystemExit("unrelated preserved MCP server should not receive managed approval settings")

# Parity: the managed Codex MCP server set must equal the mcp.json source set
# so Codex, Claude, and Pi cannot diverge. The fixture preserves an `unrelated`
# server that is not from mcp.json; it must be the only extra entry.
source = json.loads(Path(sys.argv[2]).read_text())
source_servers = set(source.get("mcpServers", {}).keys())
codex_servers = set(data.get("mcp_servers", {}).keys())
extra = codex_servers - source_servers
if extra != {"unrelated"}:
    raise SystemExit(f"Codex MCP set diverges from mcp.json (extra: {extra})")
missing = source_servers - codex_servers
if missing:
    raise SystemExit(f"Codex MCP set missing mcp.json servers: {missing}")
PY

DOCTOR_JSON="$TMP_DIR/doctor.json"
CODEX_HOME="$TMP_DIR" codex --strict-config doctor --json >"$DOCTOR_JSON" 2>/dev/null || true

python3 - "$DOCTOR_JSON" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
config = data.get("checks", {}).get("config.load", {})
if config.get("status") != "ok":
    raise SystemExit(f"Codex config.load check failed: {config}")
PY

echo "  OK  Codex managed config"
