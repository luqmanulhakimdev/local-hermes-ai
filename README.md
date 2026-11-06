# Local Hermes AI

A local AI engineering laboratory for building and experimenting with LLM-powered applications, AI agents, tool calling, memory, and retrieval-augmented generation.

The project runs AI models locally using **Ollama + Qwen3** and uses Python to explore how modern AI applications are designed, tested, and secured.

> **Goal:** Learn AI Engineering by building real systems locally — from basic LLM applications to tool-using agents and RAG pipelines.

---

## 🚀 Project Overview

Local Hermes AI is an ongoing AI Engineering portfolio project.

The project currently focuses on:

- Local LLM inference
- LLM application development
- Prompt engineering
- Conversation history
- Tool calling / function calling
- Agent decision loops
- Persistent memory
- Sandboxed local tools
- Automated testing
- Retrieval-Augmented Generation (RAG)
- Semantic search
- Retrieval and answer quality evaluation

The long-term goal is to build a capable **local personal AI system** while documenting the engineering decisions behind it.

### Project Philosophy

This project follows several principles:

- **Local-first:** Run models and store application data locally whenever practical.
- **Learn by building:** Implement core AI application concepts using Python.
- **Understand the fundamentals:** Learn how components work instead of relying entirely on high-level frameworks.
- **Security by design:** Apply basic security controls to tools, file access, and data handling.
- **Test and evaluate:** Verify application behavior through automated tests and experiments.
- **Incremental development:** Build the system step by step and document its limitations.

---

## 🧠 Current Architecture

The repository currently contains two main application projects:

1. Local Personal AI Agent
2. Document Q&A with Retrieval-Augmented Generation (RAG)

### 1. Personal AI Agent Architecture

The personal agent follows this architecture:

```text
                        ┌──────────────────┐
                        │       User       │
                        └────────┬─────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │   Python AI Agent   │
                      └──────────┬──────────┘
                                 │
                          Agent Decision
                              Loop
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
         ┌────────────┐   ┌────────────┐   ┌─────────────┐
         │ Calculator │   │ Time Tool  │   │ File Tools  │
         └────────────┘   └────────────┘   └─────────────┘
                │                │                │
                └────────────────┼────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │       Ollama        │
                      │       Qwen3         │
                      └──────────┬──────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │    SQLite Memory    │
                      └─────────────────────┘
```

The agent follows an iterative loop:

```text
User Request
     ↓
LLM Reasoning
     ↓
Tool Required?
  ↙       ↘
Yes        No
 ↓          ↓
Execute    Final Answer
Tool
 ↓
Tool Result
 ↓
LLM
 ↓
Final Answer
```

The LLM determines whether a tool is needed. If a tool is selected, the Python application validates and executes it, then sends the result back to the model.

The loop continues until the model produces a final response or the configured tool execution limit is reached.

### 2. RAG Architecture

The RAG application uses a separate pipeline for document ingestion and question answering.

**Document ingestion:**

```text
       ┌──────────────────────────┐
       │     Local Documents      │
       │      Markdown / TXT      │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │      Document Loader     │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │       Text Chunker       │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │      Embedding Model     │
       │     nomic-embed-text     │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │     SQLite Vector Store  │
       └──────────────────────────┘
```

**Question answering:**

```text
       ┌──────────────────────────┐
       │       User Question      │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │      Query Embedding     │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │     Similarity Search    │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │    Retrieved Context     │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │       Qwen3 LLM          │
       └────────────┬─────────────┘
                    │
                    ▼
       ┌──────────────────────────┐
       │     Answer + Sources     │
       └──────────────────────────┘
```

The ingestion pipeline prepares documents and stores their embeddings.

The question-answering pipeline converts a user question into an embedding, retrieves relevant document chunks, and passes the retrieved context to the LLM.

The LLM is instructed to answer using the provided context rather than relying on unsupported information.

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Operating System | Ubuntu Linux |
| Language | Python 3 |
| LLM Runtime | Ollama |
| Personal Agent Model | Qwen3 |
| RAG Chat Model | `qwen3:4b-instruct-2507-q4_K_M` |
| Embedding Model | `nomic-embed-text` |
| Agent Framework | Custom Python implementation |
| External Agent Experiment | Hermes Agent |
| Database | SQLite |
| Vector Search | Cosine Similarity |
| HTTP Client | Requests |
| Testing | `unittest`, `unittest.mock` |
| Version Control | Git |
| Platform | GitHub |

