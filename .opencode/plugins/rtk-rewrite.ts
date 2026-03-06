/**
 * rtk-rewrite — OpenCode plugin equivalent of the Claude Code PreToolUse:Bash hook.
 *
 * Transparently rewrites raw commands to their rtk equivalents before execution,
 * providing 60-90% token savings on dev operations.
 *
 * Uses `rtk rewrite` as single source of truth — no duplicate mapping logic here.
 * To add support for new commands, update the rtk binary (src/discover/registry.rs).
 */
import type { Plugin } from "@opencode-ai/plugin"

export const RtkRewrite: Plugin = async ({ $ }) => {
  // Check if rtk is available at plugin load time
  try {
    await $`rtk --version`
  } catch {
    // rtk not installed — skip silently
    return {}
  }

  return {
    "tool.execute.before": async (input: any, output: any) => {
      if (input.tool !== "bash") return
      const cmd = output.args?.command
      if (typeof cmd !== "string" || !cmd) return

      // Skip if already using rtk
      if (/^rtk\s/.test(cmd) || /\/rtk\s/.test(cmd)) return
      // Skip heredocs
      if (cmd.includes("<<")) return

      // Delegate all rewrite logic to the rtk binary.
      try {
        const result = await $`rtk rewrite ${cmd}`
        const rewritten = result.stdout.trim()

        // If output is empty or identical, nothing to do.
        if (!rewritten || rewritten === cmd) return

        output.args.command = rewritten
      } catch {
        // rtk rewrite exits 1 when there's no rewrite — pass through silently.
        return
      }
    },
  }
}
