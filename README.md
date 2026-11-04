# Local Hermes AI

An experimental local AI agent environment built with Hermes Agent, Ollama, and Python.

## Project Goals

- Run AI models locally using Ollama.
- Explore AI agent architecture, tool calling, and autonomous decision loops.
- Learn Python and AI Engineering fundamentals.
- Implement persistent memory and sandboxed system tools.
- Experiment with local LLM workflows and build practical portfolio agents.

## Tech Stack

- **OS**: Ubuntu Linux
- **Language**: Python 3.10+
- **LLM Runtime**: Ollama
- **Model**: Qwen3 (`qwen3:4b`)
- **Agent Framework**: Hermes Agent
- **Database**: SQLite (built-in persistent memory)
- **Testing**: Python `unittest` & `unittest.mock`
- **Version Control & CI**: Git & GitHub

## Project Structure

```text
local-hermes-ai/
├── data/                       # Local SQLite databases (gitignored)
├── docs/
│   └── learning-roadmap.md     # Learning milestones and phases
├── experiments/                # Experimental scripts and prototypes
│   └── README.md
├── scripts/                    # Utility scripts
├── src/
│   ├── __init__.py
│   ├── agent.py                # Multi-turn conversational AI agent
│   ├── main.py                 # Streaming CLI chatbot
│   ├── memory.py               # Persistent SQLite memory store
│   ├── personal_agent.py       # Autonomous personal assistant with tool calling
│   └── tools/
│       ├── __init__.py
│       ├── calculator.py       # Safe mathematical evaluator (restricted AST)
│       └── system_tools.py     # Safe time, file listing, and reading tools
├── tests/
│   ├── __init__.py
│   ├── test_agent.py           # Unit tests for multi-turn agent
│   ├── test_calculator.py      # Unit tests for safe calculator
│   ├── test_main.py            # Unit tests for streaming chatbot
│   ├── test_memory.py          # Unit tests for SQLite memory store
│   ├── test_personal_agent.py  # Unit tests for autonomous tool-calling agent
│   └── test_system_tools.py    # Unit tests for system tools
├── requirements.txt            # Project dependencies
└── README.md
```

## Python Applications & Modules

### 1. Personal AI Agent (`src/personal_agent.py`)
An autonomous personal AI assistant featuring:
- **Function Calling**: Integrates with Ollama's tool calling API. The model automatically selects and invokes tools when necessary.
- **ReAct Decision Loop**: Supports up to 5 iterative tool execution rounds before outputting final answers.
- **Persistent Long-Term Memory**: Automatically loads saved memories into system prompt context and remembers past conversations across sessions via SQLite.
- **Built-in CLI Slash Commands**:
  - `/remember key=value` – Store user facts or preferences.
  - `/memories` – View all currently stored memories in JSON format.
  - `/forget key` – Delete a specific stored key.
  - `/reset` – Clear active conversation message history while preserving memories.
  - `/exit` – Exit the application safely.

### 2. Conversational Agent (`src/agent.py`)
A multi-turn conversational agent with in-memory message history tracking:
- Maintains context across multiple queries in a session.
- Provides `reset` to clear history and `exit` to terminate.
- Gracefully handles connection drops and invalid model outputs.

### 3. Streaming CLI Chatbot (`src/main.py`)
A fast, lightweight interactive streaming chat interface:
- Real-time token streaming using Ollama's `/api/chat` streaming response.
- Injects `/no_think` directive for concise direct answers with Qwen3.
- User greeting, input validation, and detailed connection error diagnosis.

### 4. Persistent Memory Store (`src/memory.py`)
SQLite-backed storage class (`Memory`):
- `messages` table: Stores chronological interaction history (`role`, `content`, `created_at`).
- `memories` table: Stores persistent key-value pairs with conflict resolution (`UPSERT`).
- Supports dependency injection with custom database paths for isolated unit testing.

### 5. Sandboxed Agent Tools (`src/tools/`)
- **Calculator (`src/tools/calculator.py`)**: Safe mathematical expression evaluation using a restricted Python Abstract Syntax Tree (AST). Rejects unsafe builtins, function calls, and dangerous operations, with strict limits on expression length, exponent size, and result magnitude.
- **System Tools (`src/tools/system_tools.py`)**:
  - `get_current_time()`: Retrieves local machine date, time, and timezone.
  - `list_project_files()`: Scans repository files while filtering out `.git`, `.venv`, `__pycache__`, and `.env`.
  - `read_project_file(filename)`: Reads project file contents with path-traversal protection and file-size guardrails (<100 KB).

---

## Prerequisites

1. **Ollama**: Ensure Ollama is installed and running:
   ```bash
   ollama --version
   sudo systemctl start ollama   # or run: ollama serve
   ```

2. **Model**: Pull the local Qwen3 model:
   ```bash
   ollama pull qwen3:4b
   ```

---

## Setup & Installation

1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Applications

### Run Personal Agent (Tools + Memory)
```bash
python3 src/personal_agent.py
```
Example interaction:
```text
==================================================
          LOCAL PERSONAL AI AGENT
==================================================

Special commands:
/remember key=value
/memories
/forget key
/reset
/exit

AI is ready!

You: /remember name=Luqman
AI: Information saved successfully.

You: What is 25 * 18, and what time is it right now?
[AGENT] Selected tool: calculate
[TOOL] calculate executed successfully.
[AGENT] Selected tool: get_current_time
[TOOL] get_current_time executed successfully.

AI: 25 * 18 is 450. The current local time is 19:35:00 WIB on 2026-11-04.
```

### Run Multi-Turn Agent
```bash
python3 src/agent.py
```

### Run Streaming Chatbot
```bash
python3 src/main.py
```

---

## Running Unit Tests

The project includes 63 comprehensive unit tests covering all tools, memory operations, agents, and error handlers with 100% mocked isolation.

Execute all unit tests:
```bash
python3 -m unittest discover tests
```

To run with verbose output:
```bash
python3 -m unittest -v discover tests
```

Or run individual test modules:
```bash
python3 -m unittest -v tests/test_personal_agent.py
python3 -m unittest -v tests/test_calculator.py
python3 -m unittest -v tests/test_system_tools.py
python3 -m unittest -v tests/test_memory.py
python3 -m unittest -v tests/test_agent.py
python3 -m unittest -v tests/test_main.py
```

---

## Current Progress

- [x] Install Hermes Agent
- [x] Install Ollama
- [x] Run Qwen3 locally
- [x] Configure Hermes with a local model
- [x] Build first Python LLM application
- [x] Build multi-turn conversational agent
- [x] Implement persistent SQLite memory
- [x] Implement safe agent tools (Calculator & System Tools)
- [x] Build autonomous personal AI agent with tool calling
- [x] 100% unit test coverage for Python modules (63 tests)

## Project Status

Learning and experimentation in progress.