---

## 📁 Project Structure

```text
local-hermes-ai/
│
├── data/
│   └── *.db                     # Local SQLite databases (gitignored)
│
├── docs/
│   ├── architecture.md          # Technical architecture documentation
│   └── learning-roadmap.md      # AI Engineering learning roadmap
│
├── documents/
│   ├── ai-engineering.md        # RAG knowledge source
│   └── llm-basics.md            # RAG knowledge source
│
├── experiments/
│   └── README.md                # Experimental scripts and prototypes
│
├── src/
│   ├── __init__.py
│   ├── agent.py                 # Multi-turn conversational agent
│   ├── main.py                  # Streaming CLI chatbot
│   ├── memory.py                # Persistent SQLite memory
│   ├── personal_agent.py        # Tool-calling personal AI agent
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── calculator.py        # Restricted AST calculator
│   │   └── system_tools.py      # Time and sandboxed file tools
│   │
│   └── rag/
│       ├── __init__.py
│       ├── app.py               # Interactive RAG application
│       ├── chunker.py           # Document loading and chunking
│       ├── embeddings.py        # Ollama embedding integration
│       ├── retriever.py         # Cosine similarity utilities
│       ├── vector_store.py      # SQLite vector storage and search
│       ├── ingest.py            # Document ingestion pipeline
│       ├── qa.py                # RAG question-answering pipeline
│       └── evaluation.py        # Retrieval and answer evaluation
│
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_calculator.py
│   ├── test_main.py
│   ├── test_memory.py
│   ├── test_personal_agent.py
│   ├── test_system_tools.py
│   ├── test_rag_chunker.py
│   ├── test_rag_retriever.py
│   └── test_rag_qa.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

### Data Directory

The `data/` directory contains local SQLite databases.

Current databases include:

| Database | Purpose |
|---|---|
| `agent.db` | Conversation history and persistent agent memory |
| `rag.db` | Document chunks and their embeddings |

Database files are excluded from Git because they contain local application data and can be regenerated.

---

# 🤖 Applications

## 1. Local Personal AI Agent

**File:** `src/personal_agent.py`

The main AI agent implementation.

This application demonstrates how an LLM can interact with external Python functions through tool calling.

### Features

#### Function Calling

Uses Ollama's tool calling interface to allow the LLM to select available Python tools.

The application handles tool execution and returns the results to the model.

#### Agent Decision Loop

Supports iterative tool execution with a configurable maximum number of tool rounds.

The agent can select a tool, receive its result, and continue processing the original request.

#### Persistent Memory

Stores conversation history and user-defined memories using SQLite.

Memory remains available after the application is restarted.

#### Sandboxed Tools

Provides controlled access to:

- Calculator
- Current time
- Project files

#### CLI Commands

```text
/remember key=value
/memories
/forget key
/reset
/exit
```

### Example

```text
You: /remember name=Luqman

AI: Information saved successfully.

You: What is 25 * 18, and what time is it right now?

[AGENT] Selected tool: calculate
[TOOL] calculate executed successfully.

[AGENT] Selected tool: get_current_time
[TOOL] get_current_time executed successfully.

