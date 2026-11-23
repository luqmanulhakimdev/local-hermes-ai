# Local Hermes AI v1.0 — System Architecture

## 1. System Overview

Local Hermes AI v1.0 is a local-first AI engineering system integrating:
- **Local LLM Inference**: Ollama running Qwen3 (`qwen3:4b-instruct-2507-q4_K_M`) for chat and planning, and `nomic-embed-text` for vector embeddings.
- **Persistent Conversational Memory**: SQLite-backed history and user preference store.
- **Local RAG Pipeline**: Document ingestion, chunking, SQLite vector storage, cosine similarity search, and context-grounded Q&A.
- **Safety-Hardened Automation Engine**: Multi-step task planner, AST-based tools, schema validation, human approval gates, retry policy, cancellation, persistence, and state recovery.
- **Hermes Agent Integration**: Safe subprocess adapter and high-level service bridge integrating the project with the local Hermes Agent (`v0.22.6`) without compromising core safety boundaries.

---

## 2. End-to-End Architecture

```text
                           ┌───────────────┐
                           │     User      │
                           └───────┬───────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │ Hermes Agent  │
                           │ Orchestration │
                           └───────┬───────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │ Hermes Integration  │
                        │   (src/hermes)      │
                        └──────────┬──────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │     Local Hermes AI Core    │
                    └──────────────┬──────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
             Conversation        Local             AI
                Memory            RAG          Automation
              (SQLite)             │            Agent
                                   │                │
                                   │                ▼
                                   │             Planner
                                   │          (TaskPlanner)
                                   │                │
                                   │                ▼
                                   │             Validator
                                   │          (TaskValidator)
                                   │                │
                                   │                ▼
                                   │             Approval
                                   │           (Fail-Closed)
                                   │                │
                                   │                ▼
                                   │             Executor
                                   │          (TaskExecutor)
                                   │                │
                                   │                ▼
                                   │              Tools
                                   │           (Allowlist)
                                   │                │
                                   └───────────────┐│
                                                   ▼▼
                                            TaskStore & Logs
                                            (SQLite Audit)
```

---

## 3. Subsystem Breakdown

### 3.1 Personal Agent & Memory (`src/agent.py`, `src/memory.py`)
- Provides conversational chat with persistent state in SQLite (`data/agent.db`).
- Tracks user facts (name, preferences, goals) across turns.
- Uses strict prompt boundaries and sanitized history extraction.

### 3.2 Retrieval-Augmented Generation (`src/rag/`)
- Ingests Markdown and plain text documents from `documents/`.
- Chunks text into bounded segments.
- Generates 768-dimensional embeddings via local `nomic-embed-text`.
- Stores vectors in SQLite (`data/rag.db`) with cosine similarity retrieval.
- Enforces similarity thresholds and context limits; abstains when relevant context is unavailable.
- Treats all retrieved text as **untrusted reference data**.

### 3.3 Automation Engine (`src/automation/`)
- **Planner (`TaskPlanner`)**: Converts requests into structured JSON `TaskPlan` models. If RAG context is supplied, formats it into isolated prompt sections with explicit negative constraints.
- **Validator (`TaskValidator`)**: Validates task structure, enforces maximum 5 steps, requires sequential step IDs, checks tool allowlists, and enforces backward-only step output references (`$step_N`).
- **Tool Registry (`ToolRegistry`)**: Maintains explicit allowlists with required and optional argument schema checks. Prevents unauthorized tool execution.
- **Human Approval Gate**: Sensitive tools flagged `requires_approval=True` halt execution into `AWAITING_APPROVAL` status. Prompts claiming prior approval fail closed; only explicit human approval permits execution.
- **Executor (`TaskExecutor`)**: Dispatches steps, resolves previous step references, bounds output size (`max_output_size`), enforces bounded execution timeouts, handles transient error retries, and supports cancellation.
- **Task Store (`TaskStore`)**: Persists task and step state transitions into SQLite (`data/automation.db`). Supports deterministic resumption of interrupted tasks without re-executing completed steps.
- **Logger (`TaskLogger`)**: Emits structured, machine-readable audit events with automatic secret redaction (`password`, `token`, `secret`, `api_key`).

### 3.4 Hermes Integration Layer (`src/hermes/`)
- **CLI Adapter (`HermesCLIAdapter`)**: Executes `hermes chat` in oneshot mode with captured stdout/stderr, strict timeouts, output truncation, and no `shell=True`.
- **Protocol Models (`HermesRequest`, `HermesResponse`)**: Typed and validated request/response contracts for operations: `run_automation`, `query_knowledge`, `get_task_status`, `resume_task`.
- **Service Bridge (`HermesService`)**: Maps Hermes requests to authoritative project modules.
- **One-Way Dependency**: Core modules never import Hermes; the core project remains 100% functional without Hermes.

---

## 4. Security Invariants

1. **No Arbitrary Execution**: Neither the LLM nor Hermes can invoke arbitrary shell commands or unregistered Python functions.
2. **Untrusted Context**: Text from RAG documents or user input cannot override planning rules or bypass approvals.
3. **Fail-Closed Approvals**: Missing handlers, non-boolean values, or LLM-generated assertions of approval fail closed.
4. **AST Calculator**: Mathematical expressions are evaluated via restricted Python AST traversal without calling `eval()`.
5. **Path Traversal Protection**: Filesystem tools restrict reads to permitted project paths.

---

## 5. Persistence and Recovery

- All tasks and steps transition through deterministic state machines (`pending` -> `running` -> `completed` / `failed` / `cancelled` / `awaiting_approval`).
- Interrupted or cancelled tasks can be resumed deterministically. Completed steps are loaded from `TaskStore` outputs and never re-executed.

---

## 6. Observability and Evaluation

- Complete task execution histories can be reconstructed from structured logs.
- Quantitative evaluation metrics measure plan validity, tool selection accuracy, execution outcome, recovery success, trace completeness, and approval compliance.
