# AI Automation Agent Architecture

## 1. Overview

The AI Automation Agent uses a Planner-Executor architecture.

The Planner converts user instructions into structured task plans. The Executor validates and runs each step using tools registered in the Tool Registry.

The LLM is responsible for planning, while Python controls actual tool execution.

## 2. Core Components

### Automation Agent

- Receives user requests.
- Coordinates the planner and executor.
- Returns execution results.

### Planner

- Converts natural language instructions into structured task plans.
- Produces JSON-compatible output.
- Does not execute tools directly.

### Plan Validator

- Validates task structure.
- Checks required fields and argument types.
- Rejects unknown tools.
- Enforces the maximum step limit.

### Tool Registry

- Stores available tool definitions.
- Provides an allowlist of executable tools.
- Exposes tool metadata and execution functions.

### Executor

- Executes validated steps sequentially.
- Resolves references to previous step outputs.
- Handles execution errors.
- Stops execution when a step fails.

### Logger

- Records task IDs and step IDs.
- Records execution status and timestamps.
- Stores error information for failed steps.

## 3. Execution Flow

1. Receive a user request.
2. Generate a task plan using the LLM.
3. Parse and validate the plan.
4. Verify that all requested tools are registered.
5. Execute steps sequentially.
6. Resolve outputs from previous steps when needed.
7. Record each step's status.
8. Return the final task result.

## 4. Task Data Model

A task contains:
- Task ID
- Description
- List of steps
- Overall execution status

Each step contains:
- Step ID
- Tool name
- Arguments
- Execution status
- Output or error information

## 5. Safety Controls

- Only registered tools may be executed.
- Tool arguments must be validated.
- Maximum of 5 steps per task.
- File access must remain within permitted directories.
- No unrestricted shell execution.
- Destructive and external actions require explicit confirmation.
- Failed steps stop the current task.
- Previous step outputs are treated as data, not executable instructions.

## 6. Initial Tool Set

- read_file
- list_files
- summarize_text
- save_note
- search_notes
- calculator
- get_current_time

## 7. Execution Strategy

The initial implementation uses sequential execution.

Parallel execution, background scheduling, and external service integrations are deferred until the basic execution engine is stable.

## 8. Testing Strategy

Automated tests will cover:
- Task and step model validation.
- Planner output parsing.
- Unknown tool rejection.
- Invalid argument rejection.
- Maximum step enforcement.
- Sequential execution.
- Step output references.
- Execution failures and logging.

## 9. Evaluation & Observability

Stage 13 establishes a deterministic evaluation and observability framework for automation:

### 9.1 Metrics and Dataset
- **EvaluationMetrics**: Immutable representation of task execution quality including plan validity, task success, step success rate, approval compliance, recovery success, and trace completeness.
- **EvaluationCase & EVALUATION_CASES**: Standardized golden evaluation dataset with required tools, step count, and expected outcomes.
- **Reference Plans**: Deterministic baseline plans (`REFERENCE_PLANS`) for testing evaluation framework without live LLM non-determinism.

### 9.2 Evaluation Layers
- **Planning Evaluation** (`evaluate_planning`): Validates tool sequence matching, step count accuracy, and planning success.
- **Tool Selection Evaluation** (`evaluate_tool_selection`): Measures exact tool sequence selection accuracy against golden cases.
- **Execution Outcome Evaluation** (`evaluate_execution_outcome`): Evaluates whether execution succeeded or failed relative to expected outcomes.
- **Aggregate Metrics** (`calculate_evaluation_summary`): Computes overall dataset accuracy rates across planning, tool selection, and execution outcomes.

### 9.3 Observability and Tracing
- **Structured Tracing** (`TaskTrace`, `StepTrace`, `build_task_trace`): Reconstructs hierarchical execution trees from SQLite task logs.
- **Structured Run Metrics** (`RunMetrics`, `collect_run_metrics`): Extracts run metadata, step counts, approval counts, and duration in seconds.
- **Trace Completeness** (`evaluate_trace_completeness`): Verifies lifecycle events (`task_started`, `step_started`, `step_completed`/`step_failed`, approval resolution, and `task_completed`/`task_failed`).
- **Approval Compliance** (`evaluate_approval_compliance`): Ensures tools requiring approval are gated by `approval_requested` and `approval_granted`.
- **Recovery Success** (`evaluate_recovery_success`): Detects task resumption and measures post-recovery completion.

### 9.4 Regression and Reporting
- **Regression Evaluator** (`RegressionEvaluator`, `run_regression_evaluation`): Evaluates golden dataset against reference plans with optional strict failure enforcement.
- **Evaluation Report Generator** (`generate_evaluation_report`): Generates structured human-readable markdown summaries covering dataset size, planning accuracy, execution outcome accuracy, and reliability metrics.

## 10. Production Hardening

Stage 14 hardens the automation runtime without changing core product behavior:

### 10.1 Configuration Management & Validation
- **`AutomationConfig`**: Immutable, typed configuration object governing `tool_timeout`, `max_output_size`, `max_task_steps`, `require_approval_for_sensitive_tools`, and `db_path`.
- **Fail-Closed Validation**: Startup validation rejects non-positive timeouts, non-positive output limits, step limits outside `[1, 5]`, non-boolean approval flags, and empty paths.

### 10.2 Bounded Retry Policy
- **`RetryPolicy`**: Bounded retry configuration with injectable sleeper for zero-delay unit testing.
- **Safety Boundaries**: Only transient errors (`TimeoutError`, `ConnectionError`) on non-approval-required tools may be retried. Non-retryable errors (`ValueError`, `TypeError`, `PermissionError`) fail immediately. Approval-required operations are never retried automatically.
- **Observability**: Retries are structured and logged via `"step_retry"` events.

