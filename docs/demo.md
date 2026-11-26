# Local Hermes AI v1.0 — Official Demonstration Workflow

This document provides a complete, reproducible, end-to-end demonstration workflow for **Local Hermes AI v1.0**.

Every step runs locally on Ubuntu with Ollama and Hermes Agent without external cloud dependencies or API keys.

---

## Prerequisites & Environment

Verify required components:

```bash
# 1. Verify Python version (3.14.x)
python3 --version

# 2. Verify Ollama service and models
ollama list
# Expected:
# - qwen3:4b-instruct-2507-q4_K_M
# - nomic-embed-text:latest

# 3. Verify Hermes Agent CLI (v0.22.6)
hermes --version
```

---

## Step-by-Step Demo Workflow

### Step 1: Ingest Project Knowledge into Local RAG Vector Store

Ingest permitted Markdown documents from the `documents/` directory into the local SQLite vector database (`data/rag.db`):

```bash
python3 -m src.rag.ingest
```

Expected output:
```text
Ingestion complete. Processed documents, generated embeddings using nomic-embed-text, and stored chunks in data/rag.db.
```

---

### Step 2: Verify Hermes Integration Health

Audit the local Hermes installation and Ollama connectivity:

```bash
python3 -m src.hermes --check
```

Expected output:
```json
{
  "status": "ok",
  "executable_exists": true,
  "version": "Hermes Agent v0.22.6 (2026.9.24) · stable · local f0d94882e89a",
  "ollama_reachable": true,
  "details": "Hermes Hermes Agent v0.22.6 ...; Ollama reachable=True"
}
```

---

### Step 3: Interactive Personal Agent (Workflow A & B)

Run the interactive local personal agent with SQLite memory:

```bash
python3 -m src.main
```

1. Enter user name.
2. Ask factual questions or store facts: `Remember that my primary coding language is Python`.
3. Retrieve remembered context in subsequent turns.
4. Type `exit` to quit.

---

### Step 4: Interactive Document Q&A with RAG (Workflow C)

Run the RAG question-answering CLI:

```bash
python3 -m src.rag.app
```

Ask questions grounded in the ingested documents:
- Query: `What are the core principles of AI engineering?`
- The system retrieves top matching chunks by cosine similarity, answers strictly from context, and provides citations.

---

### Step 5: Automation via Hermes Bridge (Workflow D & H)

Dispatch an automation task through the Hermes service bridge:

```bash
python3 -m src.hermes --run "What tools are available?"
```

Expected output:
```text
Status: completed
Message: Task completed successfully
Task ID: <uuid>
Data: {
  "status": "completed",
  "description": "List all available automation tools",
  "output": [
    "list_files",
    "list_tools",
    "read_file",
    "save_note",
    "search_notes",
    "summarize_text"
  ]
}
```

---

### Step 6: Knowledge-Grounded Automation with RAG (Workflow G & I)

Run an automation task that retrieves project knowledge before planning:

```bash
python3 -m src.hermes --run "Read project files and summarize" --rag
```

Workflow executed:
1. `RAGContextRetriever` retrieves relevant chunks from `data/rag.db`.
2. Chunks are formatted as isolated, untrusted reference material in `TaskPlanner`.
3. `TaskPlanner` generates a validated multi-step `TaskPlan` (`list_files` → `read_file` → `summarize_text`).
4. `TaskValidator` validates plan structure and tool allowlists.
5. `TaskExecutor` executes tools within resource and timeout boundaries (reading all permitted `.md`/`.txt` files in `documents/`).
6. Results and structured audit events are stored in SQLite (`data/automation.db`).

---

### Step 7: Human-in-the-Loop Approval Drill (Workflow E)

Attempt to run a task requiring approval:
- Sensitive operations (e.g. `delete_database` or tools flagged `requires_approval=True`) halt execution and enter `awaiting_approval` status.
- External prompts or LLM responses claiming "pre-approved" are rejected.
- Only explicit boolean approval from human operator allows sensitive tool execution.

---

### Step 8: Task State Inspection and Recovery (Workflow F)

Inspect the durable state of any executed task:

```bash
python3 -m src.hermes --status <task_id>
```

Resume an interrupted task:

```bash
python3 -m src.hermes --resume <task_id>
```

The system verifies:
- Completed steps are NOT rerun.
- Remaining steps continue to completion.
- Recovery events are logged to SQLite audit trails.

---

### Step 9: Run Full Automated Verification Suite

Run the complete regression suite covering unit, security, integration, and evaluation tests:

```bash
python3 -m unittest discover -s tests -v
```

Expected result:
```text
Ran 482 tests in ~8s
OK (0 failures, 0 errors)
```
