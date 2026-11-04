# Local Hermes AI

An experimental local AI agent environment built with Hermes Agent and Ollama.

## Project Goals

- Run AI models locally using Ollama.
- Explore AI agent architecture and tool calling.
- Learn Python and AI Engineering fundamentals.
- Experiment with local LLM workflows.
- Build practical AI projects and document the learning process.

## Tech Stack

- **OS**: Ubuntu Linux
- **Language**: Python 3.10+
- **LLM Runtime**: Ollama
- **Model**: Qwen3 (`qwen3:4b`)
- **Agent Framework**: Hermes Agent
- **Version Control & CI**: Git & GitHub

## Project Structure

```text
local-hermes-ai/
├── docs/
│   └── learning-roadmap.md     # Learning milestones and phases
├── experiments/                # Experimental scripts and prototypes
│   └── README.md
├── scripts/                    # Utility scripts
├── src/
│   ├── __init__.py
│   └── main.py                 # Local Hermes AI CLI Chatbot application
├── tests/
│   ├── __init__.py
│   └── test_main.py            # Unit test suite with mocks
├── requirements.txt            # Project dependencies
└── README.md
```

## Python LLM Application (`src/main.py`)

A lightweight, streaming interactive CLI chatbot application communicating directly with a local Ollama instance.

### Key Features

- **Streaming Responses**: Consumes Ollama's `/api/chat` streaming endpoint in real-time for immediate output.
- **Thinking Mode Control**: Prepends `/no_think` directive to focus responses directly without verbose reasoning traces when using Qwen3.
- **User Greeting & Validation**: Prompts for user name with fallback to `"User"`, validates non-empty prompt queries.
- **Resilient Error Handling**: Catches connection errors (with instructions to start the Ollama service), timeouts, HTTP errors, and general exceptions.
- **High Test Coverage**: Backed by a full unit test suite using `unittest` and `unittest.mock` without requiring external testing frameworks.

### Prerequisites

1. **Ollama**: Ensure Ollama is installed and running:
   ```bash
   ollama --version
   sudo systemctl start ollama   # or run: ollama serve
   ```

2. **Model**: Pull the local Qwen3 model (or model of choice):
   ```bash
   ollama pull qwen3:4b
   ```

### Setup & Installation

1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the chatbot from the project root:
```bash
python3 src/main.py
```

Example interaction:
```text
========================================
       LOCAL HERMES AI CHATBOT
========================================

Enter your name: Alice

Hello, Alice! Welcome to Local Hermes AI.
Feel free to ask the AI anything.

You: Explain how neural networks learn in simple terms.

AI: Neural networks learn by making predictions, comparing them to the correct answer, and adjusting internal connection weights to minimize errors over time...
```

### Running Unit Tests

Execute the unit test suite with:
```bash
python3 -m unittest discover tests
```

To run with verbose output:
```bash
python3 -m unittest -v tests/test_main.py
```

## Current Progress

- [x] Install Hermes Agent
- [x] Install Ollama
- [x] Run Qwen3 locally
- [x] Configure Hermes with a local model
- [x] Build first Python LLM application
- [ ] Experiment with tool calling
- [ ] Build a custom AI agent

## Project Status

Learning and experimentation in progress.