AI: 25 * 18 is 450. The current local time is ...
```

### Engineering Concepts

This project explores:

- LLM tool calling
- Function schemas
- Agent orchestration
- Tool execution
- Conversation state
- Persistent memory
- Error handling
- Input validation
- Basic application security

---

## 2. Multi-Turn Conversational Agent

**File:** `src/agent.py`

A simpler agent implementation focused on understanding conversation history and LLM interaction.

### Features

- Maintains multi-turn context
- Uses system prompts
- Handles conversation resets
- Handles connection failures
- Sends messages through the Ollama API
- Demonstrates the fundamentals of LLM conversation state

### Learning Objectives

This application provides a foundation for understanding how messages are structured and how conversation history is passed to a language model.

It also demonstrates why a stateless LLM API request needs application-side history management to support multi-turn conversations.

---

## 3. Streaming CLI Chatbot

**File:** `src/main.py`

A lightweight LLM application demonstrating direct interaction with the Ollama API.

### Features

- Real-time streaming responses
- User input validation
- Error handling
- Local Qwen3 inference
- `/no_think` directive for concise responses

### Learning Objectives

- Understand basic LLM API integration
- Handle streaming responses
- Process incremental output
- Handle network and model errors
- Build a simple terminal-based AI application

---

## 4. Document Q&A with Retrieval-Augmented Generation (RAG)

**Directory:** `src/rag/`

A local document question-answering system using Retrieval-Augmented Generation.

The application retrieves relevant information from local documents and uses the retrieved context to generate answers with a locally hosted language model.

Instead of relying only on the knowledge stored in the LLM parameters, the application provides relevant document content at inference time.

### Features

- Load Markdown and text documents
- Split documents into smaller chunks
- Generate embeddings using `nomic-embed-text`
- Store document chunks and embeddings in SQLite
- Retrieve relevant chunks using cosine similarity
- Generate answers using Qwen3 through Ollama
- Include source document names and similarity scores
- Reject questions when no sufficiently relevant context is found
- Evaluate retrieval performance using a small test dataset
- Evaluate generated answers using expected keyword coverage
- Run dedicated RAG unit tests independently of live Ollama inference

### RAG Components

#### A. Document Loading

**File:** `src/rag/chunker.py`

Loads text from local documents.

The initial implementation supports:

- Markdown (`.md`)
- Plain text (`.txt`)

The document loader reads the file content before passing it to the chunking process.

#### B. Text Chunking

**File:** `src/rag/chunker.py`

Splits document text into smaller chunks.

The current implementation uses word-based chunking.

Two main parameters control the process:

| Parameter | Description |
|---|---|
| `chunk_size` | Maximum number of words in a chunk |
| `overlap` | Number of words shared between consecutive chunks |

Example:

```text
Original Document:

AI Engineering is the process of building
reliable AI-powered applications.

LLMs can understand and generate text.

             ↓

Chunk 1:
AI Engineering is the process of building
reliable AI-powered applications.

Chunk 2:
reliable AI-powered applications.
LLMs can understand and generate text.
```

Overlap helps preserve context between adjacent chunks.

The current chunker uses word-based splitting. It does not yet implement advanced semantic or structure-aware chunking.

#### C. Embedding Generation

**File:** `src/rag/embeddings.py`

Uses Ollama's embedding API with:

```text
nomic-embed-text
```

An embedding represents text as a numerical vector.

The current embedding model produces vectors with 768 dimensions.

Example concept:

```text
"Large Language Models process tokens"

                ↓

         Embedding Model

                ↓

[0.012, -0.034, 0.056, ..., 0.021]
```

These vectors allow the application to compare text based on semantic similarity.

#### D. Vector Storage

**File:** `src/rag/vector_store.py`

Stores document chunks and their embeddings in SQLite.

The current database table is:

```sql
CREATE TABLE document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    chunk_index INTEGER,
    content TEXT,
    embedding TEXT,
    UNIQUE(source, chunk_index)
);
```

Embeddings are serialized as JSON before being stored in SQLite.

The vector store provides methods to:

- Add document chunks
- Replace previously indexed chunks from a source
- Store embeddings
- Search for similar chunks
- Return similarity scores and source information

SQLite is used as a lightweight local storage solution. Similarity calculations are currently performed in Python rather than through a dedicated vector database extension.

#### E. Semantic Retrieval

**Files:** `src/rag/retriever.py` and `src/rag/vector_store.py`

The retrieval process compares the question embedding against stored document embeddings.

The current implementation uses cosine similarity.

The cosine similarity formula is:

\[
\text{similarity}(A,B) =
\frac{A \cdot B}{\|A\| \|B\|}
\]

A higher score indicates that two vectors point in a more similar direction.

The vector store:

1. Converts the user question into an embedding.
2. Loads stored document embeddings.
3. Calculates cosine similarity.
4. Applies a similarity threshold.
5. Sorts results by similarity.
6. Returns the top relevant chunks.

The current retrieval configuration uses:

```python
top_k = 3
threshold = 0.65
```

These values are initial experimental settings, not universal optimal values.

#### F. RAG Question Answering

**File:** `src/rag/qa.py`

Combines retrieved document chunks with a user question and sends the context to Qwen3.

The system prompt instructs the model to:

- Answer in Indonesian
- Use only the provided context
- Avoid inventing facts
- Say when information is unavailable
- Prefer concise answers

If retrieval returns no relevant chunks, the application returns:

```text
Tidak ditemukan informasi yang relevan.
```

The LLM is not called when retrieval produces no results.

When relevant context is found, the application generates an answer and includes source document names and similarity scores.

#### G. Document Ingestion

**File:** `src/rag/ingest.py`

The ingestion script processes supported documents inside the `documents/` directory.

The pipeline:

```text
Documents Directory
        ↓
