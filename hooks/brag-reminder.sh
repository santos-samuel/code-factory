#!/usr/bin/env bash
# brag-reminder.sh — Claude Code Stop hook that reminds about /brag
#
# Wire into settings.json as a Stop hook:
#   "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/brag-reminder.sh"}]}]
#
# Blocks session end if /brag hasn't been run today, giving you a chance to log accomplishments.

STATE_FILE="$HOME/log/.brag-state.json"
TODAY=$(date +%Y-%m-%d)

# No reminder if brag hasn't been set up yet
if [ ! -f "$STATE_FILE" ]; then
  echo '{"decision":"approve"}'
  exit 0
fi

LAST_RUN=$(jq -r '.last_run // ""' "$STATE_FILE" 2>/dev/null || echo "")

if [ "$LAST_RUN" != "$TODAY" ]; then
  echo "{\"decision\":\"block\",\"reason\":\"You haven't run /brag today. Consider running it to log your accomplishments before ending the session.\"}"
else
  echo '{"decision":"approve"}'
fi
