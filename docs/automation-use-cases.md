# AI Automation Agent — Use Cases

## 1. Project Objective

Build a local AI automation agent that can plan, execute, and monitor multi-step tasks using a controlled set of tools.

The agent must prioritize safety, predictable execution, and traceability.

## 2. Core Use Cases

### Use Case 1: File Automation

**Goal:** Find and summarize local project documents.

Example request:

"Find all Markdown files in the documents directory and summarize them."

Execution steps:
1. List Markdown files in the allowed directory.
2. Read the selected files.
3. Generate summaries.
4. Return the summaries to the user.

Expected result:
- Relevant files are discovered.
- Only permitted files are read.
- The user receives a summary with source filenames.

### Use Case 2: Notes Automation

**Goal:** Save and retrieve personal notes.

Example requests:
- "Save a note about RAG evaluation."
- "Find my notes about AI agents."

Execution steps:
1. Identify the requested note operation.
2. Validate the note content or search query.
3. Save or retrieve notes using SQLite.
4. Return the result.

Expected result:
- Notes persist between sessions.
- Users can retrieve previously saved notes.
- Invalid operations are rejected safely.

### Use Case 3: Multi-Step Task Automation

**Goal:** Execute a task that requires multiple tools.

Example request:

"Read ai-engineering.md, summarize the main concepts, and save the summary as a note."

Execution steps:
1. Read the requested document.
2. Summarize its content.
3. Save the summary as a note.
4. Report the execution result.

Expected result:
- Steps execute in the correct order.
- Each step has a recorded status.
- Failed steps are reported clearly.
- The agent does not claim success when an operation fails.

## 3. Safety Requirements

- Only registered tools can be executed.
- Tool arguments must be validated.
- File operations must remain inside permitted directories.
- Execution must have a maximum step limit.
- Destructive or external actions require explicit user confirmation.
- Tool execution errors must be handled without crashing the agent.

## 4. Initial Scope

Included:
- Local file operations
- SQLite-based notes
- LLM-based task planning
- Sequential task execution
- Execution logging
- Automated tests

Not included in the initial version:
- Unrestricted shell execution
- Autonomous deletion of files
- Sending emails or messages
- Unrestricted internet access
- Background autonomous execution

External service integrations can be added after the local execution engine is stable.

## 5. Success Criteria

The project is considered successful when:

- The agent can interpret the three core use cases.
- The planner produces structured task plans.
- The executor runs only registered tools.
- Tool arguments and execution limits are validated.
- Multi-step tasks produce traceable results.
- Errors are logged and handled safely.
- Automated tests cover normal and failure scenarios.