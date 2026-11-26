# AI Engineering Observability Guide

This document describes the **Observability** framework (`src/observability/`) in Local Hermes AI.

---

## 1. Observability vs. Evaluation

- **Observability** (`src/observability/`): Answers *"What happened?"* — captures structured events, reconstructs execution lifecycles, measures latency, classifies errors, tracks tokens/cost, and enables single-run debugging.
- **Evaluation** (`src/evaluation/`): Answers *"Was what happened correct?"* — consumes observability evidence (traces, logs, approvals, recovery events) to score correctness, safety, and regression.

---

## 2. Core Components

### 2.1 Structured Logging (`src/observability/logging_schema.py`)
- `StructuredLogRecord`: Machine-readable event schema with `timestamp`, `level` (`DEBUG`, `INFO`, `WARNING`, `ERROR`), `event` (validated against `EVENT_TAXONOMY`), correlation IDs (`run_id`, `task_id`, `step_id`), `component`, `status`, `duration_ms`, `error_type`, `message`, and `metadata`.
- **Best-Effort Persistence**: `ObservabilityLogger` forwards records to SQLite `TaskLogger` without ever crashing the application if logging fails.
- **Privacy & Resource Bounds**: Automatically redacts sensitive keys (`password`, `token`, `secret`, `api_key`, etc.), caps metadata keys (`MAX_METADATA_KEYS = 50`), and bounds in-memory retention (`MAX_STORED_EVENTS = 10,000`).

### 2.2 Run Tracing (`src/observability/tracing.py`)
- `build_run_trace(run_id, logs)` reconstructs a `RunTrace` with `SpanTrace` entries (LLM, retrieval, tool, approval, step) and reuses `build_task_trace()` from `src/automation/tracing.py`.
- Validates lifecycle transitions (detecting impossible sequences such as `step_completed` without `step_started`, or `approval_granted` without `approval_requested`).

### 2.3 Latency, Error, Token & Cost Metrics (`src/observability/metrics.py`)
- **Latency (`LatencyBreakdown`)**: Computes `total_ms`, `planning_ms`, `retrieval_ms`, `llm_ms`, `tools_ms`, `approval_ms`, and `other_ms` strictly from valid timestamps (`None` if missing/invalid).
- **Errors (`ErrorMetrics`)**: Categorizes errors into `ERROR_CATEGORIES` (`validation_error`, `planning_error`, `tool_error`, `execution_error`, `retrieval_error`, `llm_error`, `approval_error`, `timeout_error`, `resource_limit_error`, `persistence_error`, `recovery_error`, `unknown_error`) and computes safe error rates (`None` when denominator is zero).
- **Tokens (`TokenUsage`)**: Aggregates `input_tokens`, `output_tokens`, and `total_tokens` across LLM calls without fabricating unavailable counts (`None` when unavailable).
- **Cost (`PricingConfig`, `calculate_cost`)**: Computes monetary cost **only** when both token counts and explicit `PricingConfig` exist; otherwise returns `None` (`UNKNOWN`).

### 2.4 Run Inspection (`src/observability/inspector.py`)
- `RunInspector.inspect_run(run_id, logs, task=..., pricing=...)`: Produces a `RunInspectionReport` with truncated step output summaries (`MAX_SUMMARY_OUTPUT_LEN = 200`).
- `RunInspector.search_runs(logs, run_id=..., task_id=..., status=..., error_category=...)`: Filters runs cleanly.
- `format_observability_summary(report)`: Formats a readable terminal summary using `N/A` / `UNKNOWN` for missing evidence.

---

## 3. Running Observability Tests

```bash
python3 -m unittest tests/test_obs_*.py -v
```
