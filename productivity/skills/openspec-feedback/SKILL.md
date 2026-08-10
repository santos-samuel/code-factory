---
name: openspec-feedback
description: >
  Use when the user wants to submit feedback about OpenSpec — collecting,
  enriching, and anonymizing context before sending. Triggers: "openspec
  feedback", "opsx feedback", "submit feedback", "send feedback about openspec".
argument-hint: "[feedback summary]"
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash(openspec:feedback:*), AskUserQuestion
---

# OpenSpec Feedback

Announce: "I'm using the openspec-feedback skill to draft and submit OpenSpec feedback."

Collect, enrich, and submit user feedback about OpenSpec with privacy-preserving anonymization.

## Step 1: Gather Context from the Conversation

Review recent conversation history for context:
- Identify what task was being performed.
- Note what worked well or poorly.
- Capture specific friction points or praise.

Do not invent feedback the user did not express.

## Step 2: Draft Enriched Feedback

Draft a clear, descriptive title (single sentence; no "Feedback:" prefix needed) and a body that includes:
- What the user was trying to do.
- What happened (good or bad).
- Relevant context from the conversation.
- Any specific suggestions or requests.

## Step 3: Anonymize Sensitive Information

Before showing the draft, redact anything sensitive:
- Replace file paths with `<path>` or generic descriptions.
- Replace API keys, tokens, and secrets with `<redacted>`.
- Replace company or organization names with `<company>`.
- Replace personal names with `<user>`.
- Replace specific URLs with `<url>` unless they are public and relevant.

Keep the technical details that help explain the issue.

## Step 4: Present the Draft for Approval

Show the complete draft (title and body) to the user and ask for explicit approval before submitting.
Allow the user to request modifications.

## Step 5: Submit on Confirmation

Only after the user confirms, submit with:

```bash
openspec feedback "<title>" --body "<body content>"
```

The command automatically attaches metadata (version, platform, timestamp).

## Error Handling

| Failure | Resolution |
|-|-|
| `openspec` is missing | Tell the user to run this repository's `./init.sh` or install `@fission-ai/openspec`. |
| User declines to approve | Do not submit; ask what to change and revise the draft. |
| Feedback text is empty | Ask the user what to report before drafting. |
| Submission command fails | Show the error output and retry once the user confirms the corrected input. |
| Sensitive data detected after submit | Inform the user; OpenSpec does not support recall, so confirm anonymization before sending. |
