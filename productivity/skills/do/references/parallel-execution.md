# Bounded Parallel Execution

Parallelize only when each task is independent, substantial enough to offset coordination cost,
has a disjoint write scope and conflict key, and has a verified capacity slot. Keep the
coordinator responsive and preserve a clear critical path.

The shared policy enforces these limits:

- at most three automatic leaf workers;
- one coordinator slot remains reserved;
- unknown capacity launches one probe, then refills only from observed free capacity;
- use wait-any completion and refill only while the critical path remains healthy;
- on the first failure, stop new dispatch, drain active workers, and skip undispatched work;
- do not retry by cycling models or silently replace a failed worker.

The deterministic capacity check is available for validation and planning:

```bash
python3 scripts/model_router.py parallel-plan --requested <count> --capacity <total-slots>
```

If capacity is unknown, omit `--capacity`; the result must dispatch one probe. A task bundle
records `files`, `write_scope`, and `conflict_key` so overlapping ownership is rejected before
dispatch. Read-only review leaves still need disjoint module ownership when fanned out.
