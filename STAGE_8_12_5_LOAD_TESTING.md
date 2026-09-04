# Stage 8.12.5 — Load Testing

## Goal

Turn performance from an anecdote into a repeatable release gate.

## What is measured

The dependency-free `scripts/load_smoke.py` now reports and gates on:

- total requests and concurrency;
- requests per second;
- error rate;
- mean, p50, p95, p99 and max latency;
- HTTP status distribution;
- endpoint distribution;
- explicit threshold violations.

## CI workload

`.github/workflows/load-gate.yml` starts PostgreSQL, Redis and the Django ASGI application, seeds 120 representative publications, warms the service, and sends 300 requests at concurrency 20 across:

- `/api/v1/live/`;
- `/api/v1/publications/`;
- `/api/v1/search/?q=django&scope=publications`.

The default CI gate is calibrated as a regression guard for a shared GitHub runner:

- error rate <= 1%;
- p95 <= 3000 ms;
- p99 <= 4000 ms;
- throughput >= 10 requests/s.

The initial measured shared-runner baseline was 300/300 successful responses, 0% errors, 15.12 requests/s, p95 2409 ms and p99 2567 ms. The gate therefore leaves headroom for runner variance without pretending that a shared CI VM is a production capacity benchmark.

These values are regression thresholds, not a claimed production capacity target. Staging should use production-like infrastructure and tighter SLO-derived thresholds.

## Reports

Every run uploads `load-gate-report` as a workflow artifact, including failed runs. This preserves the measured numbers instead of reducing performance analysis to a red or green icon.

## Production-like use

Run the same script against staging with stricter thresholds and authenticated paths where appropriate. A staging result should be recorded before a public beta rollout.

## Acceptance criteria

- Load Gate workflow passes on the branch.
- The report artifact is produced.
- Any threshold violation fails the workflow.
- No third-party load-test dependency is required for the basic gate.
