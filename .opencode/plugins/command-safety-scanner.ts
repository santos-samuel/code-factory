/**
 * command-safety-scanner — OpenCode plugin equivalent of the Claude Code PreToolUse:Bash hook.
 *
 * Scans the FULL command string for dangerous patterns anywhere (pipes, chains,
 * find -exec, xargs, subshells). Throws an error so the command is blocked and
 * the agent sees the reason.
 *
 * This complements opencode.jsonc prefix-based permission rules. Those catch the
 * obvious case (command starts with "rm -rf"). This catches the non-obvious case
 * (command contains "rm -rf" after a pipe, chain, find -exec, etc.).
 *
 * Mirrors the logic in hooks/command-safety-scanner.sh for Claude Code.
 */
import type { Plugin } from "@opencode-ai/plugin"

interface Pattern {
  regex: RegExp
  reason: string
  name: string
}

// ============================================================
// SYSTEM COMMANDS — privilege escalation, firmware, services
// ============================================================
const SYSTEM_PATTERNS: Pattern[] = [
  {
    regex: /\bsudo\b/,
    reason: "Contains 'sudo' — requires elevated privileges",
    name: "sudo",
  },
  {
    regex: /\bdd\s+(if=|of=|bs=|count=|status=|conv=|seek=|skip=)/,
    reason: "Contains 'dd' with disk I/O flags — can overwrite raw disks",
    name: "dd-flags",
  },
  {
    regex: /(^|[|;&])\s*dd\s/,
    reason: "Contains 'dd' at command position — can overwrite raw disks",
    name: "dd-cmd",
  },
  {
    regex: /\bmkfs\b/,
    reason: "Contains 'mkfs' — creates filesystems (destroys existing data)",
    name: "mkfs",
  },
  {
    regex: /\bfdisk\b/,
    reason: "Contains 'fdisk' — modifies disk partition tables",
    name: "fdisk",
  },
  {
    regex: /\bdiskutil\s+erase/,
    reason: "Contains 'diskutil erase' — erases volumes",
    name: "diskutil-erase",
  },
  {
    regex: /\bdiskutil\s+partitionDisk/,
    reason: "Contains 'diskutil partitionDisk' — repartitions disk",
    name: "diskutil-partition",
  },
  {
    regex: /\bshutdown\b/,
    reason: "Contains 'shutdown' — shuts down the system",
    name: "shutdown",
  },
  {
    regex: /\breboot\b/,
    reason: "Contains 'reboot' — reboots the system",
    name: "reboot",
  },
  {
    regex: /\bnvram\b/,
    reason: "Contains 'nvram' — modifies firmware settings",
    name: "nvram",
  },
  {
    regex: /\bcsrutil\b/,
    reason: "Contains 'csrutil' — modifies System Integrity Protection",
    name: "csrutil",
  },
  {
    regex: /\blaunchctl\b/,
    reason: "Contains 'launchctl' — manages system services/daemons",
    name: "launchctl",
  },
  {
    regex: /\bsystemsetup\b/,
    reason: "Contains 'systemsetup' — modifies system configuration",
    name: "systemsetup",
  },
  {
    regex: /\bnetworksetup\b/,
    reason: "Contains 'networksetup' — modifies network configuration",
    name: "networksetup",
  },
]

// ============================================================
// DESTRUCTIVE FILE/PERMISSION OPERATIONS
// ============================================================
const DESTRUCTIVE_PATTERNS: Pattern[] = [
  {
    regex: /\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)/,
    reason: "Contains 'rm -rf' — recursive forced deletion",
    name: "rm-rf",
  },
  {
    regex: /\brm\s+-[a-zA-Z]*r/,
    reason: "Contains 'rm -r' — recursive deletion",
    name: "rm-r",
  },
  {
    regex: /\bchmod\s+-[a-zA-Z]*R/,
    reason: "Contains 'chmod -R' — recursive permission change",
    name: "chmod-R",
  },
  {
    regex: /\bchown\s+-[a-zA-Z]*R/,
    reason: "Contains 'chown -R' — recursive ownership change",
    name: "chown-R",
  },
]

