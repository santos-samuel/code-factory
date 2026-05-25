#!/bin/bash
# Background review poller — blocks until bot reviewers post new feedback.
# Run with run_in_background: true to avoid consuming tokens while waiting.
#
# Usage: poll-reviews.sh <pr-number> <owner/repo> <known-comment-count> <known-review-count> [bot-pattern] [poll-interval] [max-polls]
#
# Parameters:
#   pr-number            PR number to watch
#   owner/repo           Repository in owner/repo format
#   known-comment-count  Comment count before triggering reviews (baseline)
#   known-review-count   Non-COMMENTED review count before triggering (baseline)
#   bot-pattern          Regex for bot login names (default: "bot|app|\[bot\]")
#   poll-interval        Seconds between polls (default: 30)
#   max-polls            Maximum poll attempts (default: 30, ~15 min at 30s)
#
# Exit states (printed to stdout):
#   REVIEWS_READY     New bot review comments detected and :eyes: cleared
#   NO_NEW_REVIEWS    Timeout with no bot activity (reviewer may not be configured)
#   TIMEOUT           Max polls reached while :eyes: still active

set -euo pipefail

PR_NUMBER="${1:?Usage: poll-reviews.sh <pr-number> <owner/repo> <known-comment-count> <known-review-count> [bot-pattern] [poll-interval] [max-polls]}"
REPO="${2:?Usage: poll-reviews.sh <pr-number> <owner/repo> <known-comment-count> <known-review-count> [bot-pattern] [poll-interval] [max-polls]}"
KNOWN_COMMENT_COUNT="${3:?Usage: poll-reviews.sh <pr-number> <owner/repo> <known-comment-count> <known-review-count> [bot-pattern] [poll-interval] [max-polls]}"
KNOWN_REVIEW_COUNT="${4:?Usage: poll-reviews.sh <pr-number> <owner/repo> <known-comment-count> <known-review-count> [bot-pattern] [poll-interval] [max-polls]}"
BOT_PATTERN="${5:-bot|app|\\[bot\\]}"
POLL_INTERVAL="${6:-30}"
MAX_POLLS="${7:-30}"

eyes_active=false

for i in $(seq 1 "$MAX_POLLS"); do
  # Check for :eyes: emoji in PR comments (signals reviewer is investigating)
  EYES_IN_COMMENTS=$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" --paginate 2>/dev/null \
    | jq -r --arg bp "$BOT_PATTERN" '[.[] | select(.user.login | test($bp; "i")) | select(.body | test(":eyes:|👀"))] | length' 2>/dev/null) || EYES_IN_COMMENTS="0"

  # Check for :eyes: in PR body (some reviewers add it there too)
  EYES_IN_BODY=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json body --jq '.body // "" | test(":eyes:|👀")' 2>/dev/null) || EYES_IN_BODY="false"

  if [ "$EYES_IN_COMMENTS" -gt 0 ] || [ "$EYES_IN_BODY" = "true" ]; then
    eyes_active=true
    echo "poll $i/$MAX_POLLS: reviewer investigating (:eyes: detected)"
    sleep "$POLL_INTERVAL"
    continue
  fi

  # :eyes: cleared (or was never present) — check for new comments/reviews
  if [ "$eyes_active" = true ]; then
    echo "poll $i/$MAX_POLLS: :eyes: cleared, checking for new feedback"
  fi

  # Count current review comments
  CURRENT_COMMENTS=$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate 2>/dev/null \
    | jq -s 'add | length' 2>/dev/null) || CURRENT_COMMENTS="$KNOWN_COMMENT_COUNT"

  if [ "$CURRENT_COMMENTS" -gt "$KNOWN_COMMENT_COUNT" ]; then
    echo ""
    echo "REVIEWS_READY"
    echo "previous_comments=$KNOWN_COMMENT_COUNT current_comments=$CURRENT_COMMENTS"
    echo ""
    echo "NEW_COMMENTS:"
    gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --paginate
    exit 0
  fi

  # Count current non-COMMENTED reviews (actual review submissions)
  CURRENT_REVIEWS=$(gh api "repos/$REPO/pulls/$PR_NUMBER/reviews" --paginate 2>/dev/null \
    | jq -s 'add | [.[] | select(.state != "COMMENTED")] | length' 2>/dev/null) || CURRENT_REVIEWS="$KNOWN_REVIEW_COUNT"

  if [ "$CURRENT_REVIEWS" -gt "$KNOWN_REVIEW_COUNT" ]; then
    echo ""
    echo "REVIEWS_READY"
    echo "previous_reviews=$KNOWN_REVIEW_COUNT current_reviews=$CURRENT_REVIEWS"
    echo ""
    echo "NEW_REVIEWS:"
    gh api "repos/$REPO/pulls/$PR_NUMBER/reviews" --paginate
    exit 0
  fi

  # If :eyes: was seen and cleared but no new comments appeared, the reviewer
  # found nothing actionable — report as ready (clean review)
  if [ "$eyes_active" = true ]; then
    echo ""
    echo "REVIEWS_READY"
    echo "eyes_cleared=true new_comments=0 new_reviews=0"
    echo "Reviewer investigated and posted no actionable feedback."
    exit 0
  fi

  echo "poll $i/$MAX_POLLS: no new activity (comments=$CURRENT_COMMENTS reviews=$CURRENT_REVIEWS)"
  sleep "$POLL_INTERVAL"
done

echo ""
if [ "$eyes_active" = true ]; then
  echo "TIMEOUT"
  echo "Reviewer :eyes: was active but never completed within $((MAX_POLLS * POLL_INTERVAL / 60)) min"
else
  echo "NO_NEW_REVIEWS"
  echo "No bot activity detected after $((MAX_POLLS * POLL_INTERVAL / 60)) min — reviewer may not be configured"
fi
exit 1
