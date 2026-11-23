# Local Hermes AI v1.0 — Release Notes

**Release Date:** November 2026  
**Version:** `1.0.0`  
**License:** MIT / Educational Portfolio Project  

---

## 1. Highlights & Major Capabilities

Local Hermes AI v1.0 is a complete, local-first AI Engineering portfolio project running on Ubuntu with Ollama, SQLite, and the Hermes Agent. It demonstrates production-grade AI engineering patterns across:

- **Local LLM & Multi-Turn Agent**: Conversational agent running on local Qwen3 (`qwen3:4b-instruct-2507-q4_K_M`) with persistent SQLite memory.
- **Local RAG Pipeline**: Ingestion, text chunking, embedding generation with `nomic-embed-text`, vector storage in SQLite, cosine similarity search, and context-grounded Q&A.
- **Hardened Automation Engine**: Multi-step task planner, schema validation, AST-based tools, fail-closed human approval gates, retry policy, cancellation, persistence, and state recovery.
- **Local Hermes Agent Integration**: Safe subprocess adapter and high-level service bridge enabling the local Hermes Agent (`v0.22.6`) to orchestrate automation and RAG while preserving all core safety boundaries.
- **Evaluation & Observability**: Complete execution tracing, structured machine-readable logs with secret redaction, and quantitative deterministic evaluation metrics.

---

## 2. Architecture & Safety Invariant

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

**Core Invariant**: Hermes is strictly an interface and orchestration layer. The Local Hermes AI core remains authoritative for safety, plan validation, tool allowlists, human approval, task execution, persistence, and observability.

---

## 3. Verified Verification Matrix

| Area | Status | Verified Component |
|---|:---:|---|
| **Local LLM Inference** | **PASS** | Ollama + Qwen3 (`qwen3:4b-instruct-2507-q4_K_M`) |
| **Persistent Memory** | **PASS** | SQLite conversational memory (`data/agent.db`) |
| **RAG Pipeline** | **PASS** | Document ingestion, chunking, SQLite vector storage, cosine similarity |
| **Automation Planning** | **PASS** | Structured JSON planning with isolated untrusted knowledge sections |
| **Task Validation** | **PASS** | Schema validation, sequential step IDs, step limit (5), backward-only references |
| **Tool Registry** | **PASS** | Explicit tool allowlist, argument schemas, AST-based calculator |
| **Human Approval** | **PASS** | Fail-closed human approval for sensitive actions |
| **Persistence & Recovery** | **PASS** | SQLite TaskStore, resume interrupted tasks without step re-execution |
| **Observability** | **PASS** | SQLite TaskLogger, secret redaction, TaskTrace / StepTrace |
| **Evaluation Suite** | **PASS** | Planning, tool selection, outcome, aggregate metrics, regression evaluation |
| **Hermes Integration** | **PASS** | Safe subprocess adapter, HermesRequest/Response protocol, health check |
| **Adversarial Security** | **PASS** | 11/11 threat vectors tested and contained |
| **Full Regression** | **PASS** | 475 tests, 0 failures, 0 errors |

---

## 4. Security Boundaries

- **No Arbitrary Execution**: Neither the model nor Hermes can execute arbitrary shell scripts or unrestricted Python code.
- **Untrusted Context**: Text from RAG documents or user input cannot override planning rules or bypass approvals.
- **Fail-Closed Human Approval**: Missing approval handlers, non-boolean approval responses, or LLM-generated assertions of approval fail closed.
- **AST Calculator**: Mathematical expressions are evaluated via restricted Python AST traversal without calling `eval()`.
- **Path Traversal Protection**: Filesystem tools restrict reads to permitted project paths.

---

## 5. Known Limitations

- **Local-Only Single-User Architecture**: Embedded SQLite databases and synchronous agent execution are designed for single-operator local environments.
- **Hermes CLI Latency**: Calling Hermes via subprocess adds process startup latency (~0.3s).
- **Deterministic Evaluation Boundary**: Synthetic golden datasets evaluate structural and deterministic properties; live generative outputs remain subject to local model variance.

---

## 6. Future Work (Beyond v1.0)

- Asynchronous distributed worker queues (Celery/Redis).
- Web-based user interface / dashboard.
- Hybrid vector search (dense embeddings + BM25 keyword search).
- Multi-user authentication and role-based access control.
- Cross-platform containerization.