### 10.3 Graceful Shutdown & Cancellation
- **`TaskExecutor.cancel(task_id)`**: Safely transitions pending or in-progress tasks to `TaskStatus.CANCELLED`.
- **State Consistency**: Completed steps retain their outputs, pending steps remain pending, and completed/failed tasks cannot be cancelled.
- **Deterministic Resume**: Cancelled tasks can be resumed deterministically from where they were interrupted.

### 10.4 Database Reliability Hardening
- **Foreign Key Enforcement**: `PRAGMA foreign_keys = ON` enforced on every SQLite connection.
- **Atomic Transactions & Rollback**: Managed via context managers with automatic rollback on unhandled errors, preventing partial task writes.
- **Resource Cleanup**: Explicit connection closing eliminates connection leakage.

### 10.5 Logging Hardening & Redaction
- **Structured Machine-Readable Logs**: Standardized logging schema with validated event names and step references.
- **Secret & Argument Redaction**: Automatically redacts sensitive fields matching passwords, tokens, API keys, credentials, and secrets.
- **Payload Truncation**: Caps oversized detail strings (>10,000 characters) to prevent log database bloat.

### 10.6 Resource Boundaries & Attack Surface Hardening
- **Step Limits**: Enforced maximum of 5 steps per task plan.
- **Input Size Limits**: `MAX_PLANNER_REQUEST_SIZE = 10,000` characters to prevent prompt bloat and injection DoS.
- **Argument Nesting Limits**: Maximum argument traversal depth of 10 to prevent recursion exhaustion attacks.
- **Tool Allowlist Boundary**: Tool definitions require callable handlers, valid identifier names, and strict argument schema checking.

### 10.7 State Machine Consistency & Failure Isolation
- **`validate_task_state_consistency`**: Verifies valid status combinations between `TaskStatus` and individual `StepStatus` values.
- **Failure Isolation**: Step failures halt execution without modifying or corrupting outputs from previously successful steps.

### 10.8 Approval Safety Hardening
- **Strict Boolean Approval**: Only explicit boolean `True` grants permission. Truthy values (`1`, `"yes"`, `[True]`) fail closed as denials.
- **Resume Protection**: Tasks awaiting approval cannot be resumed automatically, preventing approval bypass.

### 10.9 Production Readiness Health Check
- **`check_production_health`**: Local lightweight audit reporting the readiness of configuration, tool registry, task store, logger, and planner.

### 10.10 Known Limitations
- **Local SQLite Architecture**: Embedded SQLite is optimized for local single-process execution; multi-process concurrency requires filesystem lock awareness.
- **No Distributed Workers**: Execution is synchronous and local-first; background scheduling and worker queues are intentionally deferred.

## 11. Stage 15 — RAG + Automation Integration Architecture

### 11.1 Integrated Workflow
Stage 15 integrates project knowledge retrieval into the automation agent workflow while maintaining strict separation of concerns:

```text
User Request
  ↓
RAG Context Retrieval (RAGContextRetriever)
  ↓
Retrieved Context (Untrusted Reference Data)
  ↓
Task Planner (TaskPlanner with Context & Security Rules)
  ↓
Structured Task Plan (TaskPlan)
  ↓
Task Validation (TaskValidator)
  ↓
Approval Gate (TaskExecutor + Approval Handler)
  ↓
Tool Execution & Output Passing (ToolRegistry)
  ↓
Persistence & Observability (TaskStore & TaskLogger)
```

### 11.2 Architectural Boundaries & Untrusted Data Invariant
- **RAG as Untrusted Data Provider**: Retrieved documents provide knowledge and context only. Documents are never treated as executable code or system instructions.
- **Planner Ownership**: The `TaskPlanner` remains exclusively responsible for converting user requests and reference data into a structured `TaskPlan`.
- **Registry & Validator Enforcement**: Tools mentioned in retrieved text cannot be invoked unless already registered in `ToolRegistry` and validated by `TaskValidator`.
- **Approval Preserved**: Documents cannot claim prior approval or bypass human approval requirements for sensitive tools. Approval evaluation occurs at executor runtime.

### 11.3 Context Model & Bounded Budget
- **`RAGConfig`**: Configures `top_k`, cosine similarity `threshold`, `max_context_length` (default: 4,000 characters), and vector database path.
- **`ContextChunk`**: Immutable dataclass containing `content`, `source`, and `score`.
- **`RetrievedContext`**: Holds query, chunks, formatted text representation, and error state. Enforces deterministic length capping with `"... [TRUNCATED]"` marker to protect planner prompts against DoS and token exhaustion.

### 11.4 Prompt Contract & Section Isolation
The planner prompt isolates user requests from retrieved knowledge using distinct markdown sections and explicit negative constraints:
- `RETRIEVED KNOWLEDGE (UNTRUSTED REFERENCE MATERIAL)`: Explicitly marked as untrusted reference data.
- **Security Rules**: Informs the model that retrieved knowledge must never override planning rules, tool allowlists, or validation boundaries.

### 11.5 Failure Semantics
- **No Relevant Documents**: Returns empty chunks (`has_content = False`). For standard tasks, planning proceeds using the user request alone.
- **Retrieval Error**: Captured in `RetrievedContext.error`. If `knowledge_dependent=True`, planning fails closed with a descriptive `ValueError` rather than inventing hallucinated parameters.
- **Strict Mode**: `RAGContextRetriever.retrieve(query, strict=True)` raises exceptions immediately when caller requires strict failure propagation.

### 11.6 Observability & Tracing
- Structured `rag_context_attached` events are logged into SQLite via `TaskLogger` with `query`, `chunks_found`, `sources`, `scores`, and any retrieval `error`.
- Full traceability connects retrieved chunks to subsequent task execution.