// ============================================================
// SUPPLY CHAIN / REMOTE CODE EXECUTION
// ============================================================
const SUPPLY_CHAIN_PATTERNS: Pattern[] = [
  {
    regex: /\bcurl\b.*\|\s*(sh|bash)\b/,
    reason: "Contains 'curl | sh/bash' — executes remote code directly",
    name: "curl-pipe-sh",
  },
  {
    regex: /\bwget\b.*\|\s*(sh|bash)\b/,
    reason: "Contains 'wget | sh/bash' — executes remote code directly",
    name: "wget-pipe-sh",
  },
]

// ============================================================
// PACKAGE MANAGEMENT (system-level installs)
// ============================================================
const PACKAGE_PATTERNS: Pattern[] = [
  {
    regex: /\bbrew\s+install\b/,
    reason: "Contains 'brew install' — installs system packages",
    name: "brew-install",
  },
  {
    regex: /\bnpm\s+install\s+-g\b/,
    reason: "Contains 'npm install -g' — installs global npm packages",
    name: "npm-install-g",
  },
]

// ============================================================
// DESTRUCTIVE GIT OPERATIONS
// ============================================================
const GIT_PATTERNS: Pattern[] = [
  {
    regex: /\bgit\s+push\s+.*--force/,
    reason: "Contains 'git push --force' — overwrites remote history",
    name: "git-push-force",
  },
  {
    regex: /\bgit\s+push\s+.*-f\b/,
    reason: "Contains 'git push -f' — overwrites remote history",
    name: "git-push-f",
  },
  {
    regex: /\bgit\s+reset\s+--hard/,
    reason: "Contains 'git reset --hard' — discards all uncommitted changes",
    name: "git-reset-hard",
  },
  {
    regex: /\bgit\s+clean\s+.*-f/,
    reason: "Contains 'git clean -f' — permanently deletes untracked files",
    name: "git-clean-f",
  },
  {
    regex: /\bgit\s+branch\s+.*-D/,
    reason: "Contains 'git branch -D' — force-deletes branch without merge check",
    name: "git-branch-D",
  },
  {
    regex: /\bgit\s+checkout\s+--\s/,
    reason: "Contains 'git checkout -- ' — discards uncommitted changes",
    name: "git-checkout-discard",
  },
  {
    regex: /\bgit\s+rebase\b/,
    reason: "Contains 'git rebase' — rewrites commit history",
    name: "git-rebase",
  },
  {
    regex: /\bgit\s+stash\s+drop/,
    reason: "Contains 'git stash drop' — permanently drops stashed changes",
    name: "git-stash-drop",
  },
]

// ============================================================
// macOS DEFAULTS MUTATION
// ============================================================
const MACOS_PATTERNS: Pattern[] = [
  {
    regex: /\bdefaults\s+write/,
    reason: "Contains 'defaults write' — modifies macOS system preferences",
    name: "defaults-write",
  },
]

const ALL_PATTERNS: Pattern[] = [
  ...SYSTEM_PATTERNS,
  ...DESTRUCTIVE_PATTERNS,
  ...SUPPLY_CHAIN_PATTERNS,
  ...PACKAGE_PATTERNS,
  ...GIT_PATTERNS,
  ...MACOS_PATTERNS,
]

export const CommandSafetyScanner: Plugin = async () => {
  return {
    "tool.execute.before": async (input: any, output: any) => {
      if (input.tool !== "bash") return
      const cmd = output.args?.command
      if (typeof cmd !== "string" || !cmd) return

      for (const pattern of ALL_PATTERNS) {
        if (pattern.regex.test(cmd)) {
          throw new Error(
            `[command-safety-scanner] Blocked: ${pattern.reason}\n` +
            `Command: ${cmd.slice(0, 500)}`
          )
        }
      }
    },
  }
}