Find .md and .txt Files
        ↓
Load Document Content
        ↓
Split Into Chunks
        ↓
Generate Embeddings
        ↓
Save to SQLite
        ↓
Knowledge Base Ready
```

When a source document is re-ingested, its previous chunks are replaced with newly generated chunks and embeddings.

This keeps the indexed content synchronized with the document being processed.

#### H. Interactive RAG Application

**File:** `src/rag/app.py`

Provides an interactive terminal interface for asking questions about the indexed documents.

Users can ask questions in Indonesian and receive answers generated from retrieved document context.

Example:

```text
$ python3 -m src.rag.app

You: Apa itu token dalam Large Language Model?

Assistant:
Token adalah satuan teks kecil yang diproses oleh
suatu model bahasa. Sebuah token dapat mewakili
kata, bagian dari kata, atau tanda baca.

Sumber:
- llm-basics.md (similarity: 0.7689)
```

Example of a question outside the knowledge base:

```text
You: Apa ibu kota Jepang?

Assistant:
Tidak ditemukan informasi yang relevan.
```

### RAG Evaluation

**File:** `src/rag/evaluation.py`

The project includes retrieval evaluation, answer quality evaluation, and negative-answer evaluation.

#### Retrieval Evaluation

The retrieval evaluation dataset currently contains six test cases:

| Test Case | Expected Source |
|---|---|
| What is a token in an LLM? | `llm-basics.md` |
| What is a Large Language Model? | `llm-basics.md` |
| How does RAG work? | `ai-engineering.md` |
| What is AI Engineering? | `ai-engineering.md` |
| What is the capital of Japan? | No source expected |
| Who was the first president of Indonesia? | No source expected |

The evaluation checks whether the expected source documents are retrieved.

**Initial retrieval results:**

| Metric | Result |
|---|---:|
| Average Precision@3 | 0.92 |
| Average Recall@3 | 1.00 |
| Test Cases | 6 |

These results use a custom source-level scoring method.

For questions with expected sources, the evaluation compares the expected source set against the retrieved source set.

For questions with no expected source, an empty retrieval result is treated as a successful rejection.

#### Answer Quality Evaluation

Answer quality is evaluated using expected keyword coverage across four positive question-answer test cases.

The metric checks how many expected keywords appear in the generated answer.

**Results:**

| Metric | Result |
|---|---:|
| Average Keyword Coverage | 0.92 |
| Positive Answer Test Cases | 4 |

Keyword coverage is a simple lexical metric. It checks whether expected keywords appear in the generated answer, but it does not fully measure semantic correctness or answer faithfulness.

For example, an answer may use a synonym instead of an expected keyword and still be semantically correct.

#### Negative Answer Evaluation

The system is also tested with questions that should not be answerable from the indexed documents.

| Metric | Result |
|---|---:|
| Negative Answer Tests | 2 |
| Passed | 2/2 |

Both unsupported questions correctly returned:

```text
Tidak ditemukan informasi yang relevan.
```

#### Evaluation Limitations

- The evaluation dataset is small.
- Retrieval metrics are calculated at the source-document level, not individual chunk level.
- The custom handling of no-answer cases affects the average scores.
- Keyword coverage does not fully measure semantic answer quality.
- Retrieval accuracy does not automatically guarantee answer correctness.
- Answer faithfulness still needs a more comprehensive evaluation process.
- Results may vary depending on the language model and its generation behavior.

These results should be treated as an initial engineering experiment, not a standardized benchmark.

### RAG Unit Tests

Dedicated RAG unit tests are located in:

```text
tests/
├── test_rag_chunker.py
├── test_rag_retriever.py
└── test_rag_qa.py
```

The tests cover:

| Test Module | Areas Tested |
|---|---|
| `test_rag_chunker.py` | Chunk creation, chunk size, invalid chunk size, invalid overlap |
| `test_rag_retriever.py` | Identical, orthogonal, opposite, mismatched, and empty vectors |
| `test_rag_qa.py` | Empty questions, missing context, generated answers, source citations |

The QA tests use `unittest.mock` to replace the vector store and HTTP request. This allows the QA behavior to be tested without making actual Ollama requests.

The dedicated RAG test suite currently contains **12 passing tests**.

### Current RAG Limitations

The current implementation is intentionally simple and designed for learning.

Known limitations include:

- Word-based chunking rather than semantic chunking
- SQLite storage with in-memory cosine similarity calculations
- No approximate nearest-neighbor index
- Small evaluation dataset
- No dedicated answer faithfulness evaluation
- No advanced reranking
- No document update detection beyond re-ingestion
- No web-based user interface

These are potential areas for future improvements.

---

# 🧩 Agent Tools

## Calculator

**File:** `src/tools/calculator.py`

The calculator does **not** use unrestricted Python `eval()`.

Instead, expressions are parsed using Python's Abstract Syntax Tree (AST), and only explicitly allowed operations are executed.

Supported operations include:

```text
+
-
*
/
%
**
```

Additional guardrails limit:

- Expression length
- Exponent size
- Result magnitude
- Unsupported AST nodes

This reduces the risk of arbitrary code execution through calculator input.

---

## System Tools

**File:** `src/tools/system_tools.py`

### `get_current_time()`

Returns:

- Local date
- Local time
- Timezone

### `list_project_files()`

Lists project files while excluding sensitive or unnecessary directories such as:

```text
.git
.venv
__pycache__
.env
```

### `read_project_file(filename)`

Reads text files inside the project directory.

Security controls include:

- Path traversal protection
- Repository boundary restriction
- File size limit

These tools allow the agent to interact with a controlled part of the local development environment.

---

# 💾 Persistent Memory

The personal agent uses SQLite for local persistent storage.

Two tables are currently used:

## `messages`

Stores conversation history:

```text
id
role
content
created_at
```

## `memories`

Stores persistent key-value information:

```text
id
memory_key
memory_value
```

Example:

```text
name = Luqman
goal = Become an AI Engineer
interest = Local LLMs
```

Unlike in-memory conversation history, SQLite data survives application restarts.

### Memory Operations

The memory implementation supports:

- Saving conversation messages
- Retrieving recent conversation history
- Saving user-defined memories
- Retrieving stored memories
- Forgetting individual memories
- Clearing conversation history

Memory is managed by the Python application rather than being stored directly inside the LLM.

---

# 🔐 Security & Engineering Decisions

Security is treated as part of the application design rather than an afterthought.

## Restricted Calculator

The calculator uses AST parsing instead of unrestricted `eval()`.

Only explicitly supported mathematical operations are allowed.

## Tool Allowlist

The LLM can only invoke explicitly registered tools.

Tool execution is handled by the application rather than allowing the model to execute arbitrary Python code.

## File Sandbox

File tools are restricted to the project directory.

## Path Traversal Protection

Requests attempting to access files outside the project root are rejected.

## File Size Guardrail

Large files are rejected before being loaded into the LLM context.

## Local-First Design

Models and memory run locally, reducing the need to send project data to external LLM APIs.

## Request Timeouts

HTTP requests to Ollama use timeouts to avoid waiting indefinitely when a model service is unavailable or unresponsive.

## RAG Context Restriction

The RAG system instructs the LLM to answer using retrieved context only.

However, prompt instructions alone cannot guarantee that a model will never generate unsupported information. Answer faithfulness requires further testing.

---

# 🧪 Testing

The project uses Python's built-in testing framework:

```bash
python3 -m unittest discover tests
```

Verbose mode:

```bash
python3 -m unittest discover -v tests
```

Individual test modules:

```bash
python3 -m unittest -v tests.test_personal_agent
python3 -m unittest -v tests.test_calculator
python3 -m unittest -v tests.test_system_tools
python3 -m unittest -v tests.test_memory
python3 -m unittest -v tests.test_agent
python3 -m unittest -v tests.test_main
```

Run the dedicated RAG unit tests:

```bash
python3 -m unittest -v \
tests.test_rag_chunker \
tests.test_rag_embeddings \
tests.test_rag_retriever \
tests.test_rag_vector_store \
tests.test_rag_qa \
tests.test_rag_ingest \
tests.test_rag_app \
tests.test_rag_evaluation
```

### Current Unit Test Results

The complete test suite currently contains **110 passing tests** with **98% code coverage**.

| Test Group | Tests |
|---|---:|
| Personal Agent & supporting components | 63 |
| RAG Chunker | 6 |
| RAG Embeddings | 4 |
| RAG Retriever | 10 |
| RAG Vector Store | 6 |
| RAG QA | 3 |
| RAG Ingestion | 4 |
| RAG CLI App | 6 |
| RAG Evaluation | 8 |
| **Total** | **110** |

Latest full test execution:

```text
Ran 110 tests in 0.112s

