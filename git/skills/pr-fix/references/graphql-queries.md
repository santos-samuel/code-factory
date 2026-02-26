# GraphQL Queries and Mutations for PR Review Threads

Reference for the `pr-fix` skill. Contains all GraphQL operations needed to fetch, reply to, and resolve PR review threads.

## Fetch Unresolved Review Threads

Returns all review threads with comments, resolution status, file path, and line numbers.

```bash
gh api graphql -F owner='{owner}' -F repo='{repo}' -F pr={number} -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      title
      number
      url
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          startLine
          diffSide
          comments(first: 50) {
            nodes {
              id
              databaseId
              body
              author { login }
              outdated
              createdAt
            }
          }
        }
      }
    }
  }
}
'
```

### Parsing the Response

Filter for unresolved threads:

```bash
# Pipe the response through jq to get only unresolved threads
... | jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved == false))'
```

Key fields:

| Field | Type | Usage |
|-------|------|-------|
| `id` | String | GraphQL node ID — pass to `resolveReviewThread` mutation |
| `isResolved` | Boolean | Filter for unresolved threads |
| `isOutdated` | Boolean | Code has changed since the review comment was posted |
| `path` | String | File path relative to repo root |
| `line` | Int | End line number in the diff |
| `startLine` | Int \| null | Start line for multi-line comments (null = single line) |
| `comments.nodes[0].databaseId` | Int | REST API comment ID — pass to reply endpoint |
| `comments.nodes[0].body` | String | The review comment text |
| `comments.nodes[0].author.login` | String | GitHub username of the commenter |

## Resolve a Thread

Marks a review thread as resolved. Requires the GraphQL node `id` from the fetch query.

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {
    threadId: "{threadId}"
  }) {
    thread {
      id
      isResolved
    }
  }
}
'
```

Replace `{threadId}` with the actual `id` value from the thread.

**Permissions required:** Repository Contents: Read and Write.

## Unresolve a Thread

Reverses a thread resolution (rarely needed, included for completeness).

```bash
gh api graphql -f query='
mutation {
  unresolveReviewThread(input: {
    threadId: "{threadId}"
  }) {
    thread {
      id
      isResolved
    }
  }
}
'
```

## Reply to a Review Comment

Uses the REST API to reply directly to a review comment thread. This creates a threaded reply, not a standalone PR comment.

```bash
gh api repos/{owner}/{repo}/pulls/comments/{databaseId}/replies \
  -X POST \
  -f body='{response text}'
```

Replace:
- `{owner}/{repo}` — the repository (e.g., `DataDog/dd-source`)
- `{databaseId}` — the `databaseId` of the first comment in the thread
- `{response text}` — the reply body (supports GitHub-flavored markdown)

## Request Re-Review

After all threads are addressed, request re-review from specific reviewers:

```bash
gh pr edit {number} --add-reviewer {reviewer1},{reviewer2}
```

## Batch Processing Pattern

For PRs with many threads, process in batches to avoid API rate limits:

1. Fetch all threads in one GraphQL call (up to 100 threads, 50 comments each).
2. Apply all code changes locally (no API calls).
3. Reply to threads in sequence (REST API, one call per thread).
4. Resolve threads in sequence (GraphQL mutation, one call per thread).
5. Commit and push once.

This minimizes API calls: 1 fetch + N replies + N resolves + 1 push.
