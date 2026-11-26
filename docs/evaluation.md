# AI Engineering Evaluation Guide

This document describes the **AI Engineering Evaluation** framework (`src/evaluation/`) in Local Hermes AI.

---

## 1. Why Standard Unit Tests Are Insufficient

Standard software unit tests verify deterministic code paths (`f(x) == y`). AI applications introduce non-deterministic model outputs, retrieval quality variance, multi-step tool trajectories, and prompt injection risks. Evaluation systematically measures whether the AI system is **correct, reliable, safe, grounded, and stable across changes**.

---

## 2. Deterministic vs. Probabilistic Evaluation

| Dimension | Deterministic Evaluation | Probabilistic Evaluation (`LLMJudge`) |
|---|---|---|
| **Reproducibility** | 100% reproducible | Model-dependent & prompt-dependent |
| **Examples** | Tool selection, step count, step order, JSON format, approval state, source IDs, abstention markers | Semantic correctness, natural-language style, nuanced relevance |
| **Role** | Release gates & regression checks | Diagnostic insight & qualitative scoring |
| **State Mutation** | None | None (read-only) |

`src/evaluation/llm_eval.py` separates `evaluate_llm_deterministic()` from `LLMJudge(is_probabilistic=True)`.

---

## 3. Core Capabilities

### 3.1 Golden Datasets (`src/evaluation/golden_dataset.py`)
- `GoldenCase` & `GoldenDataset` with strict schema validation (no empty IDs/inputs, no duplicate IDs, consistent `expected_step_count` and `expected_tools`).
- `DEFAULT_GOLDEN_DATASET` (`v1.0.0`) covers 4 domains:
  - **LLM**: factual Q&A, JSON instruction following, abstention, out-of-scope refusal.
  - **RAG**: answerable queries, source-specific queries, irrelevant/insufficient-context abstention.
  - **Automation**: single-step, multi-step (`list_files -> read_file -> summarize_text`), approval-required, recovery/resume.
  - **Security**: prompt injection, unauthorized tool, approval bypass, `$step_99` reference tampering, unexpected arguments, path traversal.

### 3.2 Agent Trajectory Evaluation (`src/evaluation/trajectory_eval.py`)
Evaluates the full trajectory rather than only the final answer:
- Tool selection & step ordering
- Step count & argument schema validity
- Approval compliance (`evaluate_approval_compliance`)
- Recovery trajectory (`evaluate_recovery_success`)
- Final task status (`TaskStatus`)

### 3.3 RAG Evaluation (`src/evaluation/rag_eval.py`)
Explicitly separates failure stages:
- **`retrieval_failure`**: Expected source documents were not retrieved.
- **`grounding_failure`**: Relevant documents were retrieved, but the answer ignored them or missed expected facts.
- **`abstention_failure`**: The system fabricated an answer instead of abstaining when context was insufficient.

### 3.4 Regression Evaluation (`src/evaluation/regression.py`)
`compare_regression(baseline, current, allowed_drop=0.02)` compares baseline vs. current metrics and classifies each as:
- `improved`, `unchanged`, `regressed`, or `unknown` (when either value is `None` — missing evidence is never treated as success).

### 3.5 Failure Analysis & Clustering (`src/evaluation/failure_analysis.py`)
- Classifies failures into explicit categories (`planning_error`, `tool_selection_error`, `argument_error`, `retrieval_error`, `grounding_error`, `hallucination`, `execution_error`, `approval_error`, `safety_violation`, `recovery_error`, `timeout`, `resource_limit`, `unknown`).
- Separates **`observed_facts`** from **`inferred_root_cause`** with explicit confidence levels.
- `cluster_failures()` aggregates counts by category and affected subsystem to guide engineering fixes.

---

## 4. Running Evaluation

Run all evaluation tests deterministically:

```bash
python3 -m unittest tests/test_eval_*.py -v
```

Run the full project regression suite:

```bash
python3 -m unittest discover -s tests -v
```