OK
```

Tested areas include:

- Agent behavior
- Tool execution
- Calculator validation
- SQLite memory operations
- File-system guardrails
- Error handling
- Input validation
- RAG chunking
- Cosine similarity
- RAG question-answering behavior
- Source citations

The QA unit tests use mocks, so they do not require live LLM inference.

> Test count and code coverage are different metrics. Code coverage should only be reported when measured with a coverage tool such as `coverage.py`.

### RAG Evaluation

RAG evaluation is performed separately from the unit test suite:

```bash
python3 -m src.rag.evaluation
```

This script evaluates retrieval behavior, generated answer keyword coverage, and unsupported-question handling using the small evaluation dataset described in the RAG section.

The evaluation makes actual requests to the local Ollama service, unlike the mocked RAG QA unit tests.

---

### RAG Evaluation

The RAG system includes retrieval and answer quality evaluation.

#### Retrieval Evaluation

The retrieval evaluation uses 6 test cases:
- 4 questions with expected document sources
- 2 questions that should not retrieve any document

Results:

| Metric | Result |
|---|---:|
| Average Precision@3 | 0.92 |
| Average Recall@3 | 1.00 |

#### Answer Quality Evaluation

Answer quality is evaluated using keyword coverage across 4 questions.

Results:

| Metric | Result |
|---|---:|
| Average Keyword Coverage | 0.92 |
| Negative Answer Tests | 2/2 PASS |

Keyword coverage is a simple lexical metric. It checks whether expected keywords appear in the generated answer. It does not measure semantic correctness.

#### Evaluation Limitations

- The evaluation dataset is small.
- Retrieval metrics are calculated at the source level.
- Keyword coverage does not fully measure answer quality.
- Results may vary depending on the language model.

# ⚙️ Installation

## Prerequisites

- Ubuntu Linux or another compatible operating system
- Python 3
- Ollama
- Git

### 1. Install Ollama

Install Ollama from its official website:

[https://ollama.com/](https://ollama.com/)

Check the installation:

```bash
ollama --version
```

Make sure the Ollama service is running.

On Ubuntu systems using systemd:

```bash
sudo systemctl start ollama
```

### 2. Download the Required Models

For the personal agent, the original Qwen3 model is:

```bash
ollama pull qwen3:4b
```

For the current RAG implementation, download the chat model:

```bash
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

