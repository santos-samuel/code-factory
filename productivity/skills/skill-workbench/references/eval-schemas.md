# Eval Schemas

Reference for JSON structures used by skill evaluation, grading, and benchmarking. Load when writing eval definitions, grading assertions, or benchmark configurations.

---

## evals.json

Defines eval cases for a skill. Located at `evals/evals.json` within the skill directory.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `skill_name` | string | Name matching the skill's YAML frontmatter |
| `evals[].id` | integer | Unique identifier for this eval case |
| `evals[].prompt` | string | The task prompt to execute |
| `evals[].expected_output` | string | Human-readable description of success |
| `evals[].files` | string[] | Input file paths relative to skill root (optional) |
| `evals[].expectations` | string[] | Verifiable statements the grader checks against outputs |

---

## grading.json

Output from the skill-grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    },
    {
      "text": "The spreadsheet has a SUM formula in cell B10",
      "passed": false,
      "evidence": "No spreadsheet was created. The output was a text file."
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.50
  },
  "claims": [
    {
      "claim": "The form has 12 fillable fields",
      "type": "factual",
      "verified": true,
      "evidence": "Counted 12 fields in field_info.json"
    }
  ],
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The output includes the name 'John Smith'",
        "reason": "A hallucinated document mentioning the name would also pass — check it appears as primary contact with matching phone and email"
      }
    ],
    "overall": "Assertions check presence but not correctness. Consider adding content verification."
  }
}
```

**Important:** Use exact field names `text`, `passed`, `evidence` in the expectations array. The grader agent depends on these names.

| Field | Type | Description |
|-------|------|-------------|
| `expectations[]` | object[] | Graded expectations with evidence |
| `expectations[].text` | string | The original expectation text |
| `expectations[].passed` | boolean | Whether the expectation passes |
| `expectations[].evidence` | string | Specific quote or description supporting the verdict |
| `summary.passed` | integer | Count of passed expectations |
| `summary.failed` | integer | Count of failed expectations |
| `summary.total` | integer | Total expectations evaluated |
| `summary.pass_rate` | float | Fraction passed (0.0 to 1.0) |
| `claims[]` | object[] | Extracted and verified claims from the output |
| `claims[].claim` | string | The statement being verified |
| `claims[].type` | string | `"factual"`, `"process"`, or `"quality"` |
| `claims[].verified` | boolean | Whether the claim holds |
| `claims[].evidence` | string | Supporting or contradicting evidence |
| `eval_feedback` | object | Improvement suggestions for the evals (only when warranted) |
| `eval_feedback.suggestions[]` | object[] | Concrete suggestions with `reason` and optional `assertion` |
| `eval_feedback.overall` | string | Brief assessment of eval quality |

---

## benchmark.json

Output from benchmark runs comparing with-skill vs without-skill performance. Located at `<workspace>/iteration-N/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "example-skill",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "descriptive-name",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "errors": 0
      }
    }
  ],
  "run_summary": {
    "with_skill": {
      "pass_rate": { "mean": 0.85, "stddev": 0.05 },
      "time_seconds": { "mean": 45.0, "stddev": 12.0 },
      "tokens": { "mean": 3800, "stddev": 400 }
    },
    "without_skill": {
      "pass_rate": { "mean": 0.35, "stddev": 0.08 },
      "time_seconds": { "mean": 32.0, "stddev": 8.0 },
      "tokens": { "mean": 2100, "stddev": 300 }
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },
  "notes": [
    "Assertion 'Output is a PDF file' passes 100% in both configurations — may not differentiate skill value",
    "Skill adds 13s average execution time but improves pass rate by 50%"
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `metadata.skill_name` | string | Name of the skill being benchmarked |
| `metadata.timestamp` | string | ISO timestamp of the benchmark run |
| `metadata.evals_run` | integer[] | List of eval IDs included |
| `metadata.runs_per_configuration` | integer | Number of runs per configuration (e.g., 3) |
| `runs[].eval_id` | integer | Eval identifier |
| `runs[].eval_name` | string | Human-readable eval name |
| `runs[].configuration` | string | `"with_skill"` or `"without_skill"` |
| `runs[].run_number` | integer | Run number (1, 2, 3...) |
| `runs[].result` | object | Nested: `pass_rate`, `passed`, `failed`, `total`, `time_seconds`, `tokens`, `errors` |
| `run_summary.{config}` | object | Per-configuration stats with `mean` and `stddev` for `pass_rate`, `time_seconds`, `tokens` |
| `run_summary.delta` | object | Difference strings (e.g., `"+0.50"`) |
| `notes` | string[] | Analyst observations about the benchmark data |
