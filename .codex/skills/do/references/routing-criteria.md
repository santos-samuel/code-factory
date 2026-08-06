# Task Routing Criteria

Use task evidence to choose a model tier; agent role metadata is only the starting recommendation.
Evaluate the task on these dimensions:

- ambiguity: how much interpretation remains;
- scope: how broad the change or review is;
- coupling: how many components or contracts interact;
- verification: how difficult it is to prove the result;
- consequence: the cost of a wrong decision;
- latency: whether a slower, stronger route is acceptable.

The shared deterministic helper resolves the cross-surface matrix without network calls:

```bash
python3 scripts/model_router.py route --surface <claude|codex|pi> --task <task-class>
```

Use `--override <model[:effort-or-thinking]>` only for an explicit user choice. A valid explicit
choice wins over the policy recommendation. A route that is unavailable or cannot be verified
fails open to the configured surface default and is recorded as `verification=unverified` and
`observed=unknown`. Never cycle through models or claim that a selected route was actually used.

The route line in a task artifact or meaningful lifecycle event must distinguish:

`selected=<route>; recommended=<route>; verification=<available|unverified>; observed=<available|unknown>`

Claude source agent frontmatter keeps its Claude `model` and `effort` mapping. Codex transforms
the same `routing_tier` metadata to GPT-5.6 Luna/Sol. Pi uses only the OpenAI AI Gateway routes
from `model-routing.json`; Claude/Anthropic routes are not valid Pi overrides.