Download the embedding model:

```bash
ollama pull nomic-embed-text
```

The chat model generates answers, while the embedding model converts documents and questions into vectors.

### 3. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/local-hermes-ai.git

cd local-hermes-ai
```

Replace `YOUR_USERNAME` with your GitHub username.

### 4. Create a Python Virtual Environment

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Applications

Run commands from the repository root directory with the virtual environment activated.

Make sure Ollama is running before starting the applications.

## Personal AI Agent

```bash
python3 -m src.personal_agent
```

## Conversational Agent

```bash
python3 -m src.agent
```

## Streaming CLI Chatbot

```bash
python3 -m src.main
```

## RAG Document Ingestion

Before asking questions, index the documents:

```bash
python3 -m src.rag.ingest
```

This processes supported files in the `documents/` directory and stores their chunks and embeddings in SQLite.

## RAG Interactive Application

```bash
python3 -m src.rag.app
```

## RAG Retrieval and Answer Evaluation

```bash
python3 -m src.rag.evaluation
```

## Full Unit Test Suite

```bash
python3 -m unittest discover -v tests
```

### Typical RAG Workflow

Whenever you add or update documents:

```bash
# 1. Add or update files inside documents/

# 2. Run document ingestion
python3 -m src.rag.ingest

# 3. Start the RAG application
python3 -m src.rag.app
```

The ingestion process updates the corresponding document chunks in the local vector store.

---

# 📚 Learning Roadmap

For the detailed learning plan, see [docs/learning-roadmap.md](docs/learning-roadmap.md).

For technical architecture details, see [docs/architecture.md](docs/architecture.md).

## Phase 1 — Local AI Environment

- [x] Linux development environment
- [x] Install Ollama
- [x] Run Qwen3 locally
- [x] Configure Hermes Agent
- [x] Set up Python virtual environment

## Phase 2 — LLM Fundamentals

- [x] Python LLM application
- [x] Ollama API integration
- [x] Prompt engineering
- [x] Conversation history
- [x] Context windows
- [x] Streaming responses

## Phase 3 — AI Agents

- [x] Tool calling
- [x] Agent decision loop
- [x] Calculator tool
- [x] System tools
- [x] Persistent memory
- [x] SQLite integration
- [x] Local personal AI agent
- [x] Automated unit testing
- [x] Basic security controls

## Phase 4 — Portfolio Projects

### Project 1: Local Personal AI Agent

- [x] Conversational agent
- [x] Tool calling
- [x] Agent decision loop
- [x] Calculator integration
- [x] System tools
- [x] Persistent SQLite memory
- [x] Unit tests

### Project 2: Document Q&A with RAG

- [x] Document ingestion
- [x] Text chunking
- [x] Embedding generation
- [x] SQLite vector storage
- [x] Semantic similarity search
- [x] RAG question answering
- [x] Source citations
- [x] Initial retrieval evaluation
- [x] Answer quality evaluation
- [x] Dedicated RAG unit tests
- [x] Final documentation and testing

### Project 3: AI Automation Agent

- [ ] Define automation use cases
- [ ] Design automation architecture
- [ ] Implement controlled tool execution
- [ ] Integrate external services where appropriate
- [ ] Add task planning and execution
- [ ] Implement logging and error handling
- [ ] Add automated tests

---

# 🎯 Project Goals

The long-term goal is to progress from basic LLM applications toward a more capable local AI system.

```text
LLM API
   ↓
