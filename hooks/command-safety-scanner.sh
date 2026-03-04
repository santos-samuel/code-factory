#!/bin/bash
# command-safety-scanner.sh — PreToolUse hook that scans the FULL command string
# for dangerous patterns anywhere (pipes, chains, find -exec, xargs, subshells).
#
# Returns permissionDecision: "ask" so the user always makes the judgment call.
# Returns nothing (exit 0) for safe commands — auto-approved.
#
# This complements settings.local.json prefix-based "ask" rules. Those catch
# the obvious case (command starts with "rm -rf"). This catches the non-obvious
# case (command contains "rm -rf" after a pipe, chain, find -exec, etc.).

set -euo pipefail

# Read stdin (JSON from Claude Code runtime)
input=$(cat)

# Extract the command string from tool_input.command
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)

# No command or empty — allow
[[ -z "$cmd" ]] && exit 0

# --- Logging ---
# Append-only log of scanner decisions: ~/.claude/permission-scanner/YYYY-MM-DD.jsonl
# Set SCANNER_NO_LOG=1 to suppress (used by test harness)
# Set SCANNER_LOG_RETENTION_DAYS to override 90-day default rotation
LOG_DIR="$HOME/.claude/permission-scanner"
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).jsonl"

# --- Log rotation ---
# Runs at most once per day (uses a marker file). Deletes .jsonl files older
# than SCANNER_LOG_RETENTION_DAYS (default: 90). Best-effort, never blocks.
RETENTION_DAYS="${SCANNER_LOG_RETENTION_DAYS:-90}"
ROTATION_MARKER="$LOG_DIR/.last-rotation"
if [[ ! -f "$ROTATION_MARKER" ]] || \
   [[ "$(date +%Y-%m-%d)" != "$(cat "$ROTATION_MARKER" 2>/dev/null)" ]]; then
    find "$LOG_DIR" -name "*.jsonl" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true
    printf '%s' "$(date +%Y-%m-%d)" > "$ROTATION_MARKER" 2>/dev/null || true
fi

log_match() {
    [[ "${SCANNER_NO_LOG:-}" == "1" ]] && return 0
    local pattern_name="$1"
    local reason="$2"
    # Best-effort, never block on logging failures
    jq -nc \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg pattern "$pattern_name" \
        --arg reason "$reason" \
        --arg cmd "$cmd" \
        '{timestamp: $ts, pattern: $pattern, reason: $reason, command: ($cmd | .[0:500])}' \
        >> "$LOG_FILE" 2>/dev/null || true
}

# --- Helper: check pattern and emit ask decision on match ---
check_pattern() {
    local pattern="$1"
    local reason="$2"
    local pattern_name="${3:-$pattern}"  # optional short name for logging
    if printf '%s' "$cmd" | grep -qE "$pattern"; then
        log_match "$pattern_name" "$reason"
        jq -n --arg reason "$reason" '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "ask",
                permissionDecisionReason: $reason
            }
        }'
        exit 0
    fi
}

# ============================================================
# SYSTEM COMMANDS — privilege escalation, firmware, services
# ============================================================
check_pattern '\bsudo\b' \
    "Contains 'sudo' — requires elevated privileges" "sudo"

check_pattern '\bdd\s+(if=|of=|bs=|count=|status=|conv=|seek=|skip=)' \
    "Contains 'dd' with disk I/O flags — can overwrite raw disks" "dd-flags"

check_pattern '(^|[|;&])\s*dd\s' \
    "Contains 'dd' at command position — can overwrite raw disks" "dd-cmd"

check_pattern '\bmkfs\b' \
    "Contains 'mkfs' — creates filesystems (destroys existing data)" "mkfs"

check_pattern '\bfdisk\b' \
    "Contains 'fdisk' — modifies disk partition tables" "fdisk"

check_pattern '\bdiskutil\s+erase' \
    "Contains 'diskutil erase' — erases volumes" "diskutil-erase"

