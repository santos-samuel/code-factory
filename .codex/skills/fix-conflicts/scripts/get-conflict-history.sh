#!/usr/bin/env bash
# Usage: get-conflict-history.sh local|remote
# Shows commits that touched conflicted files for the specified side.
# Handles merge, rebase-merge, and rebase-apply operations.

set -euo pipefail

side="${1:-}"
if [[ "$side" != "local" && "$side" != "remote" ]]; then
  echo "Usage: $0 local|remote" >&2
  exit 1
fi

git_dir=$(git rev-parse --git-dir 2>/dev/null) || { echo "Not a git repository" >&2; exit 1; }

# Get conflicted file paths
files=$(git diff --name-only --diff-filter=U 2>/dev/null | tr '\n' ' ')
[ -z "$files" ] && { echo "No conflicted files"; exit 0; }

if [ -f "$git_dir/MERGE_HEAD" ]; then
  base=$(git merge-base HEAD MERGE_HEAD)
  if [ "$side" = "local" ]; then
    eval git log --oneline "\"$base\"..HEAD" -- $files
  else
    eval git log --oneline "\"$base\"..MERGE_HEAD" -- $files
  fi
elif [ -d "$git_dir/rebase-merge" ]; then
  onto=$(cat "$git_dir/rebase-merge/onto")
  orig_head=$(cat "$git_dir/rebase-merge/orig-head")
  if [ "$side" = "local" ]; then
    eval git log --oneline "\"$onto\"..HEAD" -- $files
  else
    eval git log --oneline "\"$onto\"..\"$orig_head\"" -- $files
  fi
elif [ -d "$git_dir/rebase-apply" ]; then
  onto=$(cat "$git_dir/rebase-apply/onto")
  orig_head=$(cat "$git_dir/rebase-apply/orig-head")
  if [ "$side" = "local" ]; then
    eval git log --oneline "\"$onto\"..HEAD" -- $files
  else
    eval git log --oneline "\"$onto\"..\"$orig_head\"" -- $files
  fi
elif [ -f "$git_dir/CHERRY_PICK_HEAD" ]; then
  if [ "$side" = "local" ]; then
    eval git log --oneline -5 HEAD -- $files
  else
    eval git log --oneline -1 CHERRY_PICK_HEAD -- $files
  fi
else
  echo "No merge, rebase, or cherry-pick in progress"
fi