LLM Application
   ↓
Conversational Agent
   ↓
Tool-Using Agent
   ↓
Persistent Memory
   ↓
Retrieval-Augmented Generation
   ↓
AI Automation
   ↓
Integrated Local AI System
```

The development process emphasizes:

- Understanding fundamentals
- Writing Python from scratch
- Testing and evaluation
- Security
- Reproducibility
- Local-first AI
- Clear engineering documentation

---

# 🔭 Future Improvements

Potential improvements for future development include:

### Personal AI Agent

- More specialized tools
- Improved tool error handling
- Better memory retrieval
- More robust agent planning
- Improved conversation management

### RAG System

- Structure-aware and semantic chunking
- Batch embedding generation
- More efficient vector search
- Dedicated vector database experiments
- Retrieval reranking
- Better document metadata handling
- Answer faithfulness evaluation
- Larger and more diverse evaluation datasets
- More comprehensive automated RAG tests

### Overall System

- AI automation workflows
- Improved observability and logging
- Better configuration management
- Web-based user interface
- Integration between agent tools and RAG retrieval

These improvements will be implemented incrementally as part of the learning roadmap.

---

# 📌 Project Status

**Active development / learning project**

Local Hermes AI is continuously evolving as new AI Engineering concepts and projects are implemented.

### Project 1 — Local Personal AI Agent

Implemented with:

- Multi-turn conversation
- LLM tool calling
- Agent decision loop
- Calculator and system tools
- Persistent SQLite memory
- Basic security controls
- Dedicated automated tests

### Project 2 — Document Q&A with RAG

Implemented with:

- Markdown and text document ingestion
- Word-based text chunking
- Ollama embedding generation
- SQLite vector storage
- Cosine similarity retrieval
- Context-grounded question answering
- Source citations
- Retrieval evaluation
- Answer keyword coverage evaluation
- Negative-answer evaluation
- Dedicated RAG unit tests

### Current Verification Results

| Area | Result |
|---|---:|
| Full unit test suite | 110/110 passed (98% coverage) |
| RAG unit tests | 47/47 passed |
| Average Retrieval Precision@3 | 0.92 |
| Average Retrieval Recall@3 | 1.00 |
| Average Answer Keyword Coverage | 0.92 |
| Negative Answer Tests | 2/2 passed |

The next development focus is **Project 3: AI Automation Agent**, while continuing to improve the existing agent and RAG implementations.

### Documentation

For a more detailed learning plan, see [Learning Roadmap](docs/learning-roadmap.md).

For technical architecture details, see [Architecture Documentation](docs/architecture.md).

---

*Built as part of my journey into AI Engineering.*