check_pattern '\bdiskutil\s+partitionDisk' \
    "Contains 'diskutil partitionDisk' — repartitions disk" "diskutil-partition"

check_pattern '\bshutdown\b' \
    "Contains 'shutdown' — shuts down the system" "shutdown"

check_pattern '\breboot\b' \
    "Contains 'reboot' — reboots the system" "reboot"

check_pattern '\bnvram\b' \
    "Contains 'nvram' — modifies firmware settings" "nvram"

check_pattern '\bcsrutil\b' \
    "Contains 'csrutil' — modifies System Integrity Protection" "csrutil"

check_pattern '\blaunchctl\b' \
    "Contains 'launchctl' — manages system services/daemons" "launchctl"

check_pattern '\bsystemsetup\b' \
    "Contains 'systemsetup' — modifies system configuration" "systemsetup"

check_pattern '\bnetworksetup\b' \
    "Contains 'networksetup' — modifies network configuration" "networksetup"

# ============================================================
# DESTRUCTIVE FILE/PERMISSION OPERATIONS
# ============================================================
check_pattern '\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)' \
    "Contains 'rm -rf' — recursive forced deletion" "rm-rf"

check_pattern '\brm\s+-[a-zA-Z]*r' \
    "Contains 'rm -r' — recursive deletion" "rm-r"

check_pattern '\bchmod\s+-[a-zA-Z]*R' \
    "Contains 'chmod -R' — recursive permission change" "chmod-R"

check_pattern '\bchown\s+-[a-zA-Z]*R' \
    "Contains 'chown -R' — recursive ownership change" "chown-R"

# ============================================================
# SUPPLY CHAIN / REMOTE CODE EXECUTION
# ============================================================
check_pattern '\bcurl\b.*\|\s*(sh|bash)\b' \
    "Contains 'curl | sh/bash' — executes remote code directly" "curl-pipe-sh"

check_pattern '\bwget\b.*\|\s*(sh|bash)\b' \
    "Contains 'wget | sh/bash' — executes remote code directly" "wget-pipe-sh"

# ============================================================
# PACKAGE MANAGEMENT (system-level installs)
# ============================================================
check_pattern '\bbrew\s+install\b' \
    "Contains 'brew install' — installs system packages" "brew-install"

check_pattern '\bnpm\s+install\s+-g\b' \
    "Contains 'npm install -g' — installs global npm packages" "npm-install-g"

# ============================================================
# DESTRUCTIVE GIT OPERATIONS
# ============================================================
check_pattern '\bgit\s+push\s+.*--force' \
    "Contains 'git push --force' — overwrites remote history" "git-push-force"

check_pattern '\bgit\s+push\s+.*-f\b' \
    "Contains 'git push -f' — overwrites remote history" "git-push-f"

check_pattern '\bgit\s+reset\s+--hard' \
    "Contains 'git reset --hard' — discards all uncommitted changes" "git-reset-hard"

check_pattern '\bgit\s+clean\s+.*-f' \
    "Contains 'git clean -f' — permanently deletes untracked files" "git-clean-f"

check_pattern '\bgit\s+branch\s+.*-D' \
    "Contains 'git branch -D' — force-deletes branch without merge check" "git-branch-D"

check_pattern '\bgit\s+checkout\s+--\s' \
    "Contains 'git checkout -- ' — discards uncommitted changes" "git-checkout-discard"

check_pattern '\bgit\s+rebase\b' \
    "Contains 'git rebase' — rewrites commit history" "git-rebase"

check_pattern '\bgit\s+stash\s+drop' \
    "Contains 'git stash drop' — permanently drops stashed changes" "git-stash-drop"

# ============================================================
# macOS DEFAULTS MUTATION
# ============================================================
check_pattern '\bdefaults\s+write' \
    "Contains 'defaults write' — modifies macOS system preferences" "defaults-write"

# ============================================================
# No patterns matched — allow the command
# ============================================================
exit 0
